
import unittest
from bie.infrastructure.cycle_detector import *
class T(unittest.TestCase):
    def test_acyclic(self): self.assertEqual(find_cycles({"A":{"dependencies":[]},"B":{"dependencies":["A"]}}),[])
    def test_self_cycle(self): self.assertTrue(find_cycles({"A":{"dependencies":["A"]}}))
    def test_two_cycle(self): self.assertTrue(find_cycles({"A":{"dependencies":["B"]},"B":{"dependencies":["A"]}}))
    def test_three_cycle(self): self.assertTrue(find_cycles({"A":{"dependencies":["B"]},"B":{"dependencies":["C"]},"C":{"dependencies":["A"]}}))
    def test_assert(self):
        with self.assertRaises(CycleError): assert_acyclic({"A":{"dependencies":["A"]}})
    def test_assert_valid(self): self.assertTrue(assert_acyclic({"A":{"dependencies":[]}}))
    def test_missing_dependency_ignored_here(self): self.assertEqual(find_cycles({"A":{"dependencies":["X"]}}),[])
if __name__=="__main__": unittest.main()
