from pathlib import Path
from dataclasses import asdict,replace
from copy import deepcopy
from unittest.mock import patch
import json,shutil,tempfile,unittest
from bie.compiler.hardened_scene_compile import publish_h3_scene,require_h3_workspace,compile_h3_scene
from bie.compiler.checked_scene_compile import publish_checked_scene
from bie.compiler.qa_common import digest
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from bie.compiler.real_paint import require_actual_witness
from tests.compiler.h7_test_support import state_scene,narration_scene,write_assets,BIG,reduced,equation_scene,trace_scene

class IntegratedProductionGateTests(unittest.TestCase):
    def request(self,root,receipt,p,run='h7-check'):
        comp=CompositionDescriptor('BieQA'+digest(p['scene_id'])[:16],BIG.width,BIG.height,BIG.fps,48)
        return RenderRequest(str(root),'src/index.ts',comp,'out/final.mp4',receipt.scene_fingerprint,run,browser_executable='/usr/bin/chromium',timeout_s=10)
    def test_current_production_missing_deps_explicit_block(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'s';p=state_scene();receipt=publish_h3_scene(p,root,target=BIG)
            r=full_render(self.request(root,receipt,p));self.assertFalse(r.passed);self.assertEqual(r.failure_code,'FULL_TYPECHECK_BLOCKED');self.assertFalse(r.process_started);self.assertFalse((root/'out/final.mp4').exists())
    def test_typecheck_evidence_no_simulation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'s';p=state_scene();receipt=publish_h3_scene(p,root,target=BIG);full_render(self.request(root,receipt,p))
            j=json.loads((root/'render-evidence/h7-check/isolated-typecheck/TYPECHECK.json').read_text());self.assertEqual(j['executions'],[]);self.assertEqual(j['receipt']['status'],'BLOCKED_DEPENDENCIES')
    def test_existing_source_tamper_blocks_before_tools(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'s';p=state_scene();receipt=publish_h3_scene(p,root,target=BIG);(root/'src/Scene.tsx').write_text('export const Scene=()=>null;')
            r=full_render(self.request(root,receipt,p));self.assertFalse(r.process_started);self.assertEqual(r.failure_code,'SOURCE_QA_BLOCKED')
    def test_audio_hash_revalidated_at_render_entry(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,a=narration_scene();assets=write_assets(base/'assets',a);receipt=publish_h3_scene(p,base/'s',target=BIG,asset_root=assets)
            f=base/'s/public'/next(iter(a));f.write_bytes(b'changed')
            r=full_render(self.request(base/'s',receipt,p));self.assertFalse(r.passed);self.assertFalse(r.process_started)
    def test_pending_dependency_cannot_publish_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'s';p=state_scene();receipt=publish_h3_scene(p,root,target=BIG);r=full_render(self.request(root,receipt,p));self.assertIsNone(r.artifact_sha256);self.assertIsNone(r.output_path);self.assertFalse(r.accepted)
    def test_caller_receipt_not_accepted(self):
        with self.assertRaises(ValueError):require_actual_witness({'scope':'REAL_REMOTION','passed':True},'source')
    def test_specialized_reduced_source_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'s';p=reduced(equation_scene());r=publish_h3_scene(p,root,target=BIG,motion_preference='reduced');self.assertEqual(r,require_h3_workspace(root))
    def test_reduced_variant_receipt_tamper_reject(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'s';publish_h3_scene(reduced(trace_scene()),root,target=BIG,motion_preference='reduced');p=root/'src/bie-h3-motion.json'
            if not p.exists():p=root/'src/bie-h3-identity.json'
            p.write_text('{}');self.assertRaises(ValueError,require_h3_workspace,root)
    def test_narration_standard_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p,a=narration_scene();root=base/'s';r=publish_h3_scene(p,root,target=BIG,asset_root=write_assets(base/'assets',a));self.assertEqual(r,require_h3_workspace(root))
    def test_existing_runtime_false_scope_not_upgraded(self):
        r=compile_h3_scene(state_scene(),target=BIG);self.assertFalse(r.receipt.accepted);identity=json.loads(next(x.content for x in r.codegen.files if x.path=='src/bie-h3-identity.json'));self.assertEqual(identity['content_fit_status'],'NOT_RUN')
    def test_no_implicit_installer(self):
        import inspect,bie.compiler.real_paint as p,bie.compiler.linux_worker as s
        source=inspect.getsource(p)+inspect.getsource(s);self.assertNotIn('npm install',source);self.assertNotIn('npx ',source)
    def test_kernel_producer_not_bridge(self):
        import inspect,bie.compiler.real_paint as p
        s=inspect.getsource(p.produce_actual_paint);self.assertIn('run_isolated',s);self.assertNotIn('ChromiumLayoutProbe',s);self.assertNotIn('layout_bridge',s)
