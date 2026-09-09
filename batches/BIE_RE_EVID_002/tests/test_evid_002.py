import unittest
from app.bie.reasoning.evidence_ranking import *
class T(unittest.TestCase):
 def test_rank(self):
  a=RankedEvidence("a",1,1,1);b=RankedEvidence("b",.2,.2,.2);self.assertEqual(rank_evidence([b,a])[0],a)
 def test_tie(self):
  a=RankedEvidence("a",.5,.5,.5);b=RankedEvidence("b",.5,.5,.5);self.assertEqual(rank_evidence([b,a])[0].evidence_id,"a")
 def test_score(self): self.assertAlmostEqual(RankedEvidence("a",1,1,1).score,1)
 def test_bad(self):
  with self.assertRaises(ValueError):rank_evidence([RankedEvidence("a",2,1,1)])
if __name__=="__main__":unittest.main()
