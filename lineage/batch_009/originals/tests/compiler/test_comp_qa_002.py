from dataclasses import replace
from hashlib import sha256
import unittest
from bie.compiler.capability_fallback_qa import *
from bie.compiler.qa_common import digest
from bie.scene_ir.compiler_capability_declarations import CapabilityRegistry,CompilerCapability
from bie.compiler.text_compiler import compile_text_element
from tests.compiler.qa_test_support import document, bundle

class CapabilityFallbackQATests(unittest.TestCase):
    def setUp(self):
        self.doc=document('engineering-labels')
        self.base_results=bundle('engineering-labels').element_results
        self.registry=CapabilityRegistry()
        self.registry.register(CompilerCapability('native','1',('text',),('render',),('web',),True))
    def doc_with(self,requests=(),fallbacks=()):
        return document('engineering-labels',capability_requests=requests,planned_fallbacks=fallbacks)
    def req(self,**kw):return dict({'capability_id':'missing','element_id':'e0','requested_action':'render','required':True},**kw)
    def fb(self,**kw):return dict({'fallback_id':'fb','element_id':'e0','missing_capability_id':'missing','fallback_capability_id':'native','fallback_action':'render','semantic_equivalence':'equivalent','preserves_source_refs':True,'preserves_reasoning_refs':True,'preserves_accessibility':True,'required_review':False},**kw)
    def app(self):
        e=self.doc.to_dict()['elements'][0];r=self.base_results[0]
        return FallbackApplication('fb','e0','native','render',r.source_sha256,tuple(e['source_refs']),tuple(e['reasoning_refs']),digest(e['accessibility']))
    def run_qa(self,doc=None,**kw):
        return evaluate_capability_fallbacks(doc or self.doc,self.registry,self.base_results,**kw)
    def codes(self,result):return {f.code for f in result.findings if f.severity=='ERROR'}
    def test_native_capability_passes(self):
        d=self.doc_with((self.req(capability_id='native'),));self.assertTrue(self.run_qa(d).passed)
    def test_required_unsupported_is_blocked(self):
        r=self.run_qa(self.doc_with((self.req(),)));self.assertIn('UNSUPPORTED_REQUIRED_CAPABILITY',self.codes(r))
    def test_optional_unsupported_is_visible_warning(self):
        r=self.run_qa(self.doc_with((self.req(required=False),)));self.assertTrue(r.passed);self.assertTrue(r.findings)
    def test_nonboolean_required_not_coerced(self):
        r=self.run_qa(self.doc_with((self.req(required='false'),)));self.assertIn('REQUEST_NONBOOLEAN_REQUIRED',self.codes(r))
    def test_planned_only_fallback_is_not_execution(self):
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(),)));self.assertIn('FALLBACK_NOT_APPLIED',self.codes(r))
    def test_content_bound_equivalent_fallback_contract(self):
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(),)),applications=(self.app(),))
        self.assertTrue(r.passed);self.assertEqual(r.verified_fallback_ids,('fb',));self.assertEqual(r.visual_semantic_validation,'NOT_RUN')
    def test_action_checked_not_just_capability_name(self):
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(fallback_action='teleport'),)),applications=(self.app(),))
        self.assertIn('FALLBACK_ACTION_UNSUPPORTED',self.codes(r))
    def test_wrong_profile_blocked(self):
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(),)),applications=(self.app(),),profile='unknown')
        self.assertIn('FALLBACK_ACTION_UNSUPPORTED',self.codes(r))
    def test_string_false_preservation_rejected(self):
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(preserves_source_refs='false'),)),applications=(self.app(),))
        self.assertIn('FALLBACK_NONBOOLEAN_CONTRACT',self.codes(r));self.assertFalse(r.passed)
    def test_ref_loss_rejected(self):
        a=replace(self.app(),source_refs=('other',))
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(),)),applications=(a,))
        self.assertIn('FALLBACK_APPLICATION_MISMATCH',self.codes(r))
    def test_accessibility_loss_rejected(self):
        a=replace(self.app(),accessibility_sha256='f'*64)
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(),)),applications=(a,))
        self.assertIn('FALLBACK_APPLICATION_MISMATCH',self.codes(r))
    def test_output_hash_mismatch_rejected(self):
        a=replace(self.app(),output_sha256='b'*64)
        r=self.run_qa(self.doc_with((self.req(),),(self.fb(),)),applications=(a,))
        self.assertIn('FALLBACK_APPLICATION_MISMATCH',self.codes(r))
    def test_review_required_for_degraded_output(self):
        d=self.doc_with((self.req(),),(self.fb(semantic_equivalence='degraded_but_safe'),))
        r=self.run_qa(d,applications=(self.app(),));self.assertIn('FALLBACK_REVIEW_REQUIRED',self.codes(r))
    def test_review_bound_to_scene_and_output(self):
        d=self.doc_with((self.req(),),(self.fb(required_review=True),));a=self.app()
        approval=FallbackApproval('fb',d.fingerprint,a.output_sha256,'test-reviewer','fixture:review-not-product-acceptance')
        self.assertTrue(self.run_qa(d,applications=(a,),approvals=(approval,)).passed)
        self.assertFalse(self.run_qa(d,applications=(a,),approvals=(replace(approval,scene_fingerprint='c'*64),)).passed)
    def test_illustration_does_not_satisfy_required_semantics(self):
        d=self.doc_with((self.req(),),(self.fb(semantic_equivalence='illustrative_only'),))
        self.assertIn('ILLUSTRATIVE_FALLBACK_FOR_REQUIRED_CAPABILITY',self.codes(self.run_qa(d,applications=(self.app(),))))
    def test_duplicate_fallback_keys_rejected(self):
        d=self.doc_with((self.req(),),(self.fb(),self.fb(fallback_id='other')))
        self.assertIn('AMBIGUOUS_FALLBACK',self.codes(self.run_qa(d,applications=(self.app(),))))
    def test_duplicate_request_rejected(self):
        d=self.doc_with((self.req(capability_id='native'),self.req(capability_id='native')))
        self.assertIn('DUPLICATE_CAPABILITY_REQUEST',self.codes(self.run_qa(d)))
    def test_orphan_application_rejected(self):self.assertIn('ORPHAN_FALLBACK_APPLICATION',self.codes(self.run_qa(applications=(self.app(),))))
    def test_mismatched_element_type_rejected(self):
        d=self.doc_with((self.req(capability_id='native',element_type='vector'),))
        self.assertIn('CAPABILITY_ELEMENT_TYPE_MISMATCH',self.codes(self.run_qa(d)))
    def test_nondeterministic_registry_adapter_blocked(self):
        registry=CapabilityRegistry();registry.register(CompilerCapability('native','1',('text',),('render',),('web',),False))
        r=evaluate_capability_fallbacks(self.doc_with((self.req(capability_id='native'),)),registry,self.base_results)
        self.assertIn('NONDETERMINISTIC_CAPABILITY',self.codes(r))
    def test_missing_compiled_element_detected(self):
        r=evaluate_capability_fallbacks(self.doc,self.registry,self.base_results[:1]);self.assertIn('MISSING_COMPILED_ELEMENT',self.codes(r))
    def test_tampered_compiler_bytes_detected(self):
        bad=replace(self.base_results[0],source_text='changed')
        r=evaluate_capability_fallbacks(self.doc,self.registry,(bad,self.base_results[1]));self.assertIn('COMPILED_SOURCE_HASH_MISMATCH',self.codes(r))
    def test_nonbar_is_not_safe_fallback(self):self.assertIn('CHART_KIND_DOWNGRADE',self.codes(bundle('reject-chart-kind').capability_qa))
    def test_negative_chart_sign_cannot_disappear(self):self.assertIn('CHART_SIGN_LOSS',self.codes(bundle('reject-chart-sign').capability_qa))
    def test_vector_third_dimension_cannot_disappear(self):self.assertIn('VECTOR_Z_COMPONENT_DROPPED',self.codes(bundle('reject-vector-z').capability_qa))
    def test_raw_equation_not_typeset_equation(self):self.assertIn('EQUATION_TYPESETTING_NOT_IMPLEMENTED',self.codes(bundle('reject-untypeset-equation').capability_qa))
    def test_raw_text_braces_are_executable(self):self.assertIn('TEXT_LITERAL_JSX_INJECTION',self.codes(bundle('reject-jsx-braces').capability_qa))
    def test_state_dump_not_simulation(self):self.assertIn('SIMULATION_STATE_ONLY',self.codes(bundle('reject-state-only-simulation').capability_qa))
    def test_crs_projection_not_assumed(self):self.assertIn('MAP_PROJECTION_UNVERIFIED',self.codes(bundle('reject-geographic-crs').capability_qa))
    def test_invalid_model_index_blocked(self):self.assertIn('MODEL2D_EDGE_INDEX_INVALID',self.codes(bundle('reject-model-edge').capability_qa))
    def test_plain_equation_explicitly_allows_plain_text(self):self.assertTrue(bundle('math-plain').capability_qa.passed)
    def test_nonstring_request_identifier_is_structured_failure(self):
        d=self.doc_with((self.req(capability_id=['not','a','token']),))
        self.assertIn('MALFORMED_CAPABILITY_REQUEST',self.codes(self.run_qa(d)))
    def test_nonstring_fallback_identifier_is_structured_failure(self):
        d=self.doc_with((self.req(),),(self.fb(fallback_id=['bad']),))
        self.assertIn('MALFORMED_FALLBACK_IDENTIFIERS',self.codes(self.run_qa(d)))
    def test_positive_does_not_imply_acceptance(self):self.assertFalse(self.run_qa().accepted)

if __name__=='__main__':unittest.main()
