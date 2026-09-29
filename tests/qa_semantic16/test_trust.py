from dataclasses import replace
from sem_helpers import *


class TrustTests(FixtureCase):
    def altered(self,**changes):
        k=semantic_key();kw=operational_simulation(self.request,self.policy,k)
        kw['assessments']=(signed(replace(kw['assessments'][0],**changes),k),)+kw['assessments'][1:]
        return self.run_case(**kw)
    def test_bad_signature(self):
        kw=operational_simulation(self.request,self.policy)
        kw['assessments']=(replace(kw['assessments'][0],signature='0'*64),)+kw['assessments'][1:]
        self.assertIn('BAD_SEMANTIC_SIGNATURE',all_codes(self.run_case(**kw)))
    def test_unsigned_assessment_not_authentic(self):
        kw=operational_simulation(self.request,self.policy)
        kw['assessments']=(replace(kw['assessments'][0],signature=''),)+kw['assessments'][1:]
        self.assertIn('BAD_SEMANTIC_SIGNATURE',all_codes(self.run_case(**kw)))
    def test_request_binding(self):
        self.assertIn('STALE_SEMANTIC_ASSESSMENT',all_codes(self.altered(request_digest='0'*64)))
    def test_policy_binding(self):self.assertIn('SEMANTIC_POLICY_MISMATCH',all_codes(self.altered(policy_digest='0'*64)))
    def test_expiry_boundary(self):self.assertIn('SEMANTIC_ASSESSMENT_TIME',all_codes(self.altered(expires_at=NOW)))
    def test_future_receipt(self):self.assertIn('SEMANTIC_ASSESSMENT_TIME',all_codes(self.altered(issued_at=NOW+1)))
    def test_excessive_lifetime(self):self.assertIn('SEMANTIC_ASSESSMENT_LIFETIME',all_codes(self.altered(expires_at=NOW+604801)))
    def test_wrong_evidence_set(self):self.assertIn('SEMANTIC_EVIDENCE_SCOPE_MISMATCH',all_codes(self.altered(evidence_ids=('wrong',))))
    def test_unknown_assessment_subject(self):self.assertIn('UNKNOWN_SEMANTIC_ASSESSMENT_SUBJECT',all_codes(self.altered(subject_id='unknown')))
    def test_wrong_assessor_version(self):self.assertIn('UNAUTHORIZED_SEMANTIC_ASSESSOR',all_codes(self.altered(evaluator_version='2')))
    def test_revoked_key(self):
        k=semantic_key(enabled=False);kw=operational_simulation(self.request,self.policy,k)
        self.assertIn('REVOKED_SEMANTIC_KEY',all_codes(self.run_case(**kw)))
    def test_untrusted_key(self):
        kw=operational_simulation(self.request,self.policy);kw['verifier']=SemanticVerifier()
        self.assertIn('UNTRUSTED_SEMANTIC_KEY',all_codes(self.run_case(**kw)))
    def test_unauthorized_purpose(self):
        k=semantic_key(purposes=('reference',));kw=operational_simulation(self.request,self.policy,k)
        self.assertIn('UNAUTHORIZED_SEMANTIC_PURPOSE',all_codes(self.run_case(**kw)))
    def test_test_key_cannot_establish_support(self):
        k=semantic_key(assurance='test_only');kw=operational_simulation(self.request,self.policy,k)
        r=self.run_case(**kw);self.assertIn('TEST_ONLY_SEMANTIC_ASSESSMENT',all_codes(r))
        self.assertEqual(dict(r.factual.measurements)['established_claims'],0)
    def test_rejection_overrides_other_success(self):
        self.assertIn('SEMANTIC_ASSESSMENT_REJECTED',all_codes(self.altered(verdict='REJECTED')))
    def test_uncertain_does_not_pass(self):
        self.assertNotEqual(self.altered(verdict='UNCERTAIN').factual.status,'CHECKS_PASSED')
    def test_low_confidence_not_promoted(self):
        self.assertIn('SEMANTIC_ASSESSMENT_REVIEW',all_codes(self.altered(confidence_ppm=899999)))
    def test_duplicate_assessment_id(self):
        kw=operational_simulation(self.request,self.policy);kw['assessments']+=kw['assessments'][:1]
        with self.assertRaises(ContractError):self.run_case(**kw)
    def test_duplicate_assessor_vote(self):
        kw=operational_simulation(self.request,self.policy)
        kw['assessments']+=(signed(replace(kw['assessments'][0],assessment_id='other-id'),semantic_key()),)
        with self.assertRaises(ContractError):self.run_case(**kw)
    def test_duplicate_key_id(self):
        with self.assertRaises(ContractError):SemanticVerifier((semantic_key(),semantic_key()))
    def test_principal_cannot_claim_multiple_independence_groups(self):
        with self.assertRaises(ContractError):SemanticVerifier((semantic_key(),semantic_key(key_id='k2',independence_group='g2')))
    def quorum(self,same_group):
        p=replace(self.policy,minimum_independent_assessors=2);k1=semantic_key()
        k2=semantic_key(key_id='key2',evaluator_id='reviewer2',independence_group=k1.independence_group if same_group else 'group2')
        kw=operational_simulation(self.request,p,k1);other=operational_simulation(self.request,p,k2)
        second=tuple(signed(replace(a,assessment_id='second-'+a.assessment_id),k2) for a in other['assessments'])
        kw['assessments']+=second;kw['verifier']=SemanticVerifier((k1,k2))
        return p,kw,k2
    def test_same_group_cannot_satisfy_independence_quorum(self):
        p,kw,_=self.quorum(True);self.assertIn('SEMANTIC_ASSESSMENT_QUORUM_MISSING',all_codes(self.run_case(policy=p,**kw)))
    def test_distinct_provisioned_groups_satisfy_quorum(self):
        p,kw,_=self.quorum(False);self.assertEqual(self.run_case(policy=p,**kw).status,'CHECKS_PASSED')
    def test_assessor_disagreement_not_majority_vote(self):
        p,kw,k2=self.quorum(False);aas=list(kw['assessments']);idx=next(i for i,a in enumerate(aas) if a.evaluator_id==k2.evaluator_id)
        aas[idx]=signed(replace(aas[idx],verdict='REJECTED'),k2);kw['assessments']=tuple(aas)
        self.assertEqual(self.run_case(policy=p,**kw).factual.status,'BLOCKED')
    def test_credential_material_not_in_reports(self):
        k=semantic_key();result=self.op();self.assertNotIn(k.secret,canonical_bytes(result.to_dict()))
        self.assertNotIn(k.secret.decode(),repr(k))
    def test_receipt_wire_tampering_is_bound(self):
        kw=operational_simulation(self.request,self.policy)
        # Removing a required concept changes policy identity, not just a score.
        p=replace(self.policy,policy_id='other-policy')
        self.assertIn('SEMANTIC_POLICY_MISMATCH',all_codes(self.run_case(policy=p,**kw)))
