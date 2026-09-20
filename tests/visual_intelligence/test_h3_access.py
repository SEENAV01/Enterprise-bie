import unittest
from bie.visual_intelligence.accessibility_integration import *
class T(unittest.TestCase):
 def test_font_repair(self): self.assertEqual(integrate_accessibility([AccessibleVisualNode('n','text',font_px=12)]).nodes[0].font_px,18)
 def test_font_block(self): self.assertTrue(integrate_accessibility([AccessibleVisualNode('n','text',font_px=12)],allow_auto_repair=False).blocked)
 def test_contrast(self): self.assertTrue(integrate_accessibility([AccessibleVisualNode('n','text',font_px=20)],contrast_results={'n':False}).blocked)
 def test_color(self): self.assertTrue(integrate_accessibility([AccessibleVisualNode('n','chart',color_category='A')]).blocked)
 def test_alt(self): self.assertTrue(integrate_accessibility([AccessibleVisualNode('n','image',alt_required=True)]).blocked)
 def test_handoff(self): self.assertTrue(assert_accessible_for_handoff(integrate_accessibility([AccessibleVisualNode('n','text',font_px=20)],contrast_results={'n':True})))
