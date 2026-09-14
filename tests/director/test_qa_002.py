import unittest
from dataclasses import replace
from bie.director.qa_contract import SourceCatalog, bind_span
from bie.director.source_grounding_qa import SourceBytes, source_grounding_qa, validate_grounding_report
from qa_fixtures import case, codes


class GroundingTests(unittest.TestCase):
    def artifacts(self, c, media="text/plain; charset=utf-8"):
        return tuple(SourceBytes(s, data, media) for s, data in c.source_data)

    def test_actual_text_bytes_exact_page_and_quote_pass_scoped_grounding(self):
        c = case(); r = source_grounding_qa(c.snapshot, c.claims, c.catalog, self.artifacts(c))
        self.assertEqual(r.status, "CHECKS_PASSED"); self.assertFalse(r.accepted)
        self.assertEqual(dict(r.measurements)["source_artifacts_checked"], 1)

    def test_missing_actual_bytes_block(self):
        c = case(); self.assertIn("SOURCE_BYTES_MISSING", codes(source_grounding_qa(c.snapshot, c.claims, c.catalog)))

    def test_changed_source_bytes_block(self):
        c = case(); a = SourceBytes("source1", b"changed content", "text/plain; charset=utf-8")
        self.assertIn("SOURCE_HASH_MISMATCH", codes(source_grounding_qa(c.snapshot, c.claims, c.catalog, (a,))))

    def test_pdf_hash_is_not_extraction_accuracy(self):
        c = case(); r = source_grounding_qa(c.snapshot, c.claims, c.catalog, self.artifacts(c, "application/pdf"))
        self.assertIn("EXTRACTION_ACCURACY_UNVERIFIED", codes(r)); self.assertEqual(r.status, "REVIEW_REQUIRED")

    def test_changed_extraction_same_source_hash_block(self):
        c = case(); p = replace(c.catalog.pages[0], text="A wrong extraction.")
        e = replace(c.catalog.passages[0], page_fingerprint=p.fingerprint(), end_char=len(p.text), quote=p.text)
        r = source_grounding_qa(c.snapshot, c.claims, SourceCatalog((p,), (e,)), self.artifacts(c))
        self.assertIn("TEXT_EXTRACTION_MISMATCH", codes(r))

    def test_edited_quote_and_stale_page_reference_rejected(self):
        c = case()
        for e in (replace(c.catalog.passages[0], quote="An invented quote."),
                  replace(c.catalog.passages[0], page_fingerprint="sha256:"+"0"*64)):
            with self.assertRaises(ValueError): source_grounding_qa(c.snapshot, c.claims, replace(c.catalog, passages=(e,)), self.artifacts(c))

    def test_partial_valid_citations_do_not_hide_missing_reference(self):
        c = case(); claim = replace(c.claims[0], evidence_ids=("e1", "missing"))
        r = source_grounding_qa(c.snapshot, (claim,), c.catalog, self.artifacts(c))
        self.assertIn("CITATION_UNRESOLVED", codes(r)); self.assertEqual(r.status, "BLOCKED")

    def test_citation_presence_without_claim_span_is_not_coverage(self):
        c = case(); r = source_grounding_qa(c.snapshot, (), c.catalog, self.artifacts(c))
        self.assertTrue({"GROUNDING_COVERAGE_GAP", "UNASSIGNED_DRAFT_CITATION"} <= codes(r))

    def test_overlapping_spans_do_not_inflate_grounding(self):
        c = case(); claim = replace(c.claims[0], span=bind_span(c.snapshot, "u1", 0, 10))
        r = source_grounding_qa(c.snapshot, (claim, replace(claim, claim_id="c2")), c.catalog, self.artifacts(c))
        self.assertEqual(dict(r.measurements)["covered_words"], 2); self.assertEqual(r.status, "BLOCKED")

    def test_unknown_draft_reference_blocks_even_if_claims_are_retagged(self):
        c = case(); empty = SourceCatalog((), ())
        r = source_grounding_qa(c.snapshot, c.claims, empty)
        self.assertIn("DRAFT_CITATION_UNRESOLVED", codes(r))

    def test_duplicate_pages_mixed_revisions_and_bool_page_rejected(self):
        c = case(); p = c.catalog.pages[0]
        for pages in ((p, replace(p, page_id="p2")), (p, replace(p, page_id="p2", page_number=2, source_sha256="sha256:"+"0"*64)), (replace(p, page_number=True),)):
            with self.assertRaises(ValueError): source_grounding_qa(c.snapshot, c.claims, replace(c.catalog, pages=pages))

    def test_duplicate_empty_and_mutable_artifact_bytes_rejected(self):
        c = case(); a = self.artifacts(c)
        for artifacts in (a*2, (replace(a[0], data=b""),), (replace(a[0], data=bytearray(b"x")),)):
            with self.assertRaises(ValueError): source_grounding_qa(c.snapshot, c.claims, c.catalog, artifacts)

    def test_grounding_report_binds_actual_bytes(self):
        c = case(); a = self.artifacts(c); r = source_grounding_qa(c.snapshot, c.claims, c.catalog, a)
        self.assertEqual(validate_grounding_report(r, c.snapshot, c.claims, c.catalog, a), r)
        with self.assertRaises(ValueError): validate_grounding_report(r, c.snapshot, c.claims, c.catalog, (replace(a[0], data=b"changed"),))

    def test_unicode_text_uses_character_spans_and_actual_utf8_hash(self):
        c = case(("पानी ठंडा है।",), language="hi")
        self.assertEqual(source_grounding_qa(c.snapshot, c.claims, c.catalog, self.artifacts(c)).status, "CHECKS_PASSED")
