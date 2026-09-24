import unittest,tempfile,json,base64,hashlib
from dataclasses import replace
from bie.audio.common import AudioError,fingerprint
from bie.audio.neural_transport import HTTPReply
from bie.audio.neural_store import canonical
from bie.audio.neural_response import decode_response,bind_neural_alignment
from bie.audio.tts_generation import generate_speech
from bie.audio.pcm_audio import validate_wav
from bie.audio.sync_contract import validate_alignment
from tests.audio.neural_test_support import setup,plan,wire_response

class ResponseTests(unittest.TestCase):
    def setUp(self):
        from tests.audio.neural_test_support import enter_fixture_scope;enter_fixture_scope(self);
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.plan,self.pr,self.requests,self.t=setup(self.tmp.name);self.r=self.requests[0]
    def decode(self,row=None):return decode_response(HTTPReply(200,canonical(row or wire_response(self.r.segment.spoken_text)),'fixture','CONTRACT_FIXTURE'),self.r,max_bytes=7500000)
    def test_pcm_lossless_wrap(self):
        row=wire_response(self.r.segment.spoken_text);d=self.decode(row);_,pcm=validate_wav(d.wav_bytes,self.r.settings.format)
        self.assertEqual(pcm,base64.b64decode(row['audio_base64']))
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(AudioError):decode_response(HTTPReply(200,b'{"x":1,"x":2}','x'),self.r,max_bytes=7500000)
    def test_unknown_response_shape(self):
        row=wire_response(self.r.segment.spoken_text);row['accepted']=True
        with self.assertRaisesRegex(AudioError,'SCHEMA'):self.decode(row)
    def test_invalid_base64(self):
        row=wire_response(self.r.segment.spoken_text);row['audio_base64']='###'
        with self.assertRaisesRegex(AudioError,'ENCODING'):self.decode(row)
    def test_odd_pcm_bytes(self):
        row=wire_response(self.r.segment.spoken_text);row['audio_base64']=base64.b64encode(b'abc').decode()
        with self.assertRaisesRegex(AudioError,'PCM_LAYOUT'):self.decode(row)
    def test_silent_pcm_rejected(self):
        row=wire_response(self.r.segment.spoken_text);row['audio_base64']=base64.b64encode(bytes(48000)).decode()
        with self.assertRaisesRegex(AudioError,'EMPTY_AUDIO'):self.decode(row)
    def test_alignment_required(self):
        row=wire_response(self.r.segment.spoken_text);row['alignment']=None
        with self.assertRaisesRegex(AudioError,'ALIGNMENT'):self.decode(row)
    def test_normalized_text_cannot_change_reading(self):
        row=wire_response(self.r.segment.spoken_text);row['normalized_alignment']['characters'][0]='Z'
        with self.assertRaisesRegex(AudioError,'TEXT_NORMALIZED'):self.decode(row)
    def test_optional_normalized_null(self):
        row=wire_response(self.r.segment.spoken_text);row['normalized_alignment']=None;self.decode(row)
    def test_missing_last_char_detected(self):
        row=wire_response(self.r.segment.spoken_text);row['alignment']['characters'].pop()
        with self.assertRaisesRegex(AudioError,'CHARACTER_COUNT'):self.decode(row)
    def test_nonfinite_timing(self):
        for v in [True,-1,float('nan'),float('inf')]:
            row=wire_response(self.r.segment.spoken_text);row['alignment']['character_start_times_seconds'][0]=v
            with self.subTest(v=v),self.assertRaises((AudioError,ValueError)):self.decode(row)
    def test_time_outside_waveform(self):
        row=wire_response(self.r.segment.spoken_text);row['alignment']['character_end_times_seconds'][-1]=100
        with self.assertRaisesRegex(AudioError,'AUDIO_BOUNDS'):self.decode(row)
    def test_reverse_char_intervals(self):
        row=wire_response(self.r.segment.spoken_text);row['alignment']['character_start_times_seconds'][1]=.4
        with self.assertRaisesRegex(AudioError,'TIME_ORDER'):self.decode(row)
    def test_no_uniform_word_guess_when_zero_duration(self):
        row=wire_response(self.r.segment.spoken_text)
        for key in ('character_start_times_seconds','character_end_times_seconds'):row['alignment'][key]=[0]*len(self.r.segment.spoken_text)
        self.t.mutation=lambda _:row
        with self.assertRaisesRegex(AudioError,'WORD_TIME_RANGE'):generate_speech(self.r,self.pr)
        self.assertEqual(list(self.pr.store.entries.iterdir()),[])
    def test_exact_pause_and_source_bound_words(self):
        p,pr,rr,_=setup(self.tmp.name,p=plan(pause=300));asset=generate_speech(rr[0],pr);a,e=pr.alignment_for(asset)
        self.assertEqual(a.pause_samples,7200);self.assertEqual(a.provider_samples+a.pause_samples,asset.info.samples_per_channel)
        self.assertEqual(a.words[0].source[0].original,'First');self.assertFalse(e['acoustic_alignment_verified']);validate_alignment(asset,a)
    def test_fixture_basis_is_never_live_provider_basis(self):
        a=generate_speech(self.r,self.pr);t,e=self.pr.alignment_for(a)
        self.assertEqual(t.basis,'NEURAL_CHARACTER_FIXTURE_SAME_PCM');self.assertEqual(e['scope'],'CONTRACT_FIXTURE')
    def test_stale_waveform_rejected(self):
        asset=generate_speech(self.r,self.pr)
        with self.assertRaisesRegex(AudioError,'WAVEFORM_MISMATCH'):self.pr.alignment_for(replace(asset,provider_audio_sha256='0'*64))
    def test_stale_invocation_rejected(self):
        asset=generate_speech(self.r,self.pr)
        with self.assertRaisesRegex(AudioError,'INVOCATION'):self.pr.alignment_for(replace(asset,invocation_id='different'))
    def test_hindi_combining_codepoints_preserved(self):
        p,pr,rr,_=setup(self.tmp.name,p=plan('यह एक परीक्षण है।',language='hi'));asset=generate_speech(rr[0],pr);a,_=pr.alignment_for(asset)
        self.assertEqual(tuple(w.spoken for w in a.words),('यह','एक','परीक्षण','है।'))
    def test_same_response_identity(self):
        asset=generate_speech(self.r,self.pr);a,e=self.pr.alignment_for(asset);self.assertEqual(e['request_fingerprint'],self.r.fingerprint());self.assertEqual(a.media_sha256,asset.info.sha256)

    def test_fixture_cannot_pass_default_measured_gate(self):
        from bie.audio.fixture_scope import synthetic_timing_scope
        a=generate_speech(self.r,self.pr);alignment,_=self.pr.alignment_for(a)
        with synthetic_timing_scope(enabled=False):
            with self.assertRaisesRegex(AudioError,'DIAGNOSTIC_OPT_IN_REQUIRED'):validate_alignment(a,alignment)
    def test_fixture_cannot_masquerade_as_live_timing(self):
        a=generate_speech(self.r,self.pr);alignment,_=self.pr.alignment_for(a)
        with self.assertRaisesRegex(AudioError,'PROVIDER_IDENTITY_MISMATCH'):
            validate_alignment(a,replace(alignment,basis='ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE'))
