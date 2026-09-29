from audit_helpers import *
import subprocess,unittest
from bie.qa.repair_audit_v2.codec import load_request,load_policy
from bie.qa.repair_audit_v2.bridge import prepare_release_evidence

class RunnerTests(AuditFixture):
    def collect(self,fn,timeout=10):
        registry={**self.registry,'numeric':fn}
        ap=replace(self.ap,checks=tuple(replace(x,validator_digest=validator_digest(registry[x.check_id])) for x in self.ap.checks),phase_timeout_seconds=timeout)
        return collect_regression(self.snapshot,self.p,self.root,self.candidate_root,self.policy,ap,registry=registry,as_of=NOW)
    def test_missing_case_is_execution_error(self):
        r=self.collect(omitted_cases);self.assertEqual(r['candidate']['error'],'AUDIT_CASE_COVERAGE')
    def test_actual_worker_exception_recorded(self):
        r=self.collect(exception_cases);self.assertEqual(r['candidate']['error'],'AUDIT_VALIDATOR_EXCEPTION')
    def test_actual_worker_timeout_recorded(self):
        r=self.collect(timeout_cases,1);self.assertEqual(r['candidate']['error'],'AUDIT_WORKER_TIMEOUT')
    def test_validator_mutation_does_not_touch_candidate(self):
        r=self.collect(mutate_cases);self.assertEqual(r['candidate']['error'],'AUDIT_VALIDATOR_MUTATED_COPY')
        self.assertEqual((self.candidate_root/'generated/lesson.txt').read_bytes(),b'2+3')
    def test_validator_extra_file_detected(self):
        r=self.collect(added_file_cases);self.assertEqual(r['candidate']['error'],'AUDIT_VALIDATOR_MUTATED_COPY')
    def test_registry_identity_checked_before_execution(self):
        self.assertRaises(ContractError,collect_regression,self.snapshot,self.p,self.root,self.candidate_root,self.policy,self.ap,registry={**self.registry,'numeric':omitted_cases},as_of=NOW)
    def test_registry_omission_rejected(self):
        self.assertRaises(ContractError,collect_regression,self.snapshot,self.p,self.root,self.candidate_root,self.policy,self.ap,registry={'numeric':numeric_cases},as_of=NOW)
    def test_same_root_not_baseline_and_candidate(self):
        self.assertRaises(ContractError,collect_regression,self.snapshot,self.p,self.root,self.root,self.policy,self.ap,registry=self.registry,as_of=NOW)
    def test_wire_roundtrip(self):
        self.assertEqual(load_request(canonical_bytes(asdict(self.request))),self.request)
        self.assertEqual(load_policy(canonical_bytes(asdict(self.ap))),self.ap)
    def test_wire_unknown_fields_rejected(self):
        obj=asdict(self.request);obj['callback']='arbitrary';self.assertRaises(ContractError,load_request,canonical_bytes(obj))
    def test_policy_cannot_omit_dependency(self):
        self.ap=replace(self.ap,checks=self.ap.checks[1:]);self.assertCode('AUDIT_POLICY_CHECK_COVERAGE')
    def test_policy_cannot_target_wrong_failure(self):
        self.ap=replace(self.ap,targets=(replace(self.ap.targets[0],failure_id='other'),));self.assertCode('AUDIT_TARGET_FAILURE_COVERAGE')
    def test_fixtures_cannot_be_repaired(self):
        self.ap=replace(self.ap,protected_artifact_ids=self.ap.protected_artifact_ids+('lesson',));self.assertCode('AUDIT_PROTECTED_MUTATION')
    def test_case_witness_nan_rejected(self):
        self.assertRaises(ContractError,Observation,'case','PASS',(),'{"number":NaN}')
    def test_case_pass_cannot_hide_failure_reason(self):
        self.assertRaises(ContractError,Observation,'case','PASS',('ERROR',),'{"x":1}')
    def test_unsigned_bridge_never_claims_full_regression_pass(self):
        cand=ReleaseCandidate('2.0.0','candidate',self.snapshot.run_id,self.snapshot.revision,candidate_for(self.snapshot,self.p).artifacts)
        out=prepare_release_evidence(self.request,self.root,self.candidate_root,self.policy,self.ap,cand,as_of=NOW)
        self.assertEqual(out.envelope.status,'NOT_RUN');self.assertEqual(out.envelope.signature,'')
    def test_blocked_bridge_is_fail(self):
        self.edit_regression(lambda x:x['candidate'].update(worker_executed=False))
        cand=ReleaseCandidate('2.0.0','candidate',self.snapshot.run_id,self.snapshot.revision,candidate_for(self.snapshot,self.p).artifacts)
        out=prepare_release_evidence(self.request,self.root,self.candidate_root,self.policy,self.ap,cand,as_of=NOW)
        self.assertEqual(out.envelope.status,'FAIL')
    def test_cli_unsigned_result_and_no_overwrite(self):
        files=[]
        for name,obj in (('request',self.request),('repair-policy',self.policy),('audit-policy',self.ap)):
            path=self.home/(name+'.json');path.write_bytes(canonical_bytes(asdict(obj)));files.append(str(path))
        out=self.home/'report.json';cmd=[sys.executable,'-B','-m','bie.qa.repair_audit_v2',*files,'--original-root',str(self.root),'--candidate-root',str(self.candidate_root),'--as-of',str(NOW),'--output',str(out)]
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,3,result.stderr);raw=out.read_bytes()
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,4);self.assertEqual(out.read_bytes(),raw)

    def test_existing_release_gate_blocks_local_audit(self):
        from bie.qa.release_v2.evaluator import ReleaseEvaluator
        cand=ReleaseCandidate('2.0.0','candidate',self.snapshot.run_id,self.snapshot.revision,candidate_for(self.snapshot,self.p).artifacts)
        out=prepare_release_evidence(self.request,self.root,self.candidate_root,self.policy,self.ap,cand,as_of=NOW)
        path=self.candidate_root/out.envelope.report.path
        path.parent.mkdir(parents=True);path.write_bytes(out.report_bytes)
        result=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',cand,(out.envelope,)),self.candidate_root,as_of=NOW)
        self.assertEqual(result.release_status,'BLOCKED');self.assertFalse(result.product_accepted)
    def test_structural_schemas(self):
        from jsonschema import Draft202012Validator
        pairs=[('audit_request',asdict(self.request)),('audit_policy',asdict(self.ap)),('observation',asdict(obs('case',True,dict(x=1))))]
        for name,data in pairs:
            with self.subTest(schema=name):
                schema=json.loads((ROOT/'docs/qa_section16/batch016'/f'{name}.schema.json').read_text())
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(json.loads(canonical_bytes(data)))
                bad={**data,'unapproved_field':1}
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(bad)))
