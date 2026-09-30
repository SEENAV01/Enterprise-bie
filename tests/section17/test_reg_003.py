from dataclasses import replace, asdict
import hashlib
from helpers import Base, case
from bie.evaluation.benchmarks.governance import Authority, AuthorityStore, Approval

SCI=Authority('science-reviewer','SCIENCE_REVIEWER','TEST-ONLY-SCIENCE',b'TEST_ONLY_SCIENCE_KEY_NOT_A_SECRET__')
GOV=Authority('dataset-governor','DATASET_GOVERNOR','TEST-ONLY-GOVERNOR',b'TEST_ONLY_GOVERNOR_KEY_NOT_A_SECRET_')
REVIEW=b'Test-only review event; not a real expert assessment.'

class GovernanceTests(Base):
    def setUp(self):
        super().setUp(); self.s=self.snapshot([case(evidence_grade='REFERENCE_CANDIDATE',split='HOLDOUT')]); self.auth=AuthorityStore((SCI,GOV))
    def sign(self,key=SCI.key_id,**kw):
        args=dict(decision='APPROVE',issued_at=10,expires_at=100,review_evidence=REVIEW,nonce='test-nonce'); args.update(kw)
        return self.auth.sign(key,self.s,**args)
    def evidence(self): return {hashlib.sha256(REVIEW).hexdigest():REVIEW}
    def authorize(self,approvals=None,**kw):
        args=dict(now=50,evidence=self.evidence());args.update(kw)
        return self.auth.authorize_holdout(self.s,approvals or (self.sign(),self.sign(GOV.key_id)),**args)
    def test_independent_role_quorum(self):
        r=self.authorize(); self.assertTrue(r['evaluation_authorized']); self.assertFalse(r['product_accepted']); self.assertFalse(r['release_authorized'])
    def test_authorized_is_not_real_world_identity(self): self.assertEqual('OPERATOR_PROVISIONED_HMAC',self.authorize()['identity_scope'])
    def test_tampered_signature_rejected(self): self.code('INVALID_APPROVAL_SIGNATURE',self.auth.verify,replace(self.sign(),signature='0'*64),self.s,now=50,review_evidence=REVIEW)
    def test_tampered_review_evidence_rejected(self): self.code('REVIEW_EVIDENCE_MISMATCH',self.auth.verify,self.sign(),self.s,now=50,review_evidence=b'changed')
    def test_expiry_exclusive(self): self.code('APPROVAL_NOT_CURRENT',self.authorize,now=100)
    def test_not_yet_valid(self): self.code('APPROVAL_NOT_CURRENT',self.authorize,now=9)
    def test_wrong_dataset_rejected(self): self.code('APPROVAL_DATASET_MISMATCH',self.auth.verify,replace(self.sign(),dataset_sha256='0'*64),self.s,now=50,review_evidence=REVIEW)
    def test_signer_role_cannot_be_changed(self): self.code('AUTHORITY_BINDING_MISMATCH',self.auth.verify,replace(self.sign(),role='DATASET_GOVERNOR'),self.s,now=50,review_evidence=REVIEW)
    def test_unknown_key_rejected(self): self.code('AUTHORITY_NOT_ACTIVE',self.auth.verify,replace(self.sign(),key_id='unknown'),self.s,now=50,review_evidence=REVIEW)
    def test_revocation_is_checked_at_use(self):
        a=self.sign(); revoked=AuthorityStore((replace(SCI,revoked=True),GOV)); self.code('AUTHORITY_NOT_ACTIVE',revoked.verify,a,self.s,now=50,review_evidence=REVIEW)
    def test_reject_is_veto(self): self.code('REVIEW_REJECTED',self.authorize,(self.sign(decision='REJECT'),self.sign(GOV.key_id)))
    def test_duplicate_reviewer_not_quorum(self): self.code('DUPLICATE_REVIEWER',self.authorize,(self.sign(),self.sign()))
    def test_one_reviewer_insufficient(self): self.code('INSUFFICIENT_INDEPENDENT_REVIEWS',self.authorize,(self.sign(),))
    def test_self_review_blocked(self):
        a=replace(SCI,principal_id='unit-author'); self.auth=AuthorityStore((a,GOV)); self.code('SELF_REVIEW',self.authorize)
    def test_missing_role_blocked(self):
        second=replace(GOV,role='SCIENCE_REVIEWER');self.auth=AuthorityStore((SCI,second));self.code('MISSING_REVIEW_ROLE',self.authorize)
    def test_diagnostic_cannot_be_promoted_by_signatures(self):
        self.s=self.snapshot([case('diagnostic',2)],dataset_id='diagnostic-dataset');self.code('DIAGNOSTIC_NOT_GOLDEN',self.authorize)
    def test_empty_review_body_rejected(self): self.code('REVIEW_EVIDENCE_REQUIRED',self.sign,review_evidence=b'')
    def test_excessive_validity_rejected(self): self.code('INVALID_APPROVAL_TIME',self.sign,expires_at=100000000)
    def test_boolean_clock_rejected(self): self.code('INVALID_NUMBER',self.authorize,now=True)
    def test_weak_authority_key_rejected(self): self.code('INVALID_AUTHORITY',replace,SCI,key=b'short')
    def test_duplicate_authority_key_rejected(self): self.code('DUPLICATE_AUTHORITY_KEY',AuthorityStore,(SCI,SCI))
    def test_unknown_approval_fields_rejected(self):
        b=asdict(self.sign());b['force_approve']=True;self.code('INVALID_FIELDS',Approval.from_dict,b)
    def test_round_trip_approval(self): self.assertEqual(self.sign(),Approval.from_dict(asdict(self.sign())))
