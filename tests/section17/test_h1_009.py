import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from batch005_helpers import cohort
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
from bie.evaluation.benchmarks.release import gate
class DurableRecoveryBoundary(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'release.db';self.db=ReleaseLedger(self.path);self.m,self.p,self.rows=cohort()
    def tearDown(self):self.db.close();self.tmp.cleanup()
    def execute(self,attempt='a'):
        return self.db.execute(campaign_id='c',attempt_id=attempt,manifest=self.m,policy=self.p,assessments=self.rows,expected_manifest_sha256=digest(self.m),expected_policy_sha256=digest(self.p))
    def interrupt(self):
        with patch.object(gate,'evaluate',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.execute()
        return self.db.db.execute('SELECT inputs_sha FROM release_attempts WHERE id="a"').fetchone()[0]
    def recover(self,pin):return self.db.recover_incomplete('a',expected_inputs_sha256=pin,operator_id='operator',reason='WORKER_STOPPED')
    def test_final_receipt_binds_artifact(self):self.assertEqual(self.m['artifact_sha256'],self.execute()['artifact_sha256'])
    def test_artifact_column_tamper_detected(self):
        self.execute();self.db.db.execute('UPDATE release_attempts SET artifact=?',(digest('other'),))
        with self.assertRaisesRegex(BenchmarkError,'ARTIFACT_MISMATCH'):self.db.get('a')
    def test_terminal_recovery_is_blocked(self):
        pin=self.interrupt();o=self.recover(pin);self.assertEqual('BLOCKED',o['report']['outcome']);self.assertFalse(o['report']['benchmark_gate_passed'])
    def test_recovery_persists_after_reopen(self):
        pin=self.interrupt();o=self.recover(pin)
        with ReleaseLedger(self.path) as db:self.assertEqual(o,db.get('a'))
    def test_recovery_never_gives_retry(self):
        pin=self.interrupt();self.recover(pin)
        with self.assertRaisesRegex(BenchmarkError,'ALREADY_RECORDED'):self.execute('retry')
    def test_recovery_wrong_pin_refused(self):
        self.interrupt()
        with self.assertRaisesRegex(BenchmarkError,'RECOVERY_INPUTS_MISMATCH'):self.recover('0'*64)
    def test_completed_attempt_cannot_be_recovered(self):
        o=self.execute()
        with self.assertRaisesRegex(BenchmarkError,'RECOVERY_STATE_CONFLICT'):self.recover(o['inputs_sha256'])
    def test_unknown_recovery_refused(self):
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_RELEASE_ATTEMPT'):self.recover('0'*64)
    def test_double_recovery_refused(self):
        pin=self.interrupt();self.recover(pin)
        with self.assertRaisesRegex(BenchmarkError,'RECOVERY_STATE_CONFLICT'):self.recover(pin)
    def test_raced_finalization_not_falsely_reported_success(self):
        original=gate.evaluate
        def interfere(*args,**kwargs):
            result=original(*args,**kwargs);self.db.db.execute("UPDATE release_attempts SET state='INTERRUPTED' WHERE id='a'");return result
        with patch.object(gate,'evaluate',side_effect=interfere):
            with self.assertRaisesRegex(BenchmarkError,'RELEASE_FINALIZE_CONFLICT'):self.execute()
    def test_missing_campaign_typed_error(self):
        self.execute();self.db.db.execute('PRAGMA foreign_keys=OFF');self.db.db.execute('DELETE FROM release_campaigns')
        with self.assertRaises(BenchmarkError):self.db.get('a')
    def test_inner_report_tamper_even_with_outer_hash_detected(self):
        o=self.execute();o['report']['outcome']='PASS'
        self.db.db.execute('UPDATE release_attempts SET receipt=?,receipt_sha=?',(canonical_json(o),digest(o)))
        with self.assertRaisesRegex(BenchmarkError,'REPORT_INTEGRITY'):self.db.get('a')
    def test_legacy_receipt_not_silently_promoted(self):
        o=self.execute();o.pop('artifact_sha256');self.db.db.execute('UPDATE release_attempts SET receipt=?,receipt_sha=?',(canonical_json(o),digest(o)))
        with self.assertRaisesRegex(BenchmarkError,'LEGACY_RECEIPT'):self.db.get('a')
