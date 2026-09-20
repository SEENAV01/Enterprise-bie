"""Cross-task regression of H3 adoption, provenance, variants and evidence limits."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import json,subprocess,sys,tempfile,unittest
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.frame_layout import iter_frame_layers
from bie.compiler.content_fit_qa import inspect_content_fit,require_real_layout_authorization
from bie.compiler.qa_common import digest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.render_contracts import RenderRequest
from tests.compiler.h3_test_support import scene,move,variant,sim_props,TARGET,ROOT,measurement

BIG=replace(TARGET,width=1280,height=720)

def combined():
    p=scene('equation',{'expression':r'\frac{1}{2}at^2','format':'latex'},duration_ms=3000)
    p['elements'][0]['normalized_box']={'x':.05,'y':.05,'width':.4,'height':.2}
    s=scene('simulation',sim_props(),duration_ms=3000)['elements'][0];s['element_id']='sim';s['normalized_box']={'x':.05,'y':.35,'width':.9,'height':.6}
    t=scene('text',{'text':'Synthetic source-bound technical scene'})['elements'][0];t['element_id']='label';t['normalized_box']={'x':.55,'y':.05,'width':.4,'height':.2}
    p['elements'] += [s,t]
    return variant(p)

class H3IntegrationTests(unittest.TestCase):
    def test_combined_families_pass_hardened_source(self):
        r=compile_h3_scene(combined(),target=BIG);self.assertTrue(r.receipt.source_gate_passed);self.assertEqual(len(r.bundle.element_results),3)
    def test_combined_reduced_preserves_all_content_and_provenance(self):
        p=combined();before=deepcopy(p);r=compile_h3_scene(p,target=BIG,motion_preference='reduced');self.assertEqual(p,before);self.assertEqual(r.effective_document['elements'],p['elements']);self.assertEqual(r.motion['frozen_simulation_frames'],{'sim':48});self.assertTrue(all(span.origin.source_refs and span.origin.reasoning_refs for span in r.bundle.source_map.spans))
    def test_every_frame_all_layers_in_combined_scene(self):
        r=compile_h3_scene(combined(),target=BIG);rows=list(iter_frame_layers(r.effective_document,BIG));self.assertEqual(len(rows),72);self.assertEqual(sum(len(row) for row in rows),216);self.assertTrue(r.layout['passed'])
    def test_combined_standard_and_reduced_use_different_simulation_behavior(self):
        a=compile_h3_scene(combined(),target=BIG);b=compile_h3_scene(combined(),target=BIG,motion_preference='reduced');sa=next(e.source_text for e in a.bundle.element_results if e.element_type=='simulation');sb=next(e.source_text for e in b.bundle.element_results if e.element_type=='simulation');self.assertIn('const frame = useCurrentFrame()',sa);self.assertIn('const frame = 48;',sb);self.assertNotEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_h3_svg_baseline_fix_is_scoped_to_new_wrapper(self):
        r=compile_h3_scene(combined(),target=BIG);s=next(f.content for f in r.codegen.files if 'qa-layers/QALayer_sim_' in f.path);self.assertIn('data-bie-content-viewport="svg"',s);self.assertIn('display: "flex"',s);self.assertNotIn('overflow: "hidden"',s)
    def test_missing_variant_blocks_whole_publication(self):
        p=combined();p['metadata']['compiler_h3']['reduced_motion_variants']={}
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'source'
            with self.assertRaises(ValueError):publish_h3_scene(p,d,target=BIG,motion_preference='reduced')
            self.assertFalse(d.exists())
    def test_intentional_overlap_remains_bound_in_published_policy(self):
        p=scene();e=deepcopy(p['elements'][0]);e['element_id']='overlay';p['elements'].append(e);p['metadata']['compiler_h3']={'layout':{'allow_overlap':[{'elements':['e0','overlay'],'reason':'Explicit technical overlay, not a readability approval','source_refs':['fixture:h3'],'reasoning_refs':['reasoning:h3']}]}}
        r=compile_h3_scene(p);self.assertTrue(r.receipt.source_gate_passed);self.assertEqual(r.layout['intentional_overlaps'][0]['count'],24);self.assertFalse(r.layout['paint_verified'])
    def test_original_fingerprinted_input_derives_new_source_identity(self):
        from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
        p=variant(move());p=decode_scene_ir(p).to_dict();r=compile_h3_scene(p,motion_preference='reduced');self.assertTrue(r.receipt.source_gate_passed);self.assertNotEqual(r.receipt.scene_fingerprint,p['fingerprint'])
    def test_render_fingerprint_cannot_switch_selected_variant(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';a=publish_h3_scene(combined(),root,target=BIG,motion_preference='reduced');b=compile_h3_scene(combined(),target=BIG)
            with self.assertRaisesRegex(ValueError,'IDENTITY_MISMATCH'):require_h3_workspace(root,expected_scene_fingerprint=b.receipt.scene_fingerprint)
    def test_render_target_change_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';r=publish_h3_scene(scene(),root);c=CompositionDescriptor('BieQA'+digest(scene()['scene_id'])[:16],1280,720,24,24);req=RenderRequest(str(root),'src/index.ts',c,'out/test.mp4',r.scene_fingerprint,'integration')
            with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):require_h3_workspace(root,render_request=req)
    def test_measurements_cannot_cross_standard_reduced_identity(self):
        a=compile_h3_scene(variant(move()));b=compile_h3_scene(variant(move()),motion_preference='reduced');report=measurement(a.effective_document,manifest=a.codegen.manifest_sha256);fit=inspect_content_fit(report,b.effective_document,TARGET,b.codegen.manifest_sha256);self.assertFalse(fit['passed']);self.assertIn('LAYOUT_EVIDENCE_IDENTITY_MISMATCH',{f['code'] for f in fit['findings']})
    def test_exhaustive_bridge_pass_never_grants_release(self):
        r=compile_h3_scene(scene());fit=inspect_content_fit(measurement(r.effective_document,manifest=r.codegen.manifest_sha256),r.effective_document,TARGET,r.codegen.manifest_sha256);self.assertTrue(fit['passed']);self.assertFalse(fit['release_authorized'])
        with self.assertRaisesRegex(ValueError,'REAL_LAYOUT_EVIDENCE_REQUIRED'):require_real_layout_authorization(fit)
    def test_missing_combined_layer_frames_blocks_content_gate(self):
        r=compile_h3_scene(combined(),target=BIG);m=measurement(r.effective_document,target=BIG,manifest=r.codegen.manifest_sha256);m['records']=[x for x in m['records'] if x['element_id']!='sim'];q=inspect_content_fit(m,r.effective_document,BIG,r.codegen.manifest_sha256);self.assertFalse(q['passed']);self.assertIn('LAYOUT_FRAME_COVERAGE_INCOMPLETE',{f['code'] for f in q['findings']})
    def test_parent_h2_original_and_golden_bytes_retained(self):
        rows=json.loads((ROOT/'lineage/hardening_h2/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for row in rows:
            if row['path'].startswith('fixtures/'):
                self.assertEqual(sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])
    def test_parent_member_changes_have_exact_lineage_copy(self):
        rows=json.loads((ROOT/'lineage/hardening_h2/ORIGINAL_MEMBER_HASHES.json').read_text())['members']
        for row in rows:
            p=ROOT/row['path'];self.assertTrue(p.is_file(),row['path'])
            if sha256(p.read_bytes()).hexdigest()!=row['sha256']:
                b=ROOT/'lineage/hardening_h2'/row['path'];self.assertTrue(b.is_file(),row['path']);self.assertEqual(sha256(b.read_bytes()).hexdigest(),row['sha256'],row['path'])
    def test_independent_process_compilation_matches_current_host(self):
        p=combined();r=compile_h3_scene(p,target=BIG,motion_preference='reduced')
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'scene.json';f.write_text(json.dumps(p));code="import json,sys;from dataclasses import replace;from bie.compiler.hardened_scene_compile import compile_h3_scene;from bie.compiler.qa_scene_compile import CompilerQATarget;t=replace(CompilerQATarget(),compiler_version='1.3.0-comp-h3',width=1280,height=720);r=compile_h3_scene(json.load(open(sys.argv[1])),target=t,motion_preference='reduced');print(r.codegen.manifest_sha256)"
            out=subprocess.run([sys.executable,'-c',code,str(f)],cwd=ROOT,capture_output=True,text=True,timeout=30);self.assertEqual(out.returncode,0,out.stderr);self.assertEqual(out.stdout.strip(),r.codegen.manifest_sha256)

if __name__=='__main__':unittest.main()
