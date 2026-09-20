import unittest
from bie.visual_intelligence.vis_section_gate import *
from bie.visual_intelligence.canonical_dir_codec import *
from bie.visual_intelligence.rep_original_codec import EXPECTED_REP_ARCHIVE_SHA256
class T(unittest.TestCase):
 def good(self,dirv=True,repv=True,fail=0):return GateEvidence(CANONICAL_DIR_COMMIT,CANONICAL_DIR_TREE,dirv,{k:repv for k in EXPECTED_REP_ARCHIVE_SHA256},500,fail,0,0)
 def test_current_block(self):self.assertEqual(evaluate_section_exit(self.good(False,False)).status,'BLOCKED')
 def test_dir(self):self.assertIn('canonical_dir_source_not_executed',evaluate_section_exit(self.good(False,True)).blockers)
 def test_rep(self):self.assertIn('original_rep_archives_not_all_byte_verified',evaluate_section_exit(self.good(True,False)).blockers)
 def test_clean_logic(self):self.assertTrue(evaluate_section_exit(self.good(True,True)).implementation_scope_complete)
 def test_regression(self):self.assertIn('local_regression_not_clean',evaluate_section_exit(self.good(True,True,1)).blockers)
