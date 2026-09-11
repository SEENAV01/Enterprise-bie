import unittest
from bie.reasoning.downstream_impact_paths import DependencyEdge, downstream_impact_paths

class TestImpactPaths(unittest.TestCase):
    def test_paths_and_provenance(self):
        r=downstream_impact_paths(["a","b","c"],[
          DependencyEdge("a","b",("e1",)),DependencyEdge("b","c",("e2",))],"a")
        c=[x for x in r if x.target=="c"][0]
        self.assertEqual(c.nodes,("a","b","c"))
        self.assertEqual(c.evidence_ids,("e1","e2"))

    def test_shortest_deterministic_path(self):
        r=downstream_impact_paths(["a","b","c"],[
          DependencyEdge("a","c"),DependencyEdge("a","b"),DependencyEdge("b","c")],"a")
        c=[x for x in r if x.target=="c"][0]
        self.assertEqual(c.nodes,("a","c"))

    def test_unknown_edge_node_rejected(self):
        with self.assertRaises(ValueError):
            downstream_impact_paths(["a"],[DependencyEdge("a","x")],"a")
