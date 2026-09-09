import unittest
from bie.math_intelligence.solver_adapter import *
class Fake:
 def solve(self,r):return SolverResult("x=2",True,"fake-cas","deterministic-test")
class Bad:
 def solve(self,r):return SolverResult("x=2",True,"","")
class T(unittest.TestCase):
 def test_contract(self): self.assertTrue(governed_solve(Fake(),SolverRequest("solve","x+1=3")).verified)
 def test_block(self):
  with self.assertRaises(ValueError):governed_solve(Fake(),SolverRequest("execute","x"))
 def test_empty(self):
  with self.assertRaises(ValueError):governed_solve(Fake(),SolverRequest("solve",""))
 def test_provenance(self):
  with self.assertRaises(ValueError):governed_solve(Bad(),SolverRequest("solve","x=1"))
if __name__=="__main__":unittest.main()
