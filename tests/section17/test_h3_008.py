import unittest,tempfile,shutil,json,hashlib,os,subprocess,sys
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import *

from bie.evaluation.benchmarks.adoption.ledger import AdoptionStore
from bie.evaluation.benchmarks.adoption.release import evaluate as release_av
class GovernedReleaseTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=AdoptionStore(self.root/'eval.db');self.m,self.p,self.rows,self.a=gate_inputs()
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def run_gate(self,**kw):
        opts=dict(adoption_policy=self.a,expected_adoption_sha256=digest(self.a),store=self.store,expected_manifest_sha256=digest(self.m),expected_policy_sha256=digest(self.p));opts.update(kw)
        return release_av(self.m,self.p,self.rows,**opts)
    def fill(self):
        for n in (12,13,15):store_run(self.store,n)
    def test_fresh_stored_profiles_flow_through_existing_gate(self):
        self.fill();r=self.run_gate();self.assertEqual('DIAGNOSTIC_PASS',r['outcome']);self.assertEqual(3,len(r['adopted_assessment_sha256s']));self.assertFalse(r['release_authorized'])
    def test_missing_actual_runs_block_even_with_human_pass(self):
        r=self.run_gate();self.assertEqual('BLOCKED',r['outcome']);self.assertIn('AV_RUN_UNKNOWN',r['reasons'])
    def test_one_missing_av_case_blocks(self):
        store_run(self.store,12);store_run(self.store,13);self.assertEqual('BLOCKED',self.run_gate()['outcome'])
    def test_caller_cannot_submit_deterministic_pass(self):
        self.rows.append(make_assessment(context(12),'av-deterministic-v3','DETERMINISTIC','1'))
        with self.assertRaisesRegex(BenchmarkError,'AV_ASSESSMENT_INJECTION_REJECTED'):self.run_gate()
    def test_cannot_omit_metric_from_governed_roster(self):
        self.a['required_cases'].pop()
        with self.assertRaisesRegex(BenchmarkError,'AV_RELEASE_COVERAGE_WEAKENED'):self.run_gate()
    def test_wrong_policy_pin_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'AV_RELEASE_POLICY_PIN'):self.run_gate(expected_adoption_sha256='0'*64)
    def test_store_like_candidate_object_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'TRUSTED_AV_STORE_REQUIRED'):self.run_gate(store={})
    def test_changed_context_cannot_reuse_run(self):
        self.fill();self.m['cases'][0]['context']['candidate_sha256']='0'*64;self.rows[0]=make_assessment(self.m['cases'][0]['context'],'human','HUMAN','1',execution='FIXTURE');self.assertEqual('BLOCKED',self.run_gate()['outcome'])
    def test_original_human_agreement_gate_still_required(self):
        self.fill();self.rows=[];r=self.run_gate();self.assertEqual('BLOCKED',r['outcome']);self.assertIn('AGREEMENT_INCOMPLETE',r['reasons'])
    def test_changed_campaign_pin_blocks_stored_runs(self):
        self.fill();self.a['campaign_sha256']='0'*64;self.assertEqual('BLOCKED',self.run_gate()['outcome'])
    def test_production_cannot_use_three_metric_diagnostic_roster(self):
        self.p['mode']='PRODUCTION'
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_unexpected_native_job_cannot_be_injected(self):
        with self.assertRaisesRegex(BenchmarkError,'UNEXPECTED_NATIVE_EVIDENCE_CASE'):self.run_gate(native_jobs={'unknown':{'passed':True}})
    def test_wrong_base_policy_pin_rejected_before_store_reads(self):
        with patch.object(self.store,'get') as get,self.assertRaisesRegex(BenchmarkError,'SNAPSHOT_MISMATCH'):
            self.run_gate(expected_policy_sha256='0'*64)
        get.assert_not_called()
    def test_production_blocked_assessment_does_not_crash_gate(self):
        from batch005_helpers import cohort
        self.m,self.p,all_rows=cohort(all_metrics=True,production=True)
        cg=campaign();cg['split']='HOLDOUT';ref,c=fixture(12);c['media']['path']='absent.mkv'
        cx=context(12,ref,c);cx['split']='HOLDOUT'
        store_run(self.store,12,contract=cg,ref=ref,candidate=c,ctx=cx)
        replacements={12:cx}
        for n in (13,15):
            v=context(n);v['split']='HOLDOUT';replacements[n]=v
        for row in self.m['cases']:
            n=int(row['context']['metric_id'].split('-')[-1])
            if n in replacements:row['context']=replacements[n]
        self.a={'schema_version':'av-release-policy-3','campaign_sha256':digest(cg),'required_cases':['av12','av13','av15']}
        self.p['aggregation']['raters'][0]['id']='av-deterministic-v3';self.rows=[]
        result=self.run_gate();self.assertEqual('BLOCKED',result['outcome']);self.assertIn('AV_PROFILE_NOT_PASSING',result['reasons']);self.assertFalse(result['product_accepted'])
