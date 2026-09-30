"""Batch002 boundary, source/provenance and structured grading regressions."""
from copy import deepcopy
from fractions import Fraction
from importlib import import_module
import hashlib,json
from pathlib import Path
import unittest
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.runner import PACK_MODULES,load_pack,reference_output,grade_case
from bie.evaluation.benchmarks.domains.structured import amount,quantity

ROOT=Path(__file__).resolve().parents[2]
NEW_TASKS=tuple('BIE-EVAL-'+n for n in ['BIO-001','BIO-002','BIO-003','CHEM-001','CHEM-002','CHEM-003','HIST-001','HIST-002','HIST-003','GEO-001'])

class Batch002Contracts(unittest.TestCase):
    def test_original_registry_exact_order(self):
        body=json.loads((ROOT/'metadata/section17/ORIGINAL_50_TASK_REGISTRY.json').read_text())
        self.assertEqual(list(NEW_TASKS),[t['task_id'] for t in body['rows']][10:20])
    def test_new_task_and_case_ids_are_complete(self):
        for t in NEW_TASKS:
            cases=load_pack(t);self.assertEqual({f'{t}.C{i:03}' for i in range(1,13)},{c.case_id for c in cases})
    def test_authored_cases_not_golden_or_heldout(self):
        for t in NEW_TASKS:
            for c in load_pack(t):
                self.assertEqual('DEVELOPMENT',c.split);self.assertEqual('AUTHORED_DIAGNOSTIC',c.evidence_grade)
    def test_case_source_records_not_empty(self):
        for t in NEW_TASKS:
            for c in load_pack(t):
                self.assertTrue(c.sources);self.assertTrue(c.derivation)
                for s in c.sources:self.assertEqual('REFERENCE_ONLY',s.evidence_kind);self.assertTrue(s.url.startswith('https://'))
    def test_candidate_views_do_not_expose_expected_or_derivation(self):
        for t in NEW_TASKS:
            for c in load_pack(t):
                v=c.candidate_view();self.assertNotIn('expected',v);self.assertNotIn('derivation',v)
    def test_each_new_domain_has_wrong_result_control(self):
        paths={
            'BIO-001':['net_consumed_mol','CO2'],'BIO-002':['probability_sum'],
            'BIO-003':['cardiac_output_L_per_min'],'CHEM-001':['formal_charge_sum'],
            'CHEM-002':['mechanism_experimentally_established'],'CHEM-003':['reactants','hydrogen'],
            'HIST-001':['events',0,'date'],'HIST-002':['causality_proven'],
            'HIST-003':['b_minus_a_days_min'],'GEO-001':['separation_cm_per_yr']}
        for t in NEW_TASKS:
            with self.subTest(task=t):
                c=load_pack(t)[0];answer=deepcopy(c.expected);cursor=answer['values'];path=paths[t.removeprefix('BIE-EVAL-')]
                for key in path[:-1]:cursor=cursor[key]
                key=path[-1];value=cursor[key];cursor[key]=(not value) if type(value) is bool else value+1 if type(value) is int else 'defective-value'
                self.assertEqual('FAIL',grade_case(c,answer)['status'])
    def test_expected_output_extra_fields_fail(self):
        for t in NEW_TASKS:
            c=load_pack(t)[0];answer=deepcopy(c.expected);answer['product_accepted']=True;self.assertEqual('FAIL',grade_case(c,answer)['status'])
    def test_runtime_crash_not_disguised_as_academic_rejection(self):
        module=import_module('bie.evaluation.benchmarks.domains.photosynthesis')
        with patch.object(module,'solve',side_effect=RuntimeError('injected-runtime-fault')):
            with self.assertRaises(RuntimeError):reference_output(NEW_TASKS[0],load_pack(NEW_TASKS[0])[0].inputs)
    def test_every_module_refuses_unknown_operation(self):
        for t in NEW_TASKS:self.assertEqual({'status':'REJECTED','error_code':'UNSUPPORTED_OPERATION'},reference_output(t,{'op':'not-installed'}))
    def test_every_module_refuses_non_object_input(self):
        for t in NEW_TASKS:
            for value in [None,True,3,'answer',[]]:self.assertEqual('REJECTED',reference_output(t,value)['status'])
    def test_reference_input_json_cannot_contain_python_objects(self):
        for value in [Fraction(1,2),object(),{1,2}]:
            with self.assertRaises(BenchmarkError):reference_output(NEW_TASKS[0],{'op':'net_budget','glucose_mol':value})
    def test_fraction_unit_conversion_exact_internal_path(self):
        self.assertEqual(Fraction(3,40),quantity({'value':75,'unit':'mL'},{'mL':Fraction(1,1000)}))
    def test_internal_rational_denominator_resource_bound(self):
        with self.assertRaises(BenchmarkError) as ctx:amount(Fraction(1,2**513))
        self.assertEqual('RATIONAL_SIZE_LIMIT',ctx.exception.code)
    def test_foreign_keys_and_boolean_units_not_coerced(self):
        for data in [{'op':'calvin_budget','co2_mol':1,'approved':True}, {'op':'cardiac_output','stroke_volume':{'value':1,'unit':True},'heart_rate':{'value':1,'unit':'per_min'}}]:
            t=NEW_TASKS[0] if data['op']=='calvin_budget' else NEW_TASKS[2];self.assertEqual('REJECTED',reference_output(t,data)['status'])
    def test_rejection_output_error_code_is_graded(self):
        for t in NEW_TASKS:
            c=next(c for c in load_pack(t) if c.expected['status']=='REJECTED');answer=deepcopy(c.expected);answer['error_code']='MADE_UP_SUCCESS';self.assertEqual('FAIL',grade_case(c,answer)['status'])
    def test_no_reference_replay_authorizes_release(self):
        for t in NEW_TASKS:
            for c in load_pack(t):
                result=grade_case(c,c.expected);self.assertFalse(result['release_authorized']);self.assertFalse(result['product_accepted'])
    def test_original_domain_file_hashes_preserved(self):
        pre=json.loads((ROOT/'metadata/section17/BATCH001_BASELINE_FILES.json').read_text())
        # H1 allows only explicitly traced replacements; the original bytes must still exist.
        # No blanket exemption: both the exact preimage and replacement digest are checked.
        changes_path=ROOT/'metadata/section17/H1_CHANGE_LEDGER.json'
        changes=json.loads(changes_path.read_text())['changes'] if changes_path.exists() else {}
        for name,expected in pre.items():
            current=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            if current==expected:
                self.assertEqual(expected,current,name)
                continue
            self.assertIn(name,changes,name)
            change=changes[name]
            self.assertEqual(expected,change['before_sha256'],name)
            preimage=ROOT/change['preimage']
            if preimage.is_file():
                self.assertEqual(expected,hashlib.sha256(preimage.read_bytes()).hexdigest(),name)
            else:
                # Canonical Git adoption intentionally did not fabricate archive-only
                # H1 preimage bytes. Require the exact package ledger plus an explicit
                # open integration gap instead of silently treating metadata as bytes.
                delta=json.loads((ROOT/'metadata/section17/H1_WORKSPACE_DELTA.json').read_text())
                row=next((r for r in delta['changed_original_files'] if r['path']==name),None)
                self.assertIsNotNone(row,name)
                self.assertEqual(expected,row['before_sha256'],name)
                self.assertEqual(current,row['after_sha256'],name)
                self.assertEqual(change['preimage'],row['preimage'],name)
                gaps=json.loads((ROOT/'docs/section17/integration-r1/KNOWN_GAPS.json').read_text())
                gap=next((g for g in gaps.get('integration_evidence_gaps',[]) if g.get('id')=='H1-PREIMAGE-BYTES-NOT-ADOPTED'),None)
                self.assertIsNotNone(gap,name)
                self.assertEqual('OPEN',gap['status'],name)
                self.assertFalse(gap['bytes_reconstructed'],name)
            self.assertEqual(current,change['after_sha256'],name)
            self.assertTrue(change['justification'],name)
            self.assertIn(change['task_id'],{f'BIE-EVAL-H1-{i:03}' for i in range(1,11)},name)
    def test_source_reference_catalog_does_not_grant_rights(self):
        d=json.loads((ROOT/'metadata/section17/BATCH002_REFERENCE_CATALOG.json').read_text());self.assertFalse(d['independent_review']);self.assertFalse(d['source_bytes_bundled']);self.assertFalse(d['source_ingestion_rights_granted'])

    def test_authored_fixture_builder_reproduces_exact_data_bytes(self):
        import subprocess,sys,tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'rebuilt'
            process=subprocess.run([sys.executable,'-B',str(ROOT/'tools/rebuild_batch002_fixture_data.py'),'--output-dir',str(target)],capture_output=True,text=True,timeout=20)
            self.assertEqual(0,process.returncode,process.stderr)
            for task in NEW_TASKS:
                rel='bie/evaluation/benchmarks/data/'+task+'.json';self.assertEqual((ROOT/rel).read_bytes(),(target/rel).read_bytes())
