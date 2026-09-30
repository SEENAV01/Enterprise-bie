"""Actual component interoperation plus adversarial input controls."""
import hashlib,json,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
from native_qa_support import inputs,run,positive,PIN,NOW
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.native_qa import bridge
from bie.qa.release_v2.contracts import ContractError
from bie.qa.release_v2.policy import enterprise_policy

class NativeQA001(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.c,self.plan=inputs(self.root)
    def error(self,code,**kw):
        with self.assertRaises(BenchmarkError) as e:run(self.root,self.c,self.plan,**kw)
        self.assertEqual(e.exception.code,code)
    def test_canonical_source_pin_matches_ten_files(self):
        self.assertEqual(len(bridge.verify_native_runtime()),10)
    def test_source_pin_rejects_modified_expected_bytes(self):
        bad=deepcopy(PIN);bad['files'][0]['sha256']='0'*64
        with patch.object(bridge,'PIN',bad):self.error('NATIVE_QA_CODE_PIN_MISMATCH')
    def test_missing_native_dependency(self):
        with patch.object(bridge.importlib,'import_module',side_effect=ImportError):self.error('NATIVE_QA_DEPENDENCY_UNAVAILABLE')
    def test_product_candidate_pin_rejected(self):self.error('NATIVE_QA_PRODUCT_CANDIDATE_PIN_MISMATCH',expected_candidate_digest='0'*64)
    def test_policy_pin_rejected(self):self.error('NATIVE_QA_POLICY_PIN_MISMATCH',expected_policy_digest='0'*64)
    def test_entire_check_plan_pin_rejected(self):self.error('NATIVE_QA_CHECK_PLAN_PIN_MISMATCH',expected_checks_digest='0'*64)
    def test_revision_pin_rejected(self):
        self.c=replace(self.c,revision='0'*40);self.error('NATIVE_QA_REVISION_PIN_MISMATCH')
    def test_non_integer_clock_rejected(self):
        with self.assertRaises(ContractError):run(self.root,self.c,self.plan,as_of=True)
    def test_missing_execution_context_rejected(self):self.error('NATIVE_QA_EXECUTION_CONTEXT_REQUIRED',execution_context=None)
    def test_incomplete_metric_roster_rejected(self):self.plan.pop();self.error('NATIVE_QA_REQUIRED_AV_ROSTER')
    def test_duplicate_metric_rejected(self):self.plan[1]=deepcopy(self.plan[0]);self.error('NATIVE_QA_REQUIRED_AV_ROSTER')
    def test_nonstring_metric_rejected(self):self.plan[0]['metric_id']=12;self.error('NATIVE_QA_REQUIRED_AV_ROSTER')
    def test_injected_receipt_rejected(self):self.plan[0]['receipt']={'PASS':True};self.error('NATIVE_QA_CHECK_FIELDS')
    def test_reference_pin_rejected(self):self.plan[0]['expected_reference_sha256']='0'*64;self.error('NATIVE_QA_REFERENCE_PIN_MISMATCH')
    def test_metric_candidate_pin_rejected(self):self.plan[0]['expected_candidate_sha256']='0'*64;self.error('NATIVE_QA_METRIC_CANDIDATE_PIN_MISMATCH')
    def test_unbound_video_rejected(self):
        self.c=replace(self.c,artifacts=tuple(replace(a,sha256='0'*64) if a.role=='video' else a for a in self.c.artifacts));self.error('NATIVE_QA_SUBJECT_BINDING_MISMATCH')
    def test_unbound_caption_rejected(self):
        self.c=replace(self.c,artifacts=tuple(replace(a,path='other.srt') if a.role=='support' else a for a in self.c.artifacts));self.error('NATIVE_QA_SUBJECT_BINDING_MISMATCH')
    def test_dropped_additional_video_rejected(self):
        video=next(a for a in self.c.artifacts if a.role=='video');self.c=replace(self.c,artifacts=self.c.artifacts+(replace(video,artifact_id='another-video',path='another.mkv'),));self.error('NATIVE_QA_VIDEO_COVERAGE_MISMATCH')
    def test_changed_source_bytes_rejected(self):
        p=self.root/'source.txt';b=p.read_bytes();p.write_bytes(b'x'+b[1:]);self.error('NATIVE_QA_ARTIFACT_HASH_MISMATCH')
    def test_changed_game_size_rejected(self):
        (self.root/'game.html').write_bytes(b'x');self.error('NATIVE_QA_ARTIFACT_LINK_OR_SIZE')
    def test_symlink_rejected(self):
        p=self.root/'source.txt';p.rename(self.root/'real-source.txt');p.symlink_to('real-source.txt');self.error('ADOPTION_FILE_UNAVAILABLE')
    def test_hardlink_rejected(self):
        os.link(self.root/'source.txt',self.root/'linked-source.txt');self.error('NATIVE_QA_ARTIFACT_LINK_OR_SIZE')
    def test_missing_file_rejected(self):
        (self.root/'source.txt').unlink();self.error('ADOPTION_FILE_UNAVAILABLE')
    def test_reference_limits_pin_rejected(self):
        self.plan[0]['reference']['limits_sha256']='0'*64;self.plan[0]['expected_reference_sha256']=digest(self.plan[0]['reference']);self.error('NATIVE_QA_LIMITS_PIN_MISMATCH')
    def test_actual_three_collectors_execute(self):
        self.assertEqual(set(positive()['measurement_outcomes'].values()),{'PASS'})
    def test_canonical_qa_consumer_executes(self):
        out=positive();self.assertTrue(out['native_component_consumer_executed']);self.assertEqual(out['native_qa_report']['release_status'],'BLOCKED')
    def test_real_qa_reads_bound_report_bytes(self):
        out=positive();rows=out['native_qa_report']['artifact_checks'];r=next(a for a in rows if a['artifact_id']=='qa17-av-benchmark');self.assertEqual(r['status'],'PASS');self.assertEqual(r['actual_sha256'],out['report_sha256'])
    def test_native_evidence_stays_unsigned_and_not_run(self):
        e=positive()['envelope'];self.assertEqual((e['status'],e['signer_key_id'],e['signature']),('NOT_RUN','UNSIGNED',''))
    def test_partial_coverage_cannot_be_full_benchmark(self):
        p=json.loads(positive()['report_json']);self.assertEqual(len(p['metric_ids']),3);self.assertEqual(p['original_metric_roster_count'],17)
    def test_native_all_28_gates_remain_present(self):
        self.assertEqual(len(positive()['native_qa_report']['gate_results']),len(enterprise_policy().gates));self.assertEqual(len(enterprise_policy().gates),28)
    def test_no_release_authority(self):
        out=positive();self.assertFalse(out['release_authorized']);self.assertFalse(out['product_accepted']);self.assertFalse(out['native_qa_report']['product_accepted'])
    def test_report_hash_is_exact_utf8_bytes(self):
        out=positive();self.assertEqual(hashlib.sha256(out['report_json'].encode()).hexdigest(),out['report_sha256'])
    def test_candidate_identity_retained(self):
        out=positive();p=json.loads(out['report_json']);self.assertEqual(out['envelope']['candidate_digest'],p['candidate_digest']);self.assertEqual(out['native_qa_report']['candidate_digest'],p['candidate_digest'])
    def test_game_bytes_not_game_runtime_claim(self):
        p=json.loads(positive()['report_json']);self.assertEqual(p['source_and_game_scope'],'BYTES_ONLY_NOT_LEARNING_OR_RUNTIME_VALIDATION');self.assertFalse(p['native_book_pipeline_executed'])
    def test_real_frame_mismatch_propagates_failure(self):
        r=self.plan[1]['reference'];r['frame_reference']['frame_chain_sha256']='0'*64;self.plan[1]['expected_reference_sha256']=digest(r)
        out=run(self.root,self.c,self.plan);self.assertEqual(out['measurement_outcomes']['BIE-EVAL-METRIC-013'],'FAIL');self.assertEqual(out['envelope']['status'],'FAIL')
    def test_corrupt_media_propagates_blocked(self):
        p=self.root/'lesson.mkv';b=p.read_bytes();p.write_bytes(b'bad!'+b[4:]);sha=hashlib.sha256(p.read_bytes()).hexdigest()
        self.c=replace(self.c,artifacts=tuple(replace(a,sha256=sha) if a.role=='video' else a for a in self.c.artifacts))
        for row in self.plan:row['candidate']['media']['sha256']=sha;row['expected_candidate_sha256']=digest(row['candidate'])
        out=run(self.root,self.c,self.plan);self.assertEqual(out['envelope']['status'],'ERROR');self.assertIn('BLOCKED',out['measurement_outcomes'].values())
    def test_inputs_unchanged_after_actual_run(self):
        before={p.name:p.read_bytes() for p in self.root.iterdir()};c=self.c.to_dict();plan=deepcopy(self.plan)
        run(self.root,self.c,self.plan);self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()});self.assertEqual(c,self.c.to_dict());self.assertEqual(plan,self.plan)
    def test_callable_injection_not_exposed(self):
        with self.assertRaises(TypeError):run(self.root,self.c,self.plan,verifier=lambda e:True)
