from dataclasses import replace
from pathlib import Path
import json
import sys
import tempfile
import unittest
from bie.compiler.deterministic_output_qa import *
from tests.compiler.qa_test_support import ROOT, context, case_raw, bundle

class DeterminismQATests(unittest.TestCase):
    def setUp(self):self.ctx=context();self.files=(('src/a.ts','export const x=1;\n'),('src/b.ts','export const y=2;\n'))
    def snap(self,files=None,ctx=None):return snapshot_generated(files or self.files,ctx or self.ctx)
    def test_file_input_order_does_not_affect_snapshot(self):self.assertEqual(self.snap(),self.snap(tuple(reversed(self.files))))
    def test_exact_source_bytes_repeated(self):self.assertTrue(check_deterministic_generator(lambda:self.files,self.ctx).passed)
    def test_content_mutation_detected(self):
        r=compare_snapshots((self.snap(),self.snap((('src/a.ts','changed'),('src/b.ts',self.files[1][1])))),expected_runs=2)
        self.assertIn('DETERMINISM_BYTES_CHANGED',{f.code for f in r.findings})
    def test_line_endings_are_not_silently_normalized(self):
        a=snapshot_generated((('a.ts','x\n'),),self.ctx);b=snapshot_generated((('a.ts','x\r\n'),),self.ctx)
        self.assertFalse(compare_snapshots((a,b),expected_runs=2).passed)
    def test_file_addition_detected(self):
        r=compare_snapshots((self.snap(),self.snap(self.files+(('c.ts','new'),))),expected_runs=2)
        self.assertIn('DETERMINISM_FILE_ADDED',{f.code for f in r.findings})
    def test_file_removal_detected(self):
        r=compare_snapshots((self.snap(),self.snap(self.files[:1])),expected_runs=2)
        self.assertIn('DETERMINISM_FILE_MISSING',{f.code for f in r.findings})
    def test_changed_seed_cannot_be_compared_as_identical_context(self):
        self.assertFalse(compare_snapshots((self.snap(),self.snap(ctx=context(2))),expected_runs=2).passed)
    def test_changed_dependency_identity_detected(self):
        self.assertFalse(compare_snapshots((self.snap(),self.snap(ctx=replace(self.ctx,dependency_identity='b'*64))),expected_runs=2).passed)
    def test_empty_source_tree_is_not_success(self):
        with self.assertRaises(ValueError):snapshot_generated((),self.ctx)
    def test_duplicate_source_path_rejected(self):
        with self.assertRaises(ValueError):snapshot_generated((('a.ts','1'),('a.ts','2')),self.ctx)
    def test_traversal_source_path_rejected(self):
        with self.assertRaises(ValueError):snapshot_generated((('../a.ts','1'),),self.ctx)
    def test_single_run_not_determinism_proof(self):
        with self.assertRaises(ValueError):compare_snapshots((self.snap(),),expected_runs=1)
    def test_missing_repeat_never_passes(self):self.assertFalse(compare_snapshots((self.snap(),),expected_runs=2).passed)
    def test_corrupted_snapshot_rejected(self):
        with self.assertRaises(ValueError):compare_snapshots((self.snap(),replace(self.snap(),files_sha256='b'*64)),expected_runs=2)
    def test_generator_exception_is_failure_not_skipped(self):
        def fail():raise RuntimeError('fixture failure')
        r=check_deterministic_generator(fail,self.ctx);self.assertFalse(r.passed);self.assertEqual(r.runs_completed,0)
    def test_mutable_generator_counter_detected(self):
        counts=[]
        def changing():counts.append(1);return (('a.ts',str(len(counts))),)
        self.assertFalse(check_deterministic_generator(changing,self.ctx).passed)
    def test_actual_bie_generator_repeatable(self):
        from bie.compiler.qa_scene_compile import compile_scene_for_qa
        raw=case_raw('physics-vector')['document'];b=bundle('physics-vector')
        r=check_deterministic_generator(lambda:compile_scene_for_qa(raw).codegen.files,b.context,runs=3)
        self.assertTrue(r.passed)
    def test_directory_snapshot_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a.ts').write_text('x');(root/'b.ts').symlink_to(root/'a.ts')
            with self.assertRaises(ValueError):snapshot_directory(root,self.ctx)
    def test_directory_snapshot_budget_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a.ts').write_text('large')
            with self.assertRaises(ValueError):snapshot_directory(root,self.ctx,max_total_bytes=2)
    def test_directory_empty_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):snapshot_directory(Path(td),self.ctx)
    def test_directory_snapshot_binds_binary_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'asset.bin').write_bytes(b'\xff\x00')
            r=snapshot_directory(root,self.ctx);self.assertEqual(r.files[0][2],2)
    def worker(self,body,seeds=(1,2),timeout=5):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);script=root/'worker.py';script.write_text('import pathlib,sys,os\n'+body)
            req=root/'input.json';req.write_text('{}')
            return check_subprocess_generator((sys.executable,str(script)),request_file=req,context=self.ctx,
                                              working_directory=root,hash_seeds=seeds,timeout_s=timeout)
    def test_fresh_process_identical_outputs_pass(self):
        r=self.worker("(pathlib.Path(sys.argv[2])/'a.ts').write_text('stable')\n")
        self.assertTrue(r.passed);self.assertEqual(r.execution_kind,'FRESH_PROCESS_REAL_GENERATOR')
    def test_hashseed_dependent_output_fails(self):
        r=self.worker("(pathlib.Path(sys.argv[2])/'a.ts').write_text(os.environ['PYTHONHASHSEED'])\n")
        self.assertFalse(r.passed)
    def test_process_success_without_files_fails(self):self.assertFalse(self.worker('pass\n').passed)
    def test_failed_worker_not_counted_as_pass(self):self.assertFalse(self.worker('sys.exit(3)\n').passed)
    def test_worker_timeout_retained_as_failure(self):self.assertFalse(self.worker('import time;time.sleep(5)\n',timeout=0.1).passed)
    def test_actual_bie_worker_uses_fresh_hashseed_processes(self):
        b=bundle()
        with tempfile.TemporaryDirectory() as td:
            req=Path(td)/'request.json';req.write_text(json.dumps({'document':case_raw()['document']}))
            r=check_subprocess_generator((sys.executable,str(ROOT/'scripts/qa_compile_worker.py')),
                  request_file=req,context=b.context,working_directory=ROOT,hash_seeds=(13,29))
            self.assertTrue(r.passed)
    def test_no_render_determinism_claim(self):
        r=check_deterministic_generator(lambda:self.files,self.ctx)
        self.assertEqual(r.output_scope,'GENERATED_SOURCE_BYTES_NOT_VIDEO_FRAMES');self.assertFalse(r.accepted)

if __name__=='__main__':unittest.main()
