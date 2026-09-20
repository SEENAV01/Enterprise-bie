from copy import deepcopy
from dataclasses import replace,asdict
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import json,subprocess,sys,tempfile,unittest
from bie.compiler.hardened_scene_compile import *
from bie.compiler.checked_scene_compile import publish_checked_scene,verify_checked_workspace
from bie.compiler.compile_diagnostics_mapping import validate_source_map
from bie.compiler.deterministic_output_qa import snapshot_generated,compare_snapshots
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from tests.compiler.h3_test_support import scene,move,variant,sim_props,TARGET,ROOT

class HardenedAdoptionTests(unittest.TestCase):
    def test_default_safe_source_passes(self):self.assertTrue(compile_h3_scene(scene()).receipt.source_gate_passed)
    def test_offscreen_source_not_published(self):
        p=move(params={'from':{'translate_x':0},'to':{'translate_x':900}})
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source'
            with self.assertRaisesRegex(ValueError,'LAYOUT_OUTSIDE_VIEWPORT'):publish_h3_scene(p,d)
            self.assertFalse(d.exists())
    def test_variant_selected_before_emission(self):
        p=variant(move());r=compile_h3_scene(p,motion_preference='reduced');self.assertTrue(r.receipt.source_gate_passed);self.assertEqual(r.bundle.animation_results[0].action,'enter')
    def test_static_simulation_adopted_in_checked_path(self):
        p=variant(scene('simulation',sim_props(),duration_ms=3000));r=compile_h3_scene(p,motion_preference='reduced');self.assertTrue(r.receipt.source_gate_passed);self.assertIn('const frame = 48;',r.bundle.element_results[0].source_text)
    def test_parent_diagnostic_bytes_remain_source_only(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'legacy';publish_checked_scene(scene(),d)
            with self.assertRaisesRegex(ValueError,'H3_SOURCE_REQUIRED'):require_h3_workspace(d)
    def test_version_cannot_impersonate_h3_in_old_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'legacy';publish_checked_scene(scene(),d,target=TARGET)
            with self.assertRaisesRegex(ValueError,'H3_SOURCE_REQUIRED'):require_h3_workspace(d)
    def test_published_h3_revalidates(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';a=publish_h3_scene(scene(),d);self.assertEqual(a,verify_checked_workspace(d))
    def test_source_sidecar_tamper_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);(d/'src/bie-h3-layout.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'TAMPERED'):require_h3_workspace(d)
    def test_envelope_variant_tamper_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);f=d/'CHECKED_SCENE.json';r=json.loads(f.read_text());r['motion_preference']='reduced';f.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'TAMPERED'):require_h3_workspace(d)
    def test_host_change_revalidation_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);f=d/'CHECKED_SCENE.json';r=json.loads(f.read_text());r['host_identity']='0'*64;f.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'HOST_IDENTITY_CHANGED'):require_h3_workspace(d)
    def test_executable_file_addition_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);(d/'override.js').write_text('process.exit(0)')
            with self.assertRaisesRegex(ValueError,'UNINSPECTED'):require_h3_workspace(d)
    def test_manifest_tamper_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);(d/'CODEGEN_MANIFEST.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'TAMPERED'):require_h3_workspace(d)
    def test_source_symlink_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);f=d/'src/Scene.tsx';other=Path(td)/'backup';other.write_bytes(f.read_bytes());f.unlink();f.symlink_to(other)
            with self.assertRaises(ValueError):require_h3_workspace(d)
    def test_existing_destination_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';d.mkdir()
            with self.assertRaises(ValueError):publish_h3_scene(scene(),d)
    def test_parser_and_source_map_bind_new_files(self):
        r=compile_h3_scene(scene());self.assertEqual(r.receipt.parser_status,'PASS');validate_source_map(r.bundle.source_map,r.codegen.files)
    def test_source_map_provenance_retained(self):
        r=compile_h3_scene(variant(move()),motion_preference='reduced');self.assertTrue(all(s.origin.source_refs and s.origin.reasoning_refs for s in r.bundle.source_map.spans))
    def test_host_affects_determinism_context(self):
        r=compile_h3_scene(scene());self.assertNotEqual(r.bundle.context.dependency_identity,'0'*64);self.assertIn(r.host['identity_sha256'],next(f.content for f in r.codegen.files if f.path=='src/bie-h3-identity.json'))
    def test_no_implicit_real_paint_claim(self):
        r=compile_h3_scene(scene());d=json.loads(next(f.content for f in r.codegen.files if f.path=='src/bie-h3-identity.json'));self.assertEqual(d['content_fit_status'],'NOT_RUN');self.assertFalse(r.receipt.accepted)
    def test_same_input_same_host_is_deterministic(self):
        a=compile_h3_scene(scene());b=compile_h3_scene(scene());self.assertEqual(snapshot_generated(a.codegen.files,a.bundle.context),snapshot_generated(b.codegen.files,b.bundle.context))
    def test_variant_identity_differs_even_for_static_scene(self):
        a=compile_h3_scene(scene());b=compile_h3_scene(scene(),motion_preference='reduced');self.assertNotEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_real_harness_stops_at_missing_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';publish_h3_scene(scene(),d);r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_checked_remotion.py'),str(d)],capture_output=True,text=True,timeout=30);out=json.loads(r.stdout);self.assertEqual(r.returncode,2,r.stderr);self.assertIn('FULL_TYPECHECK_BLOCKED',out['failure'])
    def test_legacy_cannot_reach_renderer_even_if_typecheck_claimed_pass(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source';receipt=publish_checked_scene(p,d);comp=CompositionDescriptor('BieQA'+digest(p['scene_id'])[:16],640,360,24,24);req=RenderRequest(str(d),'src/index.ts',comp,'out/v.mp4',receipt.scene_fingerprint,'legacy-h3-test')
            from bie.compiler.generated_code_regression import typecheck_generated_workspace
            blocked=typecheck_generated_workspace(d)
            fake=replace(blocked,status='PASS')
            with patch('bie.compiler.generated_code_regression.typecheck_generated_workspace',return_value=fake):r=full_render(req)
            self.assertFalse(r.passed);self.assertFalse(r.process_started);self.assertEqual(r.failure_code,'H3_SOURCE_QA_BLOCKED')
    def test_cli_default_is_h3(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);(d/'scene.json').write_text(json.dumps(scene()));r=subprocess.run([sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),str(d/'scene.json'),str(d/'out')],capture_output=True,text=True,timeout=30);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(json.loads((d/'out/CHECKED_SCENE.json').read_text())['schema_version'],SCHEMA)
    def test_literal_jsx_still_inert(self):
        r=compile_h3_scene(scene('text',{'text':'{process.exit(1)} <script> literal'}));self.assertTrue(r.receipt.source_gate_passed)
    def test_unimplemented_family_not_silently_adopted(self):
        p=move();p['tracks'][0]['action']='morph'
        with self.assertRaises(ValueError):compile_h3_scene(p)
if __name__=='__main__':unittest.main()
