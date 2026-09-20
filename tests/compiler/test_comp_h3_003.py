from copy import deepcopy
import unittest
from bie.compiler.reduced_motion import *
from bie.compiler.simulation_compiler import compile_simulation_element
from bie.compiler.animation_track_compiler import compile_animation_track
from tests.compiler.h3_test_support import *
class ReducedMotionTests(unittest.TestCase):
    def setUp(self):self.p=variant(move())
    def resolve(self,p=None):return resolve_reduced_motion(p or self.p,TARGET,'reduced')
    def v(self):return self.p['metadata']['compiler_h3']['reduced_motion_variants']['variant:e0']
    def test_standard_preserves_tracks(self):
        e,r=resolve_reduced_motion(self.p,TARGET);self.assertEqual(e['tracks'],self.p['tracks']);self.assertEqual(r['preference'],'standard')
    def test_reduced_replaces_geometric_motion(self):
        e,r=self.resolve();self.assertEqual(e['tracks'][0]['action'],'enter');self.assertNotIn('translate_x',str(e['tracks'][0]['parameters']))
    def test_original_scene_unchanged(self):a=deepcopy(self.p);self.resolve();self.assertEqual(a,self.p)
    def test_source_and_reasoning_refs_preserved(self):
        e,r=self.resolve();self.assertEqual(e['elements'],self.p['elements']);self.assertEqual(e['tracks'][0]['source_refs'],self.p['tracks'][0]['source_refs'])
    def test_track_timing_preserved(self):
        e,r=self.resolve();self.assertEqual((e['tracks'][0]['start_ms'],e['tracks'][0]['end_ms']),(0,1000))
    def test_missing_reference_blocks(self):
        self.p['elements'][0]['accessibility'].pop('reduced_motion_variant')
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):self.resolve()
    def test_unknown_reference_blocks(self):
        self.p['elements'][0]['accessibility']['reduced_motion_variant']='other'
        with self.assertRaises(ValueError):self.resolve()
    def test_wrong_element_blocks(self):
        self.v()['element_id']='wrong'
        with self.assertRaisesRegex(ValueError,'TARGET_MISMATCH'):self.resolve()
    def test_missing_track_replacement_blocks(self):
        self.v()['track_replacements']={}
        with self.assertRaisesRegex(ValueError,'TRACK_COVERAGE'):self.resolve()
    def test_extra_track_replacement_blocks(self):
        self.v()['track_replacements']['unknown']={'action':'enter','parameters':{}}
        with self.assertRaises(ValueError):self.resolve()
    def test_geometric_replacement_blocks(self):
        self.v()['track_replacements']['h3move']={'action':'transform','parameters':{'from':{'scale':1},'to':{'scale':2}}}
        with self.assertRaisesRegex(ValueError,'MOTION_UNSUPPORTED'):self.resolve()
    def test_new_source_reference_blocks(self):
        self.v()['source_refs']=['invented']
        with self.assertRaisesRegex(ValueError,'PROVENANCE_UNBOUND'):self.resolve()
    def test_empty_reasoning_reference_blocks(self):
        self.v()['reasoning_refs']=[]
        with self.assertRaises(ValueError):self.resolve()
    def test_blank_reason_blocks(self):
        self.v()['reason']=''
        with self.assertRaises(ValueError):self.resolve()
    def test_unknown_variant_field_blocks(self):
        self.v()['hide_content']=True
        with self.assertRaises(ValueError):self.resolve()
    def test_static_simulation_frame_resolved(self):
        p=variant(scene('simulation',sim_props(),duration_ms=3000));e,r=self.resolve(p);self.assertEqual(r['frozen_simulation_frames'],{'e0':48})
    def test_static_simulation_actually_time_invariant(self):
        p=variant(scene('simulation',sim_props(),duration_ms=3000));e,r=self.resolve(p);out=compile_simulation_element(e['elements'][0],freeze_frame=48)
        trees=runtime(out,frames=(0,24,71))['trees'];self.assertEqual(trees[0]['tree'],trees[1]['tree']);self.assertEqual(trees[1]['tree'],trees[2]['tree'])
    def test_original_simulation_still_moves(self):
        p=scene('simulation',sim_props(),duration_ms=3000);out=compile_simulation_element(p['elements'][0]);trees=runtime(out,frames=(0,48))['trees'];self.assertNotEqual(trees[0]['tree'],trees[1]['tree'])
    def test_missing_static_sample_blocks(self):
        p=variant(scene('simulation',sim_props(),duration_ms=3000));p['metadata']['compiler_h3']['reduced_motion_variants']['variant:e0'].pop('freeze_frame')
        with self.assertRaisesRegex(ValueError,'FRAME_REQUIRED'):self.resolve(p)
    def test_outside_static_sample_blocks(self):
        p=variant(scene('simulation',sim_props(),duration_ms=3000));p['metadata']['compiler_h3']['reduced_motion_variants']['variant:e0']['freeze_frame']=72
        with self.assertRaises(ValueError):self.resolve(p)
    def test_unused_static_field_blocked(self):
        self.v()['freeze_frame']=0
        with self.assertRaisesRegex(ValueError,'UNCONSUMED'):self.resolve()
    def test_particle_variant_without_adapter_blocks(self):
        p=variant(scene('particle_system',{'count':1}));
        with self.assertRaisesRegex(ValueError,'FAMILY_UNSUPPORTED'):self.resolve(p)
    def test_reserved_derivation_blocks(self):
        self.p['metadata'][DERIVATION_KEY]={}
        with self.assertRaisesRegex(ValueError,'RESERVED'):self.resolve()
    def test_derivative_does_not_carry_stale_fingerprint(self):
        self.p['fingerprint']='old';e,r=self.resolve();self.assertNotIn('fingerprint',e)
    def test_identity_records_both_inputs(self):
        e,r=self.resolve();self.assertNotEqual(r['original_document_identity'],r['effective_document_identity']);self.assertFalse(r['accepted'])
    def test_invalid_preference_blocks(self):
        with self.assertRaises(ValueError):resolve_reduced_motion(self.p,TARGET,'auto')
    def test_resolved_source_has_only_opacity_style(self):
        e,r=self.resolve();out=compile_animation_track(e['tracks'][0]);self.assertIn('return {opacity:',out.source_text);self.assertNotIn('translate:',out.source_text)
if __name__=='__main__':unittest.main()
