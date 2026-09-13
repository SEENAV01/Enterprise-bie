import unittest
from bie.pedagogy.uncertainty_aware_mastery import *
class T(unittest.TestCase):
 def o(self,i,s,r=1,a=0): return MasteryObservation(i,"c",s,r,a,(i,))
 def test_conflict_review(self):
  r=infer_knowledge_state("c",[self.o("a",.1),self.o("b",.9)]); self.assertTrue(r.conflict and r.requires_review)
 def test_consistency_confidence(self):
  a=infer_knowledge_state("c",[self.o("a",.8),self.o("b",.82)])
  b=infer_knowledge_state("c",[self.o("a",.1),self.o("b",.9)])
  self.assertGreater(a.confidence,b.confidence)
 def test_no_evidence(self):
  r=infer_knowledge_state("c",[]); self.assertTrue(r.requires_review); self.assertEqual(r.confidence,0)
 def test_deterministic(self):
  a=infer_knowledge_state("c",[self.o("b",.8),self.o("a",.7)])
  b=infer_knowledge_state("c",[self.o("a",.7),self.o("b",.8)])
  self.assertEqual(a.fingerprint(),b.fingerprint())
