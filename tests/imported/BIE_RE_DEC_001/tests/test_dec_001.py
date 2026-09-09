import unittest
from app.bie.reasoning.decision_factory import *
class T(unittest.TestCase):
 def test_make(self): self.assertEqual(make_decision("d1","causal","A→B",["e1"],.9,"supported").choice,"A→B")
 def test_no_evidence(self):
  with self.assertRaises(ValueError):make_decision("d","causal","x",[],.9,"r")
 def test_abstain(self): self.assertTrue(make_decision("d","causal",None,[],.2,"uncertain",True).abstained)
 def test_type(self):
  with self.assertRaises(ValueError):make_decision("d","magic","x",["e"],1,"r")
if __name__=="__main__":unittest.main()
