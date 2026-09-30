"""Shared Batch003 metric API, custody, CLI, and preservation regressions."""
from copy import deepcopy
import hashlib,json,os,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,canonical_json,digest,strict_loads,MAX_BYTES
from bie.evaluation.benchmarks.metrics import evaluate,MODULES,evaluator_code_sha256
from bie.evaluation.benchmarks.metrics.service import MetricRunStore
from bie.evaluation.benchmarks.runner import PACK_MODULES,load_pack,grade_case,reference_output
ROOT=Path(__file__).resolve().parents[2]
DOMAINS=('BIE-EVAL-GEO-002','BIE-EVAL-GEO-003','BIE-EVAL-CIV-001','BIE-EVAL-DATA-001')

def fixture(task='BIE-EVAL-METRIC-001'):
    return json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures'/f'{task}.json').read_text())
def args(f=None,index=0):
    f=fixture() if f is None else f;r=f['reference'];c=f['cases'][index]['candidate']
    return dict(metric_id=r['metric_id'],reference=r,candidate=c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=f['source_artifacts'])
class Batch003Contracts(unittest.TestCase):
    def test_original_registry_sequence_21_to_30(self):
        registry=json.loads((ROOT/'metadata/section17/ORIGINAL_50_TASK_REGISTRY.json').read_text());self.assertEqual(list(DOMAINS)+list(MODULES),[r['task_id'] for r in registry['rows']][20:30])
    def test_four_new_packs_have_48_unique_cases(self):
        cases=[c for t in DOMAINS for c in load_pack(t)];self.assertEqual(48,len(cases));self.assertEqual(48,len({c.case_id for c in cases}))
    def test_metric_fixtures_have_6_positive_30_negative_cases(self):
        cases=[c for t in MODULES for c in fixture(t)['cases']];self.assertEqual(36,len(cases));self.assertEqual(6,sum(c['expected_outcome']=='PASS' for c in cases))
    def test_no_fixture_claims_golden_or_holdout(self):
        for t in DOMAINS:
            for c in load_pack(t):self.assertEqual(('AUTHORED_DIAGNOSTIC','DEVELOPMENT'),(c.evidence_grade,c.split))
        for t in MODULES:self.assertEqual('AUTHORED_DIAGNOSTIC',fixture(t)['reference']['evidence_grade'])
    def test_new_modules_unknown_operation_typed(self):
        for t in DOMAINS:self.assertEqual('UNSUPPORTED_OPERATION',reference_output(t,{'op':'absent'})['error_code'])
    def test_all_domain_malformed_inputs_blocked(self):
        for t in DOMAINS:
            for v in [None,False,3,[],"code"]:self.assertEqual('REJECTED',reference_output(t,v)['status'])
    def test_domain_wrong_answer_control(self):
        for t in DOMAINS:
            c=load_pack(t)[0];output=deepcopy(c.expected);output['values']['invented_extra']=True;self.assertEqual('FAIL',grade_case(c,output)['status'])
    def test_current_roster_keeps_prior_180_cases(self):
        old=[t for t in PACK_MODULES if t not in DOMAINS];self.assertEqual(16,len(old));self.assertEqual(180,sum(len(load_pack(t)) for t in old))
    def test_candidate_reference_snapshot_mismatch(self):
        a=args();a['reference']['version']='2.0.0'
        with self.assertRaisesRegex(BenchmarkError,'REFERENCE_SNAPSHOT_MISMATCH'):evaluate(**a)
    def test_candidate_output_snapshot_mismatch(self):
        a=args();a['candidate']['claims']=[]
        with self.assertRaisesRegex(BenchmarkError,'CANDIDATE_SNAPSHOT_MISMATCH'):evaluate(**a)
    def test_unknown_metric_type_is_typed_error(self):
        a=args();a['metric_id']=[]
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_reference_metric_id_mismatch(self):
        a=args();a['reference']['metric_id']='BIE-EVAL-METRIC-002';a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaisesRegex(BenchmarkError,'METRIC_IDENTITY_MISMATCH'):evaluate(**a)
    def test_no_self_declared_acceptance_field(self):
        a=args();a['candidate']['product_accepted']=True;a['expected_candidate_sha256']=digest(a['candidate'])
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_nonfinite_candidate_not_serializable(self):
        a=args();a['candidate']['claims'][0]['proposition']['object']=float('nan')
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(BenchmarkError):strict_loads('{"claims":[],"claims":[]}')
    def test_invalid_evidence_grade_not_promoted(self):
        a=args();a['reference']['evidence_grade']='GOLDEN_APPROVED';a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_missing_source_metadata_rejected(self):
        a=args();a['reference']['source_refs']=[];a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_zero_weight_reference_blocked(self):
        a=args();a['reference']['payload']['claims'][0]['weight']=0;a['expected_reference_sha256']=digest(a['reference'])
        with self.assertRaises(BenchmarkError):evaluate(**a)
    def test_reference_candidate_not_mutated(self):
        a=args();before=deepcopy(a);evaluate(**a);self.assertEqual(before,a)
    def test_report_deterministic_same_snapshot(self):
        a=args();self.assertEqual(canonical_json(evaluate(**a)),canonical_json(evaluate(**a)))
    def test_report_identity_changes_with_candidate(self):
        good=evaluate(**args());bad=evaluate(**args(index=1));self.assertNotEqual(good['candidate_sha256'],bad['candidate_sha256']);self.assertEqual(good['reference_sha256'],bad['reference_sha256'])
    def test_no_metric_promotes_product_or_native_acceptance(self):
        for t in MODULES:
            out=evaluate(**args(fixture(t)))
            for key in ['product_accepted','release_authorized','native_bie_execution_verified','independently_reviewed']:self.assertIs(False,out[key])
    def test_non_grounding_unused_artifacts_not_ignored(self):
        a=args(fixture('BIE-EVAL-METRIC-002'));a['source_artifacts']={'extra':'unexpected'}
        with self.assertRaisesRegex(BenchmarkError,'UNUSED_SOURCE_ARTIFACTS'):evaluate(**a)
    def test_unexpected_runtime_fault_propagates(self):
        with patch('bie.evaluation.benchmarks.metrics.grounding.measure',side_effect=RuntimeError('injected')):
            with self.assertRaises(RuntimeError):evaluate(**args())
    def test_resource_limit_on_candidate_claims(self):
        a=args();a['candidate']['claims']=[dict(a['candidate']['claims'][0],id='c'+str(i)) for i in range(129)];a['expected_candidate_sha256']=digest(a['candidate'])
        with self.assertRaisesRegex(BenchmarkError,'COLLECTION_SIZE_OR_TYPE'):evaluate(**a)

class MetricStoreContracts(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=MetricRunStore(self.root/'runs.sqlite3')
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def execute(self,index=0,run='run1',campaign='campaign1',f=None):return self.store.execute(run_id=run,campaign_id=campaign,**args(f,index))
    def test_receipt_persists_and_reloads(self):
        out=self.execute();self.assertEqual(out,self.store.get('run1'));self.assertEqual('PASS',out['report']['outcome'])
    def test_bad_candidate_persisted_as_measured_fail(self):self.assertEqual('FAIL',self.execute(index=1)['report']['outcome'])
    def test_missing_artifacts_persisted_blocked_without_score(self):
        a=args();a['source_artifacts']={};out=self.store.execute(run_id='r',campaign_id='c',**a);self.assertEqual('BLOCKED',out['report']['status']);self.assertNotIn('score_exact',out['report']);self.assertEqual(out,self.store.get('r'))
    def test_same_candidate_cannot_retry_with_new_run_id(self):
        self.execute()
        with self.assertRaisesRegex(BenchmarkError,'METRIC_ATTEMPT_ALREADY_RECORDED'):self.execute(run='run2')
    def test_same_run_id_cannot_be_reassigned(self):
        self.execute()
        with self.assertRaisesRegex(BenchmarkError,'METRIC_ATTEMPT_ALREADY_RECORDED'):self.execute(index=1)
    def test_new_candidate_allowed_same_frozen_campaign(self):self.execute();self.assertEqual('FAIL',self.execute(index=1,run='run2')['report']['outcome'])
    def test_reference_change_refused_same_campaign(self):
        self.execute();f=fixture();f['reference']['version']='2.0.0'
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_REFERENCE_OR_CODE_CHANGED'):self.execute(index=1,run='run2',f=f)
    def test_code_change_refused_same_campaign(self):
        self.execute()
        with patch('bie.evaluation.benchmarks.metrics.service.evaluator_code_sha256',return_value='0'*64):
            with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_REFERENCE_OR_CODE_CHANGED'):self.execute(index=1,run='run2')
    def test_receipt_tamper_detected(self):
        self.execute();self.store.db.execute("UPDATE metric_runs SET receipt='{}' WHERE run_id='run1'")
        with self.assertRaisesRegex(BenchmarkError,'METRIC_RECEIPT_INTEGRITY_FAILURE'):self.store.get('run1')
    def test_nonobject_receipt_tamper_typed(self):
        self.execute();self.store.db.execute("UPDATE metric_runs SET receipt='[]' WHERE run_id='run1'")
        with self.assertRaisesRegex(BenchmarkError,'METRIC_RECEIPT_INTEGRITY_FAILURE'):self.store.get('run1')
    def test_nonobject_report_tamper_typed(self):
        self.execute();bad={'run_id':'run1','campaign_id':'campaign1','report':[]};self.store.db.execute('UPDATE metric_runs SET receipt=?,receipt_sha=?',(canonical_json(bad),digest(bad)))
        with self.assertRaisesRegex(BenchmarkError,'METRIC_RECEIPT_INTEGRITY_FAILURE'):self.store.get('run1')
    def test_malformed_receipt_json_tamper_typed(self):
        self.execute();self.store.db.execute("UPDATE metric_runs SET receipt='invalid' WHERE run_id='run1'")
        with self.assertRaisesRegex(BenchmarkError,'METRIC_RECEIPT_INTEGRITY_FAILURE'):self.store.get('run1')
    def test_row_identity_tamper_detected(self):
        self.execute();self.store.db.execute("UPDATE metric_runs SET candidate_sha=?",('0'*64,))
        with self.assertRaisesRegex(BenchmarkError,'METRIC_RECEIPT_INTEGRITY_FAILURE'):self.store.get('run1')
    def test_unknown_receipt_typed(self):
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_METRIC_RUN'):self.store.get('notfound')
    def test_unexpected_evaluator_fault_rolls_back(self):
        with patch('bie.evaluation.benchmarks.metrics.service.evaluate',side_effect=RuntimeError('fault')):
            with self.assertRaises(RuntimeError):self.execute()
        self.assertEqual(0,self.store.db.execute('SELECT COUNT(*) FROM metric_runs').fetchone()[0]);self.assertEqual('PASS',self.execute()['report']['outcome'])
    def test_symlink_database_refused(self):
        target=self.root/'target.sqlite3';target.touch();link=self.root/'link.sqlite3';link.symlink_to(target)
        with self.assertRaisesRegex(BenchmarkError,'DATABASE_PATH_NOT_REGULAR'):MetricRunStore(link)
    def test_database_survives_new_store_instance(self):
        out=self.execute()
        with MetricRunStore(self.root/'runs.sqlite3') as other:self.assertEqual(out,other.get('run1'))

class MetricCLIContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.f=fixture();self.prepare()
    def tearDown(self):self.tmp.cleanup()
    def prepare(self,index=0):
        self.r=self.f['reference'];self.c=self.f['cases'][index]['candidate']
        for name,body in [('reference',self.r),('candidate',self.c),('artifacts',self.f['source_artifacts'])]:(self.root/(name+'.json')).write_text(json.dumps(body))
    def command(self,out='result',run='r1',candidate_sha=None):
        return [sys.executable,'-B','-m','bie.evaluation.benchmarks.metrics','--metric',self.r['metric_id'],'--reference',str(self.root/'reference.json'),'--candidate',str(self.root/'candidate.json'),'--source-artifacts',str(self.root/'artifacts.json'),'--reference-sha',digest(self.r),'--candidate-sha',candidate_sha or digest(self.c),'--database',str(self.root/'runs.sqlite3'),'--run-id',run,'--campaign-id','campaign','--output-dir',str(self.root/out)]
    def invoke(self,**kwargs):return subprocess.run(self.command(**kwargs),cwd=ROOT,text=True,capture_output=True,timeout=20)
    def test_cli_positive_persists_report(self):
        p=self.invoke();self.assertEqual(0,p.returncode,p.stderr);r=json.loads((self.root/'result/METRIC_RESULT.json').read_text());self.assertEqual('PASS',r['report']['outcome']);self.assertTrue((self.root/'runs.sqlite3').is_file())
    def test_cli_negative_exit_one(self):self.prepare(1);p=self.invoke();self.assertEqual(1,p.returncode,p.stderr);self.assertEqual('FAIL',json.loads(p.stdout)['outcome'])
    def test_cli_missing_artifact_blocks_persistently(self):
        (self.root/'artifacts.json').write_text('{}');p=self.invoke();self.assertEqual(2,p.returncode);r=json.loads((self.root/'result/METRIC_RESULT.json').read_text());self.assertEqual('BLOCKED',r['report']['status']);self.assertNotIn('score_exact',r['report'])
    def test_cli_repeated_attempt_across_processes(self):
        self.assertEqual(0,self.invoke().returncode);p=self.invoke(out='other',run='r2');self.assertEqual(2,p.returncode);self.assertIn('METRIC_ATTEMPT_ALREADY_RECORDED',p.stderr)
    def test_cli_will_not_overwrite_existing_output(self):
        self.assertEqual(0,self.invoke().returncode);before=(self.root/'result/METRIC_RESULT.json').read_bytes();self.assertEqual(2,self.invoke().returncode);self.assertEqual(before,(self.root/'result/METRIC_RESULT.json').read_bytes())
    def test_cli_duplicate_json_input_blocked(self):
        (self.root/'candidate.json').write_text('{"claims":[],"claims":[]}');p=self.invoke();self.assertEqual(2,p.returncode);self.assertFalse((self.root/'result/METRIC_RESULT.json').exists())
    def test_cli_wrong_candidate_pin_blocked(self):
        self.assertEqual(2,self.invoke(candidate_sha='0'*64).returncode);self.assertFalse((self.root/'result/METRIC_RESULT.json').exists())
    def test_cli_symlink_input_blocked(self):
        path=self.root/'candidate.json';path.rename(self.root/'actual.json');path.symlink_to(self.root/'actual.json');p=self.invoke();self.assertEqual(2,p.returncode);self.assertIn('INPUT_NOT_REGULAR_FILE',p.stderr)
    def test_cli_oversized_input_blocked(self):
        (self.root/'candidate.json').write_text(' '*(MAX_BYTES+1));p=self.invoke();self.assertEqual(2,p.returncode);self.assertIn('INPUT_SIZE_LIMIT',p.stderr)

class Batch003Reproducibility(unittest.TestCase):
    def test_authored_builder_recreates_all_four_domain_and_six_metric_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'rebuilt';p=subprocess.run([sys.executable,'-B',str(ROOT/'tools/rebuild_batch003_fixture_data.py'),'--output-dir',str(target)],cwd=ROOT,capture_output=True,text=True,timeout=20)
            self.assertEqual(0,p.returncode,p.stderr)
            paths=[f'bie/evaluation/benchmarks/data/{t}.json' for t in DOMAINS]+[f'bie/evaluation/benchmarks/metrics/fixtures/{t}.json' for t in MODULES]
            for rel in paths:self.assertEqual((ROOT/rel).read_bytes(),(target/rel).read_bytes(),rel)
    def test_persisted_metric_diagnostic_all_expected_behaviors(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'diagnostic';p=subprocess.run([sys.executable,'-B',str(ROOT/'tools/run_section17_batch003_metric_diagnostics.py'),'--output-dir',str(target)],cwd=ROOT,capture_output=True,text=True,timeout=20)
            self.assertEqual(0,p.returncode,p.stderr);r=json.loads((target/'SUMMARY.json').read_text());self.assertEqual((36,36,6,30),(r['scenarios'],r['matched'],r['positive_candidates'],r['deliberately_defective_candidates']))
    def test_same_candidate_concurrency_only_one_receipt(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'race.sqlite3'
            with MetricRunStore(db):pass
            def job(index):
                with MetricRunStore(db) as store:
                    try:store.execute(run_id='r'+str(index),campaign_id='c',**args());return 'RECORDED'
                    except BenchmarkError as e:return e.code
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(job,[1,2]))
            self.assertEqual(['METRIC_ATTEMPT_ALREADY_RECORDED','RECORDED'],sorted(results))
