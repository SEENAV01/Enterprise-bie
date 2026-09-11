import unittest
from bie.reasoning.temporal_hypothesis_reconciliation import *

class TestTemporalHypothesisReconciliation(unittest.TestCase):
    def h(self, i, c, rel="before"):
        return TemporalHypothesis(i, rel, c, ("ev-"+i,))

    def test_empty_abstains(self):
        r=reconcile_temporal_hypotheses([])
        self.assertEqual(r.status,"INSUFFICIENT_EVIDENCE")
        self.assertTrue(r.requires_review)

    def test_single_resolves(self):
        r=reconcile_temporal_hypotheses([self.h("a",.7)])
        self.assertEqual(r.preferred_id,"a")

    def test_clear_margin_resolves(self):
        r=reconcile_temporal_hypotheses([self.h("a",.9),self.h("b",.6)])
        self.assertEqual(r.preferred_id,"a")

    def test_close_candidates_preserved(self):
        r=reconcile_temporal_hypotheses([self.h("a",.8),self.h("b",.72)])
        self.assertEqual(r.status,"AMBIGUOUS")
        self.assertIsNone(r.preferred_id)
        self.assertEqual(len(r.hypotheses),2)

    def test_deterministic_tie_order(self):
        r=reconcile_temporal_hypotheses([self.h("b",.8),self.h("a",.8)])
        self.assertEqual([x.hypothesis_id for x in r.hypotheses],["a","b"])

    def test_bad_confidence_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_temporal_hypotheses([self.h("a",1.1)])

    def test_negative_margin_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_temporal_hypotheses([self.h("a",.5)],preference_margin=-.1)

if __name__=="__main__":
    unittest.main()
