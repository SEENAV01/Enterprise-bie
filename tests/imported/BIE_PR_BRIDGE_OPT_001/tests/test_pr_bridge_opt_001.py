import unittest
from bie.prerequisite_intelligence.bridge_optimizer import *
class T(unittest.TestCase):
 def test_chain(self): self.assertEqual([x.concept for x in optimize_bridge({"c"},[("a","b"),("b","c")],set(),{})],["a","b","c"])
 def test_known(self): self.assertEqual([x.concept for x in optimize_bridge({"c"},[("a","b"),("b","c")],{"b"}, {})],["c"])
 def test_minutes(self): self.assertEqual(optimize_bridge({"a"},[],set(),{"a":2})[0].minutes,2)
 def test_cycle(self):
  with self.assertRaises(ValueError): optimize_bridge({"a"},[("a","b"),("b","a")],set(),{})
if __name__=="__main__": unittest.main()
