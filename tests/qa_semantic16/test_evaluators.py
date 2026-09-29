from dataclasses import replace
from sem_helpers import *


class EvaluatorTests(FixtureCase):
    def test_unsigned_default_never_passes(self):
        r=self.run_case();self.assertNotEqual(r.status,'CHECKS_PASSED')
        self.assertIn('SEMANTIC_ASSESSMENT_QUORUM_MISSING',all_codes(r))
    def test_fully_provisioned_synthetic_control(self):
        r=self.op();self.assertEqual(r.status,'CHECKS_PASSED');self.assertEqual(dict(r.coverage.measurements)['weighted_coverage_ppm'],1000000)
    def test_no_product_acceptance_even_control(self):
        r=self.op();self.assertFalse(r.product_accepted)
        for report in (r.factual,r.coverage,r.contradiction):self.assertFalse(report.to_dict()['product_accepted'])
    def test_actual_source_bytes_tampered(self):
        (self.root/'inputs/reference.txt').write_text('Different content.')
        self.assertEqual(self.op().status,'BLOCKED')
    def test_actual_output_bytes_tampered(self):
        (self.root/'surfaces/output-1.txt').write_text('Different content.')
        self.assertEqual(self.op().status,'BLOCKED')
    def test_source_receipts_required_separately(self):
        kw=operational_simulation(self.request,self.policy);kw['source_assessments']=()
        self.assertNotEqual(self.run_case(**kw).factual.status,'CHECKS_PASSED')
    def test_missing_normalization_requires_review(self):
        req=replace(self.request,normalizations=());r=self.op(req)
        self.assertIn('CLAIM_NORMALIZATION_MISSING',codes(r.factual));self.assertNotEqual(r.factual.status,'CHECKS_PASSED')
    def test_unknown_normalization_claim_blocked(self):
        req=replace(self.request,normalizations=(Normalization('missing',(quantity(),)),))
        self.assertEqual(self.op(req).factual.status,'BLOCKED')
    def test_incorrect_fact_detected_despite_positive_assessor(self):
        req=replace(self.request,normalizations=(Normalization('claim-1',(quantity('7'),)),))
        r=self.op(req);self.assertIn('FACT_CONTRADICTS_REFERENCE',codes(r.factual));self.assertEqual(r.factual.status,'BLOCKED')
    def test_narrower_than_uncertain_reference_not_established(self):
        req=replace(self.request,references=(replace(self.request.references[0],proposition=quantity('4','6')),))
        r=self.op(req);self.assertIn('FACT_NOT_ESTABLISHED',codes(r.factual));self.assertEqual(r.factual.status,'REVIEW_REQUIRED')
    def test_wider_candidate_range_supported(self):
        req=replace(self.request,normalizations=(Normalization('claim-1',(quantity('4','6'),)),))
        self.assertEqual(self.op(req).factual.status,'CHECKS_PASSED')
    def test_reference_inventory_cannot_shrink(self):
        req=replace(self.request,references=())
        self.assertIn('REFERENCE_INVENTORY_MISMATCH',codes(self.op(req).factual))
    def test_reference_inventory_cannot_expand(self):
        ref=replace(self.request.references[0],reference_id='extra-ref')
        self.assertIn('REFERENCE_INVENTORY_MISMATCH',codes(self.op(replace(self.request,references=self.request.references+(ref,))).factual))
    def test_unapproved_reference_source(self):
        p=replace(self.policy,reference_source_ids=('unapproved',))
        self.assertIn('REFERENCE_SOURCE_NOT_APPROVED',codes(self.op(policy=p).factual))
    def test_missing_reference_citation(self):
        r=replace(self.request.references[0],citation_ids=('missing',))
        self.assertIn('REFERENCE_SOURCE_NOT_APPROVED',codes(self.op(replace(self.request,references=(r,))).factual))
    def test_different_reference_scope_not_generalized(self):
        r=replace(self.request.references[0],proposition=quantity(context=(('domain','synthetic-demonstration'),('trial','B'))))
        self.assertIn('FACT_NOT_ESTABLISHED',codes(self.op(replace(self.request,references=(r,))).factual))
    def test_missing_context_blocks(self):
        n=Normalization('claim-1',(quantity(context=(('domain','synthetic-demonstration'),)),))
        r=self.op(replace(self.request,normalizations=(n,)))
        self.assertIn('INCOMPLETE_OR_EXTRA_CONTEXT',codes(r.factual))
    def test_unknown_predicate_blocks(self):
        n=Normalization('claim-1',(quantity(predicate_id='invented'),))
        self.assertIn('UNKNOWN_PREDICATE_RULE',codes(self.op(replace(self.request,normalizations=(n,))).factual))
    def test_wrong_unit_blocks(self):
        n=Normalization('claim-1',(quantity(value=Value('quantity',lower='5',upper='5',unit='kW')),))
        self.assertIn('PREDICATE_UNIT_MISMATCH',codes(self.op(replace(self.request,normalizations=(n,))).factual))
    def test_conflicting_references_not_majority_voted(self):
        req,p,_=fixture(self.root,ref_values=('5','7'))
        r=self.op(req,p);self.assertIn('CONFLICTING_REFERENCE_FACTS',codes(r.factual));self.assertEqual(r.factual.status,'BLOCKED')
    def test_cross_channel_contradiction_detected(self):
        req,p,_=fixture(self.root,values=('5','7'),channels=('narration','caption'))
        r=self.op(req,p);self.assertIn('OUTPUT_CONTRADICTION',codes(r.contradiction));self.assertEqual(r.contradiction.status,'BLOCKED')
    def test_within_claim_contradiction_detected(self):
        req=replace(self.request,normalizations=(Normalization('claim-1',(quantity('5'),quantity('7'))),))
        self.assertIn('OUTPUT_CONTRADICTION',codes(self.op(req).contradiction))
    def test_unreviewed_conflict_is_not_proven_conflict(self):
        req,p,_=fixture(self.root,values=('5','7'))
        kw=operational_simulation(req,p)
        kw['assessments']=tuple(a for a in kw['assessments'] if a.purpose!='normalization')
        r=self.run_case(req,p,**kw);self.assertIn('UNVERIFIED_CONFLICT_CANDIDATE',codes(r.contradiction))
        self.assertNotIn('OUTPUT_CONTRADICTION',codes(r.contradiction))
    def test_consistency_scan_requires_assessment(self):
        kw=operational_simulation(self.request,self.policy)
        kw['assessments']=tuple(a for a in kw['assessments'] if a.purpose!='consistency')
        r=self.run_case(**kw);self.assertIn('UNMODELED_SEMANTIC_CONSISTENCY_UNASSESSED',codes(r.contradiction))
    def test_budget_overflow_cannot_pass_partial_scan(self):
        req,p,_=fixture(self.root,values=('5','7'))
        p=replace(p,max_comparisons=1);r=self.op(req,p)
        self.assertIn('SEMANTIC_COMPARISON_BUDGET_EXCEEDED',codes(r.contradiction))
        self.assertEqual(dict(r.contradiction.measurements)['comparisons_executed'],0)
    def test_missing_critical_concept(self):
        r=self.op(replace(self.request,coverage_links=()))
        self.assertIn('CRITICAL_CONCEPT_FACET_UNCOVERED',codes(r.coverage))
    def test_mention_is_not_teaching(self):
        req=replace(self.request,coverage_links=(replace(self.request.coverage_links[0],depth=1),))
        r=self.op(req);self.assertIn('COVERAGE_DEPTH_INSUFFICIENT',codes(r.coverage));self.assertEqual(dict(r.coverage.measurements)['requirements_covered'],0)
    def test_depth_claim_requires_alignment_assessment(self):
        kw=operational_simulation(self.request,self.policy)
        kw['assessments']=tuple(a for a in kw['assessments'] if a.purpose!='coverage')
        r=self.run_case(**kw);self.assertIn('COVERAGE_ALIGNMENT_UNASSESSED',codes(r.coverage))
    def test_wrong_channel_cannot_cover(self):
        p=replace(self.policy,requirements=(replace(self.policy.requirements[0],allowed_channels=('game_feedback',)),))
        self.assertIn('COVERAGE_CHANNEL_MISMATCH',codes(self.op(policy=p).coverage))
    def test_unknown_requirement_cannot_replace_expected(self):
        req=replace(self.request,coverage_links=(replace(self.request.coverage_links[0],requirement_id='invented'),))
        self.assertIn('UNKNOWN_COVERAGE_REQUIREMENT',codes(self.op(req).coverage))
    def test_unknown_coverage_claim(self):
        req=replace(self.request,coverage_links=(replace(self.request.coverage_links[0],claim_ids=('missing',)),))
        self.assertIn('COVERAGE_CLAIM_MISSING',codes(self.op(req).coverage))
    def test_duplicate_alternative_links_do_not_inflate(self):
        req,p,_=fixture(self.root,values=('5','5'))
        req=replace(req,coverage_links=req.coverage_links+(CoverageLink('link-2','req-1',('claim-2',),2),))
        r=self.op(req,p);self.assertEqual(dict(r.coverage.measurements)['requirements_covered'],1)
        self.assertEqual(dict(r.coverage.measurements)['weighted_coverage_ppm'],1000000)
    def test_critical_floor_cannot_be_averaged_away(self):
        main=replace(self.policy.requirements[0],weight=1000)
        missing=replace(main,requirement_id='req-2',concept_id='missing',facet='missing',weight=1)
        p=replace(self.policy,requirements=(main,missing),minimum_weighted_coverage_ppm=950000)
        r=self.op(policy=p);self.assertGreater(dict(r.coverage.measurements)['weighted_coverage_ppm'],950000)
        self.assertEqual(r.coverage.status,'BLOCKED');self.assertIn('CRITICAL_CONCEPT_FACET_UNCOVERED',codes(r.coverage))
    def test_nonfactual_label_does_not_supply_fact_teaching(self):
        sr=replace(self.request.source,claims=(replace(self.request.source.claims[0],kind='QUESTION'),))
        req=replace(self.request,source=sr,normalizations=())
        self.assertIn('COVERAGE_FACTUAL_SUPPORT_MISSING',codes(self.op(req).coverage))
    def test_deterministic_evaluation(self):
        self.assertEqual(self.op().to_dict(),self.op().to_dict())
    def test_receipt_order_does_not_change_report(self):
        kw=operational_simulation(self.request,self.policy);first=self.run_case(**kw)
        kw['assessments']=tuple(reversed(kw['assessments']));self.assertEqual(first,self.run_case(**kw))
    def test_report_recomputed_before_trust(self):
        kw=operational_simulation(self.request,self.policy);r=self.run_case(**kw)
        self.assertEqual(verify_reports(r,self.request,self.root,self.policy,as_of=NOW,**kw),r)
        edited=replace(r,factual=replace(r.factual,findings=()))
        # Ensure an actual semantic alteration, even for an otherwise green control.
        edited=replace(edited,factual=replace(edited.factual,measurements=(('forged',1),)))
        with self.assertRaises(ContractError):verify_reports(edited,self.request,self.root,self.policy,as_of=NOW,**kw)
