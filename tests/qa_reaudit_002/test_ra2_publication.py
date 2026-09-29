from ra2_support import *
from contextlib import contextmanager
import bie.qa.operational_quality_v2.publication as publication

class PublicationBoundaries(PubCase):
    def test_healthy_attested_roundtrip(self):
        r=self.publish();self.assertEqual(r['status'],'LOCAL_PUBLISHED')
        self.assertFalse(r['production_authorized']);self.assertTrue(self.serve())
    def test_expiry_during_copy_blocks_activation(self):
        original=self.store.put
        def advance(data):
            v=original(data);self.clock[0]=2_000_000_000;return v
        with patch.object(self.store,'put',advance):
            self.error('H8_STATEMENT_TIME',self.publish,self.roles('publish',NOW+1))
        self.empty_active()
    def test_expiry_after_sql_writes_rolls_back_all_tables(self):
        original=self.store._event
        def expire(c,body):
            original(c,body);self.clock[0]=2_000_000_000
        with patch.object(self.store,'_event',expire):
            self.error('H8_STATEMENT_TIME',self.publish,self.roles('publish',NOW+1))
        self.empty_active()
    def test_session_expiry_during_copy(self):
        original=self.store.put
        def expire(data):
            v=original(data);self.clock[0]=31_000_000_000;return v
        with patch.object(self.store,'put',expire):self.error('H8_SESSION_EXPIRED',self.publish)
        self.empty_active()
    def test_certificate_revoked_during_copy(self):
        original=self.store.put;once=[False]
        def revoke(data):
            v=original(data)
            if not once[0]:self.f.journal.revoke(self.cert,reason='SYNTHETIC-REVOKE',as_of=NOW);once[0]=True
            return v
        with patch.object(self.store,'put',revoke):self.error('CERTIFICATE_REVOKED',self.publish)
        self.empty_active()
    def test_revocation_at_last_transaction_boundary(self):
        original=self.store._event
        def revoke(c,body):
            original(c,body);self.f.journal.revoke(self.cert,reason='SYNTHETIC-REVOKE',as_of=NOW)
        with patch.object(self.store,'_event',revoke):self.error('CERTIFICATE_REVOKED',self.publish)
        self.empty_active()
    def test_lock_wait_cannot_borrow_early_approval(self):
        original=self.store._tx
        @contextmanager
        def delayed():
            with original() as c:
                self.clock[0]=2_000_000_000;yield c
        with patch.object(self.store,'_tx',delayed):
            self.error('H8_STATEMENT_TIME',self.publish,self.roles('publish',NOW+1))
        self.empty_active()
    def test_expiry_during_serve_read_returns_no_bytes(self):
        self.publish();original=publication.regular_bytes
        def expire(root,path,*a,**k):
            value=original(root,path,*a,**k)
            if path=='subjects/source.txt':self.clock[0]=2_000_000_000
            return value
        with patch.object(publication,'regular_bytes',expire):
            self.error('H8_STATEMENT_TIME',self.serve,self.roles('serve',NOW+1))
    def test_expiry_during_restore_blocks_serving(self):
        self.publish();original=self.store._get
        def expire(h):
            v=original(h);self.clock[0]=2_000_000_000;return v
        with patch.object(self.store,'_get',expire):
            self.error('H8_STATEMENT_TIME',self.serve,self.roles('serve',NOW+1))
    def test_raw_production_requires_fresh_authority(self):
        self.error('H39_PUBLICATION_FRESH_AUTHORITY_REQUIRED',self.raw_publish,
                   policy=replace(self.f.policy,mode='production'))
        self.empty_active()
    def test_bad_guard_type_rejected(self):
        self.error('H39_PUBLICATION_GUARD_TYPE',self.raw_publish,'callback-from-json')
    def test_boolean_guard_clock_rejected(self):
        with self.assertRaises(ContractError):self.raw_publish(lambda _:True)
    def test_guard_clock_cannot_rollback_between_checks(self):
        ticks=iter((NOW+3,NOW+2));self.error('H39_AUTHORIZATION_CLOCK_ROLLBACK',self.raw_publish,lambda _:next(ticks))
        self.empty_active()
    def test_guard_exception_fails_closed(self):
        def reject(_):raise ContractError('OPERATOR_DENIED')
        self.error('OPERATOR_DENIED',self.raw_publish,reject);self.empty_active()
    def test_fixed_clock_diagnostic_compatibility(self):
        r=self.raw_publish();self.assertFalse(r['production_authorized'])
    def test_valid_repeated_guards_still_publish(self):
        calls=[]
        def guard(root):calls.append(Path(root));return NOW
        self.raw_publish(guard);self.assertGreaterEqual(len(calls),4)
        self.assertTrue(any(p!=self.f.root for p in calls))
    def test_idempotent_retry_is_rechecked(self):
        self.publish();self.clock[0]=2_000_000_000
        self.error('H8_STATEMENT_TIME',self.publish,self.roles('publish',NOW+1))
        with sqlite3.connect(self.store.db) as c:self.assertEqual(c.execute('select count(*) from audit').fetchone()[0],1)
    def test_store_reopen_after_rejected_publish_remains_inactive(self):
        self.test_expiry_after_sql_writes_rolls_back_all_tables()
        PublicationStore(self.store.path);self.empty_active()
