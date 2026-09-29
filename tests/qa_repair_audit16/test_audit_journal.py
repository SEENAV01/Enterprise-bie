from audit_helpers import *

class JournalTests(AuditFixture):
    def test_actual_export_chain_matches(self):
        r=inspect_journal(self.journal_data,self.snapshot,self.p,self.policy,json.loads(canonical_bytes(self.attempt)),as_of=NOW,max_age=3600)
        self.assertEqual(r['proposal_digest'],self.p.content_digest)
    def test_unanchored_head_rejected(self):
        self.edit_journal(lambda x:x.update(chain_head='0'*64),rechain=False);self.assertCode('AUDIT_JOURNAL_HEAD')
    def test_missing_finish_rejected(self):
        self.edit_journal(lambda x:x['events'].pop());self.assertCode('AUDIT_JOURNAL_EVENT_LIMIT')
    def test_journal_wrong_binding(self):
        self.edit_journal(lambda x:x['binding'].update(run_id='other'));self.assertCode('AUDIT_JOURNAL_BINDING')
    def test_reserved_wrong_proposal(self):
        self.edit_journal(lambda x:x['events'][0].update(proposal_digest='0'*64));self.assertCode('AUDIT_RESERVED_PROPOSAL')
    def test_reserved_effect_wrong(self):
        self.edit_journal(lambda x:x['events'][0].update(effect_digest='0'*64));self.assertCode('AUDIT_RESERVED_EFFECT')
    def test_reserved_size_wrong(self):
        self.edit_journal(lambda x:x['events'][0].update(reserved_bytes=1));self.assertCode('AUDIT_RESERVED_SIZE')
    def test_reservation_future_rejected(self):
        self.edit_journal(lambda x:x['events'][0].update(reserved_at=NOW+1));self.assertCode('AUDIT_JOURNAL_CLOCK')
    def test_attempt_stale(self):self.assertCode('AUDIT_ATTEMPT_STALE',self.audit(as_of=NOW+3601))
    def test_finish_hash_binding(self):
        self.edit_journal(lambda x:x['events'][1].update(receipt_digest='0'*64));self.assertCode('AUDIT_FINISH_RECEIPT')
    def test_finish_status_binding(self):
        self.edit_journal(lambda x:x['events'][1].update(status='REJECTED'));self.assertCode('AUDIT_FINISH_STATUS')
    def test_unknown_event_kind(self):
        self.edit_journal(lambda x:x['events'][0].update(kind='APPROVED'));self.assertCode('AUDIT_JOURNAL_EVENT_KIND')
    def test_no_reservation_before_finish(self):
        self.edit_journal(lambda x:x['events'].reverse());self.assertCode('AUDIT_ORPHAN_FINISH')
    def test_attempt_renumbering_rejected(self):
        self.edit_journal(lambda x:x['events'][0].update(attempt=2));self.assertCode('AUDIT_ATTEMPT_ORDER')
    def test_additional_claim_after_staged_rejected(self):
        self.edit_journal(lambda x:x['events'].append(x['events'][0].copy()));self.assertCode('AUDIT_JOURNAL_AFTER_STAGED')
    def test_resource_reservation_not_shrunk(self):
        self.edit_journal(lambda x:x['events'][0].update(reserved_seconds=1));self.assertCode('AUDIT_RESERVATION_TIME')
