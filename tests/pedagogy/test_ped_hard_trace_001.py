import unittest
from bie.pedagogy.pedagogy_provenance import build_lineage,validate_lineage_graph

class TestPedagogyProvenance(unittest.TestCase):
    def test_upstream_lineage_required(self):
        with self.assertRaises(ValueError):
            build_lineage("p",source_evidence_ids=["e"],reasoning_parent_ids=[])

    def test_low_confidence_requires_review(self):
        with self.assertRaises(ValueError):
            build_lineage("p",source_evidence_ids=["e"],reasoning_parent_ids=["r"],confidence=.5)

    def test_internal_cycle_detected(self):
        a=build_lineage("a",source_evidence_ids=["e"],reasoning_parent_ids=["b"])
        b=build_lineage("b",source_evidence_ids=["e"],reasoning_parent_ids=["a"])
        self.assertTrue(validate_lineage_graph([a,b]))
