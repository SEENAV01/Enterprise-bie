from h3_support import *
from copy import deepcopy

class ReadinessChecks(TempCase):
    def setUp(self):super().setUp();self.p,self.b,self.g,self.l,self.lr=readiness_fixture(self.root);self.refs=()
    def refresh(self):self.lr=save(self.root,'lesson.json',self.l,identifier='lesson')
    def run_check(self,**kwargs):return evaluate_readiness(self.g,self.lr,self.refs,self.root,self.b,self.p,learner_id='learner1',now=NOW,**kwargs)
    def diagnostic(self,**changes):
        d=dict(schema_version='bie.qa.learner-diagnostic/1',observation_id='obs-a',learner_id='learner1',concept_id='a',assessed_at=NOW-5,policy_digest=self.p.content_digest,
               scores={'knowledge':900000,'application':900000},reported_mastery=True,provenance_mode='diagnostic');d.update(changes)
        ref=save(self.root,'diagnostic.json',d,identifier='diag');self.refs=(ref,);return d,ref
    def approve(self,ref,subject='obs-a',**kwargs):
        req=digest(dict(binding=asdict(self.b),lesson=asdict(self.lr),diagnostic=asdict(ref),learner_id='learner1'))
        return signed(subject,'mastery',req,self.p.content_digest,(ref.artifact_id,),**kwargs)
    def test_transitive_native_graph(self):self.assertEqual(prerequisites(self.g)['c'],{'a','b'})
    def test_healthy_plan_not_mastery(self):
        r,d=self.run_check();self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertFalse(d['real_learner_mastery_certified'])
    def test_unavailable_source_adapter_requires_review(self):self.assertIn('NATIVE_LESSON_SOURCE_EVIDENCE_REQUIRED',codes(self.run_check()[0]))
    def test_cycle_rejected(self):
        self.g=build_graph(('a','b','c'),(Edge('a','b'),Edge('b','c'),Edge('c','a')))
        with self.assertRaisesRegex(ContractError,'PREREQUISITE_CYCLE'):self.run_check()
    def test_inconsistent_native_graph_rejected(self):
        self.g.incoming['b'].clear()
        with self.assertRaisesRegex(ContractError,'ASYMMETRIC_LEGACY_PR_GRAPH'):self.run_check()
    def test_wrong_default_order(self):
        self.l['routes'][0]['concept_order']=['c','a','b'];self.refresh();self.blocked(self.run_check()[0],'PREREQUISITE_NOT_READY')
    def test_bad_alternate_branch_cannot_hide(self):
        self.l['routes'][1]['concept_order']=['a','c','b'];self.refresh();self.blocked(self.run_check()[0],'PREREQUISITE_NOT_READY')
    def test_missing_route(self):
        self.l['routes'].pop();self.refresh()
        with self.assertRaisesRegex(ContractError,'LESSON_ROUTE_INVENTORY'):self.run_check()
    def test_missing_required_concept(self):
        self.l['routes'][0]['concept_order']=['a','b'];self.refresh();self.blocked(self.run_check()[0],'REQUIRED_LESSON_CONCEPT_MISSING')
    def test_unknown_route_concept(self):
        self.l['routes'][0]['concept_order'].append('other');self.refresh()
        with self.assertRaisesRegex(ContractError,'ROUTE_CONCEPT_SCOPE'):self.run_check()
    def test_foreign_learner(self):
        self.l['learner_id']='other';self.refresh()
        with self.assertRaisesRegex(ContractError,'LEARNER_IDENTITY_MISMATCH'):self.run_check()
    def test_foreign_lesson_binding(self):
        self.l['binding']['revision']='b'*40;self.refresh()
        with self.assertRaisesRegex(ContractError,'NATIVE_BINDING_MISMATCH'):self.run_check()
    def test_synthetic_observation_is_not_mastery(self):
        d,ref=self.diagnostic();r,data=self.run_check(reviews=(self.approve(ref),),verifier=ReviewVerifier((SYNTHETIC_KEY,)))
        self.assertEqual(data['routes']['default']['prior_diagnostic_concepts'],[])
    def test_unsigned_observed_diagnostic_is_not_mastery(self):
        self.diagnostic(provenance_mode='observed');r,data=self.run_check();self.assertEqual(data['routes']['default']['prior_diagnostic_concepts'],[])
    def test_authorized_observed_contract_can_supply_prior(self):
        d,ref=self.diagnostic(provenance_mode='observed');r,data=self.run_check(reviews=(self.approve(ref),),verifier=ReviewVerifier((SYNTHETIC_KEY,)))
        self.assertEqual(data['routes']['default']['prior_diagnostic_concepts'],['a']);self.assertFalse(data['real_learner_mastery_certified'])
    def test_mastery_label_cannot_hide_criterion_failure(self):
        self.diagnostic(scores={'knowledge':1000000,'application':750000});self.blocked(self.run_check()[0],'MASTERY_LABEL_CONTRADICTS_SCORES')
    def test_diagnostic_wrong_learner(self):self.diagnostic(learner_id='other');self.blocked(self.run_check()[0],'DIAGNOSTIC_SCOPE_MISMATCH')
    def test_diagnostic_wrong_policy(self):self.diagnostic(policy_digest='f'*64);self.blocked(self.run_check()[0],'DIAGNOSTIC_SCOPE_MISMATCH')
    def test_diagnostic_stale(self):self.diagnostic(assessed_at=NOW-900000);self.blocked(self.run_check()[0],'DIAGNOSTIC_STALE')
    def test_diagnostic_future(self):self.diagnostic(assessed_at=NOW+1);self.blocked(self.run_check()[0],'DIAGNOSTIC_STALE')
    def test_missing_criterion_score(self):
        self.diagnostic(scores={'knowledge':1000000})
        with self.assertRaisesRegex(ContractError,'DIAGNOSTIC_CRITERION_COVERAGE'):self.run_check()
    def test_duplicate_diagnostic_ref(self):
        self.diagnostic();self.refs*=2
        with self.assertRaisesRegex(ContractError,'DUPLICATE_DIAGNOSTIC'):self.run_check()
    def test_duplicate_observation_under_another_file(self):
        d,r=self.diagnostic();r2=save(self.root,'second.json',d,identifier='diag2');self.refs=(r,r2)
        with self.assertRaisesRegex(ContractError,'DUPLICATE_OBSERVATION'):self.run_check()
    def test_failed_observation_not_outvoted(self):
        d,r=self.diagnostic(provenance_mode='observed');d2={**d,'observation_id':'obs-a-fail','scores':{'knowledge':100000,'application':100000},'reported_mastery':False}
        r2=save(self.root,'failed.json',d2,identifier='diag2');self.refs=(r,r2)
        reviews=(self.approve(r),self.approve(r2,'obs-a-fail'));report,data=self.run_check(reviews=reviews,verifier=ReviewVerifier((SYNTHETIC_KEY,)))
        self.assertEqual(data['routes']['default']['prior_diagnostic_concepts'],[])
    def test_no_math_does_not_remove_gate(self):
        self.l['applicability']=[dict(gate_id='math_correctness',decision='NOT_APPLICABLE_REQUESTED',source_claim_ids=['claim1'],rationale='This declared source has no mathematical expressions.')];self.refresh()
        r,d=self.run_check();self.assertEqual(d['retained_required_gate_ids'],list(self.p.required_gate_ids));self.assertEqual(d['gates_waived'],[]);self.assertIn('APPLICABILITY_REQUIRES_GROUNDED_REVIEW',codes(r))
    def test_unknown_applicability_claim(self):
        self.l['applicability']=[dict(gate_id='math_correctness',decision='NOT_APPLICABLE_REQUESTED',source_claim_ids=['missing'],rationale='not used')];self.refresh()
        with self.assertRaisesRegex(ContractError,'APPLICABILITY_SOURCE_SCOPE'):self.run_check()
    def test_source_native_request_executed(self):
        q,sp,kp,kb,links,refs=knowledge_fixture(self.root);self.l['source_claim_ids']=[q.claims[0].claim_id];self.refresh()
        r,d=self.run_check(source_request=q,source_policy=sp);self.assertNotIn('NATIVE_LESSON_SOURCE_EVIDENCE_REQUIRED',codes(r));self.assertEqual(len(r.inspected),3)
    def test_unknown_claim_cannot_borrow_source_request(self):
        q,sp,kp,kb,links,refs=knowledge_fixture(self.root)
        with self.assertRaisesRegex(ContractError,'LESSON_SOURCE_UNKNOWN_CLAIM'):self.run_check(source_request=q,source_policy=sp)
    def test_old_signed_observation_cannot_apply_to_changed_lesson(self):
        d,r=self.diagnostic(provenance_mode='observed');approval=self.approve(r)
        self.l['routes'].reverse();self.refresh();self.blocked(self.run_check(reviews=(approval,),verifier=ReviewVerifier((SYNTHETIC_KEY,)))[0],'DIAGNOSTIC_AUTHENTICATION_FAILED')
