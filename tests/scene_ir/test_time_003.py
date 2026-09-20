import unittest
from bie.scene_ir.event_timeline import *
class T(unittest.TestCase):
 def test_sort(self):self.assertEqual([x.event_id for x in build_event_timeline([TimelineEvent("b",10,"x",("e",)),TimelineEvent("a",0,"x",("e",))],100)],["a","b"])
 def test_outside(self):
  with self.assertRaises(TemporalIRError):build_event_timeline([TimelineEvent("a",101,"x",("e",))],100)
 def test_dup(self):
  with self.assertRaises(TemporalIRError):build_event_timeline([TimelineEvent("a",0,"x",("e",)),TimelineEvent("a",1,"x",("e",))],100)
 def test_target(self):
  with self.assertRaises(TemporalIRError):TimelineEvent("a",0,"x",())
 def test_payload(self):self.assertEqual(TimelineEvent("a",0,"x",("e",),{"k":1}).payload["k"],1)
