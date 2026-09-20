import unittest
from bie.visual_intelligence.continuity_ledger import *
class T(unittest.TestCase):
 def test_stable(self):
  l=ContinuityLedger();x=VisualIdentity("e","red","circle","F","xy","vector","main");l.observe("s1",x,("src",));l.observe("s2",x,("src",));self.assertEqual(l.token_for("e").color_token,"red")
 def test_unjustified(self):
  l=ContinuityLedger();l.observe("s1",VisualIdentity("e","red"),("src",))
  with self.assertRaises(ContinuityError):l.observe("s2",VisualIdentity("e","blue"),("src",))
 def test_transition(self):
  l=ContinuityLedger();l.observe("s1",VisualIdentity("e","red"),("src",));l.observe("s2",VisualIdentity("e","blue"),("src",),{"color_token":"state change"});self.assertEqual(len(l.transitions),1)
 def test_requires_evidence(self):
  l=ContinuityLedger();l.observe("s1",VisualIdentity("e","red"),("src",))
  with self.assertRaises(ContinuityError):l.observe("s2",VisualIdentity("e","blue"),(),{"color_token":"state"})
 def test_frame(self):
  l=ContinuityLedger();l.observe("s1",VisualIdentity("e",coordinate_frame="xy"),("src",))
  with self.assertRaises(ContinuityError):l.observe("s2",VisualIdentity("e",coordinate_frame="polar"),("src",))
 def test_fingerprint(self):
  l=ContinuityLedger();l.observe("s1",VisualIdentity("e","red"),("src",));self.assertEqual(l.fingerprint(),l.fingerprint())
