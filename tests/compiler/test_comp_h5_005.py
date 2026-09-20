from copy import deepcopy
from pathlib import Path
from dataclasses import asdict
import json,shutil,subprocess,sys,tempfile,unittest
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.compile_diagnostics_mapping import validate_source_map
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.content_fit_qa import require_real_layout_authorization
from tests.compiler.h5_test_support import *

class AdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=[camera_scene(),equation_scene(),trace_scene()]
        cls.outputs=[compile_h3_scene(p,target=BIG) for p in cls.inputs]
        cls.tmp=tempfile.TemporaryDirectory();cls.base=Path(cls.tmp.name)
        cls.published=cls.base/'source';publish_h3_scene(cls.inputs[2],cls.published,target=BIG)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_three_source_paths_pass(self):self.assertTrue(all(r.receipt.source_gate_passed for r in self.outputs))
    def test_actual_source_parser_passes(self):self.assertTrue(all(r.receipt.parser_status=='PASS' for r in self.outputs))
    def test_all_source_maps_validate(self):
        for r in self.outputs:validate_source_map(r.bundle.source_map,r.codegen.files)
    def test_tracks_bind_source_map(self):
        for r in self.outputs:self.assertTrue(any(s.origin.track_id and s.origin.source_refs for s in r.bundle.source_map.spans))
    def test_specialized_contracts_are_emitted(self):
        for r in self.outputs:
            data=json.loads(next(f.content for f in r.codegen.files if f.path=='src/bie-behavior-contracts.json'))
            self.assertEqual(len(data['specialized']),1);self.assertFalse(data['specialized'][0]['symbolic_equivalence_verified'])
    def test_existing_publication_revalidates(self):self.assertTrue(require_h3_workspace(self.published).source_gate_passed)
    def test_wrong_target_blocks_publication(self):
        p=camera_scene();p['tracks'][0]['parameters']['viewport']['width']=600
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out'
            with self.assertRaisesRegex(ValueError,'PUBLICATION_BLOCKED'):publish_h3_scene(p,out,target=BIG)
            self.assertFalse(out.exists())
    def test_content_ownership_conflict_blocks(self):
        p=equation_scene();t=deepcopy(p['tracks'][0]);t['track_id']='second';p['tracks'].append(t)
        r=compile_h3_scene(p,target=BIG);self.assertFalse(r.receipt.source_gate_passed)
        self.assertIn('ANIMATION_PROPERTY_OWNERSHIP_CONFLICT',{f.code for f in r.receipt.findings})
    def test_camera_transform_ownership_blocks(self):
        p=camera_scene();p['tracks'].append(track('transform',{'from':{'scale':1},'to':{'scale':2}},track_id='conflict',source_refs=p['source_refs'],reasoning_refs=p['reasoning_refs']))
        r=compile_h3_scene(p,target=BIG);self.assertFalse(r.receipt.source_gate_passed)
    def test_camera_no_implicit_crop(self):
        p=camera_scene();p['tracks'][0]['parameters']['to']['zoom']=10
        r=compile_h3_scene(p,target=BIG);self.assertFalse(r.layout['passed']);self.assertFalse(r.receipt.source_gate_passed)
    def test_reduced_motion_cannot_erase_steps(self):
        with self.assertRaisesRegex(ValueError,'SPECIALIZED_REDUCED_VARIANT_REQUIRED'):compile_h3_scene(equation_scene(),target=BIG,motion_preference='reduced')
    def test_reduced_motion_cannot_erase_trace(self):
        with self.assertRaisesRegex(ValueError,'SPECIALIZED_REDUCED_VARIANT_REQUIRED'):compile_h3_scene(trace_scene(),target=BIG,motion_preference='reduced')
    def test_source_bytes_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'source';shutil.copytree(self.published,r)
            f=next((r/'src/animations').glob('*.tsx'));f.write_text(f.read_text()+'\n//tamper')
            with self.assertRaisesRegex(ValueError,'SOURCE_TAMPERED'):require_h3_workspace(r)
    def test_source_contract_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'source';shutil.copytree(self.published,r);f=r/'CHECKED_SCENE.json';d=json.loads(f.read_text());d['document']['tracks'][0]['parameters']['head_marker']=False;f.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'ENVELOPE_TAMPERED'):require_h3_workspace(r)
    def test_unconsumed_state_binding_still_blocks(self):
        # Existing broad contracts are not silently unlocked by the three H5 consumers.
        p=trace_scene();p['state_bindings']=[{'binding_id':'state','element_id':'e0','state_path':'state.value','property_name':'opacity','target_id':'e0','transform':'identity'}]
        from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
        decode_scene_ir(p)  # Schema validity is established before testing the unconsumed gate.
        r=compile_scene_for_qa(p,target=BIG)
        self.assertFalse(r.source_contract_passed)
        self.assertIn('UNCONSUMED_SCENE_CONTRACT',{f.code for f in r.findings})
    def test_typesetter_failure_not_published(self):
        p=equation_scene();p['tracks'][0]['parameters']['states'][-1]['expression']=r'\unknowncommand{x}'
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out'
            with self.assertRaises(ValueError):publish_h3_scene(p,out,target=BIG)
            self.assertFalse(out.exists())
    def test_real_harness_retains_dependency_gate(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_checked_remotion.py'),str(self.published)],capture_output=True,text=True,timeout=45)
        d=json.loads(r.stdout);self.assertEqual(r.returncode,2);self.assertIn('FULL_TYPECHECK_BLOCKED',d['failure']);self.assertFalse(d['accepted'])
    def test_truth_boundaries_retained(self):
        for r in self.outputs:self.assertFalse(r.receipt.accepted);self.assertFalse(r.receipt.full_compile_verified);self.assertEqual(r.receipt.real_render_status,'NOT_RUN')
    def test_actual_layout_authorization_still_required(self):
        with self.assertRaisesRegex(ValueError,'REAL_LAYOUT_EVIDENCE_REQUIRED'):require_real_layout_authorization({'passed':True})
    def test_existing_cli_explicit_target_consumes_camera(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'scene.json';p.write_text(json.dumps(self.inputs[0]))
            r=subprocess.run([sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),str(p),str(root/'project'),'--width','1280','--height','720','--fps','24'],capture_output=True,text=True,timeout=40)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertTrue(json.loads(r.stdout)['source_gate_passed'])
    def test_new_emitters_strict_tsc_explicit_declaration_doubles(self):
        from bie.compiler.specialized_camera import compile_specialized_camera
        from bie.compiler.specialized_equation import compile_specialized_equation
        from bie.compiler.specialized_trace import compile_specialized_trace
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for i,(p,fn) in enumerate(zip(self.inputs,[compile_specialized_camera,compile_specialized_equation,compile_specialized_trace])):
                (root/f'c{i}.tsx').write_text(fn(p['tracks'][0],p['elements'][0]).source_text)
            (root/'ambient.d.ts').write_text("""// Explicit dependency declaration doubles, NOT installed React/Remotion.
declare module 'react' { namespace React { type ReactNode=unknown; type PropsWithChildren={children?:unknown}; type FC<P={}>=(p:P)=>unknown; function createElement(tag:string,props:unknown,...children:unknown[]):unknown; } export = React; }
declare module 'react/jsx-runtime' { export namespace JSX { interface IntrinsicElements {[name:string]:any;} } }
declare module 'remotion' { export function useCurrentFrame():number; export function useVideoConfig():{fps:number}; }
""")
            r=subprocess.run(['tsc','--noEmit','--strict','--esModuleInterop','--moduleResolution','node','--target','ES2022','--jsx','react-jsx',*map(str,root.glob('*'))],capture_output=True,text=True,timeout=35)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)

if __name__=='__main__':unittest.main()
