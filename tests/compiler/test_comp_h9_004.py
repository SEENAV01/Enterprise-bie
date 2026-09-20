import unittest
from copy import deepcopy
from dataclasses import replace
from bie.compiler.registered_actions import *
from bie.compiler.registered_action_compiler import compile_registered_track
from bie.compiler.animation_behavior import motion_contract,motion_state
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h9_test_support import action_scene,T,runtime,full_tree,nodes

class RegisteredConsumerTests(unittest.TestCase):
    def c(self,a):return registered_contract(action_scene(a)['tracks'][0])
    def emit(self,a):
        p=action_scene(a);return compile_registered_track(p['tracks'][0],p['elements'][0])
    def bad(self,p,code):
        with self.assertRaisesRegex(ValueError,code):validate_registered_binding(p['tracks'][0],p['elements'][0],T,p['duration_ms'])
    def test_all_seven_have_checked_source(self):
        for action in sorted(ACTIONS):
            with self.subTest(action=action):
                p=action_scene(action);r=compile_h3_scene(p,target=T);self.assertTrue(r.receipt.source_gate_passed,r.receipt.findings)
    def test_all_seven_execute_full_tree_at_endpoints(self):
        for action in sorted(ACTIONS):
            with self.subTest(action=action):
                p=action_scene(action);r=compile_h3_scene(p,target=T);last=(p['duration_ms']*T.fps+999)//1000-1;out=full_tree(r,frames=[0,last],target=T);self.assertIn(action,str(out));self.assertEqual(len(out['trees']),2)
    def test_original_action_identity_retained(self):
        for action in sorted(ACTIONS):self.assertEqual(self.emit(action).action,action)
    def test_static_focus_no_motion_between_frames(self):
        c=self.c('static_focus');self.assertEqual(motion_state(c,0,12),motion_state(c,11,12));self.assertEqual(motion_state(c,1,12)['scale'],1)
    def test_static_focus_viewport_mismatch(self):
        p=action_scene('static_focus');p['tracks'][0]['parameters']['viewport']['width']=500;self.bad(p,'VIEWPORT_MISMATCH')
    def test_static_focus_translation_matches_inverse_camera(self):
        p=action_scene('static_focus');p['tracks'][0]['parameters']['pose']['focus_x']=300;c=registered_contract(p['tracks'][0]);self.assertEqual(motion_state(c,0,12)['translate_x'],20)
    def test_static_trace_always_full_source(self):
        c=self.c('static_trace');self.assertEqual([action_progress(c,f,12) for f in (0,11,23)],[1,1,1])
    def test_static_trace_actual_dash_offset_zero(self):
        r=self.emit('static_trace');out=runtime(r,frames=[0],fps=12,calls=[{'name':'evaluateTrace','args':[0,12]}]);self.assertIn('dashOffset',str(out));tree=out['trees'][0]['tree'];paths=[n for n in nodes(tree) if n['tag']=='path'];self.assertTrue(any(n['props'].get('strokeDashoffset')==0 for n in paths))
    def test_static_trace_keeps_signed_domains_and_units(self):
        s=self.emit('static_trace').source_text;self.assertIn('[-3.0, 3.0]',s);self.assertIn('"x_unit": "s"',s);self.assertIn('"y_unit": "m"',s)
    def test_progressive_trace_plateaus(self):
        c=self.c('progressive_static_trace');self.assertEqual(action_progress(c,0,12),action_progress(c,5,12));self.assertGreater(action_progress(c,6,12),action_progress(c,5,12))
    def test_progressive_trace_all_source_vertices_required(self):
        p=action_scene('progressive_static_trace');p['tracks'][0]['parameters']['milestones'].pop(1);self.bad(p,'VERTEX_MILESTONE_MISSING')
    def test_progressive_trace_reverse_seek_same(self):
        c=self.c('progressive_static_trace');self.assertEqual([action_progress(c,f,12) for f in range(24)],[action_progress(c,f,12) for f in reversed(range(24))][::-1])
    def test_progressive_trace_collapsed_times_rejected(self):
        p=action_scene('progressive_static_trace');p['tracks'][0]['parameters']['milestones'][1]['at_ms']=1;self.bad(p,'UNSAMPLED')
    def test_progressive_trace_unknown_series(self):
        p=action_scene('progressive_static_trace');p['tracks'][0]['parameters']['series_id']='missing';self.bad(p,'SERIES_MISSING')
    def test_progressive_trace_unbound_observation(self):
        p=action_scene('progressive_static_trace');p['tracks'][0]['parameters']['milestones'][0]['observation_ref']='invented';self.bad(p,'OBSERVATION_UNBOUND')
    def test_crossfade_keeps_first_source_expression(self):
        p=action_scene('crossfade_states');p['tracks'][0]['parameters']['states'][0]['expression']='x=999';self.bad(p,'INITIAL_STATE_MISMATCH')
    def test_crossfade_all_expressions_typeset(self):
        s=self.emit('crossfade_states').source_text;self.assertIn('EquationNode',s);self.assertIn('sideConditions',s);self.assertNotIn('JSON.stringify(initialState',s)
    def test_crossfade_unbound_state_provenance(self):
        p=action_scene('crossfade_states');p['tracks'][0]['parameters']['states'][0]['source_refs']=['new'];self.bad(p,'PROVENANCE_UNBOUND')
    def test_crossfade_cannot_target_text(self):
        p=action_scene('crossfade_states');p['elements'][0]['element_type']='text';self.bad(p,'TARGET_UNSUPPORTED')
    def test_simulation_state_uses_model_endpoints(self):
        c=self.c('simulation_state');self.assertEqual(action_model_time(c,0,12),0);self.assertEqual(action_model_time(c,23,12),2)
    def test_simulation_state_javascript_clock_matches_python(self):
        c=self.c('simulation_state');r=self.emit('simulation_state');out=runtime(r,frames=[0,23],fps=12,calls=[{'name':'evaluateRegisteredTime','args':[f,12]} for f in (0,6,12,23)]);self.assertEqual(out['calls'],[action_model_time(c,f,12) for f in (0,6,12,23)])
    def test_simulation_model_mismatch(self):
        p=action_scene('simulation_state');p['tracks'][0]['parameters']['model_ref']='other';self.bad(p,'MODEL_MISMATCH')
    def test_simulation_final_state_not_dropped(self):
        p=action_scene('simulation_state');p['tracks'][0]['parameters']['to_time_s']=1.5;self.bad(p,'ENDPOINTS')
    def test_simulation_no_initial_state_drop(self):
        p=action_scene('simulation_state');p['tracks'][0]['parameters']['from_time_s']=.1;self.bad(p,'ENDPOINTS')
    def test_snapshots_have_three_static_observations(self):
        c=self.c('state_snapshots');self.assertEqual({action_model_time(c,f,12) for f in range(24)},{0,1,2})
    def test_snapshots_javascript_time_matches_python(self):
        c=self.c('state_snapshots');r=self.emit('state_snapshots');frames=[0,8,9,17,18,23];out=runtime(r,frames=frames,fps=12,calls=[{'name':'evaluateRegisteredTime','args':[f,12]} for f in frames]);self.assertEqual(out['calls'],[action_model_time(c,f,12) for f in frames])
    def test_snapshots_reduced_preference_keeps_observations(self):
        p=action_scene('state_snapshots');r=compile_h3_scene(p,target=T,motion_preference='reduced');self.assertTrue(r.receipt.source_gate_passed,r.receipt.findings);self.assertEqual(r.effective_document['tracks'],p['tracks'])
    def test_dynamic_simulation_not_implicitly_reduced(self):
        p=action_scene('simulation_state');self.assertRaisesRegex(ValueError,'REDUCED_VARIANT_UNRESOLVED',compile_h3_scene,p,target=T,motion_preference='reduced')
    def test_snapshot_duplicate_time_rejected(self):
        p=action_scene('state_snapshots');p['tracks'][0]['parameters']['snapshots'][1]['at_ms']=0;self.bad(p,'ORDER')
    def test_snapshot_final_not_in_frame_window(self):
        p=action_scene('state_snapshots');p['tracks'][0]['parameters']['snapshots'][-1]['at_ms']=1999;self.bad(p,'UNSAMPLED')
    def test_endpoint_display_preserves_source_polyline(self):
        p=action_scene('path_endpoints_with_progress_marker');r=compile_h3_scene(p,target=T);out=full_tree(r,frames=[0,11],target=T);self.assertIn('polyline',str(out));self.assertIn('Progress 0%',str(out));self.assertIn('Progress 100%',str(out))
    def test_endpoint_marker_does_not_move_source(self):
        c=self.c('path_endpoints_with_progress_marker');self.assertEqual(motion_state(c,0,12),{});self.assertEqual(motion_state(c,11,12),{})
    def test_endpoint_path_mismatch(self):
        p=action_scene('path_endpoints_with_progress_marker');p['tracks'][0]['parameters']['points'][1][0]+=10;self.bad(p,'GEOMETRY_MISMATCH')
    def test_endpoint_marker_mode_not_ignored(self):
        p=action_scene('path_endpoints_with_progress_marker');p['tracks'][0]['parameters']['marker_mode']='flying';self.bad(p,'MODE_UNSUPPORTED')
    def test_conflicting_replacements_block(self):
        p=action_scene('state_snapshots');t=deepcopy(p['tracks'][0]);t['track_id']='second';p['tracks'].append(t);r=compile_h3_scene(p,target=T);self.assertFalse(r.receipt.source_gate_passed);self.assertIn('ANIMATION_PROPERTY_OWNERSHIP_CONFLICT',[f.code for f in r.receipt.findings])
    def test_schema_required_for_every_registered_action(self):
        for a in sorted(ACTIONS):
            p=action_scene(a);p['tracks'][0]['parameters'].pop('schema_version');self.assertRaisesRegex(ValueError,'ACTION_UNSUPPORTED',registered_contract,p['tracks'][0])
    def test_unknown_field_not_ignored(self):
        for a in sorted(ACTIONS):
            p=action_scene(a);p['tracks'][0]['parameters']['discard_content']=True;self.assertRaises(ValueError,registered_contract,p['tracks'][0])
    def test_provenance_not_invented(self):
        p=action_scene('static_trace');p['tracks'][0]['source_refs']=['invented'];self.bad(p,'PROVENANCE_UNBOUND')
    def test_inputs_remain_byte_equivalent(self):
        for a in sorted(ACTIONS):
            p=action_scene(a);q=deepcopy(p);compile_registered_track(p['tracks'][0],p['elements'][0]);self.assertEqual(q,p)
    def test_no_acceptance_claim(self):
        for a in sorted(ACTIONS):self.assertFalse(self.emit(a).accepted)
