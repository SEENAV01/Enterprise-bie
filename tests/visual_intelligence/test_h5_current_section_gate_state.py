import unittest
from bie.visual_intelligence.vis_section_gate import GateEvidence,evaluate_section_exit
from bie.visual_intelligence.canonical_dir_codec import CANONICAL_DIR_COMMIT,CANONICAL_DIR_TREE
from bie.visual_intelligence.rep_original_codec import EXPECTED_REP_ARCHIVE_SHA256
class T(unittest.TestCase):
 def test_rep_blocker_closed_but_dir_blocker_remains(self):
  e=GateEvidence(CANONICAL_DIR_COMMIT,CANONICAL_DIR_TREE,False,{k:True for k in EXPECTED_REP_ARCHIVE_SHA256},1,0,0,0)
  r=evaluate_section_exit(e)
  self.assertEqual(r.status,"BLOCKED")
  self.assertIn("canonical_dir_source_not_executed",r.blockers)
  self.assertNotIn("original_rep_archives_not_all_byte_verified",r.blockers)
