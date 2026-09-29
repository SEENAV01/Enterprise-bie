import unittest,itertools,json
from dataclasses import replace,asdict
from bie.qa.reasoning_v2 import *
from bie.qa.release_v2.contracts import ContractError,canonical_bytes
from bie.qa.reasoning_v2.codec import request_from_dict,policy_from_dict,load_request,load_policy
from re_helpers import FixtureCase

class LogicTests(unittest.TestCase):
    def setUp(self):self.p=Expr('atom','p');self.q=Expr('atom','q')
    def test_modus_ponens(self):
        self.assertEqual(entailment((self.p,Expr('implies','',(self.p,self.q))),self.q).status,'ENTAILED')
    def test_affirming_consequent_counterexample(self):
        result=entailment((self.q,Expr('implies','',(self.p,self.q))),self.p)
        self.assertEqual(result.status,'COUNTEREXAMPLE');self.assertEqual(dict(result.witness),{'p':False,'q':True})
    def test_denying_antecedent_counterexample(self):
        self.assertEqual(entailment((Expr('not','',(self.p,)),Expr('implies','',(self.p,self.q))),Expr('not','',(self.q,))).status,'COUNTEREXAMPLE')
    def test_inconsistent_premises_not_explosion(self):self.assertEqual(entailment((self.p,Expr('not','',(self.p,))),self.q).status,'INCONSISTENT_PREMISES')
    def test_modus_tollens(self):self.assertEqual(entailment((Expr('implies','',(self.p,self.q)),Expr('not','',(self.q,))),Expr('not','',(self.p,))).status,'ENTAILED')
    def test_conjunction_elimination(self):self.assertEqual(entailment((Expr('and','',(self.p,self.q)),),self.p).status,'ENTAILED')
    def test_disjunction_not_conjunction(self):self.assertEqual(entailment((Expr('or','',(self.p,self.q)),),Expr('and','',(self.p,self.q))).status,'COUNTEREXAMPLE')
    def test_biconditional(self):self.assertEqual(entailment((self.p,Expr('iff','',(self.p,self.q))),self.q).status,'ENTAILED')
    def test_assignment_budget(self):self.assertEqual(entailment((self.p,),self.q,max_assignments=1).status,'RESOURCE_LIMIT')
    def test_atom_budget(self):self.assertEqual(entailment((self.p,),self.q,max_atoms=1).status,'RESOURCE_LIMIT')
    def test_node_budget(self):self.assertEqual(entailment((self.p,),self.q,max_node_visits=1).status,'RESOURCE_LIMIT')
    def test_empty_premises_rejected(self):
        with self.assertRaises(ContractError):entailment((),self.p)
    def test_nonboolean_assignment(self):
        with self.assertRaises(ContractError):truth(self.p,{'p':1})
    def test_missing_assignment(self):
        with self.assertRaises(ContractError):truth(self.p,{})
    def test_boolean_budget_rejected(self):
        with self.assertRaises(ContractError):entailment((self.p,),self.q,max_atoms=True)
    def test_unsupported_operator(self):
        with self.assertRaises(ContractError):Expr('forall','',(self.p,))
    def test_wrong_arity(self):
        with self.assertRaises(ContractError):Expr('implies','',(self.p,))
    def test_invalid_atom_token(self):
        with self.assertRaises(ContractError):Expr('atom','p;import os')
    def test_non_tuple_args(self):
        with self.assertRaises(ContractError):Expr('not','',[self.p])
    def test_depth_limit(self):
        e=self.p
        for _ in range(15):e=Expr('not','',(e,))
        with self.assertRaises(ContractError):Expr('not','',(e,))
    def test_all_two_variable_boolean_implications(self):
        # Independent bitmask oracle: 16 Boolean functions x 16 consequents.
        assignments=tuple(itertools.product((False,True),repeat=2))
        def dnf(mask):
            terms=[]
            for i,values in enumerate(assignments):
                if mask&(1<<i):
                    literals=tuple(atom if val else Expr('not','',(atom,)) for atom,val in zip((self.p,self.q),values))
                    terms.append(Expr('and','',literals))
            if not terms:return Expr('and','',(self.p,Expr('not','',(self.p,))))
            out=terms[0]
            for term in terms[1:]:out=Expr('or','',(out,term))
            return out
        for a,b in itertools.product(range(16),repeat=2):
            with self.subTest(premise_mask=a,conclusion_mask=b):
                result=entailment((dnf(a),),dnf(b))
                expected='INCONSISTENT_PREMISES' if a==0 else ('ENTAILED' if a&~b==0 else 'COUNTEREXAMPLE')
                self.assertEqual(result.status,expected)

class ModelTests(FixtureCase):
    def test_healthy_authorized_fixture(self):
        r=self.run_check();self.assertEqual(r.status,'CHECKS_PASSED');self.assertEqual(r.decision_witnesses[0].required_action,'publish')
    def test_request_roundtrip(self):self.assertEqual(load_request(canonical_bytes(self.request.to_dict())),self.request)
    def test_policy_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(self.policy.to_dict())),self.policy)
    def test_digest_changes_with_graph(self):self.assertNotEqual(self.policy.content_digest,replace(self.policy,prerequisites=()).content_digest)
    def test_digest_changes_with_proof(self):
        req=replace(self.request,steps=(replace(self.request.steps[0],method='causal'),));self.assertNotEqual(req.content_digest,self.request.content_digest)
    def test_duplicate_ids(self):
        with self.assertRaises(ContractError):replace(self.request,steps=self.request.steps*2)
    def test_subject_collision(self):
        with self.assertRaises(ContractError):replace(self.request,events=(replace(self.request.events[0],event_id='s1'),self.request.events[1]))
    def test_same_event_position(self):
        with self.assertRaises(ContractError):replace(self.request,events=(self.request.events[0],replace(self.request.events[1],position=1)))
    def test_duplicate_claim_mapping(self):
        with self.assertRaises(ContractError):replace(self.request,statements=(self.request.statements[0],replace(self.request.statements[1],claim_id='claim-1'),self.request.statements[2]))
    def test_unknown_target(self):
        with self.assertRaises(ContractError):replace(self.policy,target_concepts=('unknown',))
    def test_duplicate_edge(self):
        with self.assertRaises(ContractError):replace(self.policy,prerequisites=self.policy.prerequisites+(replace(self.policy.prerequisites[0],rule_id='r2'),))
    def test_self_prerequisite(self):
        with self.assertRaises(ContractError):PrerequisiteRule('r','x','x')
    def test_self_support(self):
        with self.assertRaises(ContractError):InferenceStep('x','a',('a',))
    def test_conclusion_as_premise(self):
        with self.assertRaises(ContractError):replace(self.request.arguments[0],conclusion_id='s1')
    def test_assumption_not_root(self):
        with self.assertRaises(ContractError):replace(self.request.arguments[0],assumption_ids=('s3',))
    def test_confidence_boolean(self):
        with self.assertRaises(ContractError):replace(self.request.decisions[0],confidence_ppm=True)
    def test_confidence_float(self):
        with self.assertRaises(ContractError):replace(self.request.decisions[0],confidence_ppm=950000.0)
    def test_policy_floor_not_weakened(self):
        with self.assertRaises(ContractError):replace(self.policy,minimum_review_confidence_ppm=1)
    def test_mastery_score_fraction(self):self.assertEqual(self.add_mastery(2,3).masteries[0].score_ppm,666666)
    def test_mastery_invalid_score(self):
        with self.assertRaises(ContractError):self.add_mastery(11,10)
    def test_mastery_boolean_score(self):
        with self.assertRaises(ContractError):self.add_mastery(True,10)
    def test_unsupported_schema(self):
        with self.assertRaises(ContractError):replace(self.request,schema_version='2.0.0')
    def test_non_tuple_arguments(self):
        with self.assertRaises(ContractError):replace(self.request,arguments=list(self.request.arguments))
    def test_duplicate_evidence_payload(self):
        with self.assertRaises(ContractError):replace(self.request,evidence=self.request.evidence+(replace(self.request.evidence[0],evidence_id='new'),))
    def test_mastery_artifact_collision(self):
        r=self.add_mastery()
        with self.assertRaises(ContractError):replace(r,masteries=(replace(r.masteries[0],artifact=self.request.calibrations[0].artifact),))
    def test_witnesses_deterministic(self):self.assertEqual(self.run_check().to_dict(),self.run_check().to_dict())
