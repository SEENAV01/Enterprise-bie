
import unittest
from enterprise.event_stream import *
class T(unittest.TestCase):
 def test_publish(self):self.assertEqual(EventStream().publish("r","stage",{}).seq,1)
 def test_seq(self):
  s=EventStream();s.publish("r","a",{});self.assertEqual(s.publish("r","b",{}).seq,2)
 def test_since(self):
  s=EventStream();s.publish("r","a",{});s.publish("r","b",{});self.assertEqual(len(s.since(1)),1)
 def test_filter(self):
  s=EventStream();s.publish("r","a",{});s.publish("x","a",{});self.assertEqual(len(s.since(0,"r")),1)
 def test_required(self):
  with self.assertRaises(EventStreamError):EventStream().publish("","a",{})
 def test_bound(self):
  s=EventStream(1);s.publish("r","a",{});s.publish("r","b",{});self.assertEqual(len(s.events),1)
if __name__=="__main__":unittest.main()
