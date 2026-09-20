from copy import deepcopy
import unittest
from bie.compiler.specialized_motion import *
from bie.compiler.animation_behavior import motion_contract,frame_window
from tests.compiler.h5_test_support import camera_scene,equation_scene,trace_scene,BIG

class ContractTests(unittest.TestCase):
    def mutate(self,fn,edit,code):
        p=fn();edit(p)
        with self.assertRaisesRegex(ValueError,code):
            c=specialized_contract(p['tracks'][0]);validate_specialized_bindings(p,BIG)
    def test_camera_is_distinct_action(self):self.assertEqual(motion_contract(camera_scene()['tracks'][0]).action,'camera')
    def test_content_ownership(self):self.assertEqual(specialized_contract(equation_scene()['tracks'][0]).owned_properties,('content',))
    def test_trace_ownership(self):self.assertEqual(specialized_contract(trace_scene()['tracks'][0]).owned_properties,('content',))
    def test_projection_not_inferred(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters'].update(projection='perspective'),'CAMERA_SPACE')
    def test_camera_spaces_explicit(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters'].update(coordinate_space='world'),'CAMERA_SPACE')
    def test_viewport_binds_render_target(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters']['viewport'].update(width=600),'VIEWPORT_MISMATCH')
    def test_unknown_parameter(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters'].update(unused=1),'UNCONSUMED')
    def test_zero_zoom(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters']['to'].update(zoom=0),'NUMBER_INVALID')
    def test_boolean_zoom(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters']['to'].update(zoom=True),'NUMBER_INVALID')
    def test_nonfinite_pose(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters']['to'].update(focus_x=float('nan')),'NUMBER_INVALID')
    def test_identical_camera_rejected(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters'].update(to=deepcopy(p['tracks'][0]['parameters']['from'])),'NO_VISUAL_CHANGE')
    def test_camera_focus_outside_contract(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters']['to'].update(focus_y=-1),'NUMBER_INVALID')
    def test_wrong_schema(self):self.mutate(camera_scene,lambda p:p['tracks'][0]['parameters'].update(schema_version='wrong'),'SCHEMA_REQUIRED')
    def test_initial_equation_must_match(self):self.mutate(equation_scene,lambda p:p['elements'][0]['props'].update(expression='wrong'),'INITIAL_STATE_MISMATCH')
    def test_proof_not_inferred(self):self.mutate(equation_scene,lambda p:p['tracks'][0]['parameters'].update(mode='symbol-proof'),'MODE_UNSUPPORTED')
    def test_state_provenance_bound(self):self.mutate(equation_scene,lambda p:p['tracks'][0]['parameters']['states'][1].update(source_refs=['invented']),'PROVENANCE_UNBOUND')
    def test_track_source_bound_to_element(self):self.mutate(camera_scene,lambda p:p['tracks'][0].update(source_refs=['invented']),'PROVENANCE_UNBOUND')
    def test_duplicate_state_provenance(self):self.mutate(equation_scene,lambda p:p['tracks'][0]['parameters']['states'][1].update(reasoning_refs=['reasoning:h5','reasoning:h5']),'PROVENANCE_UNBOUND')
    def test_no_adjacent_duplicate_states(self):self.mutate(equation_scene,lambda p:p['tracks'][0]['parameters']['states'][1].update(expression=p['tracks'][0]['parameters']['states'][0]['expression']),'STATES_INVALID')
    def test_states_budget(self):self.mutate(equation_scene,lambda p:p['tracks'][0]['parameters'].update(states=p['tracks'][0]['parameters']['states'][:1]),'STATES_INVALID')
    def test_sampling_insufficient(self):self.mutate(equation_scene,lambda p:p['tracks'][0].update(end_ms=100),'STATES_UNSAMPLED')
    def test_duration_exceeded(self):self.mutate(camera_scene,lambda p:p.update(duration_ms=500),'EXCEEDS_SCENE')
    def test_transition_fraction_requires_hold(self):self.mutate(equation_scene,lambda p:p['tracks'][0]['parameters'].update(transition_fraction=1),'NUMBER_INVALID')
    def test_unknown_trace_model(self):self.mutate(trace_scene,lambda p:p['tracks'][0]['parameters'].update(progress_model='physical-time'),'MODEL_UNSUPPORTED')
    def test_marker_requires_boolean(self):self.mutate(trace_scene,lambda p:p['tracks'][0]['parameters'].update(head_marker='false'),'MODEL_UNSUPPORTED')
    def test_no_external_acceptance_flag(self):
        r=validate_specialized_bindings(equation_scene(),BIG)[0];self.assertFalse(r['accepted']);self.assertFalse(r['symbolic_equivalence_verified'])
    def test_canonical_normalization(self):
        p=camera_scene();self.assertEqual(specialized_contract(p['tracks'][0]),specialized_contract(deepcopy(p)['tracks'][0]))
    def test_legacy_unsupported_action_stays_blocked(self):
        p=camera_scene();p['tracks'][0]['parameters'].pop('schema_version')
        with self.assertRaisesRegex(ValueError,'ACTION_UNSUPPORTED'):motion_contract(p['tracks'][0])

if __name__=='__main__':unittest.main()
