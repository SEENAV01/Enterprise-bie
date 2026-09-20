import unittest
from bie.visual_intelligence.access_contracts import *
from bie.visual_intelligence.readable_size import *
def i(role="body"):return VisualAccessIntent("i",role,("e",),("r",))
class T(unittest.TestCase):
 def test_body_pass(self): self.assertEqual(evaluate_readable_size(i(),font_px=24,viewport_width_px=1280).action,"readable_size_pass")
 def test_body_fail(self): self.assertEqual(evaluate_readable_size(i(),font_px=14,viewport_width_px=1280).action,"increase_text_size")
 def test_title_floor(self): self.assertEqual(evaluate_readable_size(i("title"),font_px=40,viewport_width_px=1280).payload["role_min_px"],36)
 def test_scale(self): self.assertTrue(evaluate_readable_size(i(),font_px=18,viewport_width_px=1280,viewing_scale=1.5).payload["passes"])
 def test_dense_floor(self): self.assertEqual(evaluate_readable_size(i("caption"),font_px=16,viewport_width_px=800,dense_mode=True).payload["role_min_px"],16)
 def test_bad_px(self):
  with self.assertRaises(ReadabilityError): evaluate_readable_size(i(),font_px=0,viewport_width_px=800)
 def test_bad_view(self):
  with self.assertRaises(ReadabilityError): evaluate_readable_size(i(),font_px=20,viewport_width_px=100)
 def test_warning(self): self.assertIn("below_role_minimum",evaluate_readable_size(i(),font_px=10,viewport_width_px=1920).warnings)
 def test_review(self): self.assertTrue(evaluate_readable_size(i(),font_px=24,viewport_width_px=1280).review_required)
