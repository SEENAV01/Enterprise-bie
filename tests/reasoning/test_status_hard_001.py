import unittest
from bie.reasoning.reasoning_status_semantics import normalize_status,aggregate_status

class TestReasoningStatus(unittest.TestCase):
    def test_resolved_releasable(self):
        self.assertTrue(normalize_status("RESOLVED").releasable)
    def test_conflict_dominates(self):
        r=aggregate_status("RESOLVED","AMBIGUOUS","CONFLICT")
        self.assertEqual(r.status,"CONFLICT"); self.assertTrue(r.requires_review)
    def test_empty_is_insufficient(self):
        self.assertEqual(aggregate_status().status,"INSUFFICIENT_EVIDENCE")
