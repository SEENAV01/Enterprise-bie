from repair_helpers import *
import sqlite3,concurrent.futures
from contextlib import closing

class JournalTests(Fixture):
    def test_reservation_persists(self):p=self.proposal();self.journal().reserve(p,NOW);self.assertEqual(self.journal().export()['events'][0]['proposal_id'],p.proposal_id)
    def test_unfinished_blocks_reexecution(self):p=self.proposal();self.journal().reserve(p,NOW);self.assertRaises(ContractError,self.run_proposal,p)
    def test_attempt_budget_survives_reopen(self):
        self.policy=replace(self.policy,max_attempts=1);self.run_proposal(self.proposal(b'1+8'));self.assertRaises(ContractError,self.run_proposal,self.proposal(b'2+3',pid='next'))
    def test_duplicate_proposal_rejected(self):p=self.proposal(b'2+8');self.run_proposal(p);self.assertRaises(ContractError,self.run_proposal,p)
    def test_duplicate_effect_new_id_rejected(self):self.run_proposal(self.proposal(b'2+8'));self.assertRaises(ContractError,self.run_proposal,self.proposal(b'2+8',pid='different'))
    def test_staged_session_terminal(self):self.run_proposal();self.assertRaises(ContractError,self.run_proposal,self.proposal(b'1+4',pid='next'))
    def test_total_byte_budget(self):
        self.policy=replace(self.policy,max_replacement_bytes=3,max_total_replacement_bytes=5);self.run_proposal(self.proposal(b'2+8'));self.assertRaises(ContractError,self.run_proposal,self.proposal(b'1+4',pid='next'))
    def test_total_worker_budget(self):
        self.policy=replace(self.policy,worker_timeout_seconds=1,max_total_worker_seconds=1);self.run_proposal(self.proposal(b'2+8'));self.assertRaises(ContractError,self.run_proposal,self.proposal(b'1+4',pid='next'))
    def test_budget_not_reclaimed_for_failure(self):self.run_proposal(self.proposal(b'2+8'));r=self.journal().export()['events'][0];self.assertEqual(r['reserved_bytes'],3)
    def test_finish_cannot_repeat(self):j=self.journal();a=j.reserve(self.proposal(),NOW);j.finish(a,'REJECTED','a'*64);self.assertRaises(ContractError,j.finish,a,'REJECTED','a'*64)
    def test_finish_requires_reservation(self):self.assertRaises(ContractError,self.journal().finish,1,'REJECTED','a'*64)
    def test_context_policy_change_rejected(self):self.journal();self.policy=replace(self.policy,max_attempts=9);self.assertRaises(ContractError,self.journal)
    def test_context_snapshot_change_rejected(self):self.journal();self.snapshot=replace(self.snapshot,run_id='new');self.assertRaises(ContractError,self.journal)
    def test_tamper_chain_rejected(self):
        j=self.journal();j.reserve(self.proposal(),NOW)
        with closing(sqlite3.connect(j.path,isolation_level=None)) as db:db.execute("UPDATE events SET hash=?",('0'*64,))
        self.assertRaises(ContractError,j.export)
    def test_metadata_tamper_rejected(self):
        j=self.journal()
        with closing(sqlite3.connect(j.path,isolation_level=None)) as db:db.execute("UPDATE metadata SET body='{}'")
        self.assertRaises(ContractError,j.export)
    def test_symlink_journal_rejected(self):
        path=self.home/'journal.sqlite';path.symlink_to(self.root/'sources/book.txt');self.assertRaises(ContractError,self.journal)
    def test_clock_rollback_rejected(self):
        j=self.journal();p=self.proposal(b'2+8');a=j.reserve(p,NOW);j.finish(a,'REJECTED','a'*64);self.assertRaises(ContractError,j.reserve,self.proposal(b'2+3',pid='next'),NOW-1)
    def test_concurrent_claim_exactly_one(self):
        p=self.proposal();j=self.journal()
        def claim(_):
            try:return ('ok',j.reserve(p,NOW))
            except ContractError as e:return ('blocked',e.code)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(claim,range(4)))
        self.assertEqual(sum(x[0]=='ok' for x in results),1)
    def test_each_receipt_linked(self):
        r=self.run_proposal();e=self.journal().export();self.assertEqual(e['events'][-1]['receipt_digest'],r['receipt_digest']);self.assertEqual(e['chain_head'],r['journal_head'])
    def test_reserved_timeout_budget_does_not_claim_measured_spend(self):j=self.journal();j.reserve(self.proposal(),NOW);self.assertEqual(j.export()['events'][0]['reserved_seconds'],self.policy.worker_timeout_seconds)

    def test_replaced_journal_inode_rejected(self):
        j=self.journal();saved=j.path.read_bytes();j.path.unlink();j.path.write_bytes(saved);self.assertRaises(ContractError,j.export)
