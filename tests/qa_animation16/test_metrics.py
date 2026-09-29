from fractions import Fraction
from dataclasses import replace
import unittest,random
from ani_helpers import *
from bie.qa.animation_v2.metrics import *

class TrajectoryTests(FixtureCase):
    def test_exact_midpoint(self):self.assertEqual(value_at(self.r.tracks[0],1000),120000)
    def test_fractional_interior(self):self.assertEqual(value_at(self.r.tracks[0],Fraction(1,3)),Fraction(120080,3))
    def test_step_left_and_right(self):
        t=replace(self.r.tracks[0],interpolation='step_end')
        self.assertEqual(value_at(t,2000,side='left'),40000);self.assertEqual(value_at(t,2000),200000)
    def test_step_holds_until_endpoint(self):self.assertEqual(value_at(replace(self.r.tracks[0],interpolation='step_end'),1999),40000)
    def test_linear_knots_exact(self):
        t=replace(self.r.tracks[0],keyframes=(Keyframe(0,0),Keyframe(2,7),Keyframe(5,1)))
        for k in t.keyframes:
            with self.subTest(k=k):self.assertEqual(value_at(t,k.time_ms),k.value)
    def test_rational_ntsc_no_accumulated_rounding(self):
        fps=FrameRate(30000,1001)
        self.assertEqual(frame_time_ms(30000,fps),1001000)
        self.assertEqual(frame_time_ms(1,fps),Fraction(1001,30))
    def test_motion_not_net_displacement(self):
        t=replace(self.r.tracks[0],keyframes=(Keyframe(0,0),Keyframe(1,1000000),Keyframe(2000,0)))
        r=change_track(self.r,keyframes=t.keyframes);v,s=trajectory_motion(r,self.p)
        self.assertTrue(any(x[0]=='ANI_SPEED_LIMIT' for x in v))
    def test_reversals_ignore_flat_segments(self):self.assertEqual(reversal_count([0,1,1,0,0,1]),2)
    def test_negative_coordinate_interpolation(self):
        t=replace(self.r.tracks[0],keyframes=(Keyframe(0,-10),Keyframe(10,10)))
        self.assertEqual(value_at(t,2),-6)
    def test_translation_speed_squared(self):
        r=change_track(self.r,'move-x',keyframes=(Keyframe(0,0),Keyframe(1000,500000)))
        r=change_track(r,'move-y',keyframes=(Keyframe(0,0),Keyframe(1000,500000)))
        v,s=trajectory_motion(r,self.p);self.assertTrue(any(x[0]=='ANI_SPEED_LIMIT' for x in v));self.assertEqual(s['peak_speed_squared'],500000000000)
    def test_single_pixel_exact_threshold(self):
        for delta,want in [(600000,False),(600001,True)]:
            with self.subTest(delta=delta):
                r=change_track(self.r,keyframes=(Keyframe(0,0),Keyframe(1000,delta)))
                self.assertEqual(any(v[0]=='ANI_SPEED_LIMIT' for v in trajectory_motion(r,self.p)[0]),want)
    def test_unknown_easing_not_sampled_as_proof(self):
        for kind in ('spring','cubic_bezier','external'):
            with self.subTest(kind=kind):
                with self.assertRaises(ContractError):value_at(replace(self.r.tracks[0],interpolation=kind),500)
    def test_invalid_time_values(self):
        for time in (-1,2001,1.0,True,float('nan')):
            with self.subTest(time=time):
                with self.assertRaises(ContractError):value_at(self.r.tracks[0],time)
    def test_frame_invalid_types(self):
        for value in (-1,True,1.5,20736001):
            with self.subTest(value=value):
                with self.assertRaises(ContractError):frame_time_ms(value,FrameRate(30))
    def test_linear_interpolation_property(self):
        rng=random.Random(16009)
        for _ in range(150):
            a,b=rng.randint(-10000,10000),rng.randint(-10000,10000);duration=rng.randint(1,1000);time=rng.randint(0,duration)
            with self.subTest(a=a,b=b,duration=duration,time=time):
                t=replace(self.r.tracks[0],keyframes=(Keyframe(0,a),Keyframe(duration,b)))
                self.assertEqual(value_at(t,time),Fraction(a*(duration-time)+b*time,duration))
    def test_motion_clock_translation_invariance(self):
        a=trajectory_motion(self.r,self.p)[1]
        r=replace(self.r,tracks=tuple(replace(t,keyframes=tuple(replace(k,time_ms=k.time_ms+100) for k in t.keyframes)) for t in self.r.tracks))
        self.assertEqual(trajectory_motion(r,self.p)[1],a)

class InvariantTests(FixtureCase):
    def tracks(self,kind='linear'):
        a=Track('a','standard','marker','value_milli','sum','explain',(Keyframe(0,0),Keyframe(10,10)),kind)
        b=replace(a,track_id='b',keyframes=(Keyframe(0,10),Keyframe(10,0)))
        return {'a':a,'b':b}
    def rule(self,kind='sum_constant'):return Invariant('total','standard',kind,('a','b'),0,10,10)
    def test_sum_conservation(self):self.assertIsNone(invariant_counterexample(self.rule(),self.tracks()))
    def test_step_sum_conservation(self):self.assertIsNone(invariant_counterexample(self.rule(),self.tracks('step_end')))
    def test_interior_violation_caught(self):
        t=self.tracks();t['b']=replace(t['b'],keyframes=(Keyframe(0,10),Keyframe(5,100),Keyframe(10,0)))
        self.assertEqual(invariant_counterexample(self.rule(),t)['time_ms'],5)
    def test_step_left_limit_checked(self):
        t=self.tracks('step_end');t['b']=replace(t['b'],interpolation='linear')
        self.assertEqual(invariant_counterexample(self.rule(),t)['side'],'left')
    def test_coverage_cannot_shrink(self):
        with self.assertRaises(ContractError):invariant_counterexample(replace(self.rule(),end_ms=11),self.tracks())
    def test_unknown_easing_requires_review(self):
        with self.assertRaises(ContractError):invariant_counterexample(self.rule(),self.tracks('spring'))
    def test_ordered_crossing(self):self.assertIsNotNone(invariant_counterexample(self.rule('ordered'),self.tracks()))
    def test_equal_violation(self):self.assertIsNotNone(invariant_counterexample(self.rule('equal'),self.tracks()))
    def test_tolerance_boundary(self):
        r=replace(self.rule(),value=11,tolerance=1);self.assertIsNone(invariant_counterexample(r,self.tracks()))
    def test_no_pseudoproof_from_endpoints(self):
        t=self.tracks();t['a']=replace(t['a'],keyframes=(Keyframe(0,0),Keyframe(4,50),Keyframe(10,10)))
        self.assertIsNotNone(invariant_counterexample(self.rule(),t))
    def test_interval_start_excludes_pre_interval_left_state(self):
        t=self.tracks('step_end')
        t['a']=replace(t['a'],keyframes=(Keyframe(0,0),Keyframe(5,10),Keyframe(10,10)))
        t['b']=replace(t['b'],keyframes=(Keyframe(0,0),Keyframe(10,0)))
        self.assertIsNone(invariant_counterexample(replace(self.rule(),start_ms=5),t))
    def test_closed_interval_end_includes_post_jump_state(self):
        t=self.tracks('step_end')
        t['a']=replace(t['a'],keyframes=(Keyframe(0,10),Keyframe(5,0),Keyframe(10,0)))
        t['b']=replace(t['b'],keyframes=(Keyframe(0,0),Keyframe(10,0)))
        c=invariant_counterexample(replace(self.rule(),end_ms=5),t)
        self.assertEqual((c['time_ms'],c['side']),(5,'right'))
