from h5_helpers import *
from bie.qa.media_runtime_v2.speech import *
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
import hmac
class Speech(Case):
    def seed(self,edit=None):
        p=SpeechPolicy('en','diagnostic-voice',(('w2',('two',)),));b=bind(p)
        vals=(np.sin(np.arange(16000)*0.31)*5000).astype('<i2')
        a=ref(self.root,'voice.wav',wav(vals),'voice');t=ref(self.root,'text.txt',b'one two','text')
        c=ref(self.root,'captions.srt',b'1\n00:00:00,000 --> 00:00:02,000\none two\n','captions')
        data=dict(schema_version='bie.qa.acoustic-observations/1',binding=asdict(b),audio_sha256=a.sha256,transcript_sha256=t.sha256,language='en',voice_id=p.voice_id,basis='SYNTHETIC',assessor_id='assessor',model_version='1',issued_at=NOW-10,expires_at=NOW+20,
          segments=[dict(word_id='w1',char_start=0,char_end=3,start_sample=0,end_sample=8000,heard_form='one',verdict='VERIFIED'),dict(word_id='w2',char_start=4,char_end=7,start_sample=8000,end_sample=16000,heard_form='two',verdict='VERIFIED')])
        if edit:edit(data)
        ar=save(self.root,'acoustic.json',data,'acoustic');return a,t,c,ar,b,p,data
    def run_case(self,edit=None):
        a,t,c,ar,b,p,d=self.seed(edit);return inspect_speech(self.root,a,t,c,ar,b,p,now=NOW)
    def test_synthetic_positive_is_review(self):
        r=self.run_case();self.assertTrue(r['technical_checks_clear']);self.assertIn('H5_ACOUSTIC_INDEPENDENT_EVIDENCE_REQUIRED',codes(r));self.unchanged(r)
    def test_engine_clock_not_phonetic(self):self.assertIn('H5_ACOUSTIC_INDEPENDENT_EVIDENCE_REQUIRED',codes(self.run_case(lambda d:d.update(basis='ENGINE_TIMESTAMP'))))
    def test_asr_transcript_not_phonetic(self):self.assertIn('H5_ACOUSTIC_INDEPENDENT_EVIDENCE_REQUIRED',codes(self.run_case(lambda d:d.update(basis='ASR_TRANSCRIPT'))))
    def test_unverified_independent_claim_is_review(self):
        r=self.run_case(lambda d:d.update(basis='INDEPENDENT_FORCED_ALIGNMENT'));self.assertFalse(r['details']['independent_acoustic_evidence_authenticated'])
    def test_wrong_pronunciation_form(self):self.has(self.run_case(lambda d:d['segments'][1].update(heard_form='three')),'H5_PRONUNCIATION_FORM')
    def test_rejected_occurrence(self):self.has(self.run_case(lambda d:d['segments'][1].update(verdict='REJECTED')),'H5_PRONUNCIATION_REJECTED')
    def test_uncertain_occurrence(self):self.assertIn('H5_PRONUNCIATION_UNCERTAIN',codes(self.run_case(lambda d:d['segments'][1].update(verdict='UNCERTAIN'))))
    def test_omitted_word(self):
        with self.assertRaisesRegex(ContractError,'H5_PRONUNCIATION_OCCURRENCE_MISSING'):self.run_case(lambda d:d['segments'].pop())
    def test_missing_first_word_coverage(self):self.has(self.run_case(lambda d:d['segments'].pop(0)),'H5_ACOUSTIC_WORD_COVERAGE')
    def test_duplicate_word(self):
        with self.assertRaisesRegex(ContractError,'H5_WORD_DUPLICATE'):self.run_case(lambda d:d['segments'].append(d['segments'][0]))
    def test_future_record(self):
        with self.assertRaisesRegex(ContractError,'H5_ACOUSTIC_FRESHNESS'):self.run_case(lambda d:d.update(issued_at=NOW+1))
    def test_expired_record(self):
        with self.assertRaisesRegex(ContractError,'H5_ACOUSTIC_FRESHNESS'):self.run_case(lambda d:d.update(expires_at=NOW))
    def test_wrong_voice(self):
        with self.assertRaisesRegex(ContractError,'H5_ACOUSTIC_IDENTITY'):self.run_case(lambda d:d.update(voice_id='another'))
    def test_foreign_candidate(self):
        with self.assertRaisesRegex(ContractError,'NATIVE_BINDING_MISMATCH'):self.run_case(lambda d:d['binding'].update(candidate_digest='d'*64))
    def test_word_window_order(self):
        with self.assertRaisesRegex(ContractError,'H5_WORD_ORDER'):self.run_case(lambda d:d['segments'][1].update(start_sample=1))
    def test_delayed_captions(self):
        a,t,c,ar,b,p,d=self.seed();c=ref(self.root,c.path,b'1\n00:00:00,400 --> 00:00:02,400\none two\n','captions');self.has(inspect_speech(self.root,a,t,c,ar,b,p,now=NOW),'H5_CAPTION_ACOUSTIC_OFFSET')
    def test_wrong_caption_words(self):
        a,t,c,ar,b,p,d=self.seed();c=ref(self.root,c.path,b'1\n00:00:00,000 --> 00:00:02,000\none three\n','captions');self.has(inspect_speech(self.root,a,t,c,ar,b,p,now=NOW),'H5_CAPTION_TRANSCRIPT')
    def test_changed_wav_bytes(self):
        a,t,c,ar,b,p,d=self.seed();(self.root/a.path).write_bytes(b'bad')
        with self.assertRaises(ContractError):inspect_speech(self.root,a,t,c,ar,b,p,now=NOW)
    def test_silent_audio(self):
        a,t,c,ar,b,p,d=self.seed();a=ref(self.root,a.path,wav(np.zeros(16000)),'voice');d['audio_sha256']=a.sha256;ar=save(self.root,ar.path,d,'acoustic');self.has(inspect_speech(self.root,a,t,c,ar,b,p,now=NOW),'H5_SPEECH_SILENT')
    def test_clipped_audio(self):
        a,t,c,ar,b,p,d=self.seed();a=ref(self.root,a.path,wav(np.full(16000,32767)),'voice');d['audio_sha256']=a.sha256;ar=save(self.root,ar.path,d,'acoustic');self.has(inspect_speech(self.root,a,t,c,ar,b,p,now=NOW),'H5_SPEECH_CLIPPING')
    def test_bad_signature(self):
        a,t,c,ar,b,p,d=self.seed();r=inspect_speech(self.root,a,t,c,ar,b,p,now=NOW)
        from bie.qa.reasoning_v2.attestation import Review
        # Malformed supplied authority cannot be accepted as no review.
        with self.assertRaises((ContractError,TypeError,AttributeError)):inspect_speech(self.root,a,t,c,ar,b,p,now=NOW,review={'verdict':'VERIFIED'})
class Offset(Case):
    def signals(self):
        rng=np.random.default_rng(77);env=np.repeat(rng.integers(0,20,size=200),80);s=(np.sin(np.arange(16000)*.41)*env*500).astype('<i2');return s
    def test_offset_from_actual_samples(self):
        a=self.signals();b=np.concatenate([np.zeros(800,dtype='<i2'),a]);r=waveform_offset(wav(a),wav(b));self.assertEqual(r['status'],'ESTIMATE');self.assertEqual(r['offset_samples'],800);self.assertFalse(r['phonetic_alignment_proven'])
    def test_constant_ambiguous_signal_abstains(self):
        x=np.full(16000,1000);self.assertEqual(waveform_offset(wav(x),wav(x))['status'],'AMBIGUOUS')
    def test_silence_has_no_offset(self):
        with self.assertRaisesRegex(ContractError,'H5_WAVEFORM_NO_SIGNAL'):waveform_offset(wav(np.zeros(16000)),wav(np.zeros(16000)))
    def test_different_sample_rates_rejected(self):
        with self.assertRaisesRegex(ContractError,'H5_WAVEFORM_PROFILE'):waveform_offset(wav(self.signals(),8000),wav(self.signals(),16000))
    def test_correlation_duration_limit(self):
        with self.assertRaisesRegex(ContractError,'H5_CORRELATION_DURATION_BUDGET'):waveform_offset(wav(np.ones(248000)),wav(np.ones(248000)))

class Authentication(Case):
    def seeded(self):
        # Reuse fixture constructor only, not inherited test methods.
        return Speech.seed(self,lambda d:d.update(basis='HUMAN_LISTENING'))
    def authorize(self,edit=None,key_edit=None):
        a,t,c,ar,b,p,d=self.seeded();base=inspect_speech(self.root,a,t,c,ar,b,p,now=NOW)
        k=ReviewKey('synthetic-key',b'SYNTHETIC_TEST_KEY_NEVER_PRODUCTION_0123','assessor','1','test-group',('support',),'operator_managed')
        r=Review('synthetic-review',base['details']['request_digest'],b.policy_digest,a.artifact_id,'support','VERIFIED',tuple(x.artifact_id for x in (a,t,c,ar)),1000000,'SYNTHETIC authorization fixture','assessor','1',NOW-1,NOW+60,k.key_id)
        if edit:r=replace(r,**edit)
        r=replace(r,signature=hmac.new(k.secret,r.signing_bytes(),hashlib.sha256).hexdigest())
        if key_edit:k=replace(k,**key_edit)
        return inspect_speech(self.root,a,t,c,ar,b,p,now=NOW,review=r,verifier=ReviewVerifier((k,)))
    def test_valid_scoped_signature_authenticates_not_truth(self):
        r=self.authorize();self.assertTrue(r['details']['independent_acoustic_evidence_authenticated']);self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.unchanged(r)
    def test_test_only_credentials_cannot_claim_independent_evidence(self):
        self.assertFalse(self.authorize(key_edit={'assurance':'test_only'})['details']['independent_acoustic_evidence_authenticated'])
    def test_revoked_key_rejected(self):self.has(self.authorize(key_edit={'enabled':False}),'H5_ACOUSTIC_REVIEW_INVALID')
    def test_wrong_purpose_rejected(self):self.has(self.authorize(edit={'purpose':'teaching'}),'H5_ACOUSTIC_REVIEW_INVALID')
    def test_wrong_signed_artifact_inventory_rejected(self):self.has(self.authorize(edit={'evidence_ids':('voice',)}),'H5_ACOUSTIC_REVIEW_INVALID')
    def test_wrong_signed_binding_rejected(self):self.has(self.authorize(edit={'request_digest':'b'*64}),'H5_ACOUSTIC_REVIEW_INVALID')
    def test_signed_rejection_preserved(self):self.has(self.authorize(edit={'verdict':'REJECTED'}),'H5_ACOUSTIC_REVIEW_INVALID')
