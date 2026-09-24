import json,unittest
from dataclasses import replace
from bie.audio.common import AudioError,fingerprint
from bie.audio.qa_pronunciation import pronunciation_targets,pronunciation_qa,PronunciationObservation
from .qa_test_support import native,reseal

class PronunciationQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,_=native()
    def test_targets_bind_delivered_wav(self):
        ts=pronunciation_targets(self.m,self.s);self.assertTrue(ts)
        self.assertTrue(all(t['media_sha256']==self.m.clock()['output_audio_sha256'] for t in ts))
    def test_source_readings_unchanged(self):
        ts=pronunciation_targets(self.m,self.s)
        self.assertEqual([t['expected_spoken'] for t in ts],[sp.spoken for s in self.s.plan.segments for sp in s.spans])
    def test_rule_ids_and_spans_retained(self):
        ts=pronunciation_targets(self.m,self.s)
        self.assertEqual([(t['start'],t['end'],t['rule_fingerprint']) for t in ts],[(sp.start,sp.end,sp.rule_fingerprint) for s in self.s.plan.segments for sp in s.spans])
    def test_no_listening_self_pass(self):
        r=pronunciation_qa(self.m,self.s);self.assertEqual(r.status,'REVIEW');self.assertFalse(json.loads(r.metrics_json)['pronunciation_verified'])
    def test_formant_voice_flagged(self):self.assertIn('TECHNICAL_VOICE_NOT_CINEMATIC',[f.code for f in pronunciation_qa(self.m,self.s).findings])
    def observation(self,**kw):
        t=pronunciation_targets(self.m,self.s)[0];values=dict(target_fingerprint=t['target_fingerprint'],media_sha256=t['media_sha256'],observed_text=t['expected_spoken'],verdict='MATCH',method='human_reported',reviewer_id='synthetic-reviewer',evidence_refs=('synthetic:test-observation',));values.update(kw);return PronunciationObservation(**values)
    def test_reported_match_does_not_prove_phonetics(self):self.assertEqual(pronunciation_qa(self.m,self.s,(self.observation(),)).status,'REVIEW')
    def test_reported_mismatch_fails(self):self.assertEqual(pronunciation_qa(self.m,self.s,(self.observation(verdict='MISMATCH'),)).status,'FAIL')
    def test_asr_match_not_listening_acceptance(self):self.assertEqual(pronunciation_qa(self.m,self.s,(self.observation(method='asr_reported'),)).status,'REVIEW')
    def test_unknown_observation_rejected(self):
        with self.assertRaises(AudioError):pronunciation_qa(self.m,self.s,(self.observation(target_fingerprint=fingerprint('different')),))
    def test_wrong_audio_observation_rejected(self):
        with self.assertRaises(AudioError):pronunciation_qa(self.m,self.s,(self.observation(media_sha256='0'*64),))
    def test_duplicate_observation_rejected(self):
        o=self.observation()
        with self.assertRaises(AudioError):pronunciation_qa(self.m,self.s,(o,o))
    def test_invalid_method(self):
        with self.assertRaises(AudioError):self.observation(method='automatically-certified')
    def test_blank_evidence(self):
        with self.assertRaises(AudioError):self.observation(evidence_refs=())
    def test_bool_verdict_rejected(self):
        with self.assertRaises(AudioError):self.observation(verdict=True)
    def test_observation_collection_exact(self):
        with self.assertRaises(AudioError):pronunciation_qa(self.m,self.s,[self.observation()])
    def test_modified_clock_rejected(self):
        c=self.m.clock();c['words'][0]['spoken']='not source'
        with self.assertRaises(AudioError):pronunciation_qa(reseal(self.m,c),self.s)
    def test_hindi_unicode_targets(self):
        s,m,_=native(language='hindi');ts=pronunciation_targets(m,s);self.assertTrue(any(any(ord(ch)>127 for ch in t['expected_spoken']) for t in ts))
    def test_inputs_not_mutated(self):
        before=self.m.receipt_json,fingerprint(self.s.receipt());pronunciation_qa(self.m,self.s);self.assertEqual(before,(self.m.receipt_json,fingerprint(self.s.receipt())))
