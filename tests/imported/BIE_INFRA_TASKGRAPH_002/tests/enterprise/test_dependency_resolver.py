
import unittest
from enterprise.dependency_resolver import *
class T(unittest.TestCase):
    def setUp(self):
        self.tasks={"A":{"dependencies":[]},"B":{"dependencies":["A"]},"C":{"dependencies":["A","B"]}}
    def test_missing_none(self): self.assertEqual(missing_dependencies(self.tasks),{})
    def test_missing(self): self.assertEqual(missing_dependencies({"A":{"dependencies":["X"]}}),{"A":["X"]})
    def test_dependents(self): self.assertEqual(dependents(self.tasks)["A"],["B","C"])
    def test_transitive(self): self.assertEqual(transitive_dependencies(self.tasks,"C"),["A","B"])
    def test_topo(self): self.assertEqual(topo_order(self.tasks),["A","B","C"])
    def test_unknown(self):
        with self.assertRaises(DependencyError): transitive_dependencies(self.tasks,"X")
    def test_missing_raises_topo(self):
        with self.assertRaises(DependencyError): topo_order({"A":{"dependencies":["X"]}})
    def test_cycle_raises(self):
        with self.assertRaises(DependencyError): topo_order({"A":{"dependencies":["B"]},"B":{"dependencies":["A"]}})
if __name__=="__main__": unittest.main()
