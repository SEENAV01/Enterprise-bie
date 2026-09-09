import unittest
from bie.prerequisite_intelligence.e2e_acceptance import *
class T(unittest.TestCase):
 def test_all(self):
  gs=[Gate(n,True,"artifact") for n in REQUIRED];self.assertTrue(assess(gs).accepted)
 def test_missing(self): self.assertFalse(assess([]).accepted)
 def test_failed(self):
  gs=[Gate(n,n!="necessity","e") for n in REQUIRED];self.assertIn("necessity",assess(gs).blockers)
 def test_no_evidence(self):
  gs=[Gate(n,True,"e") for n in REQUIRED];gs[0]=Gate(REQUIRED[0],True,"");self.assertFalse(assess(gs).accepted)
if __name__=="__main__": unittest.main()
