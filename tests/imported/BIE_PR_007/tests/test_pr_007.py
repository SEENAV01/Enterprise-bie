import unittest
from bie.prerequisite_intelligence.transitive_reduction import *
class T(unittest.TestCase):
 def test_reduce(self):
  r=transitive_reduction(["a","b","c"],[("a","b"),("b","c"),("a","c")])
  self.assertEqual(r,[("a","b"),("b","c")])
 def test_keep_chain(self): self.assertEqual(len(transitive_reduction(["a","b"],[("a","b")])),1)
 def test_unknown(self):
  with self.assertRaises(ValueError): transitive_reduction(["a"],[("a","b")])
 def test_self(self):
  with self.assertRaises(ValueError): transitive_reduction(["a"],[("a","a")])
if __name__=="__main__": unittest.main()
