import unittest
from bie.prerequisite_intelligence.evidence import *
class T(unittest.TestCase):
 def test_aggregate(self):
  s=aggregate_evidence([Evidence("p1","explicit",.8),Evidence("p2","semantic",.5)])
  self.assertEqual(s.confidence,.9); self.assertEqual(s.source_count,2)
 def test_dedup(self):
  e=Evidence("p1","x",.5); self.assertEqual(aggregate_evidence([e,e]).confidence,.5)
 def test_empty(self): self.assertEqual(aggregate_evidence([]).confidence,0)
 def test_invalid(self):
  with self.assertRaises(ValueError): Evidence("p","x",1.1)
if __name__=="__main__": unittest.main()
