import unittest
from bie.visual_intelligence.layout_qa import *
def e(i,x,y,w=.2,h=.2,req=True,role="diagram"): return LayoutElement(i,role,Box(x,y,w,h),req)
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(evaluate_layout_qa([e("a",.1,.1),e("b",.6,.6)],["e"],["r"]).passed)
 def test_collision(self): self.assertIn("required_collisions",evaluate_layout_qa([e("a",.1,.1),e("b",.2,.2)],["e"],["r"]).blockers)
 def test_safe(self): self.assertIn("outside_safe_area",evaluate_layout_qa([e("a",0,0)],["e"],["r"]).blockers)
 def test_small(self): self.assertIn("below_min_area",evaluate_layout_qa([e("a",.1,.1,.02,.02)],["e"],["r"]).blockers)
 def test_subtitle(self): self.assertIn("subtitle_conflict",evaluate_layout_qa([e("a",.1,.8,.2,.1)],["e"],["r"],subtitle_zone=Box(0,.75,1,.2)).blockers)
 def test_dup(self):
  with self.assertRaises(LayoutQAError): evaluate_layout_qa([e("a",.1,.1),e("a",.6,.6)],["e"],["r"])
 def test_not_accepted(self): self.assertFalse(evaluate_layout_qa([e("a",.1,.1)],["e"],["r"]).accepted)
