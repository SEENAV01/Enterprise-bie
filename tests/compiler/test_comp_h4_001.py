from copy import deepcopy
import unittest
from bie.compiler.layout_repair_contracts import *
from tests.compiler.h4_test_support import text_case,map_case,equation_case,scene

class LayoutPermissionTests(unittest.TestCase):
    def setUp(self): self.p,self.policy=text_case()
    def test_exact_source_policy_validates(self): self.assertEqual(validate_policy(self.p,self.policy)[1]['max_candidates'],16)
    def test_policy_does_not_mutate_input(self):
        a,b=deepcopy(self.p),deepcopy(self.policy);list(candidates(self.p,self.policy));self.assertEqual(a,self.p);self.assertEqual(b,self.policy)
    def test_unknown_field_rejected(self):
        self.policy['drop_text']=True
        with self.assertRaisesRegex(ValueError,'POLICY_INVALID'):validate_policy(self.p,self.policy)
    def test_source_change_invalidates_policy(self):
        self.p['elements'][0]['props']['text']='Changed'
        with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):validate_policy(self.p,self.policy)
    def test_zero_candidate_budget_rejected(self):
        self.policy['max_candidates']=0
        with self.assertRaisesRegex(ValueError,'BUDGET'):validate_policy(self.p,self.policy)
    def test_bool_candidate_budget_rejected(self):
        self.policy['max_candidates']=True
        with self.assertRaises(ValueError):validate_policy(self.p,self.policy)
    def test_excessive_budget_rejected(self):
        self.policy['max_candidates']=33
        with self.assertRaises(ValueError):validate_policy(self.p,self.policy)
    def test_unknown_owner_rejected(self):
        self.policy['owners']['other']=self.policy['owners'].pop('e0')
        with self.assertRaisesRegex(ValueError,'OWNER_UNSUPPORTED'):validate_policy(self.p,self.policy)
    def test_outside_viewport_region_rejected(self):
        self.policy['owners']['e0']['region']['width']=2
        with self.assertRaisesRegex(ValueError,'BOX_INVALID'):validate_policy(self.p,self.policy)
    def test_nonfinite_region_rejected(self):
        self.policy['owners']['e0']['region']['width']=float('nan')
        with self.assertRaises(ValueError):validate_policy(self.p,self.policy)
    def test_original_must_be_within_permission(self):
        self.policy['owners']['e0']['region']['x']=.3
        self.policy['owners']['e0']['region']['width']=.4
        with self.assertRaisesRegex(ValueError,'EXCLUDES_ORIGINAL'):validate_policy(self.p,self.policy)
    def test_unbound_provenance_rejected(self):
        self.policy['source_refs']=['fabricated:source']
        with self.assertRaisesRegex(ValueError,'PROVENANCE'):validate_policy(self.p,self.policy)
    def test_empty_reason_rejected(self):
        self.policy['reason']=' '
        with self.assertRaises(ValueError):validate_policy(self.p,self.policy)
    def test_font_reduction_rejected(self):
        self.policy['owners']['e0']['presentation']['font_px']=12
        with self.assertRaisesRegex(ValueError,'FONT_REDUCTION'):validate_policy(self.p,self.policy)
    def test_arbitrary_css_rejected(self):
        self.policy['owners']['e0']['presentation']['overflow']='hidden'
        with self.assertRaisesRegex(ValueError,'PRESENTATION_INVALID'):validate_policy(self.p,self.policy)
    def test_first_candidate_is_original(self): self.assertEqual(next(candidates(self.p,self.policy)).document,canonical_scene(self.p))
    def test_candidate_order_deterministic(self): self.assertEqual(list(candidates(self.p,self.policy)),list(candidates(self.p,self.policy)))
    def test_budget_is_honored(self):
        self.policy['max_candidates']=2;self.assertEqual(len(list(candidates(self.p,self.policy))),2)
    def test_repaired_text_cannot_change(self):
        c=list(candidates(self.p,self.policy))[1].document;c['elements'][0]['props']['text']='Cut content'
        with self.assertRaisesRegex(ValueError,'SEMANTIC_CHANGE'):verify_repair(self.p,c,self.policy)
    def test_timing_cannot_change(self):
        c=deepcopy(self.p);c['duration_ms']+=1000
        with self.assertRaisesRegex(ValueError,'SEMANTIC_CHANGE'):verify_repair(self.p,c,self.policy)
    def test_accessibility_cannot_change(self):
        c=deepcopy(self.p);c['elements'][0]['accessibility']['alt']='different'
        with self.assertRaisesRegex(ValueError,'SEMANTIC_CHANGE'):verify_repair(self.p,c,self.policy)
    def test_owner_cannot_shrink(self):
        c=deepcopy(self.p);c['elements'][0]['normalized_box']['width']=.01
        with self.assertRaisesRegex(ValueError,'SHRINK'):verify_repair(self.p,c,self.policy)
    def test_equation_expression_and_format_remain_exact(self):
        p,q=equation_case();self.assertTrue(all(c.document['elements'][0]['props']==p['elements'][0]['props'] for c in candidates(p,q)))
    def test_map_coordinates_and_projection_remain_exact(self):
        p,q=map_case()
        for c in candidates(p,q):
            props=dict(c.document['elements'][0]['props']);props.pop('compiler_layout',None);self.assertEqual(props,p['elements'][0]['props'])
    def test_unauthorized_owner_is_immutable(self):
        second=deepcopy(self.p['elements'][0]);second['element_id']='fixed';self.p['elements'].append(second)
        self.policy['scene_identity']=digest(canonical_scene(self.p));c=deepcopy(self.p);c['elements'][1]['normalized_box']['x']=.2
        with self.assertRaisesRegex(ValueError,'SEMANTIC_CHANGE'):verify_repair(self.p,c,self.policy)
    def test_no_learning_acceptance_in_invariant(self):
        row=next(candidates(self.p,self.policy));self.assertFalse(row.invariants['learning_equivalence_verified']);self.assertFalse(row.invariants['accepted'])
    def test_default_does_not_grant_empty_viewport(self):
        p,q=text_case(expand=False);self.assertEqual(q['owners']['e0']['region'],p['elements'][0]['normalized_box'])
    def test_relocation_candidates_are_available(self):
        rows=list(candidates(self.p,self.policy));self.assertTrue(any(c.document['elements'][0]['normalized_box']['x']>.05 for c in rows))

if __name__=='__main__':unittest.main()
