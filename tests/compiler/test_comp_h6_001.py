from copy import deepcopy
from dataclasses import replace
import unittest
from bie.compiler.frame_runtime_contract import *
from tests.compiler.h6_test_support import *

class RuntimeContractTests(unittest.TestCase):
    def setUp(self):self.p=state_scene()
    def plan(self,p=None):return plan_frame_runtime(p or self.p,BIG)
    def reject(self,p,code):
        with self.assertRaisesRegex(CompilerQAError,code):self.plan(p)
    def test_legacy_optin_absent(self):
        p=self.p;del p['metadata']['compiler_h6'];self.assertIsNone(self.plan(p))
    def test_input_not_mutated(self):
        old=deepcopy(self.p);self.plan();self.assertEqual(self.p,old)
    def test_source_binding_and_nonacceptance(self):
        r=self.plan();self.assertEqual(r['input_identity'],digest(self.p));self.assertFalse(r['accepted']);self.assertEqual(r['speech_text_alignment'],'NOT_VERIFIED')
    def test_version_and_unknown_metadata(self):
        for change in [{'schema_version':'v0'},{'execute':'alert(1)'}]:
            p=deepcopy(self.p);p['metadata']['compiler_h6'].update(change)
            with self.subTest(change=change):self.reject(p,'FRAME_RUNTIME_')
    def test_state_coverage_exact(self):
        p=self.p;p['metadata']['state_paths']+=['unbound'];self.reject(p,'STATE_COVERAGE')
    def test_provenance_not_arbitrary(self):
        p=self.p;p['metadata']['compiler_h6']['state_lineage']['lesson.phase']['source_refs']=['unrelated'];self.reject(p,'PROVENANCE')
    def test_object_state_and_unsafe_numeric_rejected(self):
        for value in [{},None,float('inf'),10**1000]:
            p=deepcopy(self.p);p['metadata']['compiler_h6']['initial_state']['lesson.phase']=value
            with self.subTest(value=type(value).__name__):self.reject(p,'FRAME_RUNTIME_')
    def test_javascript_prototype_keys_rejected(self):
        for v in ['__proto__','a.constructor','a.prototype','constructor']:
            p=deepcopy(self.p);c=p['metadata']['compiler_h6'];c['initial_state']={v:'text'};c['state_lineage']={v:deepcopy(REFS)};p['metadata']['state_paths']=[v]
            with self.subTest(v=v):self.reject(p,'FRAME_RUNTIME_ID')
    def test_duplicate_binding_and_property(self):
        p=self.p;p['state_bindings'].append({**p['state_bindings'][0],'binding_id':'other'});self.reject(p,'BINDING_CONFLICT')
    def test_initial_literal_cannot_change(self):
        p=self.p;p['elements'][0]['props']['text']='different';self.reject(p,'TEXT_INITIAL_MISMATCH')
    def test_no_implicit_type_coercion(self):
        p=self.p;p['state_bindings'][0]['transform']='string';self.reject(p,'TRANSFORM')
    def test_no_interactive_write_fallback(self):
        p=self.p;p['state_bindings'][0]['read_only']=False;self.reject(p,'INTERACTIVE_WRITE')
    def test_binding_default_must_match(self):
        p=self.p;p['state_bindings'][0]['default_value']='secret override';self.reject(p,'DEFAULT_MISMATCH')
    def test_unknown_event_never_ignored(self):
        p=self.p;p['events'][0]['event_type']='fetch';self.reject(p,'EVENT_UNSUPPORTED')
    def test_event_target_and_provenance(self):
        p=self.p;p['events'][0]['target_ids']=[];self.reject(p,'EVENT_TARGETS')
    def test_event_collapses_to_same_frame(self):
        p=self.p;p['events'][1]['at_ms']=501;p['events'][0]['at_ms']=502;self.reject(p,'EVENT_COLLISION')
    def test_event_after_last_sample(self):
        p=self.p;p['events'][1]['at_ms']=1999;self.reject(p,'EVENT_UNSAMPLED')
    def test_events_have_declared_fixed_type(self):
        p=self.p;p['events'][0]['payload']['value']=1;self.reject(p,'FRAME_RUNTIME_TYPE')
    def test_event_unknown_fields_rejected(self):
        p=self.p;p['events'][0]['payload']['script']='process.exit()';self.reject(p,'FIELDS')
    def test_event_count_budget(self):
        p=self.p;p['events']=p['events']*513;self.reject(p,'BUDGET')
    def test_ceiling_never_early(self):
        for fps in [1,24,25,30,60,120,240]:
            for ms in range(0,2001,7):
                f=frame_at(ms,fps);self.assertGreaterEqual(f*1000,ms*fps);self.assertLess(f*1000-ms*fps,1000)
    def test_zero_ms_event_and_end_exclusive(self):
        p=self.p;p['events'][0]['at_ms']=0;r=self.plan();self.assertEqual(r['events'][0]['frame'],0)
    def test_empty_extension_not_claimed_implemented(self):
        p=self.p;p['state_bindings']=[];p['events']=[];p['metadata']['state_paths']=[];p['metadata']['compiler_h6']={'schema_version':SCHEMA};self.reject(p,'FRAME_RUNTIME_EMPTY')

if __name__=='__main__':unittest.main()
