"""REPRO contract, tamper, actual clean-process, wire and release-boundary tests."""
from pathlib import Path
from dataclasses import replace,asdict
import copy,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
import jsonschema
from repro18_support import *
from bie.qa.release_v2.contracts import ContractError,ReleaseCandidate
from bie.qa.repair_v2.codec import decode
from bie.qa.reproducibility_v2.models import profile_object,binding
from bie.qa.reproducibility_v2.environment import file_digest
from bie.qa.reproducibility_v2.runner import inventory
from bie.qa.reproducibility_v2.bridge import prepare_release_evidence

ROOT=Path(__file__).resolve().parents[2]

class ReproTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment=capture_environment();cls.control=Fixture(cls.environment);cls.control.actual()
    @classmethod
    def tearDownClass(cls):cls.control.close()
    def setUp(self):self.f=Fixture.clone(self.control)
    def tearDown(self):self.f.close()
    def blocked(self,code):
        self.f.rebind();result=self.f.evaluate();self.assertEqual(result.status,'BLOCKED');self.assertIn(code,codes(result));return result
    def change_artifact(self,field,obj,index=0):
        r=self.f.record['runs'][index][field];data=canonical_bytes(obj);(self.f.evidence/r['path']).write_bytes(data)
        r['sha256']=hashlib.sha256(data).hexdigest();r['size']=len(data)
    def test_output_id_reserved_prefix_budget(self):
        with self.assertRaises(ContractError):OutputSpec('a'*97,'result.json')
    def test_output_root_symlink(self):
        link=self.f.root/'output-link';link.symlink_to(self.f.source_root,target_is_directory=True)
        with self.assertRaisesRegex(ContractError,'REPRO_UNSAFE_OUTPUT_ROOT'):inventory(link,self.f.policy)
    def test_healthy_bounded_checks(self):self.assertEqual(self.f.evaluate().status,'CHECKS_PASSED')
    def test_unsigned_needs_review(self):self.assertEqual(self.f.evaluate(reviews=(),verifier=None).status,'REVIEW_REQUIRED')
    def test_healthy_is_not_product_acceptance(self):self.assertIs(self.f.evaluate().to_dict()['product_accepted'],False)
    def test_exact_source_unicode_preserved(self):
        self.assertIn('जोड़', (self.f.source_root/'lesson.txt').read_text())
        self.assertEqual(self.f.source,self.control.source)
    def test_reports_have_original_ids(self):self.assertEqual([r.task_id for r in self.f.evaluate().reports],[f'BIE-QA-REPRO-{i:03}' for i in range(1,4)])
    def test_no_cross_machine_claim(self):self.assertIs(self.f.evaluate().to_dict()['cross_machine_verified'],False)
    def test_environment_profile_is_cold_venv(self):
        p=profile_object(self.environment);self.assertTrue(p['isolated_prefix']);self.assertFalse(p['system_site_enabled']);self.assertEqual(p['distributions'],[])
    def test_independent_execution_ids(self):self.assertNotEqual(*(r['execution_id'] for r in self.f.record['runs']))
    def test_profile_before_after_equal(self):
        r=self.f.record['runs'][0];self.assertEqual((self.f.evidence/r['environment_before']['path']).read_bytes(),(self.f.evidence/r['environment_after']['path']).read_bytes())
    def test_source_file_modified(self):
        (self.f.source_root/'lesson.txt').write_text('corrupted');self.blocked('ARTIFACT_SIZE_MISMATCH')
    def test_unlisted_source_file(self):
        (self.f.source_root/'hidden.txt').write_text('extra');self.blocked('AUDIT_SNAPSHOT_FILE_SET')
    def test_missing_source(self):
        (self.f.source_root/'lesson.txt').unlink();self.blocked('AUDIT_SNAPSHOT_FILE_SET')
    def test_source_symlink(self):
        p=self.f.source_root/'lesson.txt';p.unlink();p.symlink_to(self.f.source_root/'video.bin');self.blocked('AUDIT_UNSAFE_ENTRY')
    def test_execution_bytes_modified_without_rebinding(self):
        (self.f.evidence/'execution.json').write_bytes(b'{}');self.assertIn('ARTIFACT_SIZE_MISMATCH',codes(self.f.evaluate()))
    def test_output_bytes_tamper(self):
        p=self.f.evidence/self.f.record['runs'][0]['outputs'][0]['path'];p.write_bytes(b'bad');self.blocked('ARTIFACT_SIZE_MISMATCH')
    def test_output_same_size_tamper(self):
        p=self.f.evidence/self.f.record['runs'][0]['outputs'][0]['path'];data=p.read_bytes();p.write_bytes(b'X'+data[1:]);self.blocked('ARTIFACT_HASH_MISMATCH')
    def test_rehashed_output_difference_not_hidden(self):
        row=self.f.record['runs'][1]['outputs'][0];p=self.f.evidence/row['path'];data=p.read_bytes()+b' ';p.write_bytes(data);row.update(sha256=hashlib.sha256(data).hexdigest(),size=len(data));self.blocked('REPRO_OUTPUT_BYTES_DIFFER')
    def test_missing_output_file(self):
        (self.f.evidence/self.f.record['runs'][0]['outputs'][0]['path']).unlink();self.blocked('ARTIFACT_OPEN_OR_READ_FAILED')
    def test_extra_evidence_file(self):
        (self.f.evidence/'hidden.txt').write_text('extra');self.blocked('REPRO_EXTRA_OR_MISSING_EVIDENCE')
    def test_symlink_output(self):
        row=self.f.record['runs'][0]['outputs'][0];p=self.f.evidence/row['path'];p.unlink();p.symlink_to(self.f.evidence/self.f.record['runs'][1]['outputs'][0]['path']);self.blocked('ARTIFACT_OPEN_OR_READ_FAILED')
    def test_hardlink_output(self):
        p=self.f.evidence/self.f.record['runs'][0]['outputs'][0]['path'];q=p.with_name('link.json');os.link(p,q);self.blocked('HARD_LINK_REJECTED')
    def test_duplicate_run_id(self):self.f.record['runs'][1]['execution_id']=self.f.record['runs'][0]['execution_id'];self.blocked('REPRO_EXECUTION_REUSED')
    def test_missing_run(self):self.f.record['runs'].pop();self.blocked('REPRO_RUN_COVERAGE')
    def test_extra_run(self):self.f.record['runs'].append(copy.deepcopy(self.f.record['runs'][0]));self.blocked('REPRO_RUN_COVERAGE')
    def test_run_index_boolean_rejected(self):self.f.record['runs'][0]['index']=True;self.blocked('REPRO_RUN_BINDING')
    def test_process_exit_boolean_rejected(self):self.f.record['runs'][0]['process']['process_exit']=False;self.blocked('REPRO_PRODUCER_NOT_EXECUTED')
    def test_process_unstarted(self):self.f.record['runs'][0]['process']['started']=False;self.blocked('REPRO_PRODUCER_NOT_EXECUTED')
    def test_bootstrap_unstarted(self):self.f.record['runs'][0]['bootstrap']['started']=False;self.blocked('REPRO_ENVIRONMENT_NOT_CREATED')
    def test_probe_unstarted(self):self.f.record['runs'][0]['probe_before_process']['started']=False;self.blocked('REPRO_PROFILE_NOT_MEASURED')
    def test_process_clock_reverse(self):self.f.record['runs'][0]['process']['wall_finished_ns']=1;self.blocked('REPRO_PROCESS_CLOCK')
    def test_process_phase_order(self):self.f.record['runs'][1]['bootstrap']['wall_started_ns']=1;self.blocked('REPRO_PROCESS_ORDER')
    def test_failed_collection_cannot_pass(self):self.f.record['runs'][0]['error']='REPRO_WORKER_TIMEOUT';self.blocked('REPRO_WORKER_TIMEOUT')
    def test_stale_receipt(self):self.f.record['evaluated_at']=NOW-3601;self.blocked('REPRO_RECEIPT_STALE')
    def test_future_receipt(self):self.f.record['evaluated_at']=NOW+1;self.blocked('REPRO_RECEIPT_STALE')
    def test_claimed_acceptance(self):self.f.record['product_accepted']=True;self.blocked('REPRO_SCOPE_CLAIM')
    def test_claimed_full_product(self):self.f.record['full_product_reproduced']=True;self.blocked('REPRO_SCOPE_CLAIM')
    def test_claimed_cross_machine(self):self.f.record['cross_machine_verified']=True;self.blocked('REPRO_SCOPE_CLAIM')
    def test_claimed_security_sandbox(self):self.f.record['hostile_code_sandbox']=True;self.blocked('REPRO_SCOPE_CLAIM')
    def test_changed_collector(self):self.f.record['collector_digest']='a'*64;self.blocked('REPRO_COLLECTOR_IDENTITY')
    def test_changed_probe(self):self.f.record['probe_digest']='a'*64;self.blocked('REPRO_PROBE_IDENTITY')
    def test_unknown_receipt_field(self):self.f.record['ignored_success']=True;self.blocked('REPRO_RECEIPT_FIELDS')
    def test_changed_job_binding(self):self.f.record['binding']['job_id']='another';self.blocked('REPRO_RECEIPT_BINDING')
    def test_changed_run_source_binding(self):self.f.record['runs'][0]['source_digest']='b'*64;self.blocked('REPRO_RUN_BINDING')
    def test_missing_output_row(self):self.f.record['runs'][0]['outputs'].pop();self.blocked('REPRO_OUTPUT_INVENTORY')
    def test_changed_output_role(self):self.f.record['runs'][0]['outputs'][0]['role']='source';self.blocked('REPRO_EVIDENCE_LOCATION')
    def test_redirect_output_path(self):self.f.record['runs'][0]['outputs'][0]['path']=self.f.record['runs'][1]['outputs'][0]['path'];self.blocked('REPRO_EVIDENCE_LOCATION')
    def test_profile_changed_and_rehashed(self):
        row=self.f.record['runs'][0]['environment_before'];obj=json.loads((self.f.evidence/row['path']).read_text());obj['machine']='another';self.change_artifact('environment_before',obj);self.blocked('REPRO_ENVIRONMENT_MISMATCH')
    def test_profile_after_changed_and_rehashed(self):
        row=self.f.record['runs'][0]['environment_after'];obj=json.loads((self.f.evidence/row['path']).read_text());obj['machine']='another';self.change_artifact('environment_after',obj);self.blocked('REPRO_ENVIRONMENT_MUTATED')
    def test_log_hash_tamper(self):
        row=self.f.record['runs'][0]['logs'];obj=json.loads((self.f.evidence/row['path']).read_text());obj['stdout']['sha256']='a'*64;self.change_artifact('logs',obj);self.blocked('REPRO_LOG_HASH')
    def test_log_hex_invalid(self):
        row=self.f.record['runs'][0]['logs'];obj=json.loads((self.f.evidence/row['path']).read_text());obj['stdout'].update(size=1,hex='zz');self.change_artifact('logs',obj);self.blocked('REPRO_LOG_ENCODING')
    def test_log_size_boolean(self):
        row=self.f.record['runs'][0]['logs'];obj=json.loads((self.f.evidence/row['path']).read_text());obj['stdout']['size']=False;self.change_artifact('logs',obj);self.blocked('INVALID_INTEGER')
    def test_changed_system_site_config(self):
        row=self.f.record['runs'][0]['venv_config'];p=self.f.evidence/row['path'];data=p.read_bytes().replace(b'include-system-site-packages = false',b'include-system-site-packages = true');p.write_bytes(data);row.update(sha256=hashlib.sha256(data).hexdigest(),size=len(data));self.blocked('REPRO_VENV_SYSTEM_PACKAGES')
    def test_golden_mismatch(self):
        self.f.policy=replace(self.f.policy,outputs=(replace(self.f.policy.outputs[0],golden_sha256='c'*64),self.f.policy.outputs[1]));self.f.record['binding']=binding(self.f.request.job_id,self.f.source,self.f.policy);self.blocked('REPRO_GOLDEN_HASH_MISMATCH')
    def test_correct_golden(self):
        self.f.policy=replace(self.f.policy,outputs=(replace(self.f.policy.outputs[0],golden_sha256=self.f.record['runs'][0]['outputs'][0]['sha256']),self.f.policy.outputs[1]));self.f.record['binding']=binding(self.f.request.job_id,self.f.source,self.f.policy);self.f.rebind();self.assertEqual(self.f.evaluate().status,'CHECKS_PASSED')
    def test_old_review_cannot_authorize_changed_request(self):
        reviews=self.f.reviews;self.f.record['runs'][0]['execution_id']='updated-exec';self.f.rebind();self.assertEqual(self.f.evaluate(reviews=reviews).status,'REVIEW_REQUIRED')
    def test_test_only_key_cannot_authorize(self):self.assertEqual(self.f.evaluate(verifier=ReviewVerifier((replace(KEY,assurance='test_only'),))).status,'REVIEW_REQUIRED')
    def test_revoked_key(self):self.assertEqual(self.f.evaluate(verifier=ReviewVerifier((replace(KEY,enabled=False),))).status,'REVIEW_REQUIRED')
    def test_duplicate_review(self):
        with self.assertRaises(ContractError):self.f.evaluate(reviews=self.f.reviews+self.f.reviews[:1])
    def test_unexpected_review(self):
        self.assertIn('REPRO_UNEXPECTED_REVIEW',codes(self.f.evaluate(reviews=(replace(self.f.reviews[0],subject_id='other'),))))
    def test_input_type(self):
        with self.assertRaises(ContractError):evaluate({},self.f.source_root,self.f.evidence,self.f.policy,as_of=NOW)
    def test_root_overlap(self):self.assertIn('REPRO_ROOT_OVERLAP',codes(evaluate(self.f.request,self.f.source_root,self.f.source_root,self.f.policy,as_of=NOW)))
    def test_existing_collector_destination(self):
        with self.assertRaisesRegex(ContractError,'REPRO_NEW_EVIDENCE_ROOT_REQUIRED'):collect('job',self.f.source,self.f.source_root,self.f.evidence,self.f.policy,as_of=NOW)
    def test_wrong_interpreter_identity(self):
        with self.assertRaisesRegex(ContractError,'REPRO_INTERPRETER_IDENTITY'):collect('job',self.f.source,self.f.source_root,self.f.root/'new',self.f.policy,as_of=NOW,python='/bin/true')
    def test_source_policy_mismatch(self):
        with self.assertRaisesRegex(ContractError,'REPRO_SOURCE_POLICY_BINDING'):collect('job',self.f.source,self.f.source_root,self.f.root/'new',replace(self.f.policy,source_digest='c'*64),as_of=NOW)
    def test_producer_identity_mismatch(self):
        with self.assertRaisesRegex(ContractError,'REPRO_PRODUCER_IDENTITY'):collect('job',self.f.source,self.f.source_root,self.f.root/'new',replace(self.f.policy,producer_sha256='b'*64),as_of=NOW)
    def test_deterministic_report_recomputation(self):self.assertEqual(self.f.evaluate().to_dict(),self.f.evaluate().to_dict())
    def test_schema_policy(self):jsonschema.validate(json.loads(canonical_bytes(asdict(self.f.policy))),json.loads((ROOT/'docs/qa_section16/batch018/repro_policy.schema.json').read_text()))
    def test_schema_request(self):jsonschema.validate(json.loads(canonical_bytes(asdict(self.f.request))),json.loads((ROOT/'docs/qa_section16/batch018/repro_request.schema.json').read_text()))
    def test_schema_output(self):jsonschema.validate(asdict(self.f.policy.outputs[0]),json.loads((ROOT/'docs/qa_section16/batch018/output_spec.schema.json').read_text()))
    def test_wire_roundtrip_policy(self):self.assertEqual(decode(json.loads(canonical_bytes(asdict(self.f.policy))),ReproPolicy),self.f.policy)
    def test_wire_roundtrip_request(self):self.assertEqual(decode(json.loads(canonical_bytes(asdict(self.f.request))),ReproRequest),self.f.request)
    def test_cli_unsigned(self):
        p=self.f.root/'policy.json';q=self.f.root/'request.json';out=self.f.root/'out.json'
        p.write_bytes(canonical_bytes(asdict(self.f.policy)));q.write_bytes(canonical_bytes(asdict(self.f.request)))
        args=[sys.executable,'-B','-m','bie.qa.reproducibility_v2','--request',str(q),'--policy',str(p),'--source-root',str(self.f.source_root),'--evidence-root',str(self.f.evidence),'--as-of',str(NOW),'--output',str(out)]
        r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,3,r.stderr);self.assertEqual(json.loads(out.read_text())['status'],'REVIEW_REQUIRED')
        r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,4)
    def candidate(self):return ReleaseCandidate('2.0.0', 'release-candidate',self.f.source.run_id,self.f.source.revision,tuple(r for r in self.f.source.artifacts if r.role in ('source','video','game')))
    def test_bridge_not_full_pass(self):
        ev=prepare_release_evidence(self.f.request,self.f.source_root,self.f.evidence,self.f.policy,self.candidate(),as_of=NOW,reviews=self.f.reviews,verifier=VERIFIER)
        self.assertEqual(ev.envelope.status,'NOT_RUN');self.assertEqual(ev.envelope.signature,'');self.assertEqual(ev.envelope.gate_id,'reproducibility')
    def test_bridge_detects_blocker(self):
        (self.f.source_root/'lesson.txt').write_bytes(b'changed');ev=prepare_release_evidence(self.f.request,self.f.source_root,self.f.evidence,self.f.policy,self.candidate(),as_of=NOW);self.assertEqual(ev.envelope.status,'FAIL')
    def test_bridge_wrong_candidate(self):
        with self.assertRaises(ContractError):prepare_release_evidence(self.f.request,self.f.source_root,self.f.evidence,self.f.policy,replace(self.candidate(),revision='b'*40),as_of=NOW)

# Each generated method is one separately collected boundary test, not a subcase count.
def _policy_test(field,value):
    def test(self):
        with self.assertRaises(ContractError):replace(self.f.policy,**{field:value})
    return test
for name,field,value in [('one_run','repetitions',1),('too_many_runs','repetitions',6),('bool_seed','seed',True),('negative_seed','seed',-1),('large_seed','seed',2**32),('zero_timeout','timeout_seconds',0),('large_timeout','timeout_seconds',61),('zero_size','max_output_bytes',0),('large_size','max_output_bytes',16777217),('zero_age','max_receipt_age_seconds',0),('no_outputs','outputs',()),('params_not_object','parameters_json','[]'),('params_not_canonical','parameters_json','{ "a":1}'),('unbounded_float','parameters_json','{"a":0.1}'),('zero_producer_hash','producer_sha256','0'*64),('unknown_environment','environment_json','{}')]:
    setattr(ReproTests,'test_policy_'+name,_policy_test(field,value))

class ActualProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.environment=capture_environment()
    def execute(self,script,code=None,timeout=10,limit=16777216):
        f=Fixture(self.environment,script)
        try:
            f.policy=replace(f.policy,timeout_seconds=timeout,max_output_bytes=limit);f.actual();result=f.evaluate()
            if code:self.assertIn(code,codes(result));self.assertEqual(result.status,'BLOCKED')
            else:self.assertEqual(result.status,'CHECKS_PASSED')
            self.assertEqual(len(f.record['runs']),2)
            self.assertEqual((f.source_root/'producer.py').read_text(),script)
            return result
        finally:f.close()
    def test_actual_different_outputs(self):self.execute(NONDETERMINISTIC,'REPRO_OUTPUT_BYTES_DIFFER')
    def test_actual_missing_output(self):self.execute(MISSING,'REPRO_OUTPUT_INVENTORY')
    def test_actual_extra_output(self):self.execute(EXTRA,'REPRO_OUTPUT_INVENTORY')
    def test_actual_symlink_output(self):self.execute(LINK,'REPRO_UNSAFE_OUTPUT')
    def test_actual_mutated_input(self):self.execute(MUTATE,'ARTIFACT_SIZE_MISMATCH')
    def test_actual_producer_exception(self):self.execute(FAIL,'REPRO_PRODUCER_EXIT')
    def test_actual_worker_timeout(self):self.execute(TIMEOUT,'REPRO_WORKER_TIMEOUT',timeout=1)
    def test_actual_output_budget(self):self.execute(GOOD,'REPRO_OUTPUT_SIZE',limit=1)
    def test_actual_unset_secret(self):
        old=os.environ.get('BIE_TEST_SECRET');os.environ['BIE_TEST_SECRET']='never-copy-to-worker'
        try:self.execute(GOOD+"\nimport os\nassert 'BIE_TEST_SECRET' not in os.environ\n")
        finally:
            if old is None:os.environ.pop('BIE_TEST_SECRET',None)
            else:os.environ['BIE_TEST_SECRET']=old
    def test_actual_hashseed_control(self):self.execute(GOOD+"\n(p/'game.json').write_text(str(hash('reproduction-hash-seed')))\n")

if __name__=='__main__':unittest.main()
