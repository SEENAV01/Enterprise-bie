from h8_helpers import *
import sqlite3

class PublicTrust(Temp):
    def clocks(self,s=None):
        s=s or self.session
        return tuple(self.k.envelope(s,'clock',s.challenge_digest,dict(utc_ms=NOW*1000,uncertainty_ms=0,trust_digest=s.policy.content_digest),key_id='clock'+str(i)) for i in range(2))
    def status(self,s=None,**kw):
        s=s or self.session
        return self.k.envelope(s,'status',s.policy.content_digest,dict(epoch=kw.get('epoch',1),revoked_key_ids=kw.get('revoked',[]),trust_digest=s.policy.content_digest))
    def att(self,**kw):
        return self.k.envelope(self.session,'review','e'*64,dict(decision='APPROVE',trust_digest=self.session.policy.content_digest),**kw)
    def test_time_and_public_signature(self):
        self.ready();r=self.session.verify(self.att(),purpose='review',subject_digest='e'*64);self.assertEqual(r['principal_id'],'p-review0');self.assertTrue(r['diagnostic'])
    def test_not_established(self):self.error('H8_TIME_NOT_ESTABLISHED',self.session.window)
    def test_unknown_key(self):
        self.ready();a=self.att();a['key_id']='unknown';self.error('H8_UNKNOWN_KEY',self.session.verify,a,purpose='review',subject_digest='e'*64)
    def test_changed_signed_payload(self):
        self.ready();a=self.att();a['payload']['decision']='REJECT';self.error('H8_BAD_SIGNATURE',self.session.verify,a,purpose='review',subject_digest='e'*64)
    def test_changed_subject(self):
        self.ready();self.error('H8_STATEMENT_SCOPE',self.session.verify,self.att(),purpose='review',subject_digest='f'*64)
    def test_changed_binding(self):
        self.ready();a=self.att();a['binding']['run_id']='other';a=self.k.resign(a);self.error('H8_STATEMENT_BINDING',self.session.verify,a,purpose='review',subject_digest='e'*64)
    def test_wrong_nonce(self):
        self.ready();a=self.att();a['nonce']='f'*64;a=self.k.resign(a);self.error('H8_STATEMENT_BINDING',self.session.verify,a,purpose='review',subject_digest='e'*64)
    def test_wrong_purpose(self):
        self.ready();self.error('H8_STATEMENT_SCOPE',self.session.verify,self.att(),purpose='issuer',subject_digest='e'*64)
    def test_key_purpose(self):
        self.ready();a=self.att(key_id='issuer0');self.error('H8_KEY_PURPOSE',self.session.verify,a,purpose='review',subject_digest='e'*64)
    def test_expired_statement(self):
        self.ready();self.error('H8_STATEMENT_TIME',self.session.verify,self.att(expires=NOW),purpose='review',subject_digest='e'*64)
    def test_future_statement(self):
        self.ready();self.error('H8_STATEMENT_TIME',self.session.verify,self.att(created=NOW+1),purpose='review',subject_digest='e'*64)
    def test_key_expiry(self):
        keys=tuple(replace(k,not_after=NOW) if k.key_id=='review0' else k for k in self.k.keys)
        self.session=self.fresh(policy=TrustPolicy('trust','tenant',keys));self.ready()
        self.error('H8_AUTHORITY_TIME',self.session.verify,self.att(),purpose='review',subject_digest='e'*64)
    def test_stale_statement(self):
        self.session=self.fresh(policy=self.k.policy(max_statement_age_seconds=20));self.ready()
        self.error('H8_STATEMENT_STALE',self.session.verify,self.att(created=NOW-21),purpose='review',subject_digest='e'*64)
    def test_revoked_content_key(self):
        self.k.establish(self.session,revoked=('review0',));self.error('H8_KEY_REVOKED',self.session.verify,self.att(),purpose='review',subject_digest='e'*64)
    def test_revoked_clock(self):self.error('H8_ROOT_REVOKED',self.k.establish,self.session,revoked=('clock0',))
    def test_revoked_status(self):self.error('H8_ROOT_REVOKED',self.k.establish,self.session,revoked=('status0',))
    def test_clock_quorum(self):self.error('H8_CLOCK_QUORUM',self.session.establish,self.clocks()[:1],self.status())
    def test_clock_disagreement(self):
        cs=list(self.clocks());cs[1]['payload']['utc_ms']+=3000;cs[1]=self.k.resign(cs[1]);self.error('H8_CLOCK_DISAGREEMENT',self.session.establish,tuple(cs),self.status())
    def test_clock_uncertainty(self):
        cs=list(self.clocks());cs[0]['payload']['uncertainty_ms']=100000;cs[0]=self.k.resign(cs[0])
        with self.assertRaises(ContractError):self.session.establish(tuple(cs),self.status())
    def test_clock_roundtrip(self):
        self.clock[0]=11_000_000_000;self.error('H8_CLOCK_ROUNDTRIP',self.session.establish,self.clocks(),self.status())
    def test_clock_independence(self):
        cs=self.clocks();self.error('H8_CLOCK_INDEPENDENCE',self.session.establish,(cs[0],cs[0]),self.status())
    def test_minimum_status_epoch(self):
        self.session=self.fresh(policy=self.k.policy(minimum_status_epoch=3))
        with self.assertRaises(ContractError):self.k.establish(self.session,epoch=2)
    def test_status_rollback(self):
        self.k.establish(self.session,epoch=2);s=self.fresh();self.error('H8_STATUS_ROLLBACK',self.k.establish,s,epoch=1)
    def test_status_equivocation(self):
        self.ready();s=self.fresh();self.error('H8_STATUS_EQUIVOCATION',self.k.establish,s,revoked=('review0',))
    def test_new_epoch_revocation(self):
        self.ready();s=self.fresh();self.k.establish(s,epoch=2,revoked=('review0',));self.assertEqual(s.window(),(NOW*1000,NOW*1000))
    def test_time_rollback_persistent(self):
        self.ready();self.journal=AuthorityJournal(self.root/'authority');s=self.fresh()
        self.error('H8_CLOCK_ROLLBACK',self.k.establish,s,utc_ms=NOW*1000-1)
    def test_replayed_session(self):
        self.ready();s=self.fresh();s._nonce=self.session.challenge['nonce'];self.error('H8_REPLAY',self.k.establish,s)
    def test_establish_once(self):self.ready();self.error('H8_SESSION_ALREADY_ESTABLISHED',self.k.establish,self.session)
    def test_session_expiry(self):self.ready();self.clock[0]=31_000_000_000;self.error('H8_SESSION_EXPIRED',self.session.window)
    def test_monotonic_rollback(self):self.ready();self.clock[0]=-1000000;self.error('H8_SESSION_EXPIRED',self.session.window)
    def test_status_expiry(self):
        st=self.status();st['expires_at']=NOW+1;st=self.k.resign(st);self.session.establish(self.clocks(),st);self.clock[0]=1_000_000_000
        self.error('H8_STATUS_EXPIRED',self.session.window)
    def test_status_binding(self):
        st=self.status();st['payload']['trust_digest']='d'*64;self.error('H8_TRUST_BINDING',self.session.establish,self.clocks(),self.k.resign(st))
    def test_unknown_revocation(self):self.error('H8_UNKNOWN_REVOCATION',self.k.establish,self.session,revoked=('not-a-key',))
    def test_positive_role_quorum(self):
        self.ready();r=self.session.verify_roles(self.k.roles(self.session,'e'*64),'e'*64);self.assertEqual(len(r),3)
    def test_missing_role(self):
        self.ready();self.error('H8_ROLE_CENSUS',self.session.verify_roles,self.k.roles(self.session,'e'*64)[:2],'e'*64)
    def test_shared_principal(self):
        keys=tuple(replace(k,principal_id='p-review0') if k.key_id=='issuer0' else k for k in self.k.keys)
        self.session=self.fresh(policy=TrustPolicy('trust','tenant',keys));self.ready()
        self.error('H8_ROLE_INDEPENDENCE',self.session.verify_roles,self.k.roles(self.session,'e'*64),'e'*64)
    def test_shared_group(self):
        keys=tuple(replace(k,independence_group='g-review0') if k.key_id=='issuer0' else k for k in self.k.keys)
        self.session=self.fresh(policy=TrustPolicy('trust','tenant',keys));self.ready()
        self.error('H8_ROLE_INDEPENDENCE',self.session.verify_roles,self.k.roles(self.session,'e'*64),'e'*64)
    def test_root_content_role(self):
        keys=tuple(replace(k,principal_id='p-status0') if k.key_id=='review0' else k for k in self.k.keys)
        self.session=self.fresh(policy=TrustPolicy('trust','tenant',keys));self.ready()
        self.error('H8_ROOT_SIGNED_CONTENT',self.session.verify_roles,self.k.roles(self.session,'e'*64),'e'*64)
    def test_rejected_decision(self):
        self.ready();es=list(self.k.roles(self.session,'e'*64));es[0]['payload']['decision']='REJECT';es[0]=self.k.resign(es[0])
        self.error('H8_PAYLOAD_BINDING',self.session.verify_roles,tuple(es),'e'*64)
    def test_production_rejects_diagnostic(self):
        self.session=self.fresh(policy=self.k.policy(mode='production'));self.error('H8_DIAGNOSTIC_AUTHORITY',self.k.establish,self.session)
    def test_production_quorum_floor(self):self.error('H8_PRODUCTION_CLOCK_QUORUM',self.k.policy,mode='production',clock_quorum=1)
    def test_shared_public_key_rejected(self):
        ks=list(self.k.keys);ks[-1]=replace(ks[-1],public_key_hex=ks[-2].public_key_hex);self.error('H8_SHARED_PUBLIC_KEY',TrustPolicy,'p','t',tuple(ks))
    def test_duplicate_key_ids(self):self.error('H8_KEY_ALIAS',TrustPolicy,'p','t',self.k.keys+(self.k.keys[0],))
    def test_unknown_envelope_fields(self):
        e=self.att();e['private_key']='bad';self.error('H8_ENVELOPE_FIELDS',signing_bytes,e)
    def test_boolean_timestamp(self):
        e=self.att();e['created_at']=True
        with self.assertRaises(ContractError):signing_bytes(e)
    def test_signature_encoding(self):
        e=self.att();e['signature']='x'*128;self.error('H8_SIGNATURE_ENCODING',signing_bytes,e)
    def test_policy_not_serialized_secret(self):
        self.assertNotIn('private',json.dumps(asdict(self.k.policy())));self.assertNotIn('secret',json.dumps(asdict(self.k.policy())))
    def test_journal_reopen(self):self.ready();j=AuthorityJournal(self.root/'authority');self.assertTrue(j.db.exists())
    def test_journal_permissions(self):
        d=self.root/'public';d.mkdir(mode=0o755);self.error('H8_JOURNAL_PRIVATE',AuthorityJournal,d)
    def test_journal_link(self):
        d=self.root/'link';d.symlink_to(self.journal.path)
        with self.assertRaises(ContractError):AuthorityJournal(d)
    def test_clock_authority_expiry_during_session(self):
        cs=list(self.clocks());cs[0]['expires_at']=NOW+1;cs[0]=self.k.resign(cs[0]);self.session.establish(tuple(cs),self.status())
        self.clock[0]=2_000_000_000;self.error('H8_ROOT_TIME_EXPIRED',self.session.window)
    def test_malformed_role_object(self):
        self.ready();self.error('H8_ROLE_FIELDS',self.session.verify_roles,({}, {}, {}),'e'*64)
