import unittest
from bie.visual_intelligence.text_contracts import *
from bie.visual_intelligence.density_control import *
def d(text="abc",box=None,action="show_text"):
 i=TextIntent((text[:1] or "x")+str(len(text)),text or "x","title",("e",),("r",))
 return decision(i,action=action,display_text=text,box=box,rationale=("x",))
class T(unittest.TestCase):
 def test_low(self):self.assertEqual(evaluate_text_density([d("abc")]).level,"low")
 def test_high_chars(self):self.assertIn("character_density_exceeded",evaluate_text_density([d("x"*1000)]).blockers)
 def test_high_items(self):self.assertIn("item_count_exceeded",evaluate_text_density([d(str(i)) for i in range(13)]).blockers)
 def test_area(self):self.assertIn("text_area_exceeded",evaluate_text_density([d("a",Box(0,0,.9,.9))]).blockers)
 def test_action_reduce(self):self.assertEqual(density_action(evaluate_text_density([d("x"*1000)])),"reduce_or_reflow")
 def test_omit_excluded(self):self.assertEqual(evaluate_text_density([d("",action="omit_optional_text")]).text_items,0)
 def test_bad_area(self):
  with self.assertRaises(DensityError):evaluate_text_density([],canvas_area=0)
 def test_bad_threshold(self):
  with self.assertRaises(DensityError):evaluate_text_density([],max_items=0)
 def test_review(self):self.assertTrue(evaluate_text_density([d("abc")]).review_required)
