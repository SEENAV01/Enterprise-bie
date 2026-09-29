from pub22_support import *
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from bie.qa.publication_v2.authority import approval_digest
from bie.qa.publication_v2.certification import _bytes

class Certificates(Case):
    def test_diagnostic_roundtrip(self):
        c=self.f.issue();r=self.f.verify(c);self.assertTrue(r['verified']);self.assertEqual(r['status'],'DIAGNOSTIC_ONLY');self.assertFalse(r['product_accepted'])
    def test_no_default_authority(self):self.raises('APPROVAL_COVERAGE',self.f.issue,approvals=())
    def test_gate_failure_cannot_be_approved(self):
        self.f.update_ev(status='FAIL',diagnostics=('FAILURE',));self.raises('PUBLICATION_BLOCKED',self.f.issue)
    def test_expiry_capped_by_approvals(self):self.assertEqual(self.f.issue()['expires_at'],NOW+1800)
    def test_expiry_capped_by_policy(self):
        self.f.policy=replace(self.f.policy,max_certificate_lifetime_seconds=100);self.assertEqual(self.f.issue()['expires_at'],NOW+100)
    def test_expiry_capped_by_evidence(self):
        self.f.update_ev(expires_at=NOW+50);self.assertEqual(self.f.issue()['expires_at'],NOW+50)
    def test_signature_tamper(self):
        c=self.f.issue();c['signature']='0'*64;self.raises('CERTIFICATE_SIGNATURE',self.f.verify,c)
    def test_certificate_extra_fields(self):
        c=self.f.issue();c['override']=True;self.raises('PUBLICATION_FIELDS',self.f.verify,c)
    def test_certificate_expired(self):self.raises('CERTIFICATE_TIME',self.f.verify,self.f.issue(),as_of=NOW+1800)
    def test_certificate_before_issue(self):self.raises('CERTIFICATE_TIME',self.f.verify,self.f.issue(),as_of=NOW-1)
    def test_artifacts_rechecked_after_issuance(self):
        c=self.f.issue();a=self.f.approvals();(self.root/'subjects/video.fixture').write_bytes(b'tamper')
        self.raises('CERTIFICATE_CURRENT_EVIDENCE_BLOCKED',self.f.verify,c,approvals=a)
    def test_approval_revoked_after_issue(self):
        c=self.f.issue();keys=(replace(self.f.keys[0],enabled=False),)+self.f.keys[1:]
        self.raises('AUTHORITY_UNKNOWN_OR_REVOKED',self.f.verify,c,authorities=AuthorityStore(keys))
    def test_issuer_revoked_after_issue(self):
        c=self.f.issue();keys=self.f.keys[:-1]+(replace(self.f.keys[-1],enabled=False),)
        self.raises('AUTHORITY_UNKNOWN_OR_REVOKED',self.f.verify,c,authorities=AuthorityStore(keys))
    def test_gate_key_revoked_after_issue(self):
        c=self.f.issue();self.raises('CERTIFICATE_CURRENT_EVIDENCE_BLOCKED',self.f.verify,c,verifier=HmacEvidenceVerifier((replace(self.f.evkey,enabled=False),)))
    def test_certificate_revocation(self):
        c=self.f.issue();self.f.journal.revoke(c,reason='TEST_WITHDRAWAL',as_of=NOW);self.raises('CERTIFICATE_REVOKED',self.f.verify,c)
    def test_idempotent_issue(self):self.assertEqual(self.f.issue(),self.f.issue())
    def test_concurrent_exact_issue(self):
        with ThreadPoolExecutor(max_workers=4) as p:certs=list(p.map(lambda _:self.f.issue(),range(4)))
        self.assertTrue(all(x==certs[0] for x in certs));self.assertTrue(self.f.verify(certs[0])['verified'])
    def test_conflicting_version(self):
        self.f.issue();self.f.policy=replace(self.f.policy,max_certificate_lifetime_seconds=100)
        self.raises('PUBLICATION_VERSION_CONFLICT',self.f.issue)
    def test_new_release_version_separate(self):
        c=self.f.issue();self.f.request=replace(self.f.request,release_version='0.0.2');self.assertNotEqual(c['signature'],self.f.issue()['signature'])
    def test_journal_reopen_verify(self):
        c=self.f.issue();self.f.journal=ReleaseJournal(self.f.jdir/'publication.db');self.assertTrue(self.f.verify(c)['verified'])
    def test_unjournaled_certificate_rejected(self):
        c=self.f.issue();p=self.root/'other-private';p.mkdir(mode=0o700);self.f.journal=ReleaseJournal(p/'journal.db')
        self.raises('CERTIFICATE_NOT_JOURNALED',self.f.verify,c)
    def test_revocation_precedes_issue(self):self.raises('REVOCATION_BEFORE_ISSUE',self.f.journal.revoke,self.f.issue(),reason='REASON',as_of=NOW-1)
    def test_journal_requires_private_dir(self):
        p=self.root/'not-private';p.mkdir(mode=0o755);self.raises('JOURNAL_PRIVATE_DIRECTORY_REQUIRED',ReleaseJournal,p/'db')
    def test_journal_symlink_rejected(self):
        p=self.f.jdir/'linked';p.symlink_to(self.f.jdir/'publication.db');self.raises('JOURNAL_PATH',ReleaseJournal,p)
    def test_journal_hardlink_rejected(self):
        import os
        p=self.f.jdir/'hardlink';os.link(self.f.jdir/'publication.db',p);self.raises('JOURNAL_UNSAFE_FILE',ReleaseJournal,p)
    def test_no_test_key_production_authority(self):
        p=replace(self.f.policy,mode='production');a=self.f.approvals();self.raises('AUTHORITY_TEST_ONLY',self.f.authorities.check,a,self.f.assess().content_digest,p,as_of=NOW)
    def test_no_prod_promotion_even_resigned_diagnostic(self):
        c=self.f.issue();c['status']='SUCCESS';c['release_authorized']=True;c['product_accepted']=True
        c['signature']=hmac.new(self.f.keys[-1].secret,_bytes(c),hashlib.sha256).hexdigest()
        self.raises('CERTIFICATE_SCOPE',self.f.verify,c)
    def test_no_bool_promotion_even_resigned(self):
        c=self.f.issue();c['product_accepted']=True;c['signature']=hmac.new(self.f.keys[-1].secret,_bytes(c),hashlib.sha256).hexdigest()
        self.raises('CERTIFICATE_PROMOTED',self.f.verify,c)
    def test_wrong_environment(self):
        c=self.f.issue();self.f.policy=replace(self.f.policy,environment_id='elsewhere');self.raises('CERTIFICATE_SCOPE',self.f.verify,c)
    def test_delayed_independent_approval_and_issue(self):
        a=tuple(sign_approval(replace(x,created_at=NOW+10),k) for x,k in zip(self.f.approvals(),self.f.keys))
        c=self.f.issue(approvals=a,as_of=NOW+30,assessment_at=NOW)
        self.assertEqual(c['assessed_at'],NOW);self.assertEqual(c['issued_at'],NOW+30)
        self.assertTrue(self.f.verify(c,approvals=a,as_of=NOW+60)['verified'])
    def test_future_assessment_clock_rejected(self):
        self.raises('INVALID_INTEGER',self.f.issue,assessment_at=NOW+1)
    def test_secret_not_repr(self):self.assertNotIn(self.f.keys[0].secret.decode(),repr(self.f.keys[0]))

class Approvals(Case):
    def check(self,a,keys=None):return (AuthorityStore(keys) if keys is not None else self.f.authorities).check(a,self.f.assess().content_digest,self.f.policy,as_of=NOW)
    def change(self,**kwargs):
        a=list(self.f.approvals());a[0]=sign_approval(replace(a[0],**kwargs),self.f.keys[0]);return tuple(a)
    def test_approval_time_future(self):self.raises('APPROVAL_TIME',self.check,self.change(created_at=NOW+1))
    def test_approval_expired(self):self.raises('APPROVAL_TIME',self.check,self.change(expires_at=NOW))
    def test_approval_too_long(self):self.raises('APPROVAL_TIME',self.check,self.change(expires_at=NOW+90000))
    def test_approval_decision_rejected(self):self.raises('APPROVAL_REJECTED',self.check,self.change(decision='REJECT'))
    def test_approval_stale(self):self.raises('APPROVAL_STALE_BINDING',self.check,self.change(assessment_digest='a'*64))
    def test_approval_wrong_principal(self):self.raises('APPROVAL_PRINCIPAL',self.check,self.change(principal_id='another'))
    def test_approval_bad_signature(self):
        a=list(self.f.approvals());a[0]=replace(a[0],signature='0'*64);self.raises('APPROVAL_SIGNATURE',self.check,tuple(a))
    def test_approval_missing_purpose(self):self.raises('APPROVAL_COVERAGE',self.check,self.f.approvals()[:-1])
    def test_approval_duplicate_purpose(self):
        a=list(self.f.approvals());a[0]=replace(a[0],purpose=a[1].purpose);self.raises('APPROVAL_PURPOSE_COVERAGE',self.check,tuple(a))
    def test_approval_duplicate_id(self):
        a=list(self.f.approvals());a[0]=replace(a[0],approval_id=a[1].approval_id);self.raises('APPROVAL_DUPLICATE_ID',self.check,tuple(a))
    def test_approval_same_principal(self):
        a=list(self.f.approvals());a[0]=replace(a[0],principal_id=a[1].principal_id);self.raises('APPROVAL_INDEPENDENCE',self.check,tuple(a))
    def test_approval_purpose_unauthorized(self):
        keys=(replace(self.f.keys[0],purposes=('issuer',)),)+self.f.keys[1:];self.raises('AUTHORITY_PURPOSE',self.check,self.f.approvals(),keys)
    def test_approval_key_future(self):
        keys=(replace(self.f.keys[0],not_before=NOW+1),)+self.f.keys[1:];self.raises('AUTHORITY_KEY_TIME',self.check,self.f.approvals(),keys)
    def test_approval_key_expired(self):
        keys=(replace(self.f.keys[0],not_after=NOW),)+self.f.keys[1:];self.raises('AUTHORITY_KEY_TIME',self.check,self.f.approvals(),keys)
    def test_approval_outlives_key(self):
        keys=(replace(self.f.keys[0],not_after=NOW+2),)+self.f.keys[1:];self.raises('APPROVAL_EXCEEDS_KEY_LIFETIME',self.check,self.f.approvals(),keys)
    def test_distinct_keys_cannot_share_secret_for_independence(self):
        keys=(replace(self.f.keys[0],secret=self.f.keys[1].secret),)+self.f.keys[1:];self.raises('AUTHORITY_SHARED_PRINCIPAL_SECRET',AuthorityStore,keys)
    def test_duplicate_keys_rejected(self):self.raises('AUTHORITY_DUPLICATE_KEY',AuthorityStore,(self.f.keys[0],self.f.keys[0]))
    def test_wrong_key_collection(self):self.raises('AUTHORITY_KEYS',AuthorityStore,list(self.f.keys))
    def test_issuer_independent(self):
        keys=self.f.keys[:-1]+(replace(self.f.keys[-1],principal_id=self.f.keys[0].principal_id),)
        self.raises('ISSUER_NOT_INDEPENDENT',self.f.issue,authorities=AuthorityStore(keys))
    def test_approval_order_independent(self):
        a=self.f.approvals();self.assertEqual(approval_digest(a),approval_digest(a[::-1]))
