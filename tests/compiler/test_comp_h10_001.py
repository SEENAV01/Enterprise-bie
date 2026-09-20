import unittest
from copy import deepcopy
from bie.compiler.frame_runtime_contract import plan_frame_runtime
from bie.compiler.state_motion_composition import composed_targets
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h10_test_support import composed_scene,bind,T
from tests.compiler.h9_test_support import highlight_scene

class StateMotionContractsTests(unittest.TestCase):
    def plan(self,p=None):return plan_frame_runtime(p or composed_scene(),T)
    def bad(self,change,code):
        p=composed_scene();change(p);self.assertRaisesRegex(ValueError,code,self.plan,p)
    def test_explicit_composition_binds_target(self):self.assertEqual(composed_targets(self.plan()),{'e0'})
    def test_original_input_not_mutated(self):
        p=composed_scene();q=deepcopy(p);self.plan(p);self.assertEqual(p,q)
    def test_opacity_trace_has_no_conflicting_writer(self):self.assertTrue(self.plan(composed_scene('trace',('opacity',)))['state_motion_compositions'])
    def test_visibility_can_mask_fade_without_replacing_it(self):self.assertTrue(self.plan(composed_scene('enter')))
    def test_two_opacity_writers_rejected(self):self.assertRaisesRegex(ValueError,'OPACITY_CONFLICT',self.plan,composed_scene('enter',('opacity',)))
    def test_no_implicit_consent(self):self.bad(lambda p:p['metadata'].pop('compiler_h10'),'FRAME_RUNTIME_PROPERTY_CONFLICT')
    def test_invalid_version(self):self.bad(lambda p:p['metadata']['compiler_h10'].update(schema_version='v2'),'VERSION')
    def test_unconsumed_config_field(self):self.bad(lambda p:p['metadata']['compiler_h10'].update(extra=True),'FIELDS')
    def test_policy_cannot_implicitly_override_opacity(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0].update(policy='override'),'POLICY')
    def test_no_compositions(self):self.bad(lambda p:p['metadata']['compiler_h10'].update(compositions=[]),'BUDGET')
    def test_missing_composition_field(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0].pop('policy'),'FIELDS')
    def test_unknown_target(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0].update(target_id='missing'),'TARGET')
    def test_duplicate_target(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'].append(deepcopy(p['metadata']['compiler_h10']['compositions'][0])),'TARGET')
    def test_missing_track_id(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0].update(track_ids=['missing']),'TRACK_COVERAGE')
    def test_extra_track_id(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0]['track_ids'].append('extra'),'TRACK_COVERAGE')
    def test_duplicate_track_ids(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0]['track_ids'].append('trace'),'LIST_INVALID')
    def test_extra_state_property(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0]['state_properties'].append('opacity'),'PROPERTY_COVERAGE')
    def test_invalid_source_ref(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0].update(source_refs=['forged']),'PROVENANCE')
    def test_reasoning_ref_cannot_be_empty(self):self.bad(lambda p:p['metadata']['compiler_h10']['compositions'][0].update(reasoning_refs=[]),'LIST_INVALID')
    def test_no_runtime_cannot_silently_ignore_policy(self):self.bad(lambda p:p['metadata'].pop('compiler_h6'),'RUNTIME_REQUIRED')
    def test_both_visible_and_opacity_exact_coverage(self):self.assertEqual(self.plan(composed_scene('trace',('visible','opacity')))['state_motion_compositions'][0]['state_properties'],['opacity','visible'])
    def test_fingerprint_binds_policy_and_tracks(self):
        p=composed_scene();a=self.plan(p)['plan_sha256'];p['tracks'][0]['track_id']='renamed';p['metadata']['compiler_h10']['compositions'][0]['track_ids']=['renamed'];self.assertNotEqual(a,self.plan(p)['plan_sha256'])
    def test_all_composed_target_rows_required(self):
        p=composed_scene();e=deepcopy(p['elements'][0]);e['element_id']='e1';p['elements'].append(e)
        tr=deepcopy(p['tracks'][0]);tr.update(track_id='trace2',element_id='e1');p['tracks'].append(tr)
        b=deepcopy(p['state_bindings'][0]);b.update(binding_id='second',target_id='e1');p['state_bindings'].append(b)
        self.assertRaisesRegex(ValueError,'TARGET_COVERAGE',self.plan,p)
    def test_highlight_target_state_contract_remains_bound(self):self.assertTrue(self.plan(bind(highlight_scene(moving=True))))
