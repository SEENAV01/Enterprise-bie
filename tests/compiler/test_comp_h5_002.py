from copy import deepcopy
import unittest
from bie.compiler.specialized_camera import compile_specialized_camera
from bie.compiler.specialized_motion import specialized_contract,camera_state,progress_at
from bie.compiler.animation_behavior import motion_state
from bie.compiler.frame_layout import frame_layer
from tests.compiler.h5_test_support import camera_scene,BIG,runtime

class CameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=camera_scene();cls.t=cls.p['tracks'][0];cls.e=cls.p['elements'][0];cls.c=specialized_contract(cls.t)
        cls.result=compile_specialized_camera(cls.t,cls.e)
        cls.frames=(0,1,12,23,35,47,60)
        cls.execution=runtime(cls.result,frames=cls.frames,calls=[{'name':'evaluateCamera','args':[f,24]} for f in cls.frames])
    def test_python_js_all_selected_frames(self):
        for f,actual in zip(self.frames,self.execution['calls']):
            for k,v in camera_state(self.c,f,24).items():self.assertAlmostEqual(actual[k],v,places=12)
    def test_first_pose(self):self.assertEqual(camera_state(self.c,0,24)['scale'],.55)
    def test_last_included_pose(self):self.assertEqual(camera_state(self.c,47,24)['scale'],1)
    def test_after_end_holds(self):self.assertEqual(camera_state(self.c,60,24),camera_state(self.c,47,24))
    def test_before_start_holds(self):
        t=deepcopy(self.t);t.update(start_ms=500,end_ms=1500);c=specialized_contract(t)
        self.assertEqual(camera_state(c,0,24),camera_state(c,12,24))
    def test_camera_inverse_pan(self):
        t=deepcopy(self.t);t['parameters']['to']['focus_x']+=50;c=specialized_contract(t)
        self.assertEqual(camera_state(c,47,24)['translate_x'],-50)
    def test_focus_maps_to_center(self):
        t=deepcopy(self.t);t['parameters']['to'].update(focus_x=300,focus_y=120,zoom=1.2);c=specialized_contract(t)
        from bie.compiler.frame_layout import transform_point
        s=camera_state(c,47,24);self.assertEqual(transform_point((300,120),s,640,360),(320,180))
    def test_smoothstep_numeric(self):
        t=deepcopy(self.t);t['parameters']['easing']='smoothstep';c=specialized_contract(t);u=12/47
        self.assertAlmostEqual(progress_at(c,12,24),u*u*(3-2*u))
    def test_css_is_applied(self):
        self.assertEqual(self.execution['trees'][0]['tree']['props']['style']['scale'],.55)
        self.assertEqual(self.execution['trees'][-1]['tree']['props']['style']['scale'],1)
    def test_no_css_animation_timer(self):
        self.assertNotIn('requestAnimationFrame',self.result.source_text);self.assertNotIn('transition:',self.result.source_text)
    def test_keeps_children(self):self.assertIn('Visible technical fixture',str(self.execution['trees'][0]['tree']))
    def test_frame_layout_uses_camera_projection(self):
        rows=[frame_layer(self.e,[self.c],f,BIG) for f in (0,47)]
        self.assertLess(rows[0]['bounds_ltrb'][2]-rows[0]['bounds_ltrb'][0],rows[1]['bounds_ltrb'][2]-rows[1]['bounds_ltrb'][0])
    def test_motion_state_matches_reference(self):self.assertEqual(motion_state(self.c,12,24),camera_state(self.c,12,24))
    def test_source_hash_repeatable(self):self.assertEqual(self.result,compile_specialized_camera(deepcopy(self.t),deepcopy(self.e)))
    def test_missing_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'TARGET_REQUIRED'):compile_specialized_camera(self.t)
    def test_wrong_element_rejected(self):
        e=deepcopy(self.e);e['element_id']='different'
        with self.assertRaisesRegex(ValueError,'TARGET_MISMATCH'):compile_specialized_camera(self.t,e)
    def test_invalid_frame(self):
        with self.assertRaisesRegex(ValueError,'FRAME_INVALID'):camera_state(self.c,-1,24)
    def test_invalid_fps(self):
        with self.assertRaisesRegex(ValueError,'FPS_INVALID'):camera_state(self.c,0,0)
    def test_truth_boundary(self):self.assertFalse(self.execution['accepted']);self.assertIn('TEST_DOUBLES',self.execution['execution_kind'])

if __name__=='__main__':unittest.main()
