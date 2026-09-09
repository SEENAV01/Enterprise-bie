import unittest
from app.bie.prerequisite_intelligence.bridge_scope import *
class T(unittest.TestCase):
 def test_expand(self):
  r=plan_bridge_scope({"c"},[("a","b"),("b","c")]); self.assertEqual([x.concept for x in r],["a","b","c"])
 def test_limit(self): self.assertNotIn("a",[x.concept for x in plan_bridge_scope({"c"},[("a","b"),("b","c")],1)])
 def test_minutes(self): self.assertEqual(plan_bridge_scope({"a"},[],minutes_per_concept=7)[0].minutes,7)
 def test_invalid(self):
  with self.assertRaises(ValueError): plan_bridge_scope({"a"},[],minutes_per_concept=0)
if __name__=="__main__": unittest.main()
