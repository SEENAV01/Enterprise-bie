import unittest
from app.bie.prerequisite_intelligence.depth import *
class T(unittest.TestCase):
 def test_chain(self): self.assertEqual(prerequisite_depth({"a","b","c"},[("a","b"),("b","c")])["c"],2)
 def test_multi_parent(self):
  d=prerequisite_depth({"a","b","c"},[("a","c"),("b","c")]); self.assertEqual(d["c"],1)
 def test_cycle(self):
  with self.assertRaises(ValueError): prerequisite_depth({"a","b"},[("a","b"),("b","a")])
 def test_isolated(self): self.assertEqual(prerequisite_depth({"a"},[])["a"],0)
if __name__=="__main__": unittest.main()
