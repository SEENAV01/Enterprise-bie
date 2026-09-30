import unittest,subprocess,sys,tempfile,json,os,base64
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from batch005_helpers import ROOT,cohort,judgement_fixture,FixtureProvider,trust,token,NOW,TEST_KEY
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.release import model,gate
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
class Batch005AuditContracts(unittest.TestCase):
    def test_unexpected_adapter_exception_is_recorded_blocked(self):
        ctx,rubric,reference,candidate,_=judgement_fixture()
        p=FixtureProvider(error=RuntimeError('secret-error-message'))
        out=model.execute(ctx,rubric,reference,candidate,provider=p,provider_id=p.provider_id,model_version=p.model_version,assessor_id='model')
        self.assertEqual('BLOCKED',out['status']);self.assertNotIn('secret-error-message',canonical_json(out))
    def test_gate_records_evaluation_time_for_attestation_audit(self):
        m,p,a=cohort();out=gate.evaluate(m,p,a,expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p),now=NOW)
        self.assertEqual(NOW,out['evaluated_at'])
    def test_signed_evidence_identity_is_in_report(self):
        m,p,a=cohort();p['required_attestations']=['POLICY_APPROVAL'];blob={'authored':True}
        t=token('POLICY_APPROVAL',gate.evidence_scope(m,p,a),{'outcome':'PASS','evidence_sha256':digest(blob)})
        out=gate.evaluate(m,p,a,expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p),now=NOW,
                          attestations=[t],trust=trust(roles=['POLICY_APPROVAL']),artifacts={digest(blob):blob})
        self.assertEqual(digest(t),out['attestations'][0]['attestation_sha256'])
    def test_ledger_external_evidence_inputs_are_bound(self):
        m,p,a=cohort()
        with tempfile.TemporaryDirectory() as tmp,ReleaseLedger(Path(tmp)/'audit.sqlite3') as db:
            out=db.execute(campaign_id='campaign',attempt_id='attempt',manifest=m,policy=p,assessments=a,
                           expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p),now=NOW)
            self.assertIn('external_evidence_inputs_sha256',out)
    def test_integrity_digest_is_not_declared_signature(self):
        # Structural consistency only; authentication is the separate attestation service.
        from bie.evaluation.benchmarks.release.contracts import make_assessment,assessment
        from batch005_helpers import ctx
        o=make_assessment(ctx(),'det','DETERMINISTIC',1)
        self.assertNotIn('signature',o);self.assertEqual(o,assessment(o))
    def test_no_automatic_external_provider_configuration(self):
        ctx,rubric,reference,candidate,_=judgement_fixture()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'not-a-real-key','GEMINI_API_KEY':'not-a-real-key'}):
            o=model.execute(ctx,rubric,reference,candidate,provider=None,provider_id='none',model_version='none',assessor_id='model')
            self.assertEqual('BLOCKED',o['status'])
    def test_all_registry_task_names_for_new_batch_are_unchanged(self):
        rows=json.loads((ROOT/'metadata/section17/ORIGINAL_50_TASK_REGISTRY.json').read_text())['rows']
        expected=['BIE-EVAL-METRIC-017']+[f'BIE-EVAL-RATER-{i:03}' for i in range(1,6)]+[f'BIE-EVAL-REL-{i:03}' for i in range(1,5)]
        self.assertEqual(expected,[r['task_id'] for r in rows[40:50]])
class Batch005CLIContracts(unittest.TestCase):
    def invoke(self,m,p,a,path,extra=()):
        for name,v in [('manifest',m),('policy',p),('assessments',a)]: (path/(name+'.json')).write_text(json.dumps(v))
        command=[sys.executable,'-B','-m','bie.evaluation.benchmarks.release','--manifest',str(path/'manifest.json'),
            '--policy',str(path/'policy.json'),'--assessments',str(path/'assessments.json'),
            '--manifest-sha256',digest(m),'--policy-sha256',digest(p),'--database',str(path/'release.sqlite3'),
            '--campaign-id','cli-campaign','--attempt-id','cli-attempt','--output-dir',str(path/'output'),*extra]
        return subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=20)
    def test_cli_actual_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);r=self.invoke(*cohort(),path);self.assertEqual(0,r.returncode,r.stderr)
            saved=json.loads((path/'output/RELEASE_RESULT.json').read_text());self.assertEqual('DIAGNOSTIC_PASS',saved['report']['outcome'])
            with ReleaseLedger(path/'release.sqlite3') as db:self.assertEqual(saved,db.get('cli-attempt'))
    def test_cli_missing_rater_nonzero_and_receipt(self):
        m,p,a=cohort();a.pop()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);r=self.invoke(m,p,a,path);self.assertEqual(2,r.returncode,r.stderr);self.assertTrue((path/'output/RELEASE_RESULT.json').exists())
    def test_cli_no_output_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'output').mkdir();r=self.invoke(*cohort(),path);self.assertEqual(2,r.returncode);self.assertIn('OUTPUT_ALREADY_EXISTS',r.stderr)
    def test_cli_missing_trust_secret_fails_closed(self):
        metadata={'key':{'secret_env':'BIE_ATTEST_TEST_ABSENT','subject_id':'reviewer','roles':['POLICY_APPROVAL'],'not_before':0,'expires_at':99999,'revoked':False,'fixture_only':True}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);f=path/'trust.json';f.write_text(json.dumps(metadata));r=self.invoke(*cohort(),path,extra=['--trust-metadata',str(f)])
            self.assertEqual(2,r.returncode);self.assertIn('ATTESTATION_SECRET_UNAVAILABLE',r.stderr)
    def test_trust_loader_no_packaged_production_key(self):
        from bie.evaluation.benchmarks.release.__main__ import load_trust
        self.assertEqual({},load_trust(None))
    def test_trust_loader_restricted_environment_names(self):
        from bie.evaluation.benchmarks.release.__main__ import load_trust
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'trust.json';p.write_text(json.dumps({'k':{'secret_env':'PATH','subject_id':'r','roles':['REVIEW'],'not_before':0,'expires_at':99999,'revoked':False,'fixture_only':True}}))
            with self.assertRaisesRegex(BenchmarkError,'INVALID_SECRET_ENV_NAME'):load_trust(p)
    def test_trust_loader_base64_decodes_without_logging_key(self):
        from bie.evaluation.benchmarks.release.__main__ import load_trust
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'BIE_ATTEST_TEST':base64.b64encode(TEST_KEY).decode()}):
            p=Path(tmp)/'trust.json';p.write_text(json.dumps({'k':{'secret_env':'BIE_ATTEST_TEST','subject_id':'r','roles':['REVIEW'],'not_before':0,'expires_at':99999,'revoked':False,'fixture_only':True}}))
            self.assertEqual(TEST_KEY,load_trust(p)['k']['secret'])
    def test_json_duplicate_keys_refused_by_cli_loader(self):
        from bie.evaluation.benchmarks.release.__main__ import read_json
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json';p.write_text('{"score":0,"score":1}')
            with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_JSON_KEY'):read_json(p)
