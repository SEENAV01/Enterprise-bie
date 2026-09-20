import unittest
from bie.visual_intelligence.text_contracts import *
from bie.visual_intelligence.annotation_placement import *
def i():return TextIntent("a","Important","annotation",("e",),("r",))
def t():return AnnotationTarget("target",Box(.3,.3,.2,.2))
class T(unittest.TestCase):
 def test_place(self):self.assertEqual(place_annotation(i(),t()).action,"place_annotation")
 def test_leader(self):self.assertTrue(place_annotation(i(),t()).style["leader_line"])
 def test_target(self):self.assertEqual(place_annotation(i(),t()).style["target_id"],"target")
 def test_collision_choice(self):
  occ=(Box(.52,.52,.25,.12),);d=place_annotation(i(),t(),occupied=occ);self.assertNotEqual(d.style["placement"],"bottom_right")
 def test_bad_role(self):
  with self.assertRaises(TextVisualValidationError):place_annotation(TextIntent("x","x","title",("e",),("r",)),t())
 def test_bad_geom(self):
  with self.assertRaises(PlacementError):place_annotation(i(),t(),width=0)
 def test_escalate(self):
  d=place_annotation(i(),AnnotationTarget("t",Box(0,0,1,1)),width=.9,height=.9);self.assertEqual(d.action,"escalate_annotation_placement")
 def test_review(self):self.assertTrue(place_annotation(i(),t()).review_required)
 def test_not_accepted(self):self.assertFalse(place_annotation(i(),t()).accepted)
