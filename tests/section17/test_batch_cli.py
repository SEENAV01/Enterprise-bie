from copy import deepcopy
import json,os,subprocess,sys
from pathlib import Path
from helpers import Base
from bie.evaluation.benchmarks.runner import PACK_MODULES,load_pack,reference_output

ROOT=Path(__file__).resolve().parents[2]
class BatchCLITests(Base):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-B','-m','bie.evaluation.benchmarks',*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=20)
    def grade_args(self,out='graded',**kw):
        answers=[{'case_id':c.case_id,'output':reference_output(c.task_id,c.inputs)} for t in PACK_MODULES for c in load_pack(t)]
        self.answers_file=self.root/'answers.json';self.answers_file.write_text(json.dumps(answers))
        return ['grade','--answers',self.answers_file,'--candidate-sha','e'*64,'--database',self.root/'ledger.sqlite3','--campaign-id','test-campaign','--run-id','test-run','--output-dir',self.root/out]
    def test_diagnostic_cli_writes_real_persisted_report(self):
        p=self.run_cli('diagnostic','--output-dir',self.root/'diagnostic');self.assertEqual(0,p.returncode,p.stderr);r=json.loads((self.root/'diagnostic/RESULT.json').read_text());self.assertEqual(sum(len(load_pack(t)) for t in PACK_MODULES),r['report']['passed_count']);self.assertIn('NOT_BIE',r['scope'])
    def test_export_prompts_redacts_answers(self):
        p=self.run_cli('export-prompts','--output',self.root/'prompts.json');self.assertEqual(0,p.returncode,p.stderr);r=json.loads((self.root/'prompts.json').read_text());self.assertEqual(sum(len(load_pack(t)) for t in PACK_MODULES),len(r['cases']));self.assertFalse(any('expected' in c for c in r['cases']))
    def test_grade_external_structured_file(self):
        p=self.run_cli(*self.grade_args());self.assertEqual(0,p.returncode,p.stderr);r=json.loads((self.root/'graded/RESULT.json').read_text());self.assertFalse(r['native_bie_execution_verified'])
    def test_scientific_mutation_returns_nonzero(self):
        args=self.grade_args();a=json.loads(self.answers_file.read_text());a[0]['output']={'status':'OK','values':{'wrong':'answer'}};self.answers_file.write_text(json.dumps(a));p=self.run_cli(*args);self.assertEqual(1,p.returncode,p.stderr)
    def test_repeated_candidate_attempt_blocked_across_processes(self):
        args=self.grade_args();self.assertEqual(0,self.run_cli(*args).returncode);args[-1]=self.root/'second';p=self.run_cli(*args);self.assertEqual(2,p.returncode);self.assertIn('ATTEMPT_ALREADY_CLAIMED',p.stderr)
    def test_output_directory_not_overwritten(self):
        d=self.root/'existing';d.mkdir();(d/'sentinel').write_text('keep');p=self.run_cli('diagnostic','--output-dir',d);self.assertEqual(2,p.returncode);self.assertEqual(['sentinel'],[f.name for f in d.iterdir()])
    def test_duplicate_json_keys_rejected_at_boundary(self):
        args=self.grade_args();self.answers_file.write_text('[{"case_id":"a","case_id":"b","output":{}}]');p=self.run_cli(*args);self.assertEqual(2,p.returncode);self.assertIn('DUPLICATE_JSON_KEY',p.stderr)
    def test_oversized_submission_blocked(self):
        args=self.grade_args();self.answers_file.write_bytes(b' '*2_000_001);p=self.run_cli(*args);self.assertEqual(2,p.returncode);self.assertIn('SUBMISSION_SIZE_LIMIT',p.stderr)
