from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json,subprocess,sys,tempfile,unittest
from bie.compiler.checked_scene_compile import *
from bie.compiler.qa_scene_compile import compile_scene_for_qa,CompilerQATarget
from bie.compiler.generated_code_regression import probe_typescript_sources,typecheck_generated_workspace
from bie.compiler.deterministic_output_qa import snapshot_generated,compare_snapshots
from bie.compiler.capability_fallback_qa import inspect_emitted_semantics
from bie.compiler.element_compiler_common import ElementCompileResult
from bie.compiler.equation_compiler import compile_equation_element
from bie.compiler.map_compiler import compile_map_element
from bie.compiler.simulation_compiler import compile_simulation_element
from bie.compiler.animation_track_compiler import compile_animation_track
from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
from tests.compiler.h2_test_support import ROOT,scene,sim_props,geo_props,track,element,runtime,nodes

class H2IntegrationTests(unittest.TestCase):
    def combined(self):
        p=scene('equation',{'expression':r'\frac{1}{2}at^2','format':'latex'});p['duration_ms']=3000
        for i,(kind,props) in enumerate([('simulation',sim_props()),('map',geo_props())],start=1):
            s=scene(kind,props);e=s['elements'][0];e['element_id']='h2e'+str(i);p['elements'].append(e)
        p['elements'][0]['normalized_box']={'x':0,'y':0,'width':1,'height':.2}
        p['elements'][1]['normalized_box']={'x':0,'y':.2,'width':.5,'height':.8}
        p['elements'][2]['normalized_box']={'x':.5,'y':.2,'width':.5,'height':.8}
        p['tracks']=[track(element_id=p['elements'][0]['element_id'])]
        return p
    def test_multiple_fixed_families_assemble(self):
        b,r=compile_scene_checked(self.combined());self.assertTrue(r.source_gate_passed);self.assertEqual(len(b.element_results),3);self.assertEqual(len(b.animation_results),1)
    def test_source_change_changes_manifest(self):
        p=self.combined();a=compile_scene_for_qa(p);p['elements'][0]['props']['expression']='at';b=compile_scene_for_qa(p);self.assertNotEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_model_change_changes_source_identity(self):
        p=self.combined();a=compile_scene_for_qa(p);p['elements'][1]['props']['parameters']['ax']=.1;b=compile_scene_for_qa(p);self.assertNotEqual(a.scene_fingerprint,b.scene_fingerprint)
    def test_frame_rate_changes_dependency_context(self):
        p=self.combined();a=compile_scene_for_qa(p);b=compile_scene_for_qa(p,target=CompilerQATarget(fps=30));self.assertNotEqual(a.context.dependency_identity,b.context.dependency_identity)
    def test_full_scene_byte_determinism(self):
        p=self.combined();a=compile_scene_for_qa(p);b=compile_scene_for_qa(p);self.assertTrue(compare_snapshots([snapshot_generated(a.codegen.files,a.context),snapshot_generated(b.codegen.files,b.context)],expected_runs=2).passed)
    def test_bad_element_blocks_valid_siblings(self):
        p=self.combined();p['elements'][2]['props'].pop('projection');self.assertFalse(compile_scene_checked(p)[1].source_gate_passed)
    def test_unconsumed_scene_contract_still_blocks(self):
        p=self.combined();p['state_bindings']=[{'binding_id':'unimplemented','element_id':p['elements'][0]['element_id'],'state_ref':'s','property_path':'x'}]
        try:b,r=compile_scene_checked(p)
        except ValueError:return # Existing DSL rejection also correctly blocks malformed bindings.
        self.assertFalse(r.source_gate_passed);self.assertIn('UNCONSUMED_SCENE_CONTRACT',{f.code for f in r.findings})
    def test_historical_untypeset_source_still_fails(self):
        p=json.loads((ROOT/'fixtures/comp_h1/corpus.json').read_text());c=next(c for c in p['cases'] if c['case_id']=='reject-untypeset-equation');data=json.loads((ROOT/'fixtures/comp_h2/historical_h1_behavior_results.json').read_text());row=data[c['case_id']]['elements'][0]
        for key in ('required_dependencies','asset_paths','warnings'):row[key]=tuple(row[key])
        codes={f.code for f in inspect_emitted_semantics(decode_scene_ir(c['document']),[ElementCompileResult(**row)])};self.assertIn('EQUATION_TYPESETTING_NOT_IMPLEMENTED',codes);self.assertIn('HARDENED_EMITTER_OUTPUT_MISMATCH',codes)
    def test_historical_metadata_motion_evidence_retained(self):
        d=json.loads((ROOT/'fixtures/comp_h2/historical_h1_behavior_results.json').read_text());old=d['reject-metadata-animation']['tracks'][0]['source_text'];self.assertIn('data-bie-progress={progress}',old);self.assertNotIn('style=',old)
    def test_original_h1_corpus_and_golden_bytes_unchanged(self):
        manifest=json.loads((ROOT/'lineage/hardening_h1/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for rec in manifest:
            if rec['path'].startswith('fixtures/comp_h1/'):
                self.assertEqual(sha256((ROOT/rec['path']).read_bytes()).hexdigest(),rec['sha256'])
    def test_new_corpus_keeps_old_source_documents(self):
        a=json.loads((ROOT/'fixtures/comp_h1/corpus.json').read_text());b=json.loads((ROOT/'fixtures/comp_h2/corpus.json').read_text());self.assertEqual([c['document'] for c in a['cases']],[c['document'] for c in b['cases']])
    def test_every_modified_parent_file_preserved(self):
        rows=json.loads((ROOT/'lineage/hardening_h1/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for row in rows:
            path=ROOT/row['path'];self.assertTrue(path.is_file(),row['path'])
            if sha256(path.read_bytes()).hexdigest()!=row['sha256']:
                backup=ROOT/'lineage/hardening_h1'/row['path'];self.assertTrue(backup.is_file(),row['path']);self.assertEqual(sha256(backup.read_bytes()).hexdigest(),row['sha256'])
    def test_new_emitters_strict_typescript_with_labelled_api_doubles(self):
        results=[compile_equation_element(element('equation',{'format':'plain','expression':'x'})),compile_equation_element(element('equation',{'format':'latex','expression':r'\frac{x}{y}'})),compile_equation_element(element('equation',{'format':'mathml','expression':'<math><mi>x</mi></math>'})),compile_simulation_element(element('simulation',sim_props())),compile_map_element(element('map',geo_props())),compile_animation_track(track())]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for i,r in enumerate(results):(root/f'component{i}.tsx').write_text(r.source_text)
            # Real tsc checking with deliberately explicit ambient API declarations.
            # This does NOT validate installed React/Remotion dependency compatibility.
            (root/'ambient.d.ts').write_text("""declare module 'react' { namespace React { type ReactNode = unknown; type PropsWithChildren = {children?: unknown}; type FC<P = {}> = (props:P) => unknown; interface CSSProperties {opacity?:number;scale?:number;translate?:string;rotate?:string;clipPath?:string;transformOrigin?:string;} function createElement(tag:string,props:unknown,...children:unknown[]):unknown; } export = React; }
declare module 'react/jsx-runtime' { export namespace JSX { interface IntrinsicElements { [name:string]: any; } } }
declare module 'remotion' { export function useCurrentFrame():number; export function useVideoConfig():{fps:number}; export function interpolate(v:number,x:number[],y:number[],options?:unknown):number; }
""")
            run=subprocess.run(['tsc','--noEmit','--strict','--esModuleInterop','--moduleResolution','node','--target','ES2022','--jsx','react-jsx',*map(str,root.glob('*'))],capture_output=True,text=True,timeout=25);self.assertEqual(run.returncode,0,run.stdout+run.stderr)
    def test_real_validation_harness_blocks_without_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source';publish_checked_scene(self.combined(),p);r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_checked_remotion.py'),str(p)],capture_output=True,text=True,timeout=25);data=json.loads(r.stdout);self.assertEqual(r.returncode,2,r.stderr);self.assertIn('FULL_TYPECHECK_BLOCKED',data['failure']);self.assertFalse(data['accepted'])
    def test_h2_cli_publishes_checked_scene_not_video(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'scene.json').write_text(json.dumps(self.combined()));r=subprocess.run([sys.executable,str(ROOT/'scripts/compile_scene_checked.py'),str(p/'scene.json'),str(p/'out')],capture_output=True,text=True,timeout=25);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertTrue((p/'out/CHECKED_SCENE.json').is_file());self.assertFalse(list((p/'out').rglob('*.mp4')))
    def test_reduced_motion_reference_is_not_claimed_as_tested_variant(self):
        p=self.combined();b,r=compile_scene_checked(p);self.assertFalse(r.accepted);self.assertEqual(r.real_render_status,'NOT_RUN');self.assertTrue(p['elements'][1]['accessibility'].get('reduced_motion_variant'))

if __name__=='__main__':unittest.main()
