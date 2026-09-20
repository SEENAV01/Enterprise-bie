import unittest,json
from copy import deepcopy
from bie.compiler.qa_scene_compile import compile_scene_for_qa
from bie.compiler.hardened_scene_compile import compile_h3_scene
from tests.compiler.h9_test_support import action_scene,T,shape_scene
from tests.compiler.h10_test_support import native_request

class ActionRealizationTests(unittest.TestCase):
    def compile(self,p):return compile_scene_for_qa(p,target=T)
    def request(self):return native_request(action_scene('static_focus'))
    def codes(self,r):return {f.code for f in r.findings}
    def test_available_but_untracked_required_action_rejected(self):
        p=self.request();p['tracks']=[];r=self.compile(p);self.assertFalse(r.source_contract_passed);self.assertIn('REQUIRED_ACTION_NOT_REALIZED',self.codes(r))
    def test_matching_emitted_track_passes(self):self.assertTrue(self.compile(self.request()).source_contract_passed)
    def test_optional_missing_action_warns_without_claiming_realization(self):
        p=self.request();p['tracks']=[];p['capability_requests'][0]['required']=False;r=self.compile(p)
        self.assertTrue(r.source_contract_passed);self.assertIn('OPTIONAL_ACTION_NOT_REALIZED',self.codes(r))
    def test_render_capability_is_element_not_track(self):
        p=shape_scene();p['capability_requests']=[{'capability_id':'comp:shape','element_id':'e0','element_type':'shape','requested_action':'render','required':True}];self.assertTrue(self.compile(p).source_contract_passed)
    def test_request_on_wrong_target_not_discharged(self):
        p=self.request();e=deepcopy(p['elements'][0]);e['element_id']='other';p['elements'].append(e);p['capability_requests'][0]['element_id']='other'
        self.assertIn('REQUIRED_ACTION_NOT_REALIZED',self.codes(self.compile(p)))
    def test_wrong_registered_action_not_discharged(self):
        p=native_request(action_scene('static_trace'),'progressive_static_trace');self.assertIn('REQUIRED_ACTION_NOT_REALIZED',self.codes(self.compile(p)))
    def test_invalid_requested_action_parameters_still_rejected(self):
        p=self.request();p['tracks'][0]['parameters']['pose']['zoom']=999;r=self.compile(p);self.assertFalse(r.source_contract_passed)
    def test_no_action_requests_does_not_add_witness_file(self):self.assertFalse(any(f.path=='src/bie-action-realization.json' for f in self.compile(shape_scene()).codegen.files))
    def test_witness_tracks_source_and_target(self):
        p=self.request();r=self.compile(p);w=json.loads(next(f.content for f in r.codegen.files if f.path=='src/bie-action-realization.json'))
        self.assertEqual(w['requests'][0]['realized_tracks'][0]['track_id'],p['tracks'][0]['track_id']);self.assertEqual(w['requests'][0]['element_id'],'e0')
    def test_realization_is_not_actual_render_proof(self):
        r=self.compile(self.request());w=json.loads(next(f.content for f in r.codegen.files if f.path=='src/bie-action-realization.json'))
        self.assertFalse(w['actual_render_verified']);self.assertFalse(w['accepted'])
    def test_two_native_requests_checked_independently(self):
        p=native_request(action_scene('static_trace'));other=deepcopy(p['capability_requests'][0]);other['requested_action']='progressive_static_trace';p['capability_requests'].append(other)
        r=self.compile(p);w=json.loads(next(f.content for f in r.codegen.files if f.path=='src/bie-action-realization.json'))
        self.assertEqual([x['status'] for x in w['requests']],['EMITTED','NOT_REALIZED'])
    def test_track_with_different_source_changes_evidence(self):
        p=self.request();r=self.compile(p);a=next(f.sha256 for f in r.codegen.files if f.path=='src/bie-action-realization.json')
        p['tracks'][0]['parameters']['pose']['zoom']=.9;r=self.compile(p);self.assertNotEqual(a,next(f.sha256 for f in r.codegen.files if f.path=='src/bie-action-realization.json'))
    def test_missing_unrecognized_action_uses_existing_capability_gate(self):
        p=self.request();p['capability_requests'][0]['requested_action']='unknown';r=self.compile(p);self.assertIn('UNSUPPORTED_REQUIRED_CAPABILITY',self.codes(r))
    def test_compiler_does_not_invent_missing_action_track(self):
        p=self.request();p['tracks']=[];q=deepcopy(p);r=self.compile(p);self.assertEqual(p,q);self.assertEqual(r.animation_results,())
    def test_registered_simulation_action_realized(self):self.assertTrue(self.compile(native_request(action_scene('simulation_state'))).source_contract_passed)
    def test_static_graph_is_not_dynamic_trace_by_name(self):
        p=native_request(action_scene('static_trace'),'render');self.assertTrue(self.compile(p).source_contract_passed)
    def test_checked_path_inherits_missing_action_guard(self):
        p=self.request();p['tracks']=[];self.assertFalse(compile_h3_scene(p,target=T).receipt.source_gate_passed)
    def test_duplicate_requests_remain_rejected(self):
        p=self.request();p['capability_requests'].append(deepcopy(p['capability_requests'][0]));self.assertIn('DUPLICATE_CAPABILITY_REQUEST',self.codes(self.compile(p)))

    def test_witness_hash_is_exact_generated_file_bytes(self):
        from hashlib import sha256
        r=self.compile(self.request());w=json.loads(next(f.content for f in r.codegen.files if f.path=='src/bie-action-realization.json'))
        row=w['requests'][0]['realized_tracks'][0];f=next(f for f in r.codegen.files if f.path==row['path'])
        self.assertEqual(row['source_sha256'],sha256(f.content.encode()).hexdigest())
