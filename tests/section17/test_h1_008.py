import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from h1_helpers import production_fixture,gate_fixture_args
from bie.evaluation.benchmarks.release.coverage import verify_coverage
from bie.evaluation.benchmarks.release import gate
class CoverageMatrixBoundary(unittest.TestCase):
    def setUp(self):self.m,self.p,self.rows,self.b,self.c,self.tr,self.tokens=production_fixture()
    def check(self):return verify_coverage(self.m,self.c,expected_sha256=digest(self.c))
    def test_full_two_domain_matrix_verifies(self):self.assertEqual('VERIFIED',self.check()['status']);self.assertEqual(34,len(self.check()['cells']))
    def test_diagonal_only_matrix_blocks(self):
        self.m['cases']=[r for i,r in enumerate(self.m['cases']) if i%2==0]
        self.assertEqual('BLOCKED',self.check()['status'])
    def test_single_missing_cell_blocks(self):self.m['cases'].pop();self.assertEqual('BLOCKED',self.check()['status'])
    def test_unknown_domain_roster_rejects(self):
        self.c['domains'].pop()
        with self.assertRaisesRegex(BenchmarkError,'DOMAIN_ROSTER'):self.check()
    def test_dropped_metric_from_contract_rejects(self):
        self.c['domains'][0]['metrics'].pop()
        with self.assertRaises(BenchmarkError):self.check()
    def test_zero_independent_minimum_rejects(self):
        self.c['domains'][0]['metrics'][0]['minimum_groups']=0
        with self.assertRaises(BenchmarkError):self.check()
    def test_bool_independent_minimum_rejects(self):
        self.c['domains'][0]['metrics'][0]['minimum_groups']=True
        with self.assertRaises(BenchmarkError):self.check()
    def test_renamed_duplicate_reference_not_independent(self):
        x=deepcopy(self.m['cases'][0]);x['context']['case_id']='renamed';x['leakage_group']='newgroup';self.m['cases'].append(x)
        self.c['domains'][0]['metrics'][0]['minimum_groups']=2
        self.assertEqual('BLOCKED',self.check()['status'])
    def test_repeated_leakage_group_not_independent(self):
        x=deepcopy(self.m['cases'][0]);x['context']['case_id']='new';x['context']['reference_sha256']=digest('other');self.m['cases'].append(x)
        self.c['domains'][0]['metrics'][0]['minimum_groups']=2;self.assertEqual('BLOCKED',self.check()['status'])
    def test_independent_reference_and_group_increases_count(self):
        x=deepcopy(self.m['cases'][0]);x['context']['case_id']='new';x['context']['reference_sha256']=digest('other');x['leakage_group']='new';self.m['cases'].append(x)
        self.c['domains'][0]['metrics'][0]['minimum_groups']=2;self.assertEqual('VERIFIED',self.check()['status'])
    def test_wrong_contract_pin_rejects(self):
        with self.assertRaisesRegex(BenchmarkError,'SNAPSHOT_MISMATCH'):verify_coverage(self.m,self.c,expected_sha256='0'*64)
    def test_missing_contract_blocks_public_production_gate(self):
        a=gate_fixture_args();a.pop('coverage_contract');o=gate.evaluate(**a)
        self.assertIn('MISSING_DOMAIN_METRIC_COVERAGE_CONTRACT',o['reasons'])
    def test_synthetic_full_production_contract_not_deployment_permission(self):
        o=gate.evaluate(**gate_fixture_args());self.assertEqual('PASS',o['outcome']);self.assertFalse(o['release_authorized']);self.assertFalse(o['product_accepted'])
    def test_attestation_scope_changes_with_contract(self):
        a=gate_fixture_args();a['coverage_contract']['domains'][0]['metrics'][0]['minimum_groups']=2
        a['expected_coverage_sha256']=digest(a['coverage_contract']);o=gate.evaluate(**a)
        self.assertIn('ATTESTATION_SCOPE_MISMATCH',o['reasons'])


class ProductionCLIInputBoundary(unittest.TestCase):
    def invoke(self,root,*,omit_bundle=False,bad_pin=False):
        import base64,os,json,io
        from contextlib import redirect_stdout,redirect_stderr
        from bie.evaluation.benchmarks.release import __main__ as cli
        a=gate_fixture_args();env={};metadata={}
        for name,row in a['trust'].items():
            variable='BIE_ATTEST_H1_'+name.upper()
            env[variable]=base64.b64encode(row['secret']).decode()
            metadata[name]={k:v for k,v in row.items() if k!='secret'}
            metadata[name]['secret_env']=variable
        docs={'manifest':a['manifest'],'policy':a['policy'],'assessments':a['assessments'],
              'attestations':a['attestations'],'artifact-evidence':a['artifacts'],'trust-metadata':metadata,
              'coverage-contract':a['coverage_contract'],'assessment-authorizations':a['assessment_tokens']}
        if not omit_bundle:docs['candidate-bundle']=a['candidate_bundle']
        argv=[]
        for name,body in docs.items():
            path=root/(name+'.json');path.write_text(json.dumps(body));argv+=['--'+name,str(path)]
        argv+=['--manifest-sha256',digest(a['manifest']),'--policy-sha256',digest(a['policy']),
               '--coverage-sha256',('0'*64 if bad_pin else digest(a['coverage_contract'])),
               '--database',str(root/'release.sqlite3'),'--campaign-id','cli-h1','--attempt-id','cli-h1',
               '--output-dir',str(root/'out')]
        with patch.dict(os.environ,env),patch.object(cli.time,'time',return_value=1000),redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            result=cli.main(argv)
        saved=json.loads((root/'out/RELEASE_RESULT.json').read_text())
        return result,saved
    def test_all_hardened_inputs_reach_cli_gate(self):
        with tempfile.TemporaryDirectory() as d:r,s=self.invoke(Path(d))
        self.assertEqual(0,r);self.assertEqual('PASS',s['report']['outcome']);self.assertFalse(s['report']['product_accepted'])
    def test_cli_absent_bundle_blocks_and_persists(self):
        with tempfile.TemporaryDirectory() as d:r,s=self.invoke(Path(d),omit_bundle=True)
        self.assertEqual(2,r);self.assertIn('MISSING_CANDIDATE_BUNDLE',s['report']['reasons'])
    def test_cli_wrong_coverage_pin_blocks_and_persists(self):
        with tempfile.TemporaryDirectory() as d:r,s=self.invoke(Path(d),bad_pin=True)
        self.assertEqual(2,r);self.assertIn('SNAPSHOT_MISMATCH',s['report']['reasons'])
