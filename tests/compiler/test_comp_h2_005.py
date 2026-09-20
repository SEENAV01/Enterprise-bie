from copy import deepcopy
from dataclasses import replace,asdict
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
import json,tempfile,unittest
from bie.compiler.checked_scene_compile import compile_scene_checked,publish_checked_scene,verify_checked_workspace
from bie.compiler.qa_scene_compile import compile_scene_for_qa,CompilerQATarget
from bie.compiler.capability_fallback_qa import inspect_emitted_semantics
from bie.compiler.scene_behavior_qa import validate_scene_behaviors
from bie.compiler.compile_diagnostics_mapping import validate_source_map
from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
from tests.compiler.h2_test_support import scene,sim_props,geo_props,track

class BehaviorGateTests(unittest.TestCase):
    def motion_scene(self,tracks=None):
        p=scene('text',{'text':'Synthetic moving text'});p['tracks']=tracks or [track(element_id=p['elements'][0]['element_id'])];return p
    def codes(self,p,target=None):return {f.code for f in compile_scene_checked(p,target=target)[1].findings}
    def test_multiline_backend_error_blocks_without_receipt_crash(self):
        b,r=compile_scene_checked(scene('equation',{'format':'latex','expression':r'\notKnown{x}'}))
        self.assertFalse(r.source_gate_passed)
        found=[f for f in r.findings if f.code=='EQUATION_LATEX_UNSUPPORTED']
        self.assertTrue(found);self.assertTrue(all('\n' not in f.message for f in found))
        self.assertIn(r'\u000a',found[0].message)
    def test_diagnostic_controls_escaped_not_silently_removed(self):
        from bie.compiler.qa_common import diagnostic_message,QAFinding
        message=diagnostic_message(ValueError('bad\x00\x1b[31m\ninput'))
        self.assertEqual(message,r'bad\u0000\u001b[31m\u000ainput')
        self.assertEqual(QAFinding('FAIL','ERROR',message).message,message)
    def test_raw_control_characters_still_rejected(self):
        from bie.compiler.qa_common import QAFinding
        with self.assertRaises(ValueError):QAFinding('FAIL','ERROR','bad\nreceipt')
    def test_fixed_equation_passes_checked_source(self):self.assertTrue(compile_scene_checked(scene('equation',{'format':'latex','expression':r'\frac{x}{2}'}))[1].source_gate_passed)
    def test_native_mathml_passes_checked_source(self):self.assertTrue(compile_scene_checked(scene('equation',{'format':'mathml','expression':'<math><mi>x</mi></math>'}))[1].source_gate_passed)
    def test_declared_projection_passes_checked_source(self):self.assertTrue(compile_scene_checked(scene('map',geo_props()))[1].source_gate_passed)
    def test_analytic_simulation_passes_with_end_sample(self):
        p=scene('simulation',sim_props());p['duration_ms']=3000;self.assertTrue(compile_scene_checked(p)[1].source_gate_passed)
    def test_applied_motion_passes_checked_source(self):self.assertTrue(compile_scene_checked(self.motion_scene())[1].source_gate_passed)
    def test_unsupported_motion_blocks_whole_scene(self):self.assertIn('ANIMATION_ACTION_UNSUPPORTED',self.codes(self.motion_scene([track('morph')])) )
    def test_bad_motion_preserves_diagnostic_stub(self):
        b,r=compile_scene_checked(self.motion_scene([track('camera')]));self.assertFalse(r.source_gate_passed);self.assertIn('throw new Error',b.animation_results[0].source_text)
    def test_failed_motion_never_published(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'blocked'
            with self.assertRaises(ValueError):publish_checked_scene(self.motion_scene([track('camera')]),p)
            self.assertFalse(p.exists())
    def test_collapsed_sampling_blocks_source(self):self.assertIn('ANIMATION_FRAME_RANGE_COLLAPSES',self.codes(self.motion_scene([track(end_ms=40)])))
    def test_emphasis_needs_visible_peak_frame(self):self.assertIn('ANIMATION_PULSE_UNSAMPLED',self.codes(self.motion_scene([track('emphasize',end_ms=84)])))
    def test_same_property_ownership_conflict_blocked(self):
        ts=[track(),track(track_id='other',start_ms=500,end_ms=1500)];self.assertIn('ANIMATION_PROPERTY_OWNERSHIP_CONFLICT',self.codes(self.motion_scene(ts)))
    def test_disjoint_enter_exit_neutral_pair_allowed(self):
        ts=[track(),track('exit',track_id='exit',start_ms=1000,end_ms=2000)];self.assertTrue(compile_scene_checked(self.motion_scene(ts))[1].source_gate_passed)
    def test_overlapping_enter_exit_blocked(self):
        ts=[track(),track('exit',track_id='exit',start_ms=500,end_ms=1500)];self.assertIn('ANIMATION_PROPERTY_OWNERSHIP_CONFLICT',self.codes(self.motion_scene(ts)))
    def test_non_neutral_opacity_pair_blocked(self):
        ts=[track(params={'from_opacity':.2,'to_opacity':.7}),track('exit',track_id='exit',start_ms=1000,end_ms=2000)];self.assertIn('ANIMATION_PROPERTY_OWNERSHIP_CONFLICT',self.codes(self.motion_scene(ts)))
    def test_distinct_properties_compose(self):
        ts=[track(),track('reveal',track_id='reveal')];self.assertTrue(compile_scene_checked(self.motion_scene(ts))[1].source_gate_passed)
    def test_sequential_translations_not_silently_added(self):
        p={'from':{'translate_x':0},'to':{'translate_x':10}};ts=[track('transform',p),track('transform',p,track_id='second',start_ms=1000,end_ms=2000)];self.assertIn('ANIMATION_PROPERTY_OWNERSHIP_CONFLICT',self.codes(self.motion_scene(ts)))
    def test_simulation_end_must_be_visible(self):self.assertIn('SIMULATION_FINAL_STATE_NOT_VISIBLE',self.codes(scene('simulation',sim_props())))
    def test_oscillator_render_aliasing_blocked(self):
        p=sim_props('oscillator');p['parameters']['omega']=40;s=scene('simulation',p);s['duration_ms']=3000;self.assertIn('SIMULATION_FRAME_ALIASING',self.codes(s))
    def test_layer_source_must_bind_to_element_lineage(self):
        p=geo_props();p['layers'][0]['source_ref']='unbound:source';self.assertIn('MAP_LAYER_SOURCE_UNBOUND',self.codes(scene('map',p)))
    def test_bound_layer_source_allowed(self):
        s=scene('map',geo_props());s['elements'][0]['props']['layers'][0]['source_ref']=s['elements'][0]['source_refs'][0];self.assertTrue(compile_scene_checked(s)[1].source_gate_passed)
    def test_behavior_sidecar_emitted(self):
        b=compile_scene_for_qa(self.motion_scene());f=next(f for f in b.codegen.files if f.path=='src/bie-behavior-contracts.json');d=json.loads(f.content);self.assertEqual(d['motion'][0]['sample_end_frame'],23);self.assertFalse(d['accepted'])
    def test_behavior_source_mapping_preserved(self):
        b=compile_scene_for_qa(self.motion_scene());validate_source_map(b.source_map,b.codegen.files);self.assertTrue(any(s.origin.track_id for s in b.source_map.spans))
    def test_source_tamper_cannot_fake_semantic_fix(self):
        p=scene('equation',{'expression':'x^2','format':'latex'});b=compile_scene_for_qa(p);r=b.element_results[0];text=r.source_text.replace('renderMathNode(equationLayout.tree as EquationNode, "equation")','expression');bad=replace(r,source_text=text,source_sha256=sha256(text.encode()).hexdigest());codes={f.code for f in inspect_emitted_semantics(decode_scene_ir(p),(bad,))};self.assertIn('HARDENED_EMITTER_OUTPUT_MISMATCH',codes)
    def test_published_h2_workspace_revalidates(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'p';r=publish_checked_scene(scene('equation',{'expression':'x^2','format':'latex'}),p);self.assertEqual(verify_checked_workspace(p),r)
    def test_behavior_sidecar_tamper_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'p';publish_checked_scene(self.motion_scene(),p);(p/'src/bie-behavior-contracts.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'TAMPERED'):verify_checked_workspace(p)
    def test_parent_compiler_identity_changes(self):self.assertEqual(CompilerQATarget().compiler_version,'1.2.0-comp-h2')
    def test_qa_receipt_never_accepted_or_rendered(self):
        b,r=compile_scene_checked(self.motion_scene());self.assertFalse(r.accepted);self.assertFalse(r.full_compile_verified);self.assertEqual(r.real_render_status,'NOT_RUN')

if __name__=='__main__':unittest.main()
