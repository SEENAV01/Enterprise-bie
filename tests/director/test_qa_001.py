import unittest
from dataclasses import replace
from bie.director.qa_contract import (bind_span, snapshot_script, fingerprint,
    validate_snapshot, ScriptClaim)
from bie.director.factual_script_qa import (factual_qa, FactualPolicy,
    SemanticReceipt, validate_factual_report)
from qa_fixtures import case, codes


class FactualTests(unittest.TestCase):
    def receipt(self, c, verdict="SUPPORTED", **kwargs):
        return SemanticReceipt(c.claims[0].claim_id, fingerprint(c.claims[0]),
            tuple(p.fingerprint() for p in c.catalog.passages), verdict,
            "fixture-evaluator", "1", kwargs.get("confidence", .95), "Controlled fixture assessment")

    def test_quote_equality_still_needs_contextual_support(self):
        c = case(); r = factual_qa(c.snapshot, c.claims, c.catalog)
        self.assertIn("EXACT_SOURCE_TEXT", codes(r))
        self.assertIn("SEMANTIC_SUPPORT_UNASSESSED", codes(r))
        self.assertEqual(r.status, "REVIEW_REQUIRED"); self.assertFalse(r.accepted)

    def test_receipt_only_passes_explicit_policy_scope(self):
        c = case(); receipt = self.receipt(c)
        r = factual_qa(c.snapshot, c.claims, c.catalog, (receipt,), FactualPolicy(trusted_evaluators=("fixture-evaluator@1",)))
        self.assertEqual(r.status, "CHECKS_PASSED"); self.assertFalse(r.accepted)

    def test_untrusted_and_low_confidence_and_uncertain_need_review(self):
        c = case()
        for receipt, policy in ((self.receipt(c), FactualPolicy()),
            (self.receipt(c, confidence=.4), FactualPolicy(trusted_evaluators=("fixture-evaluator@1",))),
            (self.receipt(c, verdict="UNCERTAIN"), FactualPolicy(trusted_evaluators=("fixture-evaluator@1",)))):
            with self.subTest(receipt=receipt):
                self.assertIn("SEMANTIC_RECEIPT_REVIEW", codes(factual_qa(c.snapshot, c.claims, c.catalog, (receipt,), policy)))

    def test_keywords_are_not_entailment(self):
        c = case(("A triangle never has three straight sides.",), ("A triangle has three straight sides.",))
        r = factual_qa(c.snapshot, c.claims, c.catalog)
        self.assertNotIn("EXACT_SOURCE_TEXT", codes(r)); self.assertEqual(r.status, "REVIEW_REQUIRED")

    def test_numeric_conflict_cannot_be_overridden_by_supported_receipt(self):
        c = case(("The measured length is 15 cm.",), ("The measured length is 12 cm.",))
        r = factual_qa(c.snapshot, c.claims, c.catalog, (self.receipt(c),), FactualPolicy(trusted_evaluators=("fixture-evaluator@1",)))
        self.assertIn("SOURCE_NUMERIC_CONFLICT", codes(r)); self.assertEqual(r.status, "BLOCKED")

    def test_any_reported_contradiction_blocks(self):
        c = case(); r = factual_qa(c.snapshot, c.claims, c.catalog, (self.receipt(c, "CONTRADICTED"),))
        self.assertIn("REPORTED_CONTRADICTION", codes(r)); self.assertEqual(r.status, "BLOCKED")

    def test_claim_coverage_is_word_union_not_sum(self):
        c = case(); span = bind_span(c.snapshot, "u1", 0, 10)
        claims = (replace(c.claims[0], span=span), replace(c.claims[0], claim_id="overlap", span=span))
        r = factual_qa(c.snapshot, claims, c.catalog)
        self.assertIn("UNCLASSIFIED_NARRATION", codes(r)); self.assertEqual(dict(r.measurements)["covered_words"], 2)

    def test_empty_claims_block_even_with_cited_draft(self):
        c = case(); self.assertEqual(factual_qa(c.snapshot, (), c.catalog).status, "BLOCKED")

    def test_nonfact_labels_cannot_bypass_review(self):
        c = case()
        for kind in ("INSTRUCTION", "QUESTION", "OTHER"):
            r = factual_qa(c.snapshot, (replace(c.claims[0], kind=kind),), c.catalog)
            self.assertIn("NONFACT_LABEL_REQUIRES_REVIEW", codes(r))

    def test_missing_and_out_of_lineage_citation(self):
        c = case(); claim = replace(c.claims[0], evidence_ids=("missing",))
        r = factual_qa(c.snapshot, (claim,), c.catalog)
        self.assertTrue({"MISSING_FACTUAL_EVIDENCE", "EVIDENCE_OUTSIDE_SCRIPT"} <= codes(r))

    def test_receipt_must_bind_exact_claim_and_source(self):
        c = case(); receipt = self.receipt(c)
        for bad in (replace(receipt, claim_fingerprint="sha256:"+"0"*64), replace(receipt, passage_fingerprints=())):
            with self.assertRaises(ValueError): factual_qa(c.snapshot, c.claims, c.catalog, (bad,))

    def test_immutable_snapshot_and_boolean_span_validation(self):
        c = case()
        with self.assertRaises(ValueError): snapshot_script(c.snapshot.script, list(c.snapshot.drafts), c.snapshot.segment_order)
        with self.assertRaises(ValueError): bind_span(c.snapshot, "u1", True, 10)
        with self.assertRaises(ValueError): bind_span(c.snapshot, "u1", 0, 5)

    def test_modified_snapshot_and_old_span_rejected(self):
        c = case(); u = c.snapshot.utterances[0]
        with self.assertRaises(ValueError): validate_snapshot(replace(c.snapshot, utterances=(replace(u, text="A different fact."),)))
        other = case(("A rectangle has four straight sides.",))
        with self.assertRaises(ValueError): factual_qa(other.snapshot, c.claims, c.catalog)

    def test_upstream_review_survives_receipt(self):
        c = case(); d = replace(c.snapshot.drafts[0], requires_review=True, unsupported_claims=("withheld fact",))
        s = snapshot_script(c.snapshot.script, (d,), ("u1",))
        claim = replace(c.claims[0], span=bind_span(s, "u1"))
        r = factual_qa(s, (claim,), c.catalog)
        self.assertTrue({"UPSTREAM_REVIEW", "UNSUPPORTED_CLAIMS_WITHHELD"} <= codes(r))

    def test_report_replay_detects_tampered_findings_or_policy(self):
        c = case(); r = factual_qa(c.snapshot, c.claims, c.catalog)
        self.assertEqual(validate_factual_report(r, c.snapshot, c.claims, c.catalog), r)
        with self.assertRaises(ValueError): validate_factual_report(replace(r, findings=()), c.snapshot, c.claims, c.catalog)
        with self.assertRaises(ValueError): validate_factual_report(r, c.snapshot, c.claims, c.catalog, policy=FactualPolicy(version="2"))

    def test_duplicate_claim_nan_confidence_and_blank_legacy_ids_rejected(self):
        c = case()
        with self.assertRaises(ValueError): factual_qa(c.snapshot, c.claims*2, c.catalog)
        with self.assertRaises(ValueError): factual_qa(c.snapshot, c.claims, c.catalog, (self.receipt(c, confidence=float("nan")),))
        bad = replace(c.snapshot.script, segments=(replace(c.snapshot.script.segments[0], segment_id=" "),))
        with self.assertRaises(ValueError): snapshot_script(bad, c.snapshot.drafts, (" ",))
