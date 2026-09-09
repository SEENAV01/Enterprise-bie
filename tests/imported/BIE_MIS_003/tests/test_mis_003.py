import unittest
from bie.misconception_intelligence.misconception_evidence import *
class T(unittest.TestCase):
 def test_combine(self): self.assertEqual(aggregate_misconception_evidence([Evidence("p1",.8,"text"),Evidence("q1",.5,"assessment")]).confidence,.9)
 def test_dedup(self):
  e=Evidence("p",.5,"x"); self.assertEqual(aggregate_misconception_evidence([e,e]).confidence,.5)
 def test_empty(self): self.assertEqual(aggregate_misconception_evidence([]).confidence,0)
 def test_invalid(self):
  with self.assertRaises(ValueError): aggregate_misconception_evidence([Evidence("p",2,"x")])
if __name__=="__main__": unittest.main()
