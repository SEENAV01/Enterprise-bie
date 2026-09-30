import unittest,tempfile,shutil,json,hashlib,os,subprocess,sys
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import *

from bie.evaluation.benchmarks.adoption.ledger import AdoptionStore
from bie.evaluation.benchmarks.adoption.__main__ import main as cli
class DurableAdoptionTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.path=self.root/'run.db';self.store=AdoptionStore(self.path)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def test_execute_persist_reopen_identical(self):
        a=store_run(self.store);self.store.close();self.store=AdoptionStore(self.path);self.assertEqual(a,self.store.get('h3_run_12',expected_campaign_sha256=digest(campaign())))
    def test_duplicate_run_id_rejected(self):
        store_run(self.store)
        with self.assertRaisesRegex(BenchmarkError,'AV_ATTEMPT_ALREADY_RESERVED'):store_run(self.store)
    def test_same_content_renamed_cannot_retry(self):
        store_run(self.store);ref,c=fixture();other=TD/'renamed.mkv';shutil.copy2(TD/c['media']['path'],other);c['media']['path']=other.name
        with self.assertRaisesRegex(BenchmarkError,'AV_ATTEMPT_ALREADY_RESERVED'):store_run(self.store,ref=ref,candidate=c,ctx=context(12,ref,c,run_id='different_run'))
    def test_campaign_changes_cannot_reuse_name(self):
        store_run(self.store);contract=campaign();contract['cases'][1]['reference_sha256']='0'*64
        with self.assertRaisesRegex(BenchmarkError,'AV_CAMPAIGN_PINS_CHANGED'):store_run(self.store,contract=contract,ctx=context(run_id='different'))
    def test_pin_mismatch_does_not_reserve(self):
        with self.assertRaisesRegex(BenchmarkError,'AV_CAMPAIGN_PIN_MISMATCH'):store_run(self.store,expected_campaign_sha256='0'*64)
        self.assertEqual(0,self.store.db.execute('SELECT COUNT(*) FROM av_h3_runs').fetchone()[0])
    def test_context_dataset_drift_rejected(self):
        ctx=context();ctx['dataset_sha256']='0'*64
        with self.assertRaisesRegex(BenchmarkError,'AV_CONTEXT_CAMPAIGN_MISMATCH'):store_run(self.store,ctx=ctx)
    def test_unknown_run_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'AV_RUN_UNKNOWN'):self.store.get('missing')
    def test_database_assessment_tamper_detected(self):
        store_run(self.store);self.store.db.execute("UPDATE av_h3_runs SET assessment_json='{}'")
        with self.assertRaisesRegex(BenchmarkError,'AV_STORE_INTEGRITY'):self.store.get('h3_run_12')
    def test_database_context_tamper_detected(self):
        store_run(self.store);self.store.db.execute("UPDATE av_h3_runs SET context_json='{}'")
        with self.assertRaisesRegex(BenchmarkError,'AV_STORE_INTEGRITY'):self.store.get('h3_run_12')
    def test_database_campaign_tamper_detected(self):
        store_run(self.store);self.store.db.execute("UPDATE av_h3_campaigns SET contract_sha=?",('0'*64,))
        with self.assertRaisesRegex(BenchmarkError,'AV_STORE_INTEGRITY'):self.store.get('h3_run_12')
    def test_terminated_worker_leaves_reserved_attempt(self):
        with patch('bie.evaluation.benchmarks.adoption.ledger.run_rater',side_effect=KeyboardInterrupt),self.assertRaises(KeyboardInterrupt):store_run(self.store)
        with self.assertRaisesRegex(BenchmarkError,'AV_RUN_NOT_FINAL'):self.store.get('h3_run_12')
        with self.assertRaisesRegex(BenchmarkError,'AV_ATTEMPT_ALREADY_RESERVED'):store_run(self.store)
    def test_recovery_requires_exact_context_then_terminal_blocked(self):
        with patch('bie.evaluation.benchmarks.adoption.ledger.run_rater',side_effect=KeyboardInterrupt),self.assertRaises(KeyboardInterrupt):store_run(self.store)
        with self.assertRaisesRegex(BenchmarkError,'AV_RECOVERY_SCOPE_MISMATCH'):self.store.recover('h3_run_12',expected_context_sha256='0'*64,operator_reason='worker_stopped')
        r=self.store.recover('h3_run_12',expected_context_sha256=digest(context()),operator_reason='worker_stopped');self.assertEqual('BLOCKED',r['status']);self.assertIn('OPERATOR_RECOVERED_ABANDONED_RUN',r['reasons'])
    def test_final_run_cannot_be_recovered(self):
        store_run(self.store)
        with self.assertRaisesRegex(BenchmarkError,'AV_RECOVERY_SCOPE_MISMATCH'):self.store.recover('h3_run_12',expected_context_sha256=digest(context()),operator_reason='stopped')
    def test_missing_artifact_yields_durable_blocked_assessment(self):
        ref,c=fixture();c['media']['path']='missing';a=store_run(self.store,ref=ref,candidate=c);self.assertEqual('BLOCKED',a['status']);self.assertEqual(a,self.store.get('h3_run_12'))
    def test_symlink_database_rejected(self):
        link=self.root/'symlink.db';link.symlink_to(self.path)
        with self.assertRaises(BenchmarkError):AdoptionStore(link)
    def test_cli_get_reads_durable_record(self):
        a=store_run(self.store)
        cmd=[sys.executable,'-B','-m','bie.evaluation.benchmarks.adoption','--db',str(self.path),'get','--run-id','h3_run_12','--campaign-sha256',digest(campaign())]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30);self.assertEqual(0,p.returncode,p.stdout+p.stderr);self.assertEqual(a,json.loads(p.stdout))
    def test_cli_unknown_run_is_fail_closed_json(self):
        cmd=[sys.executable,'-B','-m','bie.evaluation.benchmarks.adoption','--db',str(self.path),'get','--run-id','missing','--campaign-sha256',digest(campaign())]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30);self.assertEqual(2,p.returncode);self.assertEqual('BLOCKED',json.loads(p.stdout)['status'])
