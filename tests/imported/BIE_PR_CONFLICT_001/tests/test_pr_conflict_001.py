import unittest
from bie.prerequisite_intelligence.conflict_arbitration import *
class T(unittest.TestCase):
 def test_accept(self): self.assertTrue(arbitrate([EvidenceVote("text",True,1),EvidenceVote("model",False,.2)]).accepted)
 def test_reject(self): self.assertFalse(arbitrate([EvidenceVote("text",False,1)]).accepted)
 def test_conflict(self): self.assertEqual(arbitrate([EvidenceVote("a",True,1),EvidenceVote("b",False,1)]).status,"unresolved_conflict")
 def test_empty(self): self.assertEqual(arbitrate([]).status,"insufficient_evidence")
if __name__=="__main__": unittest.main()
