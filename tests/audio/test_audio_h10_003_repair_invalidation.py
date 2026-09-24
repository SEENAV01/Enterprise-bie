import unittest
from bie.audio.common import AudioError
from bie.audio.repair_dispatch import invalidation_plan,validate_invalidation_plan,GRAPH,REQUIRED,CANONICAL_MAIN
from tests.audio.h10_test_support import repair_intent,statuses

class RepairInvalidationTests(unittest.TestCase):
    def setUp(self):self.i=repair_intent();self.s=statuses();self.r=invalidation_plan(self.i,self.s)
    def test_01_canonical_main_bound(self):self.assertEqual(self.r['canonical_main'],CANONICAL_MAIN)
    def test_02_every_graph_node_invalidated(self):self.assertEqual([x['task_id'] for x in self.r['invalidations']],list(REQUIRED))
    def test_03_render_invalidated(self):self.assertIn('RENDER',[x['task_id'] for x in self.r['invalidations']])
    def test_04_comp_generated_source_invalidated(self):self.assertIn('COMP_GENERATED_SOURCE',[x['task_id'] for x in self.r['invalidations']])
    def test_05_original_dir_not_invalidated(self):self.assertNotIn('DIR_NARRATION',[x['task_id'] for x in self.r['invalidations']])
    def test_06_reading_not_mutated(self):self.assertFalse(self.r['reading_mutated']);self.assertFalse(self.r['source_text_mutated'])
    def test_07_repository_not_mutated(self):self.assertFalse(self.r['repository_mutated'])
    def test_08_previous_status_preserved(self):self.assertTrue(all(x['previous_status']=='QA_VERIFIED' for x in self.r['invalidations']))
    def test_09_already_invalidated_fails(self):
        s=dict(self.s);s['AUDIO_SYNC']='INVALIDATED'
        with self.assertRaisesRegex(AudioError,'REPAIR_ALREADY_INVALIDATED'):invalidation_plan(self.i,s)
    def test_10_missing_declared_invalidation_fails(self):
        i=dict(self.i);i['invalidates']=['AUDIO_SYNC']
        with self.assertRaisesRegex(AudioError,'REPAIR_DISPATCH_DECLARATION'):invalidation_plan(i,self.s)
    def test_11_tamper_rejected(self):
        self.r['invalidations'][0]['new_status']='READY'
        with self.assertRaisesRegex(AudioError,'REPAIR_INVALIDATION_RECEIPT_MISMATCH'):validate_invalidation_plan(self.r,self.i,self.s)
    def test_12_no_product_acceptance(self):self.assertFalse(self.r['product_accepted'])
if __name__=='__main__':unittest.main()
