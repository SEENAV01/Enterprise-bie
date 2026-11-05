"""Integration evidence uses injected media plus real FFmpeg/ffprobe, NOT Remotion."""
from dataclasses import replace
from pathlib import Path
from threading import Event
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from bie.compiler.artifact_hashing import manifest_from_dict, verify_artifacts
from bie.compiler.build_common import BuildError
from bie.compiler.full_render import full_render
from bie.compiler.smoke_render import smoke_render
from bie.compiler.render_contracts import RenderPlan
from bie.compiler.render_logs import verify_render_log
from bie.compiler.render_process import run_bounded_process
from bie.compiler.render_runtime import execute_render
from .render_test_support import fixture_workspace, FixtureRunner, fake_result

class TestRenderIntegration(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.request=fixture_workspace(self.root)
    def tearDown(self):self.tmp.cleanup()
    def test_smoke_full_log_hash_chain(self):
        smoke=smoke_render(replace(self.request,run_id='smoke',output_path='out/smoke.mp4'),frame_count=4,runner=FixtureRunner())
        full=full_render(self.request,runner=FixtureRunner())
        for receipt in (smoke,full):
            self.assertTrue(receipt.passed,receipt.errors)
            evidence=self.root/receipt.evidence_directory
            self.assertTrue(verify_render_log(evidence/'events.jsonl'))
            manifest=manifest_from_dict(json.loads((evidence/'ARTIFACT_MANIFEST.json').read_text()))
            self.assertTrue(verify_artifacts(self.root,manifest).passed)
            self.assertFalse(receipt.accepted);self.assertFalse(manifest.accepted)
        self.assertEqual(smoke.input_sha256,full.input_sha256)
        self.assertNotEqual(smoke.recipe_sha256,full.recipe_sha256)
    def test_post_render_bit_flip_is_detected(self):
        receipt=full_render(self.request,runner=FixtureRunner())
        manifest=manifest_from_dict(json.loads((self.root/receipt.evidence_directory/'ARTIFACT_MANIFEST.json').read_text()))
        output=self.root/receipt.output_path;data=bytearray(output.read_bytes());data[-1]^=1;output.write_bytes(data)
        self.assertFalse(verify_artifacts(self.root,manifest).passed)
    def test_persisted_receipt_tamper_is_detected(self):
        receipt=full_render(self.request,runner=FixtureRunner())
        evidence=self.root/receipt.evidence_directory
        manifest=manifest_from_dict(json.loads((evidence/'ARTIFACT_MANIFEST.json').read_text()))
        path=evidence/'RENDER_RECEIPT.json';path.write_text(path.read_text().replace('"accepted":false','"accepted":true'))
        self.assertFalse(verify_artifacts(self.root,manifest).passed)
    def test_failure_receipt_has_sealed_log_and_manifest(self):
        receipt=full_render(self.request,runner=FixtureRunner(outcome='FAILED',code=5))
        evidence=self.root/receipt.evidence_directory
        self.assertTrue(verify_render_log(evidence/'events.jsonl'))
        manifest=manifest_from_dict(json.loads((evidence/'ARTIFACT_MANIFEST.json').read_text()))
        self.assertTrue(verify_artifacts(self.root,manifest).passed);self.assertFalse(receipt.passed)
    def test_known_test_fixture_rejected_by_production_runner(self):
        receipt=full_render(self.request)
        self.assertEqual(receipt.failure_code,'TEST_FIXTURE_REJECTED');self.assertFalse(receipt.process_started)
    def test_forged_full_plan_rejected(self):
        with self.assertRaises(BuildError):execute_render(self.request,RenderPlan('full',0,3,4),runner=FixtureRunner())
    def test_probe_cancellation_not_mislabeled_success(self):
        fixture=FixtureRunner()
        def runner(command,**kwargs):
            if command[2]=='render':return fixture(command,**kwargs)
            return fake_result(command,kwargs['cwd'],outcome='CANCELLED',code=-15)
        receipt=full_render(self.request,runner=runner)
        self.assertEqual(receipt.failure_code,'CANCELLED');self.assertIsNone(receipt.output_path)
    def test_publication_race_keeps_other_writer_bytes(self):
        def competing_writer(root):
            (root/'out').mkdir();(root/'out/full.mp4').write_bytes(b'other-writer')
        receipt=full_render(self.request,runner=FixtureRunner(mutate=competing_writer))
        self.assertFalse(receipt.passed);self.assertEqual((self.root/'out/full.mp4').read_bytes(),b'other-writer')
    def test_process_group_timeout_stops_descendant(self):
        code=('import subprocess,sys,time;from pathlib import Path;'
              'p=subprocess.Popen([sys.executable,"-S","-c","import time;time.sleep(30)"]);'
              'Path("child.pid").write_text(str(p.pid));print("child started",flush=True);time.sleep(30)')
        result=run_bounded_process((sys.executable,'-S','-c',code),cwd=self.root,timeout_s=.8)
        self.assertEqual(result.outcome,'TIMED_OUT');self.assertTrue((self.root/'child.pid').exists())
        pid=int((self.root/'child.pid').read_text());proc=Path(f'/proc/{pid}/stat')
        # A killed child can briefly be a zombie awaiting the host init's reap.
        self.assertTrue(not proc.exists() or proc.read_text().split()[2]=='Z')
    def test_probe_cannot_change_artifact_and_still_publish(self):
        fixture=FixtureRunner()
        def runner(command,**kwargs):
            result=fixture(command,**kwargs)
            if command[2]!='render':
                p=Path(command[-1]);data=bytearray(p.read_bytes());data[-1]^=1;p.write_bytes(data)
            return result
        receipt=full_render(self.request,runner=runner)
        self.assertEqual(receipt.failure_code,'ARTIFACT_CHANGED');self.assertIsNone(receipt.output_path)
    def test_sealing_failure_rolls_back_publication(self):
        from bie.compiler import render_runtime
        real=render_runtime.hash_artifacts
        def fail_seal(root,paths,**kwargs):
            paths=tuple(paths)
            if any('RENDER_RECEIPT.json' in p for p in paths):raise BuildError('simulated evidence storage failure')
            return real(root,paths,**kwargs)
        with patch.object(render_runtime,'hash_artifacts',side_effect=fail_seal):
            with self.assertRaises(BuildError):full_render(self.request,runner=FixtureRunner())
        self.assertFalse((self.root/self.request.output_path).exists())
        self.assertTrue((self.root/'render-evidence/test-run/EVIDENCE_SEAL_FAILURE.json').exists())
    def test_completed_receipt_binds_probed_bytes(self):
        from hashlib import sha256
        r=full_render(self.request,runner=FixtureRunner())
        data=(self.root/r.output_path).read_bytes()
        self.assertEqual(r.artifact_sha256,sha256(data).hexdigest());self.assertEqual(r.artifact_size_bytes,len(data))
    def test_invalid_probe_stream_shape_is_logged(self):
        fixture=FixtureRunner()
        def runner(command,**kwargs):
            if command[2]=='render':return fixture(command,**kwargs)
            return fake_result(command,kwargs['cwd'],stdout='{"streams":[3]}')
        r=full_render(self.request,runner=runner)
        self.assertFalse(r.passed);self.assertTrue(verify_render_log(self.root/r.evidence_directory/'events.jsonl'))
