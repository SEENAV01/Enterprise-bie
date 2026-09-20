import unittest
from bie.animation_intelligence.ani_qa_repair_contract import *
class T(unittest.TestCase):
 def test_make(self):self.assertEqual(make_repair_instruction("r","q",("t",),"EASE","change_duration","timing",("src",),"fits cue").owner_stage,"EASE")
 def test_wrong_action(self):
  with self.assertRaises(QARepairError):make_repair_instruction("r","q",("t",),"EASE","repair_identity","x",("s",),"ok")
 def test_unknown_owner(self):
  with self.assertRaises(QARepairError):make_repair_instruction("r","q",("t",),"X","x","x",("s",),"ok")
 def test_empirical_auto(self):
  with self.assertRaises(QARepairError):make_repair_instruction("r","q",("t",),"QA","recompute_qa","empirical_render_fail",("s",),"pass",True)
 def test_closure(self):self.assertTrue(validate_repair_closure(make_repair_instruction("r","q",("t",),"TIMELINE","shift_track","overlap",("s",),"no overlap"),True,"PASS"))
 def test_closure_fail(self):
  with self.assertRaises(QARepairError):validate_repair_closure(make_repair_instruction("r","q",("t",),"TIMELINE","shift_track","overlap",("s",),"no overlap"),False,"PASS")
 def test_qa_still_blocked(self):
  with self.assertRaises(QARepairError):validate_repair_closure(make_repair_instruction("r","q",("t",),"TIMELINE","shift_track","overlap",("s",),"no overlap"),True,"BLOCKED")
 def test_not_accepted(self):self.assertFalse(make_repair_instruction("r","q",("t",),"EASE","change_duration","timing",("s",),"ok").accepted)
