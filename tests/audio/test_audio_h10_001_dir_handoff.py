import unittest
from dataclasses import replace
from bie.audio.common import AudioError
from bie.audio.dir_audio_handoff import bind_dir_utterances,validate_dir_audio_handoff
from tests.audio.h10_test_support import baseline

class DirAudioHandoffTests(unittest.TestCase):
    def setUp(self):self.files,self.bundle,self.plan,self.utts=baseline()
    def test_01_exact_binding_passes(self):self.assertEqual(bind_dir_utterances(self.utts,self.plan)['schema_version'],'bie.audio.dir-audio-handoff/1')
    def test_02_utterance_fingerprint_is_exact(self):self.assertEqual(bind_dir_utterances(self.utts,self.plan)['utterances'][0]['utterance_fingerprint'],self.plan.segments[0].utterance_fingerprint)
    def test_03_script_fingerprint_preserved(self):self.assertEqual(bind_dir_utterances(self.utts,self.plan)['utterances'][0]['script_fingerprint'],self.utts[0].script_fingerprint)
    def test_04_source_refs_preserved(self):self.assertEqual(bind_dir_utterances(self.utts,self.plan)['utterances'][0]['source_refs'],list(self.utts[0].evidence_ids))
    def test_05_objectives_preserved(self):self.assertEqual(set(bind_dir_utterances(self.utts,self.plan)['utterances'][0]['objective_ids']),set(self.utts[0].objective_ids))
    def test_06_text_mutation_rejected(self):
        with self.assertRaisesRegex(AudioError,'DIR_AUDIO_SOURCE_RANGE|DIR_AUDIO_TEXT_MISMATCH|DIR_AUDIO_BINDING_MISMATCH'):bind_dir_utterances((replace(self.utts[0],text='changed'),),self.plan)
    def test_07_voice_mutation_rejected(self):
        with self.assertRaisesRegex(AudioError,'DIR_AUDIO_BINDING_MISMATCH'):bind_dir_utterances((replace(self.utts[0],voice_id='voice:other'),),self.plan)
    def test_08_source_mutation_rejected(self):
        with self.assertRaisesRegex(AudioError,'DIR_AUDIO_SOURCE_REFS_MISMATCH|DIR_AUDIO_BINDING_MISMATCH'):bind_dir_utterances((replace(self.utts[0],evidence_ids=('other',)),),self.plan)
    def test_09_review_blocks(self):
        with self.assertRaisesRegex(AudioError,'DIR_AUDIO_UPSTREAM_REVIEW'):bind_dir_utterances((replace(self.utts[0],review_reasons=('review',)),),self.plan)
    def test_10_coverage_required(self):
        with self.assertRaisesRegex(AudioError,'DIR_AUDIO_UTTERANCES_REQUIRED|DIR_AUDIO_COVERAGE'):bind_dir_utterances((),self.plan)
    def test_11_receipt_tamper_rejected(self):
        r=bind_dir_utterances(self.utts,self.plan);r['source_text_mutated']=True
        with self.assertRaisesRegex(AudioError,'DIR_AUDIO_RECEIPT_MISMATCH'):validate_dir_audio_handoff(r,self.utts,self.plan)
    def test_12_never_accepts_product(self):self.assertFalse(bind_dir_utterances(self.utts,self.plan)['product_accepted'])
if __name__=='__main__':unittest.main()
