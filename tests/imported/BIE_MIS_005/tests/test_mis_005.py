import unittest
from app.bie.misconception_intelligence.concept_mapping import *
class T(unittest.TestCase):
 def test_map(self):
  r=map_misconception("m",{"mass","weight"},{"mass-v-weight":{"mass","weight"},"force":{"force"}}); self.assertEqual(r[0].concept,"mass-v-weight")
 def test_threshold(self): self.assertEqual(map_misconception("m",{"a"},{"x":{"a","b"}},.8),[])
 def test_empty(self): self.assertEqual(map_misconception("m",set(),{"x":set()}),[])
 def test_tie(self): self.assertEqual([x.concept for x in map_misconception("m",{"a"},{"b":{"a"},"a":{"a"}})],["a","b"])
if __name__=="__main__": unittest.main()
