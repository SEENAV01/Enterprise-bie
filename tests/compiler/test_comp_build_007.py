import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from threading import Event
from bie.compiler.build_common import BuildError
from bie.compiler.smoke_render import smoke_render
from bie.compiler.render_contracts import make_render_plan
from bie.compiler.render_runtime import build_render_command
from bie.compiler.render_logs import verify_render_log
from .render_test_support import fixture_workspace, FixtureRunner

class TestBuild007(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.request = fixture_workspace(self.root)
    def tearDown(self): self.tmp.cleanup()
    def test_smoke_range_inclusive(self):
        p = make_render_plan(self.request, "smoke", first_frame=3, frame_count=4)
        self.assertEqual((p.first_frame,p.last_frame,p.expected_frames), (3,6,4))
    def test_smoke_frame_zero(self):
        p = make_render_plan(self.request, "smoke", first_frame=0, frame_count=1)
        self.assertEqual(p.last_frame,0)
    def test_last_frame_allowed(self):
        self.assertEqual(make_render_plan(self.request,"smoke",first_frame=11,frame_count=1).last_frame,11)
    def test_range_overflow_rejected(self):
        with self.assertRaises(BuildError): make_render_plan(self.request,"smoke",first_frame=10,frame_count=3)
    def test_negative_start_rejected(self):
        with self.assertRaises(BuildError): make_render_plan(self.request,"smoke",first_frame=-1,frame_count=1)
    def test_boolean_count_rejected(self):
        with self.assertRaises(BuildError): make_render_plan(self.request,"smoke",frame_count=True)
    def test_zero_count_rejected(self):
        with self.assertRaises(BuildError): make_render_plan(self.request,"smoke",frame_count=0)
    def test_command_explicit_frame_window(self):
        p=make_render_plan(self.request,"smoke",first_frame=3,frame_count=4)
        cmd=build_render_command(self.request,p,cli="cli.js",node="node",staged_output="x.mp4",empty_env="empty.env")
        self.assertIn("--frames=3-6",cmd); self.assertNotIn("npx",cmd)
    def test_real_probe_of_fixture_sample(self):
        r=smoke_render(self.request,first_frame=2,frame_count=4,runner=FixtureRunner())
        self.assertTrue(r.passed,r.errors); self.assertEqual(r.media.decoded_frames,4)
        self.assertEqual(r.execution_kind,"INJECTED_TEST_RUNNER"); self.assertFalse(r.accepted)
    def test_smoke_never_becomes_full(self):
        r=smoke_render(self.request,frame_count=12,runner=FixtureRunner())
        self.assertTrue(r.passed,r.errors); self.assertEqual(r.mode,"smoke")
    def test_wrong_frame_count_blocks_publish(self):
        r=smoke_render(self.request,frame_count=4,runner=FixtureRunner(frames=3))
        self.assertFalse(r.passed); self.assertIsNone(r.output_path); self.assertFalse((self.root/'out/full.mp4').exists())
    def test_cancel_before_render_logged(self):
        event=Event();event.set()
        runner=FixtureRunner();r=smoke_render(self.request,frame_count=4,runner=runner,cancel_event=event)
        self.assertEqual(r.failure_code,"CANCELLED");self.assertFalse(r.process_started);self.assertEqual(runner.commands,[])
        self.assertTrue(verify_render_log(self.root/r.evidence_directory/'events.jsonl'))
    def test_missing_dependencies_fail_closed(self):
        (self.root/'node_modules/remotion/package.json').unlink()
        r=smoke_render(self.request,frame_count=1,runner=FixtureRunner())
        self.assertEqual(r.failure_code,"DEPENDENCIES_UNAVAILABLE");self.assertFalse(r.process_started)
    def test_dependency_version_mismatch(self):
        (self.root/'node_modules/remotion/package.json').write_text('{"version":"0.0.0"}')
        r=smoke_render(self.request,frame_count=1,runner=FixtureRunner())
        self.assertEqual(r.failure_code,"DEPENDENCY_MISMATCH")
    def test_output_traversal_rejected(self):
        with self.assertRaises(BuildError): replace(self.request,output_path="../evil.mp4")
    def test_source_output_rejected(self):
        with self.assertRaises(BuildError): replace(self.request,output_path="src/evil.mp4")
    def test_absolute_entrypoint_rejected(self):
        with self.assertRaises(BuildError): replace(self.request,entrypoint="/tmp/input.ts")
    def test_invalid_composition_metadata(self):
        for change in ({"width":None},{"fps":float('nan')},{"fps":True},{"height":181},{"duration_in_frames":0}):
            with self.subTest(change=change),self.assertRaises(BuildError):
                replace(self.request,composition=replace(self.request.composition,**change))
    def test_invalid_source_fingerprint(self):
        with self.assertRaises(BuildError): replace(self.request,scene_fingerprint="not-a-hash")
    def test_input_symlink_rejected(self):
        (self.root/'src/index.ts').unlink(); (self.root/'src/index.ts').symlink_to('/etc/hostname')
        r=smoke_render(self.request,frame_count=1,runner=FixtureRunner())
        self.assertFalse(r.passed);self.assertFalse(r.process_started)
    def test_props_finite_json(self):
        (self.root/'props.json').write_text('{"bad":NaN}')
        r=smoke_render(replace(self.request,props_file="props.json"),frame_count=1,runner=FixtureRunner())
        self.assertFalse(r.passed);self.assertFalse(r.process_started)
