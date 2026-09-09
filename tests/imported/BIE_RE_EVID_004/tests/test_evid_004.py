import unittest
from app.bie.reasoning.evidence_arbitration import *
class T(unittest.TestCase):
 def test_win(self): self.assertEqual(arbitrate([Candidate("a",1,1,1),Candidate("b",.2,.2,.2)]).winner,"a")
 def test_abstain(self): self.assertTrue(arbitrate([Candidate("a",.5,.5,.5)]).abstained)
 def test_tie(self): self.assertTrue(arbitrate([Candidate("a",.9,.9,.9),Candidate("b",.9,.9,.9)]).abstained)
 def test_empty(self): self.assertTrue(arbitrate([]).abstained)
if __name__=="__main__":unittest.main()
