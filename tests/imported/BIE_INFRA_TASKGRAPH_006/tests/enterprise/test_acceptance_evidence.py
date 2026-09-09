
import unittest
from bie.infrastructure.acceptance_evidence import *
class T(unittest.TestCase):
 def setUp(self): self.b=AcceptanceBinder([Criterion("c1","tests",("unit","integration"))])
 def ev(self,t,p=True): return Evidence("r"+t,t,p,"abc")
 def test_no_evidence_fails(self): self.assertFalse(self.b.evaluate()["accepted"])
 def test_partial_fails(self): self.b.bind("c1",self.ev("unit")); self.assertFalse(self.b.evaluate()["accepted"])
 def test_complete_passes(self):
  self.b.bind("c1",self.ev("unit")); self.b.bind("c1",self.ev("integration")); self.assertTrue(self.b.evaluate()["accepted"])
 def test_failed_evidence_not_counted(self):
  self.b.bind("c1",self.ev("unit",False)); self.b.bind("c1",self.ev("integration")); self.assertFalse(self.b.evaluate()["accepted"])
 def test_unknown_criterion(self):
  with self.assertRaises(AcceptanceError): self.b.bind("x",self.ev("unit"))
 def test_hash_required(self):
  with self.assertRaises(AcceptanceError): self.b.bind("c1",Evidence("r","unit",True,""))
 def test_failure_details(self): self.assertEqual(self.b.evaluate()["failures"]["c1"],["integration","unit"])
if __name__=="__main__": unittest.main()
