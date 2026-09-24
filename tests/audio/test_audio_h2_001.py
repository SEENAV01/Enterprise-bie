import unittest,io,wave
from dataclasses import replace
from bie.audio.common import AudioError,fingerprint
from bie.audio.acoustic_contract import AcousticPolicy,build_job,validate_job,pcm_info,english_tokens,edit_distance
from .acoustic_test_support import context,clone,rehash

class AcousticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,cls.j,*_=context()
    def test_current_mix_builds_exact_job(self):self.assertEqual(build_job(self.m,self.s),self.j)
    def test_job_binds_current_media(self):self.assertEqual(self.j['binding']['media_sha256'],self.m.clock()['output_audio_sha256'])
    def test_source_spans_preserved(self):self.assertEqual([x['spoken_text'] for x in self.j['segments']],[s.spoken_text for s in self.s.plan.segments])
    def test_voice_and_request_identity(self):self.assertEqual([x['request_fingerprint'] for x in self.j['segments']],[a.request.fingerprint() for a in self.s.assets])
    def test_dry_source_signal_is_measured(self):self.assertTrue(all(x['dry_source_has_signal'] for x in self.j['segments']))
    def test_inputs_unchanged(self):
        b=(self.m.wav_bytes,self.m.clock_json,self.s.receipt());build_job(self.m,self.s);self.assertEqual(b,(self.m.wav_bytes,self.m.clock_json,self.s.receipt()))
    def bad(self,mutate,reseal=True):
        j=clone(self.j);mutate(j)
        if reseal:rehash(j)
        with self.assertRaises((AudioError,TypeError)):validate_job(j,self.m.wav_bytes)
    def test_unknown_job_field(self):self.bad(lambda j:j.update(extra=True))
    def test_missing_source_binding(self):self.bad(lambda j:j['binding'].pop('plan_fingerprint'))
    def test_wrong_media(self):self.bad(lambda j:j['binding'].update(media_sha256='0'*64))
    def test_duplicate_segment(self):self.bad(lambda j:j['segments'].__setitem__(1,clone(j['segments'][0])))
    def test_changed_prepared_text(self):self.bad(lambda j:j['segments'][0].update(spoken_text='invented'))
    def test_missing_source_refs(self):self.bad(lambda j:j['segments'][0]['source_spans'][0].update(source_refs=[]))
    def test_invalid_source_offset(self):self.bad(lambda j:j['segments'][0]['source_spans'][0].update(end=999999))
    def test_same_engine_producer_rejected(self):self.bad(lambda j:j['segments'][0].update(producer_id='pocketsphinx-producer'))
    def test_word_changed(self):self.bad(lambda j:j['segments'][0]['provider_words'][0].update(spoken='invented'))
    def test_word_zero_window(self):self.bad(lambda j:j['segments'][0]['provider_words'][0].update(end_sample=j['segments'][0]['provider_words'][0]['start_sample']))
    def test_outside_crop(self):self.bad(lambda j:j['segments'][0].update(end_sample=j['binding']['frames']+1))
    def test_bad_hash_without_reseal(self):self.bad(lambda j:j.update(fingerprint=fingerprint('tamper')),False)
    def test_bool_clock_rejected(self):self.bad(lambda j:j['binding'].update(sample_rate=True))
    def test_dry_source_bool_exact(self):self.bad(lambda j:j['segments'][0].update(dry_source_has_signal=1))
    def test_policy_bounds(self):
        for kw in ({'deadline_seconds':0},{'max_segments':True},{'max_phone_edit_percent':101},{'disagreement_ms':0}):
            with self.subTest(kw=kw),self.assertRaises(AudioError):AcousticPolicy(**kw)
    def test_policy_change_invalidates_identity(self):self.assertNotEqual(build_job(self.m,self.s,AcousticPolicy(revision='changed'))['fingerprint'],self.j['fingerprint'])
    def test_trailing_wav_bytes_rejected(self):
        with self.assertRaises(AudioError):pcm_info(self.m.wav_bytes+b'extra',AcousticPolicy())
    def test_non_pcm16_rejected(self):
        b=io.BytesIO()
        with wave.open(b,'wb') as w:w.setnchannels(1);w.setframerate(16000);w.setsampwidth(1);w.writeframes(bytes(100))
        with self.assertRaises(AudioError):pcm_info(b.getvalue(),AcousticPolicy())
    def test_analysis_tokens_keep_codepoint_offsets(self):
        self.assertEqual(english_tokens("The cat's mat.")[1],{'word':"cat's",'spoken_start':4,'spoken_end':9})
    def test_no_silent_symbol_or_hindi_drop(self):
        for value in ('hello 123','नमस्ते','force = mass','cost $ ten'):
            with self.subTest(value=value),self.assertRaises(AudioError):english_tokens(value)
    def test_edit_distance_repeated_words(self):self.assertEqual(edit_distance(['the','the'],['the']),1)
    def test_segment_budget_rejected_not_truncated(self):
        with self.assertRaises(AudioError):build_job(self.m,self.s,AcousticPolicy(max_segments=1))
