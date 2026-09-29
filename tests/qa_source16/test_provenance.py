from dataclasses import replace
from source_helpers import *

class ProvenanceTests(FixtureCase):
    def test_actual_utf8_source_and_citation_checks_pass(self):
        result=self.check();self.assertEqual(result.provenance.status,'CHECKS_PASSED')
        self.assertEqual(result.grounding.status,'REVIEW_REQUIRED')
        self.assertEqual(dict(result.provenance.measurements)['citations_resolved'],1)
    def test_same_size_source_byte_tamper_rejected(self):
        (self.root/'inputs/source.txt').write_text(TEXT.replace('5','9'))
        self.blocked(self.request,'ARTIFACT_HASH_MISMATCH')
    def test_same_size_output_tamper_rejected(self):
        (self.root/'surfaces/narration.txt').write_text(TEXT.replace('5','9'))
        self.blocked(self.request,'ARTIFACT_HASH_MISMATCH')
    def test_missing_source_rejected(self):
        (self.root/'inputs/source.txt').unlink();self.blocked(self.request,'ARTIFACT_OPEN_OR_READ_FAILED')
    def test_missing_output_rejected(self):
        (self.root/'surfaces/narration.txt').unlink();self.blocked(self.request,'ARTIFACT_OPEN_OR_READ_FAILED')
    def test_forged_block_text_rejected_even_with_updated_digest(self):
        b=replace(self.request.blocks[0],text=TEXT.replace('5','9'))
        c=replace(self.request.citations[0],block_digest=b.content_digest,quote=b.text)
        self.blocked(replace(self.request,blocks=(b,),citations=(c,)),'UTF8_EXTRACTION_MISMATCH')
    def test_stale_citation_block_hash_rejected(self):
        c=replace(self.request.citations[0],block_digest='0'*64)
        self.blocked(replace(self.request,citations=(c,)),'CITATION_BLOCK_MISMATCH')
    def test_fabricated_quote_rejected(self):
        c=replace(self.request.citations[0],quote=TEXT.replace('5','9'))
        self.blocked(replace(self.request,citations=(c,)),'CITATION_QUOTE_MISMATCH')
    def test_citation_range_rejected(self):
        c=replace(self.request.citations[0],end=len(TEXT)+1)
        self.blocked(replace(self.request,citations=(c,)),'CITATION_QUOTE_MISMATCH')
    def test_unknown_block_rejected(self):
        c=replace(self.request.citations[0],block_id='absent')
        self.blocked(replace(self.request,citations=(c,)),'CITATION_BLOCK_MISMATCH')
    def test_wrong_source_id_and_hash_rejected(self):
        for field,value in (('source_id','absent'),('source_sha256','0'*64)):
            with self.subTest(field=field):self.blocked(replace(self.request,blocks=(replace(self.request.blocks[0],**{field:value}),)),'BLOCK_SOURCE_MISMATCH')
    def test_wrong_page_rejected(self):
        self.blocked(replace(self.request,blocks=(replace(self.request.blocks[0],page=2),)),'BLOCK_PAGE_OUT_OF_RANGE')
    def test_undeclared_expected_output_rejected(self):
        result=self.check(policy=replace(self.policy,expected_output_ids=('narration','game-feedback')))
        self.assertEqual(result.provenance.status,'BLOCKED');self.assertIn('OUTPUT_SCOPE_MISMATCH',codes(result.provenance))
    def test_unexpected_submitted_output_rejected(self):
        result=self.check(policy=replace(self.policy,expected_output_ids=('another',)))
        self.assertIn('OUTPUT_SCOPE_MISMATCH',codes(result.provenance))
    def test_claim_revision_rejected(self):
        c=replace(self.request.claims[0],output_sha256='0'*64)
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_OUTPUT_MISMATCH')
    def test_claim_text_rejected(self):
        c=replace(self.request.claims[0],text=TEXT.replace('5','9'))
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_TEXT_MISMATCH')
    def test_claim_end_outside_output_rejected(self):
        c=replace(self.request.claims[0],end=len(TEXT)+1)
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_TEXT_MISMATCH')
    def test_unknown_output_rejected(self):
        c=replace(self.request.claims[0],output_id='unknown')
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_OUTPUT_MISMATCH')
    def test_unclassified_tail_cannot_be_hidden(self):
        c=replace(self.request.claims[0],end=8,text=TEXT[:8])
        self.blocked(replace(self.request,claims=(c,)),'UNCLASSIFIED_OUTPUT_CONTENT')
    def test_missing_citation_rejected(self):
        c=replace(self.request.claims[0],citation_ids=())
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_CITATION_UNRESOLVED')
    def test_valid_citation_cannot_hide_another_bad_one(self):
        c=replace(self.request.claims[0],citation_ids=('cite-1','missing'))
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_CITATION_UNRESOLVED')
    def test_unused_citation_requires_review(self):
        c=replace(self.request.citations[0],citation_id='spare',end=3,quote='The')
        r=self.check(replace(self.request,citations=self.request.citations+(c,)))
        self.assertEqual(r.provenance.status,'REVIEW_REQUIRED');self.assertIn('UNASSIGNED_CITATION',codes(r.provenance))
    def test_claim_partial_word_rejected(self):
        c=replace(self.request.claims[0],start=1,text=TEXT[1:])
        self.blocked(replace(self.request,claims=(c,)),'CLAIM_SPLITS_TOKEN')
    def test_citation_partial_word_rejected(self):
        c=replace(self.request.citations[0],start=1,quote=TEXT[1:])
        self.blocked(replace(self.request,citations=(c,)),'CITATION_SPLITS_TOKEN')
    def test_low_extraction_confidence_never_passes(self):
        b=replace(self.request.blocks[0],confidence_ppm=800000)
        c=replace(self.request.citations[0],block_digest=b.content_digest)
        r=self.check(replace(self.request,blocks=(b,),citations=(c,)))
        self.assertEqual(r.provenance.status,'REVIEW_REQUIRED');self.assertIn('LOW_EXTRACTION_CONFIDENCE',codes(r.provenance))
    def test_unicode_exact_offsets_preserved(self):
        r,_,p=fixture(self.root,'त्रिभुज की तीन भुजाएँ हैं। Δ = 3; 木。')
        result=self.check(r,p);self.assertEqual(result.provenance.status,'CHECKS_PASSED')
    def test_whitespace_is_not_silently_normalized(self):
        r,_,p=fixture(self.root,'  exact\ntext  ')
        b=replace(r.blocks[0],text='exact text');c=replace(r.citations[0],block_digest=b.content_digest,end=10,quote=b.text)
        result=self.check(replace(r,blocks=(b,),citations=(c,)),p)
        self.assertIn('UTF8_EXTRACTION_MISMATCH',codes(result.provenance))
    def test_overlapping_claims_do_not_inflate_coverage(self):
        c=replace(self.request.claims[0],claim_id='overlap',start=4,text=TEXT[4:])
        result=self.check(replace(self.request,claims=self.request.claims+(c,)))
        m=dict(result.provenance.measurements)
        self.assertEqual(m['classified_codepoints'],m['nonspace_codepoints'])
    def test_source_block_with_duplicate_region_rejected(self):
        b=replace(self.request.blocks[0],block_id='duplicate')
        self.blocked(replace(self.request,blocks=self.request.blocks+(b,)),'DUPLICATE_SOURCE_REGION')
