import unittest,json
from copy import deepcopy
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.frame_layout import evaluate_frame_layout,iter_frame_layers,layer_box
from bie.compiler.frame_runtime_contract import plan_frame_runtime
from bie.compiler.frame_state_consumer import runtime_at,emit_bound_layer
from bie.compiler.composition_conformance import verify_composition
from tests.compiler.h10_test_support import composed_scene,bind,T
from tests.compiler.h6_test_support import state_scene
from tests.compiler.h9_test_support import highlight_scene
from bie.compiler.highlight_compiler import highlight_geometry

class FrameVisibilityCompositionTests(unittest.TestCase):
    def test_content_replacement_keeps_outer_state_controls(self):
        r=compile_h3_scene(composed_scene('static_trace'),target=T)
        self.assertTrue(r.receipt.source_gate_passed);self.assertTrue(verify_composition(r,T)['passed'])
    def test_text_and_controls_do_not_swallow_transform(self):
        r=compile_h3_scene(composed_scene('transform',('text','visible')),target=T)
        self.assertTrue(r.receipt.source_gate_passed);self.assertTrue(verify_composition(r,T)['passed'])
        files=[f for f in r.codegen.files if 'runtime-layers' in f.path];self.assertEqual(len(files),2)
    def test_content_and_controls_have_distinct_exports(self):
        p=composed_scene('transform',('text','visible'));plan=plan_frame_runtime(p,T)
        a=emit_bound_layer(plan,p['elements'][0],mode='content');b=emit_bound_layer(plan,p['elements'][0],mode='controls')
        self.assertNotEqual(a[1],b[1]);self.assertNotIn('>{children}</div>',a[0].content);self.assertIn('>{children}</div>',b[0].content)
    def test_no_content_layer_for_nontext_control(self):
        p=composed_scene();plan=plan_frame_runtime(p,T);self.assertIsNone(emit_bound_layer(plan,p['elements'][0],mode='content'))
    def test_opacity_state_graph_applies_outside_replacement(self):self.assertTrue(verify_composition(compile_h3_scene(composed_scene('trace',('opacity',)),target=T),T)['passed'])
    def test_simulation_replacement_preserves_controls(self):self.assertTrue(verify_composition(compile_h3_scene(composed_scene('simulation_state'),target=T),T)['passed'])
    def test_morph_replacement_preserves_controls(self):self.assertTrue(verify_composition(compile_h3_scene(composed_scene('morph'),target=T),T)['passed'])
    def test_layout_visibility_matches_each_runtime_frame(self):
        p=composed_scene();plan=plan_frame_runtime(p,T)
        for frame,rows in enumerate(iter_frame_layers(p,T)):
            self.assertEqual(rows[0]['visible_conservative'],runtime_at(plan,frame)['targets']['e0']['visible'])
    def test_hidden_geometry_is_still_preserved(self):
        rows=list(iter_frame_layers(composed_scene(),T));self.assertEqual(rows[0][0]['polygon'],rows[10][0]['polygon']);self.assertFalse(rows[10][0]['visible_conservative'])
    def test_alpha_layout_matches_state_opacity(self):
        p=composed_scene('trace',('opacity',));plan=plan_frame_runtime(p,T)
        for f,rows in enumerate(iter_frame_layers(p,T)):self.assertAlmostEqual(rows[0]['opacity'],runtime_at(plan,f)['targets']['e0']['opacity'])
    def hidden_overlap(self):
        p=state_scene();p['events']=[];p['metadata']['compiler_h6']['initial_state']['lesson.phase']=False;p['state_bindings'][0]['property_name']='visible'
        e=deepcopy(p['elements'][0]);e['element_id']='sibling';p['elements'].append(e);return p
    def test_hidden_layer_no_false_overlap(self):self.assertTrue(evaluate_frame_layout(self.hidden_overlap(),T)['passed'])
    def test_visible_overlap_not_waived(self):
        p=self.hidden_overlap();p['metadata']['compiler_h6']['initial_state']['lesson.phase']=True
        self.assertIn('LAYOUT_UNDECLARED_OVERLAP',{f['code'] for f in evaluate_frame_layout(p,T)['findings']})
    def test_late_visible_overlap_records_actual_start_frame(self):
        p=self.hidden_overlap();p['events']=[{'event_id':'show','at_ms':500,'event_type':'state.set','target_ids':['e0'],'payload':{'state_path':'lesson.phase','value':True,'source_refs':p['source_refs'],'reasoning_refs':p['reasoning_refs']}}]
        findings=evaluate_frame_layout(p,T)['findings'];self.assertIn('first=6',findings[0]['message'])
    def test_highlight_disappears_with_hidden_moving_target(self):
        p=bind(highlight_scene(moving=True));g=highlight_geometry(p['elements'][1],p,T)
        self.assertTrue(g['frames'][0][0]['visible']);self.assertFalse(g['frames'][5][0]['visible']);self.assertTrue(g['frames'][-1][0]['visible'])
    def test_highlight_keeps_transformed_points_when_hidden(self):
        p=bind(highlight_scene(moving=True));g=highlight_geometry(p['elements'][1],p,T)
        self.assertNotEqual(g['frames'][0][0]['points'],g['frames'][5][0]['points'])
    def test_unknown_runtime_mode_rejected(self):
        p=composed_scene();self.assertRaisesRegex(ValueError,'LAYER_MODE',emit_bound_layer,plan_frame_runtime(p,T),p['elements'][0],mode='unknown')
    def test_layer_qa_does_not_certify_actual_paint(self):self.assertFalse(evaluate_frame_layout(composed_scene(),T)['paint_verified'])
    def test_hidden_layer_still_rejects_bad_source(self):
        p=self.hidden_overlap();p['elements'][0]['props']['text']=''
        self.assertFalse(compile_h3_scene(p,target=T).receipt.source_gate_passed)
    def test_outer_state_does_not_change_track_times(self):
        p=composed_scene('progressive_static_trace');q=deepcopy(p);r=compile_h3_scene(p,target=T)
        self.assertEqual(r.effective_document['tracks'],q['tracks']);self.assertEqual(p,q)
    def test_scope_rejects_no_consent_even_when_fit(self):
        p=composed_scene('transform');p['metadata'].pop('compiler_h10');self.assertRaisesRegex(ValueError,'PROPERTY_CONFLICT',compile_h3_scene,p,target=T)
