"""Shared safety, storage, route and non-promotion contracts across ten new metrics."""
from copy import deepcopy
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from batch004_helpers import fixture,args,ROOT
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json,strict_loads
from bie.evaluation.benchmarks.metrics import evaluate,MODULES,ALL_MODULES,BATCH004_MODULES
from bie.evaluation.benchmarks.metrics.service import MetricRunStore
class Batch004Contracts(unittest.TestCase):
    def test_exact_original_batch004_registry_order(self):
        rows=json.loads((ROOT/'metadata/section17/ORIGINAL_50_TASK_REGISTRY.json').read_text())['rows'];self.assertEqual(list(BATCH004_MODULES),[r['task_id'] for r in rows[30:40]])
    def test_legacy_snapshot_six_and_new_router_sixteen(self):self.assertEqual(6,len(MODULES));self.assertEqual(16,len(ALL_MODULES));self.assertTrue(set(MODULES).isdisjoint(BATCH004_MODULES))
    def test_every_candidate_hash_is_checked(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));a['expected_candidate_sha256']='0'*64
            with self.assertRaisesRegex(BenchmarkError,'CANDIDATE_SNAPSHOT_MISMATCH'):evaluate(**a)
    def test_every_reference_hash_is_checked(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));a['expected_reference_sha256']='0'*64
            with self.assertRaisesRegex(BenchmarkError,'REFERENCE_SNAPSHOT_MISMATCH'):evaluate(**a)
    def test_candidates_cannot_claim_pass(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));a['candidate']['passed']=True;a['expected_candidate_sha256']=digest(a['candidate'])
            with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_all_correct_samples_repeat_deterministically(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));self.assertEqual(canonical_json(evaluate(**a)),canonical_json(evaluate(**a)))
    def test_measurement_does_not_mutate_submissions(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));b=deepcopy(a);evaluate(**a);self.assertEqual(b,a)
    def test_no_release_or_native_promotion_for_new_metrics(self):
        for task in BATCH004_MODULES:
            out=evaluate(**args(fixture(task)))
            for field in ['release_authorized','product_accepted','native_bie_execution_verified','independently_reviewed']:self.assertIs(False,out[field])
    def test_unknown_evidence_grade_is_not_golden(self):
        a=args(fixture('BIE-EVAL-METRIC-015'));a['reference']['evidence_grade']='GOLDEN';a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_missing_reference_source_metadata_blocked(self):
        a=args(fixture('BIE-EVAL-METRIC-007'));a['reference']['source_refs']=[];a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_structural_metric_rejects_external_observation_flag(self):
        a=args(fixture('BIE-EVAL-METRIC-007'));a['source_artifacts']={'passed':True}
        with self.assertRaisesRegex(BenchmarkError,'UNUSED_SOURCE_ARTIFACTS'):evaluate(**a)
    def test_unimplemented_metric017_still_blocked(self):
        a=args(fixture('BIE-EVAL-METRIC-016'));a['metric_id']='BIE-EVAL-METRIC-017'
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_METRIC'):evaluate(**a)
    def test_json_duplicate_fields_blocked(self):
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_JSON_KEY'):strict_loads('{"seed":0,"seed":1}')
    def test_every_nonobject_candidate_is_typed_failure(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));a['candidate']=None;a['expected_candidate_sha256']=digest(None)
            with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_every_nonobject_payload_is_typed_failure(self):
        for task in BATCH004_MODULES:
            a=args(fixture(task));a['reference']['payload']=None;a['expected_reference_sha256']=digest(a['reference'])
            with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_each_metric_positive_has_nonzero_denominator(self):
        from fractions import Fraction
        for task in BATCH004_MODULES:self.assertGreater(Fraction(evaluate(**args(fixture(task)))['total_weight']),0)
class Batch004StoreContracts(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=self.root/'runs.sqlite3';self.store=MetricRunStore(self.db)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def execute(self,task,index=0,run='run',campaign='campaign',amend=None):
        a=args(fixture(task),index)
        if amend:amend(a)
        return self.store.execute(run_id=run,campaign_id=campaign,**a)
    def test_new_metric_receipts_persist_after_reopen(self):
        expected={}
        for i,task in enumerate(BATCH004_MODULES):expected['r'+str(i)]=self.execute(task,run='r'+str(i))
        with MetricRunStore(self.db) as reopened:
            for k,v in expected.items():self.assertEqual(v,reopened.get(k))
    def test_invalid_compile_candidate_is_saved_as_fail(self):
        o=self.execute('BIE-EVAL-METRIC-011',index=1);self.assertEqual('FAIL',o['report']['outcome']);self.assertEqual(o,self.store.get('run'))
    def test_missing_trusted_evidence_saved_blocked_without_score(self):
        o=self.execute('BIE-EVAL-METRIC-011',amend=lambda a:a.update(source_artifacts={}));self.assertEqual('BLOCKED',o['report']['status']);self.assertNotIn('score_exact',o['report'])
    def test_blocked_attempt_still_consumed(self):
        self.execute('BIE-EVAL-METRIC-011',amend=lambda a:a.update(source_artifacts={}))
        with self.assertRaisesRegex(BenchmarkError,'METRIC_ATTEMPT_ALREADY_RECORDED'):self.execute('BIE-EVAL-METRIC-011',run='retry')
    def test_artifact_change_cannot_reuse_same_candidate_attempt(self):
        self.execute('BIE-EVAL-METRIC-012')
        with self.assertRaisesRegex(BenchmarkError,'METRIC_ATTEMPT_ALREADY_RECORDED'):self.execute('BIE-EVAL-METRIC-012',run='retry',amend=lambda a:a.update(source_artifacts={}))
    def test_campaign_reference_change_rejected(self):
        self.execute('BIE-EVAL-METRIC-015')
        def mutate(a):a['reference']['version']='1.0.1';a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_REFERENCE_OR_CODE_CHANGED'):self.execute('BIE-EVAL-METRIC-015',run='new',amend=mutate)
    def test_receipt_content_corruption_detected(self):
        self.execute('BIE-EVAL-METRIC-014');self.store.db.execute("UPDATE metric_runs SET receipt='{}'")
        with self.assertRaisesRegex(BenchmarkError,'METRIC_RECEIPT_INTEGRITY_FAILURE'):self.store.get('run')
    def test_missing_whole_metric_not_marked_measured(self):
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_METRIC_RUN'):self.store.get('never-submitted')
    def test_actual_receipt_carries_observation_digest(self):
        f=fixture('BIE-EVAL-METRIC-013');o=self.execute('BIE-EVAL-METRIC-013');self.assertEqual(digest(f['source_artifacts']),o['report']['source_artifacts_sha256'])
class Batch004CLI(unittest.TestCase):
    def test_help_lists_new_metric016(self):
        p=subprocess.run([sys.executable,'-B','-m','bie.evaluation.benchmarks.metrics','--help'],cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(0,p.returncode);self.assertIn('BIE-EVAL-METRIC-016',p.stdout)
    def test_new_metric_real_cli_receipt_roundtrip(self):
        f=fixture('BIE-EVAL-METRIC-015');a=args(f)
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);(d/'r.json').write_text(json.dumps(a['reference']));(d/'c.json').write_text(json.dumps(a['candidate']))
            cmd=[sys.executable,'-B','-m','bie.evaluation.benchmarks.metrics','--metric',a['metric_id'],'--reference',str(d/'r.json'),'--candidate',str(d/'c.json'),
                 '--reference-sha',a['expected_reference_sha256'],'--candidate-sha',a['expected_candidate_sha256'],'--database',str(d/'db.sqlite3'),
                 '--run-id','cli-run','--campaign-id','cli-campaign','--output-dir',str(d/'out')]
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15);self.assertEqual(0,p.returncode,p.stderr)
            out=json.loads((d/'out/METRIC_RESULT.json').read_text());self.assertEqual('PASS',out['report']['outcome'])
    def test_new_evidence_metric_cli_missing_observation_nonzero(self):
        f=fixture('BIE-EVAL-METRIC-011');a=args(f)
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);(d/'r.json').write_text(json.dumps(a['reference']));(d/'c.json').write_text(json.dumps(a['candidate']))
            cmd=[sys.executable,'-B','-m','bie.evaluation.benchmarks.metrics','--metric',a['metric_id'],'--reference',str(d/'r.json'),'--candidate',str(d/'c.json'),
                 '--reference-sha',a['expected_reference_sha256'],'--candidate-sha',a['expected_candidate_sha256'],'--database',str(d/'db.sqlite3'),
                 '--run-id','cli-run','--campaign-id','cli-campaign','--output-dir',str(d/'out')]
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=15);self.assertEqual(2,p.returncode,p.stderr)
            out=json.loads((d/'out/METRIC_RESULT.json').read_text());self.assertEqual('BLOCKED',out['report']['status'])
