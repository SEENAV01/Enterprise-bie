from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import json,tempfile,subprocess,sys,unittest
from bie.compiler.frame_runtime_contract import CompilerQAError
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.compile_diagnostics_mapping import validate_source_map
from tests.compiler.h6_test_support import *

class RuntimeAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.a=narration_scene();cls.r=compile_h3_scene(cls.p,target=BIG)
    def test_existing_checked_path_consumes_all_three_contracts(self):
        self.assertTrue(self.r.receipt.source_gate_passed);self.assertFalse(any(f.code=='UNCONSUMED_SCENE_CONTRACT' for f in self.r.receipt.findings))
    def test_precise_media_dependency_pin(self):
        p=json.loads(next(f.content for f in self.r.codegen.files if f.path=='package.json'));self.assertEqual(p['dependencies']['@remotion/media'],BIG.remotion_version)
    def test_dependency_conflict_blocked(self):
        with self.assertRaisesRegex(CompilerQAError,'DEPENDENCY_VERSION_CONFLICT'):compile_scene_for_qa(self.p,target=BIG,extra_dependency_versions={'@remotion/media':'0.0.0'})
    def test_every_generated_module_has_source_map(self):
        validate_source_map(self.r.bundle.source_map,self.r.codegen.files)
        self.assertTrue(all(s.origin.source_refs and s.origin.reasoning_refs for s in self.r.bundle.source_map.spans))
    def test_required_audio_cannot_publish_from_metadata_alone(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out'
            with self.assertRaisesRegex(CompilerQAError,'ASSET_ROOT_REQUIRED'):publish_h3_scene(self.p,out,target=BIG)
            self.assertFalse(out.exists())
    def test_source_and_verified_bytes_publish_together(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);out=base/'out';r=publish_h3_scene(self.p,out,target=BIG,asset_root=write_assets(base/'assets',self.a))
            self.assertEqual(r,require_h3_workspace(out))
            for rel,b in self.a.items():self.assertEqual((out/'public'/rel).read_bytes(),b)
    def test_asset_tamper_blocks_render_revalidation(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);out=base/'out';publish_h3_scene(self.p,out,target=BIG,asset_root=write_assets(base/'assets',self.a))
            p=out/'public'/next(iter(self.a));b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
            with self.assertRaisesRegex(CompilerQAError,'HASH_MISMATCH'):require_h3_workspace(out)
    def test_asset_deleted_blocks_revalidation(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);out=base/'out';publish_h3_scene(self.p,out,target=BIG,asset_root=write_assets(base/'assets',self.a));(out/'public'/next(iter(self.a))).unlink()
            with self.assertRaisesRegex(CompilerQAError,'UNAVAILABLE'):require_h3_workspace(out)
    def test_runtime_source_tamper_blocks_revalidation(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out';publish_h3_scene(state_scene(),out,target=BIG);(out/'src/runtime/frame-runtime.ts').write_text('export const atFrame=()=>({});')
            with self.assertRaisesRegex(CompilerQAError,'TAMPERED'):require_h3_workspace(out)
    def test_unlisted_public_file_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out';publish_h3_scene(state_scene(),out,target=BIG);(out/'public').mkdir();(out/'public/extra.js').write_text('alert(1)')
            with self.assertRaisesRegex(CompilerQAError,'UNINSPECTED'):require_h3_workspace(out)
    def test_legacy_runtime_absence_still_blocks_old_unconsumed_fields(self):
        p=state_scene();del p['metadata']['compiler_h6'];r=compile_h3_scene(p,target=BIG);self.assertFalse(r.receipt.source_gate_passed)
    def test_unimplemented_interaction_stays_blocked(self):
        p=state_scene();p['interaction_cues']=[{'cue_id':'tap','at_ms':0,'target_ids':['e0']}]
        r=compile_h3_scene(p,target=BIG);self.assertFalse(r.receipt.source_gate_passed)
    def test_existing_cli_accepts_explicit_asset_root(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);scene=base/'scene.json';scene.write_text(json.dumps(self.p));write_assets(base/'assets',self.a)
            cmd=[sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),str(scene),str(base/'out'),'--width','1280','--height','720','--asset-root',str(base/'assets')]
            r=subprocess.run(cmd,capture_output=True,text=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr+r.stdout);self.assertTrue(json.loads(r.stdout)['source_gate_passed'])
    def test_cli_missing_bytes_has_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);p=base/'p.json';p.write_text(json.dumps(self.p));r=subprocess.run([sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),str(p),str(base/'out')],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,2);self.assertIn('ASSET_ROOT_REQUIRED',r.stdout)
    def test_source_fingerprint_changes_with_event_value(self):
        p=state_scene();a=compile_h3_scene(p,target=BIG);p['events'][0]['payload']['value']='Changed';b=compile_h3_scene(p,target=BIG);self.assertNotEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_source_pass_never_claims_real_render(self):
        d=json.loads(next(f.content for f in self.r.codegen.files if f.path=='src/bie-h3-identity.json'));self.assertEqual(d['real_remotion_status'],'NOT_RUN');self.assertFalse(self.r.receipt.accepted)

if __name__=='__main__':unittest.main()
