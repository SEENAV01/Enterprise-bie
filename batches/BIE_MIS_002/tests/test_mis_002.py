import unittest
from app.bie.misconception_intelligence.likely_misconceptions import *
class T(unittest.TestCase):
 def test_infer(self):
  r=infer_likely_misconceptions("velocity",{"direction","magnitude"},{"speed-only":{"magnitude","scalar"}}); self.assertEqual(len(r),1)
 def test_no_overlap(self): self.assertEqual(infer_likely_misconceptions("x",{"a"},{"bad":{"b"}}),[])
 def test_no_conflict(self): self.assertEqual(infer_likely_misconceptions("x",{"a"},{"same":{"a"}}),[])
 def test_invalid(self):
  with self.assertRaises(ValueError): infer_likely_misconceptions("",{"a"},{})
if __name__=="__main__": unittest.main()
