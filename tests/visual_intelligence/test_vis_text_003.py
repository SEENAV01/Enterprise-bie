import unittest
from bie.visual_intelligence.text_contracts import *
from bie.visual_intelligence.label_placement import *
def i():return TextIntent("l","Force","label",("e",),("r",))
def a(side="right"):return LabelAnchor("v",Box(.3,.3,.2,.2),side)
class T(unittest.TestCase):
 def test_place(self):self.assertEqual(place_label(i(),a()).action,"place_label")
 def test_right(self):self.assertEqual(place_label(i(),a()).style["side"],"right")
 def test_fallback_side(self):
  d=place_label(i(),LabelAnchor("v",Box(.85,.3,.1,.2),"right"));self.assertNotEqual(d.style["side"],"right")
 def test_collision_avoid(self):
  occ=(Box(.515,.36,.18,.08),);d=place_label(i(),a(),occupied=occ);self.assertNotEqual(d.style["side"],"right")
 def test_bad_role(self):
  with self.assertRaises(TextVisualValidationError):place_label(TextIntent("x","x","title",("e",),("r",)),a())
 def test_bad_side(self):
  with self.assertRaises(PlacementError):place_label(i(),a("diagonal"))
 def test_bad_geometry(self):
  with self.assertRaises(PlacementError):place_label(i(),a(),label_width=0)
 def test_escalate(self):
  d=place_label(i(),LabelAnchor("v",Box(0,0,1,1),"right"),label_width=.8,label_height=.8);self.assertEqual(d.action,"escalate_label_placement")
 def test_not_accepted(self):self.assertFalse(place_label(i(),a()).accepted)
