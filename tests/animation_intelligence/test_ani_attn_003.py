import unittest
from bie.animation_intelligence.attention_contracts import *
from bie.animation_intelligence.competing_motion_prevention import *
def w(i,s,e,targets=("a",),exclusive=True):return AttentionWindow(i,targets,s,e,.8,"focus",1,exclusive)
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(prevent_competing_motion(decision_id="d",windows=[w("a",0,100),w("b",100,200)],motion_targets={"a":["x"],"b":["y"]}).status,"PASS")
 def test_block(self):self.assertEqual(prevent_competing_motion(decision_id="d",windows=[w("a",0,150),w("b",100,200)],motion_targets={"a":["x"],"b":["y"]}).status,"BLOCKED")
 def test_single_motion(self):self.assertEqual(prevent_competing_motion(decision_id="d",windows=[w("a",0,150),w("b",100,200)],motion_targets={"a":["x"],"b":["x"]}).status,"PASS")
 def test_nonexclusive(self):self.assertEqual(prevent_competing_motion(decision_id="d",windows=[w("a",0,150,exclusive=False),w("b",100,200,exclusive=False)],motion_targets={"a":["x"],"b":["y"]}).status,"PASS")
 def test_bad_limit(self):
  with self.assertRaises(AttentionError):prevent_competing_motion(decision_id="d",windows=[],motion_targets={},max_simultaneous_motion=0)
 def test_dense(self):self.assertEqual(prevent_competing_motion(decision_id="d",windows=[w(str(i),i*100,(i+1)*100) for i in range(5)],motion_targets={}).status,"REVIEW")
 def test_blocker_name(self):self.assertTrue(prevent_competing_motion(decision_id="d",windows=[w("a",0,150),w("b",100,200)],motion_targets={"a":["x"],"b":["y"]}).blockers[0].startswith("competing_motion"))
 def test_not_accepted(self):self.assertFalse(prevent_competing_motion(decision_id="d",windows=[w("a",0,100)],motion_targets={}).accepted)
