import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from bie.compiler.build_common import BuildError
from bie.compiler.full_render import full_render
from bie.compiler.render_contracts import make_render_plan
from bie.compiler.render_runtime import build_render_command
from .render_test_support import fixture_workspace, FixtureRunner, media_bytes

class TestBuild008(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.request=fixture_workspace(self.root)
    def tearDown(self):self.tmp.cleanup()
    def test_full_plan_covers_entire_composition(self):
        p=make_render_plan(self.request,"full");self.assertEqual((p.first_frame,p.last_frame,p.expected_frames),(0,11,12))
    def test_full_rejects_frame_subset(self):
        with self.assertRaises(BuildError):make_render_plan(self.request,"full",frame_count=4)
    def test_full_has_no_cli_frame_override(self):
        cmd=build_render_command(self.request,make_render_plan(self.request,"full"),cli="cli",node="node",staged_output="x.mp4",empty_env="empty.env")
        self.assertFalse(any(x.startswith('--frames=') for x in cmd));self.assertIn('--overwrite=false',cmd)
    def test_full_fixture_passes_real_ffprobe(self):
        r=full_render(self.request,runner=FixtureRunner())
        self.assertTrue(r.passed,r.errors);self.assertEqual(r.media.decoded_frames,12);self.assertFalse(r.accepted)
    def test_partial_video_cannot_pass_full_render(self):
        r=full_render(self.request,runner=FixtureRunner(frames=4))
        self.assertFalse(r.passed);self.assertFalse((self.root/self.request.output_path).exists())
    def test_zero_exit_without_output_is_failure(self):
        r=full_render(self.request,runner=FixtureRunner(no_file=True))
        self.assertFalse(r.passed);self.assertIsNone(r.output_path)
    def test_empty_output_is_failure(self):
        r=full_render(self.request,runner=FixtureRunner(media=b''))
        self.assertEqual(r.failure_code,'EMPTY_ARTIFACT')
    def test_corrupt_nonempty_output_is_failure(self):
        r=full_render(self.request,runner=FixtureRunner(media=b'not a real video'))
        self.assertEqual(r.failure_code,'MEDIA_PROBE_FAILED')
    def test_nonzero_exit_does_not_publish(self):
        r=full_render(self.request,runner=FixtureRunner(outcome='FAILED',code=9))
        self.assertFalse(r.passed);self.assertEqual(r.failure_code,'FAILED')
        self.assertTrue((self.root/r.evidence_directory/'staged.mp4').exists())
        self.assertFalse((self.root/self.request.output_path).exists())
    def test_timeout_preserves_failure(self):
        r=full_render(self.request,runner=FixtureRunner(outcome='TIMED_OUT',code=-15))
        self.assertEqual(r.failure_code,'TIMED_OUT')
    def test_old_output_untouched(self):
        output=self.root/self.request.output_path;output.parent.mkdir();output.write_bytes(b'previous')
        runner=FixtureRunner();r=full_render(self.request,runner=runner)
        self.assertEqual(r.failure_code,'OUTPUT_EXISTS');self.assertEqual(output.read_bytes(),b'previous');self.assertEqual(runner.commands,[])
    def test_source_mutation_blocks_publish(self):
        r=full_render(self.request,runner=FixtureRunner(mutate=lambda p:(p/'src/index.ts').write_text('//changed')))
        self.assertEqual(r.failure_code,'INPUT_CHANGED');self.assertFalse((self.root/self.request.output_path).exists())
    def test_new_source_file_blocks_publish(self):
        r=full_render(self.request,runner=FixtureRunner(mutate=lambda p:(p/'src/extra.ts').write_text('//new')))
        self.assertEqual(r.failure_code,'INPUT_CHANGED')
    def test_required_audio_not_silently_synthesized(self):
        r=full_render(replace(self.request,require_audio=True),runner=FixtureRunner())
        self.assertFalse(r.passed);self.assertIn('required audio',r.errors[0])
    def test_real_audio_fixture_passes_structural_gate(self):
        r=full_render(replace(self.request,require_audio=True),runner=FixtureRunner(media=media_bytes(audio=True)))
        self.assertTrue(r.passed,r.errors);self.assertEqual(r.media.audio_streams,1)
    def test_wrong_dimensions_block_publish(self):
        r=full_render(self.request,runner=FixtureRunner(media=media_bytes(width=160,height=90)))
        self.assertFalse(r.passed);self.assertIn('dimensions',r.errors[0])
    def test_wrong_fps_blocks_publish(self):
        r=full_render(self.request,runner=FixtureRunner(media=media_bytes(fps=24)))
        self.assertFalse(r.passed);self.assertIn('fps',r.errors[0])
    def test_run_id_cannot_overwrite_evidence(self):
        full_render(self.request,runner=FixtureRunner())
        with self.assertRaises(FileExistsError):full_render(self.request,runner=FixtureRunner())
    def test_output_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root/'out').symlink_to(outside,target_is_directory=True)
            with self.assertRaises(BuildError):full_render(self.request,runner=FixtureRunner())
