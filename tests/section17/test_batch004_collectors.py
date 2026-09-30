"""Actual local tool and byte-capture tests; tools missing is an error, not a skip."""
from pathlib import Path
import os,sys,tempfile,unittest,json,hashlib
from unittest.mock import patch
from batch004_helpers import ROOT
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.metrics.collectors import compile_source,decode_media,snapshot_outputs,safe_relative,local_bytes,command,tool
MEDIA=ROOT/'tests/section17/assets/batch004/reference_video.mkv'
class Batch004Collectors(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def snapshot(self,path=None,run='run'):return snapshot_outputs(path or self.root,run,'1'*64,'2'*64,'3'*64,0)
    def test_python_actual_emit_without_execution(self):
        sentinel=self.root/'executed';source=f'from pathlib import Path\nPath({str(sentinel)!r}).write_text("executed")\n'
        o=compile_source('python',source,'actual-python');self.assertEqual(0,o['facts']['exit_code']);self.assertGreater(o['facts']['output_bytes'],0);self.assertFalse(sentinel.exists())
    def test_python_syntax_failure_has_no_output(self):
        o=compile_source('python','def broken(:\n','invalid-python');self.assertNotEqual(0,o['facts']['exit_code']);self.assertEqual(0,o['facts']['output_bytes'])
    def test_typescript_actual_emit_without_execution(self):
        o=compile_source('typescript','throw new Error("must not execute");\n','actual-ts');self.assertEqual(0,o['facts']['exit_code']);self.assertGreater(o['facts']['output_bytes'],0)
    def test_typescript_type_failure_emits_nothing(self):
        o=compile_source('typescript','const x: number = "bad";\n','invalid-ts');self.assertNotEqual(0,o['facts']['exit_code']);self.assertEqual(0,o['facts']['output_bytes'])
    def test_unsupported_compiler_never_invokes_command(self):
        with patch('bie.evaluation.benchmarks.metrics.collectors.command') as call:
            with self.assertRaisesRegex(BenchmarkError,'UNSUPPORTED_COMPILER_PROFILE'):compile_source('bash','echo unsafe','r')
            call.assert_not_called()
    def test_compile_source_size_limit(self):
        with self.assertRaises(BenchmarkError):compile_source('python','x'*50001,'r')
    def test_actual_compiler_output_written_and_hash_verified(self):
        o=compile_source('python','x=1\n','saved',self.root/'capture');b=(self.root/'capture/output/lesson.pyc').read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),o['facts']['output_sha256'])
    def test_tool_missing_returns_typed_error(self):
        with patch('shutil.which',return_value=None):
            with self.assertRaisesRegex(BenchmarkError,'LOCAL_TOOL_UNAVAILABLE'):tool('ffmpeg')
    def test_timeout_returns_typed_error(self):
        with self.assertRaisesRegex(BenchmarkError,'LOCAL_TOOL_TIMEOUT'):command([sys.executable,'-I','-c','import time; time.sleep(1)'],self.root,timeout=.01)
    def test_subprocess_node_options_are_not_inherited(self):
        with patch.dict(os.environ,{'NODE_OPTIONS':'--require /does/not/exist'}):
            rc,out,err=command([sys.executable,'-I','-c','import os; print(os.environ.get("NODE_OPTIONS","absent"))'],self.root)
        self.assertEqual(0,rc);self.assertEqual(b'absent\n',out)
    def test_actual_video_is_fully_decoded(self):
        o,fr=decode_media(MEDIA,'decode',[0,11]);self.assertEqual((64,36,12),(o['facts']['width'],o['facts']['height'],o['facts']['decoded_frames']));self.assertEqual(2,len(fr['facts']['frames']))
    def test_corrupt_media_file_is_blocked(self):
        p=self.root/'bad.mkv';p.write_bytes(b'not video')
        with self.assertRaisesRegex(BenchmarkError,'MEDIA_PROBE_FAILED'):decode_media(p,'bad')
    def test_media_symlink_blocked(self):
        p=self.root/'linked.mkv';p.symlink_to(MEDIA)
        with self.assertRaisesRegex(BenchmarkError,'ARTIFACT_NOT_REGULAR_FILE'):decode_media(p,'linked')
    def test_duplicate_requested_frame_blocked(self):
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_FRAME_REQUEST'):decode_media(MEDIA,'duplicate',[0,0])
    def test_requested_missing_frame_blocked(self):
        with self.assertRaisesRegex(BenchmarkError,'REQUESTED_FRAME_NOT_DECODED'):decode_media(MEDIA,'missing',[100])
    def test_output_snapshot_hashes_real_bytes(self):
        (self.root/'x.bin').write_bytes(b'hello');o=self.snapshot();self.assertEqual(hashlib.sha256(b'hello').hexdigest(),o['facts']['outputs'][0]['sha256'])
    def test_snapshot_changes_when_bytes_change(self):
        p=self.root/'x';p.write_bytes(b'a');a=self.snapshot();p.write_bytes(b'b');b=self.snapshot(run='two');self.assertNotEqual(a['subject_sha256'],b['subject_sha256'])
    def test_snapshot_symlinks_blocked(self):
        (self.root/'x').write_text('x');(self.root/'link').symlink_to(self.root/'x')
        with self.assertRaisesRegex(BenchmarkError,'OUTPUT_SYMLINK_FORBIDDEN'):self.snapshot()
    def test_snapshot_case_collisions_blocked(self):
        (self.root/'x').write_text('1');(self.root/'X').write_text('2')
        with self.assertRaisesRegex(BenchmarkError,'CASE_COLLIDING_OUTPUT_PATHS'):self.snapshot()
    def test_empty_snapshot_blocked(self):
        with self.assertRaisesRegex(BenchmarkError,'EMPTY_OUTPUT_SNAPSHOT'):self.snapshot()
    def test_output_path_traversal_blocked(self):
        for p in ['../secret','/absolute','a/../b','a//b','a\\b','C:/file','a\x00b']:
            with self.assertRaisesRegex(BenchmarkError,'UNSAFE_OUTPUT_PATH'):safe_relative(p)
    def test_snapshot_seed_boolean_blocked(self):
        (self.root/'x').write_text('x')
        with self.assertRaisesRegex(BenchmarkError,'INTEGER_OUT_OF_PROFILE'):snapshot_outputs(self.root,'r','1'*64,'2'*64,'3'*64,False)
    def test_source_artifact_size_bound_before_read(self):
        p=self.root/'big';p.write_bytes(b'1234')
        with self.assertRaisesRegex(BenchmarkError,'ARTIFACT_SIZE_LIMIT'):local_bytes(p,3)

    def test_nonstring_compiler_profile_typed_before_launch(self):
        with patch('bie.evaluation.benchmarks.metrics.collectors.command') as call:
            with self.assertRaisesRegex(BenchmarkError,'UNSUPPORTED_COMPILER_PROFILE'):compile_source([], 'x=1', 'r')
            call.assert_not_called()
    def test_noncollection_frame_request_is_typed(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_FRAME_REQUEST'):decode_media(MEDIA,'invalid-frames',None)
