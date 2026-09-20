from copy import deepcopy
import unittest
from bie.compiler.animation_behavior import *
from bie.compiler.animation_track_compiler import compile_animation_track
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h2_test_support import track,runtime

class VisualMotionTests(unittest.TestCase):
    def s(self,a='enter',p=None,f=0,fps=24):return motion_state(motion_contract(track(a,p)),f,fps)
    def test_enter_opacity_changes(self):self.assertEqual(self.s(f=0)['opacity'],0);self.assertEqual(self.s(f=23)['opacity'],1)
    def test_exit_opacity_changes(self):self.assertEqual(self.s('exit',f=0)['opacity'],1);self.assertEqual(self.s('exit',f=23)['opacity'],0)
    def test_last_included_frame_reaches_endpoint(self):self.assertEqual(frame_window(motion_contract(track()),24),(0,23))
    def test_start_inclusive_end_exclusive_policy(self):
        c=motion_contract(track(start_ms=500,end_ms=1500));self.assertEqual(frame_window(c,24),(12,35));self.assertEqual(motion_state(c,11,24)['opacity'],0);self.assertEqual(motion_state(c,35,24)['opacity'],1)
    def test_after_end_holds_target(self):self.assertEqual(self.s(f=999)['opacity'],1)
    def test_prestart_holds_source(self):
        c=motion_contract(track(start_ms=1000,end_ms=2000));self.assertEqual(motion_state(c,0,24)['opacity'],0)
    def test_smoothstep_not_linear_at_quarter(self):
        a=self.s(p={'easing':'linear'},f=5)['opacity'];b=self.s(p={'easing':'smoothstep'},f=5)['opacity'];self.assertLess(b,a)
    def test_reveal_left_clip_changes(self):self.assertEqual(self.s('reveal',f=0)['inset_percent'],[0,100,0,0]);self.assertEqual(self.s('reveal',f=23)['inset_percent'],[0,0,0,0])
    def test_reveal_directions_are_distinct(self):self.assertEqual(len({str(self.s('reveal',{'direction':d})) for d in ('left','right','up','down')}),4)
    def test_emphasis_pulse_returns_to_identity(self):
        self.assertEqual(self.s('emphasize',f=0)['scale'],1);self.assertGreater(self.s('emphasize',f=11)['scale'],1);self.assertEqual(self.s('emphasize',f=23)['scale'],1)
    def test_transform_numeric_interpolation(self):
        p={'from':{'translate_x':0,'rotate':0,'scale':1},'to':{'translate_x':230,'rotate':230,'scale':2}};s=self.s('transform',p,f=10);self.assertAlmostEqual(s['translate_x'],100);self.assertAlmostEqual(s['rotate'],100)
    def test_path_uses_arc_length_not_vertex_index(self):
        p={'coordinate_space':'pixels','points':[[0,0],[10,0],[10,90]]};c=motion_contract(track('path_follow',p,end_ms=1100));s=motion_state(c,5,10);self.assertAlmostEqual(s['translate_x'],10);self.assertAlmostEqual(s['translate_y'],40)
    def test_path_final_point_exact(self):self.assertEqual(self.s('path_follow',{'coordinate_space':'pixels','points':[[5,5],[80,90]]},f=23),{'translate_x':80,'translate_y':90})
    def test_repeated_frame_independent_of_order(self):
        c=motion_contract(track());a=motion_state(c,12,24);motion_state(c,22,24);self.assertEqual(a,motion_state(c,12,24))
    def test_runtime_enter_style_is_applied(self):
        trees=runtime(compile_animation_track(track()),frames=(0,11,23))['trees'];self.assertEqual(trees[0]['tree']['props']['style']['opacity'],0);self.assertEqual(trees[-1]['tree']['props']['style']['opacity'],1)
    def test_runtime_transform_style_is_applied(self):
        r=compile_animation_track(track('transform',{'from':{'rotate':0,'scale':1},'to':{'rotate':90,'scale':2}}));out=runtime(r,frames=(0,23))['trees'];self.assertEqual(out[-1]['tree']['props']['style']['rotate'],'90deg');self.assertEqual(out[-1]['tree']['props']['style']['scale'],2)
    def test_runtime_path_matches_python(self):
        p={'coordinate_space':'pixels','points':[[0,0],[10,0],[10,90]]};c=motion_contract(track('path_follow',p));r=compile_animation_track(track('path_follow',p));frames=(0,5,11,23)
        for row in runtime(r,frames=frames)['trees']:
            x,y=map(lambda s:float(s.removesuffix('px')),row['tree']['props']['style']['translate'].split());s=motion_state(c,row['frame'],24);self.assertAlmostEqual(x,s['translate_x']);self.assertAlmostEqual(y,s['translate_y'])
    def test_runtime_reveal_changes_clip_not_only_metadata(self):
        r=compile_animation_track(track('reveal'));a,b=runtime(r,frames=(0,23))['trees'];self.assertNotEqual(a['tree']['props']['style']['clipPath'],b['tree']['props']['style']['clipPath'])
    def test_no_css_timer_or_transition_emitted(self):
        s=compile_animation_track(track()).source_text;self.assertNotIn('setTimeout',s);self.assertNotIn('transition:',s);self.assertNotIn('data-bie-progress',s)
    def test_unsupported_action_not_metadata_fallback(self):
        for a in ('morph','camera','simulation_state','trace'):
            with self.assertRaisesRegex(ValueError,'ACTION_UNSUPPORTED'):motion_contract(track(a))
    def test_unknown_parameters_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNCONSUMED'):motion_contract(track(params={'speed':3}))
    def test_unknown_easing_rejected(self):
        with self.assertRaisesRegex(ValueError,'EASING'):motion_contract(track(params={'easing':'bounce'}))
    def test_noop_transform_rejected(self):
        with self.assertRaisesRegex(ValueError,'NO_VISUAL_CHANGE'):motion_contract(track('transform',{'from':{'scale':1},'to':{'scale':1}}))
    def test_noop_opacity_rejected(self):
        with self.assertRaisesRegex(ValueError,'NO_VISUAL_CHANGE'):motion_contract(track(params={'from_opacity':1,'to_opacity':1}))
    def test_mismatched_transform_fields_rejected(self):
        with self.assertRaises(ValueError):motion_contract(track('transform',{'from':{'scale':1},'to':{'rotate':90}}))
    def test_nonfinite_transform_rejected(self):
        with self.assertRaises(ValueError):motion_contract(track('transform',{'from':{'rotate':0},'to':{'rotate':float('inf')}}))
    def test_path_requires_coordinate_space(self):
        with self.assertRaisesRegex(ValueError,'SPACE_REQUIRED'):motion_contract(track('path_follow',{'points':[[0,0],[1,1]]}))
    def test_duplicate_path_segment_rejected(self):
        with self.assertRaisesRegex(ValueError,'PATH_INVALID'):motion_contract(track('path_follow',{'coordinate_space':'pixels','points':[[0,0],[0,0]]}))
    def test_overlong_path_rejected(self):
        with self.assertRaises(ValueError):motion_contract(track('path_follow',{'coordinate_space':'pixels','points':[[i,0] for i in range(257)]}))
    def test_one_sample_track_rejected(self):
        with self.assertRaisesRegex(ValueError,'COLLAPSES'):frame_window(motion_contract(track(end_ms=40)),24)
    def test_unsampled_pulse_rejected(self):
        with self.assertRaisesRegex(ValueError,'PULSE_UNSAMPLED'):frame_window(motion_contract(track('emphasize',end_ms=84)),24)
    def test_invalid_frame_rejected(self):
        for f in (-1,.5,True):
            with self.assertRaises(ValueError):self.s(f=f)
    def test_invalid_fps_rejected(self):
        for fps in (0,241,True,23.98):
            with self.assertRaises(ValueError):self.s(fps=fps)
    def test_track_lineage_still_required(self):
        with self.assertRaises(ValueError):compile_animation_track(track(source_refs=[]))
    def test_generated_ast_passes(self):
        r=compile_animation_track(track());self.assertEqual(probe_typescript_sources(((r.source_path,r.source_text),)).status,'PASS')
    def test_motion_does_not_claim_acceptance(self):self.assertFalse(compile_animation_track(track()).accepted)

if __name__=='__main__':unittest.main()
