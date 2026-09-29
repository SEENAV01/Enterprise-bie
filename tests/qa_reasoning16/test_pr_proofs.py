from dataclasses import replace
import itertools
from bie.qa.reasoning_v2 import *
from bie.qa.release_v2.contracts import canonical_bytes
from re_helpers import *

class PrerequisiteTests(FixtureCase):
    def test_later_instruction_not_credit(self):
        r=replace(self.request,events=(replace(self.request.events[0],position=3),self.request.events[1]))
        self.assertCode(self.run_check(r),'prerequisite','PREREQUISITE_NOT_READY','BLOCKED')
    def test_missing_target(self):self.assertCode(self.run_check(replace(self.request,events=self.request.events[:1])),'prerequisite','TARGET_CONCEPT_NOT_SCHEDULED')
    def test_unknown_concept(self):self.assertCode(self.run_check(replace(self.request,events=(replace(self.request.events[0],concept_id='alien'),self.request.events[1]))),'prerequisite','UNKNOWN_EVENT_CONCEPT')
    def test_missing_event_claim(self):self.assertCode(self.run_check(replace(self.request,events=(replace(self.request.events[0],claim_ids=('missing',)),self.request.events[1]))),'prerequisite','EVENT_CLAIM_MISSING')
    def test_mention_depth_not_explanation(self):
        r=replace(self.request,events=(replace(self.request.events[0],depth=1),self.request.events[1]))
        self.assertCode(self.run_check(r),'prerequisite','PREREQUISITE_NOT_READY')
    def test_use_event_not_teaching(self):
        r=replace(self.request,events=(replace(self.request.events[0],kind='use'),self.request.events[1]))
        self.assertCode(self.run_check(r),'prerequisite','PREREQUISITE_NOT_READY')
    def test_question_not_explanation(self):
        src=replace(self.request.source,claims=self.request.source.claims[:3]+(replace(self.request.source.claims[3],kind='QUESTION'),))
        self.assertCode(self.run_check(replace(self.request,source=src)),'prerequisite','TEACHING_WITHOUT_EXPLANATORY_CONTENT')
    def test_bridge_instruction(self):
        r=replace(self.request,events=(replace(self.request.events[0],kind='bridge'),self.request.events[1]))
        result=self.run_check(r);self.assertEqual(result.prerequisite.status,'CHECKS_PASSED');self.assertEqual(result.readiness_witnesses[-1].status,'PRIOR_INSTRUCTION')
    def test_cycle_blocks(self):
        p=replace(self.policy,prerequisites=self.policy.prerequisites+(PrerequisiteRule('reverse','circuit','switch'),))
        self.assertCode(self.run_check(policy=p),'prerequisite','PREREQUISITE_GRAPH_CYCLE')
    def test_graph_budget_fail_closed(self):self.assertCode(self.run_check(policy=replace(self.policy,max_graph_checks=1)),'prerequisite','GRAPH_CHECK_BUDGET_EXCEEDED')
    def test_baseline_mastery_allows_missing_instruction(self):
        r=replace(self.add_mastery(),events=self.request.events[1:])
        result=self.run_check(r);self.assertEqual(result.prerequisite.status,'CHECKS_PASSED');self.assertEqual(result.readiness_witnesses[0].status,'DIAGNOSTIC_MASTERY')
    def test_low_mastery_not_ready(self):
        r=replace(self.add_mastery(3,10),events=self.request.events[1:]);self.assertCode(self.run_check(r),'prerequisite','PREREQUISITE_NOT_READY')
    def test_mastery_required_not_instruction(self):
        p=replace(self.policy,prerequisites=(replace(self.policy.prerequisites[0],mode='mastery_required'),))
        self.assertCode(self.run_check(policy=p),'prerequisite','PREREQUISITE_NOT_READY')
    def test_wrong_learner(self):self.assertCode(self.run_check(self.add_mastery(learner_id='other')),'prerequisite','MASTERY_SUBJECT_MISMATCH')
    def test_expired_mastery(self):self.assertCode(self.run_check(self.add_mastery(expires_at=NOW)),'prerequisite','MASTERY_EVIDENCE_STALE')
    def test_future_mastery(self):self.assertCode(self.run_check(self.add_mastery(observed_at=NOW+1)),'prerequisite','MASTERY_EVIDENCE_STALE')
    def test_mastery_lifetime_exceeded(self):self.assertCode(self.run_check(self.add_mastery(expires_at=NOW+604900)),'prerequisite','MASTERY_EVIDENCE_STALE')
    def test_later_diagnostic_not_ready(self):
        r=replace(self.add_mastery(available_at_position=2),events=self.request.events[1:]);self.assertCode(self.run_check(r),'prerequisite','PREREQUISITE_NOT_READY')
    def test_diagnostic_actual_bytes_must_match(self):
        r=self.add_mastery();m=r.masteries[0];data=m.payload();data['correct']=1
        ref=artifact(self.root,m.artifact.path,canonical_bytes(data),m.artifact.artifact_id)
        r=replace(r,masteries=(replace(m,artifact=ref),));self.assertCode(self.run_check(r),'prerequisite','MASTERY_ARTIFACT_CONTENT_MISMATCH')
    def test_boolean_diagnostic_not_integer_score(self):
        r=self.add_mastery(1,10);m=r.masteries[0];data=m.payload();data['correct']=True
        ref=artifact(self.root,m.artifact.path,canonical_bytes(data),m.artifact.artifact_id)
        self.assertCode(self.run_check(replace(r,masteries=(replace(m,artifact=ref),))),'prerequisite','MASTERY_ARTIFACT_CONTENT_MISMATCH')
    def test_newer_failed_mastery_overrides_old_pass(self):
        r=self.add_mastery();m=r.masteries[0];n=replace(m,observation_id='mastery-2',correct=1,observed_at=NOW-5)
        ref=artifact(self.root,'diagnostics/newer.json',canonical_bytes(n.payload()),'mastery-new')
        n=replace(n,artifact=ref);r=replace(r,masteries=(m,n),events=self.request.events[1:])
        self.assertCode(self.run_check(r),'prerequisite','PREREQUISITE_NOT_READY')
    def test_transitive_foundation_cannot_be_skipped(self):
        p=replace(self.policy,concepts=('basic','switch','circuit'),prerequisites=(PrerequisiteRule('r0','basic','switch'),)+self.policy.prerequisites)
        result=self.run_check(policy=p);self.assertCode(result,'prerequisite','PREREQUISITE_NOT_READY')
        self.assertTrue(any(w.prerequisite=='basic' and w.event_id=='use-circuit' for w in result.readiness_witnesses))
    def test_all_three_concept_sequence_permutations(self):
        p=replace(self.policy,concepts=('basic','switch','circuit'),prerequisites=(PrerequisiteRule('r0','basic','switch'),)+self.policy.prerequisites)
        events=(LearningEvent('teach-basic','basic',1,'teach',('claim-4',),2),replace(self.request.events[0],position=2),replace(self.request.events[1],position=3))
        for sequence in itertools.permutations(events):
            with self.subTest(order=tuple(e.concept_id for e in sequence)):
                ordered=tuple(replace(e,position=i+1) for i,e in enumerate(sequence));result=self.run_check(replace(self.request,events=ordered),p)
                self.assertEqual(result.prerequisite.status=='CHECKS_PASSED',tuple(e.concept_id for e in sequence)==('basic','switch','circuit'))

class ProofEvaluatorTests(FixtureCase):
    def test_counterexample_invalidates_proof(self):
        s=self.request.statements;r=replace(self.request,statements=(replace(s[0],expression=s[2].expression),s[1],replace(s[2],expression=s[0].expression)))
        result=self.run_check(r);self.assertCode(result,'validity','REASONING_COUNTEREXAMPLE');self.assertTrue(any(w.witness for w in result.proof_witnesses))
    def test_conflicting_roots_fail_even_if_one_local_conclusion_entailed(self):
        s=self.request.statements;r=replace(self.request,statements=(s[0],replace(s[1],expression=Expr('not','',(s[0].expression,))),s[2]))
        self.assertCode(self.run_check(r),'validity','INCONSISTENT_ROOT_PREMISES')
    def test_unknown_statement(self):
        a=replace(self.request.arguments[0],statement_ids=('s1','s2','s3','missing'));self.assertCode(self.run_check(replace(self.request,arguments=(a,))),'validity','ARGUMENT_REFERENCE_MISSING')
    def test_unknown_step(self):
        a=replace(self.request.arguments[0],step_ids=('missing',));self.assertCode(self.run_check(replace(self.request,arguments=(a,))),'validity','ARGUMENT_REFERENCE_MISSING')
    def test_unknown_step_premise(self):
        r=replace(self.request,steps=(replace(self.request.steps[0],premise_ids=('s1','missing')),));self.assertCode(self.run_check(r),'validity','STEP_REFERENCE_MISSING')
    def test_missing_producer(self):
        r=replace(self.request,steps=(replace(self.request.steps[0],conclusion_id='s2',premise_ids=('s1',)),));self.assertCode(self.run_check(r),'validity','CONCLUSION_HAS_NO_PRODUCER')
    def test_context_mismatch(self):
        s=self.request.statements;r=replace(self.request,statements=(s[0],replace(s[1],scope='other-context'),s[2]));self.assertCode(self.run_check(r),'validity','LOGICAL_CONTEXT_MISMATCH')
    def test_statement_output_missing(self):
        s=self.request.statements;r=replace(self.request,statements=(replace(s[0],claim_id='missing'),)+s[1:]);self.assertCode(self.run_check(r),'validity','LOGICAL_CLAIM_MISSING')
    def test_asserted_question_cannot_bypass(self):
        src=replace(self.request.source,claims=(replace(self.request.source.claims[0],kind='QUESTION'),)+self.request.source.claims[1:]);self.assertCode(self.run_check(replace(self.request,source=src)),'validity','LOGICAL_STATEMENT_NOT_FACTUAL')
    def test_root_cannot_be_derived(self):
        r=replace(self.request,steps=(replace(self.request.steps[0],conclusion_id='s1',premise_ids=('s2',)),));self.assertCode(self.run_check(r),'validity','DUPLICATE_OR_ROOT_PROOF_PRODUCER')
    def test_orphan_step_detected(self):
        r=replace(self.request,steps=self.request.steps+(InferenceStep('orphan','s3',('s1',)),));self.assertCode(self.run_check(r),'validity','ORPHAN_INFERENCE_STEPS')
    def test_orphan_statement_detected(self):
        r=replace(self.request,statements=self.request.statements+(Statement('s4','claim-4','toy-scope',Expr('atom','x')),));self.assertCode(self.run_check(r),'validity','ORPHAN_LOGICAL_STATEMENTS')
    def test_circular_steps(self):
        a=replace(self.request.arguments[0],premise_ids=('s1',),step_ids=('step-1','step-2'))
        r=replace(self.request,arguments=(a,),steps=(InferenceStep('step-1','s3',('s1','s2')),InferenceStep('step-2','s2',('s3',))))
        self.assertCode(self.run_check(r),'validity','PROOF_CYCLE_OR_UNRESOLVED_DEPENDENCY')
    def test_undisclosed_assumption(self):
        r=replace(self.request,arguments=(replace(self.request.arguments[0],assumption_ids=('s1',)),));self.assertCode(self.run_check(r),'validity','UNDISCLOSED_ASSUMPTIONS')
    def test_conditional_requires_visible_disclosure(self):
        a=replace(self.request.arguments[0],assumption_ids=('s1',),conclusion_mode='conditional')
        r=replace(self.request,arguments=(a,),evidence=self.request.evidence[1:]);self.assertCode(self.run_check(r),'validity','CONDITIONAL_DISCLOSURE_UNVERIFIED')
    def test_conditional_reviewed_not_empirical_assumption(self):
        a=replace(self.request.arguments[0],assumption_ids=('s1',),conclusion_mode='conditional')
        r=replace(self.request,arguments=(a,),evidence=self.request.evidence[1:],decisions=(replace(self.request.decisions[0],disclosure_claim_ids=('claim-3',)),))
        result=self.run_check(r);self.assertEqual(result.validity.status,'CHECKS_PASSED');self.assertTrue(result.evidence_witnesses[0].conditional_assumption)
    def test_nondeductive_needs_its_own_review(self):
        r=replace(self.request,steps=(replace(self.request.steps[0],method='causal'),));opts=options(r,self.policy);opts['reviews']=tuple(x for x in opts['reviews'] if x.purpose!='inference')
        self.assertCode(self.run_check(r,**opts),'validity','NONDEDUCTIVE_INFERENCE_UNVERIFIED')
    def test_reviewed_nondeductive_not_labeled_formal_proof(self):
        r=replace(self.request,steps=(replace(self.request.steps[0],method='causal'),));result=self.run_check(r)
        self.assertEqual(result.validity.status,'CHECKS_PASSED');self.assertTrue(any(w.status=='REVIEWED_NONDEDUCTIVE' for w in result.proof_witnesses))
    def test_formal_budget_cannot_be_skipped(self):self.assertCode(self.run_check(policy=replace(self.policy,max_truth_assignments=1)),'validity','PROOF_BUDGET_EXCEEDED')
    def test_node_budget_cannot_be_skipped(self):self.assertCode(self.run_check(policy=replace(self.policy,max_node_visits=1)),'validity','PROOF_BUDGET_EXCEEDED')
    def test_argument_inventory_omission(self):
        r=replace(self.request,arguments=());self.assertCode(self.run_check(r),'validity','ARGUMENT_INVENTORY_MISMATCH')
    def test_valid_formal_mapping_not_automatically_verified(self):
        opts=options(self.request,self.policy);opts['reviews']=tuple(x for x in opts['reviews'] if x.purpose!='mapping')
        self.assertCode(self.run_check(**opts),'validity','PROOF_TEXT_MAPPING_UNVERIFIED')
