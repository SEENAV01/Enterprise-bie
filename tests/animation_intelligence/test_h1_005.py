import unittest
from bie.animation_intelligence.continuity_ledger import *
def R(scene="s1",visual="v",frame="xy",start=(0,0),end=(1,0)):return ContinuityRecord(scene,"o",visual,"vector","F",frame,"diagram",start,end)
class T(unittest.TestCase):
 def test_first(self):self.assertTrue(ContinuityLedger().add(R()))
 def test_cont(self):l=ContinuityLedger();l.add(R());self.assertTrue(l.add(R("s2",start=(1,0),end=(2,0))))
 def test_visual(self):
  l=ContinuityLedger();l.add(R())
  with self.assertRaises(ContinuityError):l.add(R("s2",visual="v2",start=(1,0)))
 def test_auth(self):
  l=ContinuityLedger();l.add(R());self.assertTrue(l.add(R("s2",visual="v2",start=(1,0)),[ChangeAuthorization("o","visual_id","v","v2","planned")]))
 def test_position(self):
  l=ContinuityLedger();l.add(R())
  with self.assertRaises(ContinuityError):l.add(R("s2",start=(9,9)))
