from dir_helpers import *

class Fidelity(FixtureCase):
    def mapping(self,cid,**kw):return replace(self.request,fidelity=change(self.request.fidelity,'claim_id',cid,**kw))
    def test_mapping_scope_complete(self):
        self.assertCode(self.run_check(replace(self.request,fidelity=self.request.fidelity[:-1])),'fidelity','DIR_FIDELITY_SCOPE_MISMATCH')
    def test_fact_label_not_question(self):
        self.assertCode(self.run_check(self.mapping('c-example',mode='question')),'fidelity','DIR_NONFACT_LABEL_BYPASS')
    def test_fact_label_not_instruction(self):
        self.assertCode(self.run_check(self.mapping('c-example',mode='instruction')),'fidelity','DIR_NONFACT_LABEL_BYPASS')
    def test_quote_changes_detected_even_with_positive_reviews(self):
        r,p,c=fixture(self.root,output_overrides={'c-example':'Two groups of three counters contain eight counters.'})
        self.assertCode(self.run_check(r,p),'fidelity','DIR_QUOTE_CHANGED')
    def test_wrong_citation(self):
        self.assertCode(self.run_check(self.mapping('c-example',citation_ids=('cite-c-definition',))),'fidelity','DIR_FIDELITY_CITATION_MISMATCH')
    def test_unknown_citation(self):
        self.assertCode(self.run_check(self.mapping('c-example',citation_ids=('absent',))),'fidelity','DIR_FIDELITY_REFERENCE')
    def test_unknown_facet(self):
        self.assertCode(self.run_check(self.mapping('c-example',facet_ids=('absent',))),'fidelity','DIR_FIDELITY_REFERENCE')
    def test_fact_without_facet(self):
        self.assertCode(self.run_check(self.mapping('c-example',facet_ids=())),'fidelity','DIR_FACT_WITHOUT_FACET')
    def test_operator_required_source_anchor(self):
        p=replace(self.policy,facets=change(self.policy.facets,'facet_id','facet-example',citation_ids=('absent',)))
        self.assertCode(self.run_check(p=p),'fidelity','DIR_FACET_SOURCE_MISSING')
    def test_mode_not_authorized(self):
        self.assertCode(self.run_check(self.mapping('c-example',mode='analogy')),'fidelity','DIR_FACET_TRANSFORMATION_INVALID')
    def test_source_condition_cannot_be_dropped(self):
        self.assertCode(self.run_check(self.mapping('c-payoff',conditions=())),'fidelity','DIR_CONDITION_COVERAGE')
    def test_condition_id_cannot_be_replaced(self):
        self.assertCode(self.run_check(self.mapping('c-payoff',conditions=(ConditionWitness('other','c-condition'),))),'fidelity','DIR_CONDITION_COVERAGE')
    def test_self_condition_not_evidence(self):
        self.assertCode(self.run_check(self.mapping('c-payoff',conditions=(ConditionWitness('disjoint-groups','c-payoff'),))),'fidelity','DIR_CONDITION_NOT_VISIBLE')
    def test_unknown_condition_claim(self):
        self.assertCode(self.run_check(self.mapping('c-payoff',conditions=(ConditionWitness('disjoint-groups','absent'),))),'fidelity','DIR_CONDITION_NOT_VISIBLE')
    def test_late_condition_blocks(self):
        bs=change(self.request.beats,'beat_id','b-payoff',claim_ids=('c-payoff',))
        bs=change(bs,'beat_id','b-recap',claim_ids=('c-recap','c-condition'))
        self.assertCode(self.run_check(replace(self.request,beats=bs)),'fidelity','DIR_CONDITION_NOT_VISIBLE')
    def test_condition_in_different_scene_does_not_qualify(self):
        bs=change(self.request.beats,'beat_id','b-payoff',claim_ids=('c-payoff',))
        bs=change(bs,'beat_id','b-example',claim_ids=('c-example','c-condition'))
        self.assertCode(self.run_check(replace(self.request,beats=bs)),'fidelity','DIR_CONDITION_NOT_VISIBLE')
    def test_replayed_assertion_needs_condition_at_each_occurrence(self):
        extra=Beat('unqualified-copy','s1','emphasis','narration',17000,27000,('c-payoff',),('obj-count',))
        self.assertCode(self.run_check(replace(self.request,beats=self.request.beats+(extra,))),'fidelity','DIR_CONDITION_NOT_VISIBLE')
    def creative(self):
        r=self.mapping('c-example',mode='analogy')
        p=replace(self.policy,facets=change(self.policy.facets,'facet_id','facet-example',allowed_modes=('analogy',)))
        return r,p
    def test_analogy_disclosure_required(self):
        r,p=self.creative();self.assertCode(self.run_check(r,p),'fidelity','DIR_CREATIVE_DISCLOSURE_MISSING')
    def test_analogy_self_disclosure_not_accepted(self):
        r,p=self.creative();r=replace(r,fidelity=change(r.fidelity,'claim_id','c-example',disclosure_claim_ids=('c-example',)))
        self.assertCode(self.run_check(r,p),'fidelity','DIR_CREATIVE_DISCLOSURE_MISSING')
    def test_analogy_not_substitute_for_required_source_explanation(self):
        r,p=self.creative();self.assertCode(self.run_check(r,p),'fidelity','DIR_ROUTE_SOURCE_FACET_MISSING')
    def test_source_facet_needs_explanation_not_emphasis(self):
        self.assertCode(self.run_check(self.beat('b-example',role='emphasis')),'fidelity','DIR_ROUTE_SOURCE_FACET_MISSING')
    def test_faithful_paraphrase_requires_review_and_permitted_mode(self):
        r=self.mapping('c-example',mode='paraphrase')
        self.assertEqual(self.run_check(r).status,'CHECKS_PASSED')
        self.assertNotEqual(self.run_check(r,reviews=()).status,'CHECKS_PASSED')
