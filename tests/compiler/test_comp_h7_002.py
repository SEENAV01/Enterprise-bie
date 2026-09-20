import unittest,json
from copy import deepcopy
from tests.compiler.h7_test_support import reduced,equation_scene,trace_scene,camera_scene,BIG
from tests.compiler.h5_test_support import full_tree
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.motion_milestones import prepare_specialized_variants,KEY
from bie.compiler.specialized_motion import specialized_contract,progress_at,equation_state

class SpecializedVariantsTests(unittest.TestCase):
    def bad(self,p,code):
        with self.assertRaisesRegex(ValueError,code):prepare_specialized_variants(p,BIG,'reduced')
    def variant(self,p):return next(iter(p['metadata']['compiler_h7']['reduced_variants'].values()))
    def test_equation_source_compiles(self):self.assertTrue(compile_h3_scene(reduced(equation_scene()),target=BIG,motion_preference='reduced').receipt.source_gate_passed)
    def test_trace_source_compiles(self):self.assertTrue(compile_h3_scene(reduced(trace_scene()),target=BIG,motion_preference='reduced').receipt.source_gate_passed)
    def test_camera_source_compiles(self):self.assertTrue(compile_h3_scene(reduced(camera_scene()),target=BIG,motion_preference='reduced').receipt.source_gate_passed)
    def test_all_equation_states_preserved(self):
        p=equation_scene();q,r=prepare_specialized_variants(reduced(p),BIG,'reduced');c=specialized_contract(q['tracks'][0]);seen={equation_state(c,f,BIG.fps)['lower'] for f in range(48)}
        self.assertEqual(seen,{0,1,2});self.assertEqual(q['elements'],p['elements'])
    def test_plateau_no_continuous_camera_motion(self):
        q,_=prepare_specialized_variants(reduced(camera_scene()),BIG,'reduced');c=specialized_contract(q['tracks'][0]);self.assertEqual(len({progress_at(c,f,24) for f in range(48)}),3)
    def test_reverse_frame_deterministic(self):
        q,_=prepare_specialized_variants(reduced(trace_scene()),BIG,'reduced');c=specialized_contract(q['tracks'][0]);a=[progress_at(c,f,24) for f in range(48)];self.assertEqual(a,[progress_at(c,f,24) for f in reversed(range(48))][::-1])
    def test_javascript_executes_discrete_progress(self):
        r=compile_h3_scene(reduced(trace_scene()),target=BIG,motion_preference='reduced');a=full_tree(r,frames=[0,1,11,12,35,47]);self.assertEqual(len(a['trees']),6)
    def test_standard_path_keeps_tracks(self):
        p=reduced(equation_scene());q,r=prepare_specialized_variants(p,BIG,'standard');self.assertEqual(p,q);self.assertEqual(r,[])
    def test_missing_registry(self):self.bad(equation_scene(),'SPECIALIZED_REDUCED_VARIANT_REQUIRED')
    def test_missing_state_not_faded_away(self):
        p=reduced(equation_scene());self.variant(p)['milestones'].pop(1);self.bad(p,'REQUIRED_STATE_MISSING')
    def test_missing_graph_vertex(self):
        p=reduced(trace_scene());self.variant(p)['milestones'].pop(1);self.bad(p,'REQUIRED_STATE_MISSING')
    def test_wrong_endpoint(self):
        p=reduced(equation_scene());self.variant(p)['milestones'][-1]['progress']=.9;self.bad(p,'ENDPOINTS')
    def test_too_short_dwell(self):
        p=reduced(equation_scene());self.variant(p)['milestones'][-1]['frame']=47;self.bad(p,'DWELL')
    def test_unbound_refs(self):
        p=reduced(equation_scene());self.variant(p)['source_refs']=['invented'];self.bad(p,'PROVENANCE')
    def test_unknown_fields_reject(self):
        p=reduced(equation_scene());self.variant(p)['delete_text']=True;self.bad(p,'FIELDS')
    def test_nan_reject(self):
        p=reduced(equation_scene());self.variant(p)['milestones'][1]['progress']=float('nan');self.bad(p,'MILESTONES')
    def test_duplicate_time_reject(self):
        p=reduced(equation_scene());self.variant(p)['milestones'][1]['frame']=0;self.bad(p,'ORDER')
    def test_missing_review_ref(self):
        p=reduced(equation_scene());self.variant(p)['teaching_review_ref']='';self.bad(p,'REVIEW')
    def test_forged_internal_progress_reject(self):
        p=reduced(equation_scene());p['tracks'][0]['parameters'][KEY]={};self.bad(p,'DERIVATION_RESERVED')
    def test_no_learning_equivalence_claim(self):
        q,r=prepare_specialized_variants(reduced(equation_scene()),BIG,'reduced');self.assertEqual(r[0]['instructional_equivalence'],'NOT_INDEPENDENTLY_EVALUATED');self.assertFalse(r[0]['accepted'])
