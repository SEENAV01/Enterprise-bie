import unittest
from bie.reasoning.transitive_invalidation import DecisionDependency, propagate_invalidation

class TestTransitiveInvalidation(unittest.TestCase):
    def test_changed_evidence_propagates(self):
        r=propagate_invalidation(
          {"d1":["e1"],"d2":["e2"],"d3":[]},
          [DecisionDependency("d1","d2"),DecisionDependency("d2","d3")],["e1"])
        self.assertEqual({x.decision_id for x in r},{"d1","d2","d3"})
        self.assertEqual([x for x in r if x.decision_id=="d3"][0].propagation_path,("d1","d2","d3"))

    def test_unrelated_decision_stays_valid(self):
        r=propagate_invalidation({"a":["e1"],"b":["e2"]},[],["e1"])
        self.assertEqual([x.decision_id for x in r],["a"])

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):
            propagate_invalidation({"a":[]},[DecisionDependency("a","b")],[])
