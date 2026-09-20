from copy import deepcopy
from dataclasses import replace
import math,unittest
from bie.compiler.frame_layout import *
from bie.compiler.animation_behavior import motion_contract
from tests.compiler.h3_test_support import scene,move,TARGET,track

class FrameLayoutTests(unittest.TestCase):
    def codes(self,r):return {f['code'] for f in r['findings']}
    def test_static_all_frames(self):
        r=evaluate_frame_layout(scene(),TARGET);self.assertTrue(r['passed']);self.assertEqual(r['frames_evaluated'],24)
    def test_fractional_duration_ceil(self):
        r=evaluate_frame_layout(scene(duration_ms=1001),TARGET);self.assertEqual(r['frames_evaluated'],25)
    def test_translation_inside_passes(self):self.assertTrue(evaluate_frame_layout(move(),TARGET)['passed'])
    def test_translation_outside_fails(self):
        p=move(params={'from':{'translate_x':0},'to':{'translate_x':1000}});self.assertIn('LAYOUT_OUTSIDE_VIEWPORT',self.codes(evaluate_frame_layout(p,TARGET)))
    def test_interior_rotation_not_endpoint_only(self):
        p=scene();p['elements'][0]['normalized_box']={'x':0,'y':.25,'width':.25,'height':.4};p=move(p,{'from':{'rotate':0},'to':{'rotate':180}})
        rows=list(iter_frame_layers(p,TARGET));self.assertGreaterEqual(rows[0][0]['bounds_ltrb'][0],-1e-6);self.assertGreaterEqual(rows[-1][0]['bounds_ltrb'][0],-1e-6);self.assertFalse(evaluate_frame_layout(p,TARGET)['passed'])
    def test_nested_order_is_not_commutative(self):
        p=scene();e=p['elements'][0]
        a=motion_contract(track('transform',{'from':{'scale':1},'to':{'scale':2}},track_id='a'))
        b=motion_contract(track('transform',{'from':{'translate_x':0},'to':{'translate_x':40}},track_id='b'))
        r=frame_layer(e,[a,b],23,TARGET);q=frame_layer(e,[b,a],23,TARGET);self.assertAlmostEqual(r['bounds_ltrb'][0]-q['bounds_ltrb'][0],40)
    def test_css_scale_rotate_translate_point(self):
        q=transform_point((60,50),{'scale':2,'rotate':90,'translate_x':5},100,100);self.assertAlmostEqual(q[0],55);self.assertAlmostEqual(q[1],70)
    def test_distinct_layers_pass(self):
        p=scene();b=deepcopy(p['elements'][0]);b['element_id']='e1';b['normalized_box']['x']=.6;p['elements'].append(b);self.assertTrue(evaluate_frame_layout(p,TARGET)['passed'])
    def test_undeclared_overlap_rejected(self):
        p=scene();b=deepcopy(p['elements'][0]);b['element_id']='e1';p['elements'].append(b);self.assertIn('LAYOUT_UNDECLARED_OVERLAP',self.codes(evaluate_frame_layout(p,TARGET)))
    def test_intentional_overlap_has_provenance(self):
        p=scene();b=deepcopy(p['elements'][0]);b['element_id']='e1';p['elements'].append(b)
        p['metadata']['compiler_h3']={'layout':{'allow_overlap':[{'elements':['e1','e0'],'reason':'Deliberate annotation overlay','source_refs':['fixture:h3'],'reasoning_refs':['reasoning:h3']}]}}
        r=evaluate_frame_layout(p,TARGET);self.assertTrue(r['passed']);self.assertEqual(r['intentional_overlaps'][0]['count'],24)
    def test_forged_overlap_provenance_rejected(self):
        p=scene();p['metadata']['compiler_h3']={'layout':{'allow_overlap':[{'elements':['e0','none'],'reason':'bad','source_refs':['unknown'],'reasoning_refs':['bad']}]}}
        with self.assertRaises(ValueError):evaluate_frame_layout(p,TARGET)
    def test_shared_edge_not_overlap(self):self.assertFalse(convex_overlap([(0,0),(1,0),(1,1),(0,1)],[(1,0),(2,0),(2,1),(1,1)]))
    def test_separating_axis_not_aabb_only(self):
        a=[(0,1),(1,0),(2,1),(1,2)];b=[(1.8,2.8),(2.8,1.8),(3.8,2.8),(2.8,3.8)];self.assertFalse(convex_overlap(a,b))
    def test_missing_box_rejected(self):
        p=scene();p['elements'][0].pop('normalized_box')
        with self.assertRaisesRegex(ValueError,'LAYOUT_BINDING'):evaluate_frame_layout(p,TARGET)
    def test_nan_box_rejected(self):
        p=scene();p['elements'][0]['normalized_box']['x']=float('nan')
        with self.assertRaises(ValueError):evaluate_frame_layout(p,TARGET)
    def test_boolean_width_rejected(self):
        p=scene();p['elements'][0]['normalized_box']['width']=True
        with self.assertRaises(ValueError):evaluate_frame_layout(p,TARGET)
    def test_zero_extent_rejected(self):
        p=scene();p['elements'][0]['normalized_box']['height']=0
        with self.assertRaises(ValueError):evaluate_frame_layout(p,TARGET)
    def test_budget_failure_not_sampled_pass(self):
        with self.assertRaisesRegex(ValueError,'WORK_BUDGET'):evaluate_frame_layout(scene(duration_ms=2000000),TARGET)
    def test_pair_budget_rejected(self):
        p=scene(duration_ms=100000);p['elements']=[{**deepcopy(p['elements'][0]),'element_id':str(i)} for i in range(100)]
        with self.assertRaisesRegex(ValueError,'WORK_BUDGET'):evaluate_frame_layout(p,TARGET)
    def test_identical_input_rows_digest_stable(self):self.assertEqual(evaluate_frame_layout(move(),TARGET),evaluate_frame_layout(move(),TARGET))
    def test_changed_motion_changes_hash(self):
        p=move();a=evaluate_frame_layout(p,TARGET);p['tracks'][0]['parameters']['to']['translate_x']=50;self.assertNotEqual(a['frame_rows_sha256'],evaluate_frame_layout(p,TARGET)['frame_rows_sha256'])
    def test_no_paint_or_acceptance_claim(self):
        r=evaluate_frame_layout(scene(),TARGET);self.assertFalse(r['paint_verified']);self.assertFalse(r['accepted']);self.assertFalse(r['continuous_time_verified'])
    def test_unknown_policy_not_ignored(self):
        p=scene();p['metadata']['compiler_h3']={'layout':{'ignore_clipping':True}}
        with self.assertRaises(ValueError):evaluate_frame_layout(p,TARGET)
    def test_zero_opacity_is_not_visible(self):
        p=scene();c=motion_contract(track());self.assertFalse(frame_layer(p['elements'][0],[c],0,TARGET)['visible_conservative'])
    def test_scene_input_not_mutated(self):
        p=move();before=deepcopy(p);evaluate_frame_layout(p,TARGET);self.assertEqual(p,before)
if __name__=='__main__':unittest.main()
