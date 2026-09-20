import unittest,json,tempfile
from copy import deepcopy
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from bie.compiler.composition_conformance import inspect_composed_trees,verify_composition,_walk
from bie.compiler.frame_runtime_contract import plan_frame_runtime
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.frame_state_consumer import runtime_at
from tests.compiler.h10_test_support import composed_scene,native_request,T
from tests.compiler.h6_test_support import execute

class CompositionConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=composed_scene('trace');cls.comp=compile_h3_scene(cls.raw,target=T)
        cls.plan=plan_frame_runtime(cls.comp.effective_document,T);cls.frames=[23,0,8,16,23,0]
        cls.data=execute(cls.comp,cls.frames,T)
    def check(self,data=None):return inspect_composed_trees(self.plan,data or self.data,self.frames)
    def test_python_oracle_and_generated_ts_agree(self):self.assertTrue(self.check()['passed'])
    def test_reverse_duplicate_frames_are_identical(self):self.assertFalse(any(f['code']=='COMPOSITION_REVERSE_SEEK_MISMATCH' for f in self.check()['findings']))
    def test_false_real_remotion_label_rejected(self):
        d=deepcopy(self.data);d['real_remotion']=True;self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH',self.check,d)
    def test_audio_playback_claim_rejected(self):
        d=deepcopy(self.data);d['audio_played']=True;self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH',self.check,d)
    def test_missing_frame_rejected(self):
        d=deepcopy(self.data);d['trees'].pop();self.assertRaisesRegex(ValueError,'COVERAGE_MISMATCH',self.check,d)
    def test_reordered_frame_rejected(self):
        d=deepcopy(self.data);d['trees']=list(reversed(d['trees']));self.assertRaisesRegex(ValueError,'COVERAGE_MISMATCH',self.check,d)
    def test_changed_runtime_state_detected(self):
        d=deepcopy(self.data);d['trees'][0]['state']['targets']['e0']['visible']=False
        self.assertIn('COMPOSITION_RUNTIME_ORACLE_MISMATCH',{f['code'] for f in self.check(d)['findings']})
    def test_missing_controls_detected(self):
        d=deepcopy(self.data)
        for n,a in _walk(d['trees'][0]['tree']):
            if n.get('props',{}).get('data-bie-runtime-mode')=='controls':n['props'].pop('data-bie-runtime-mode')
        self.assertIn('COMPOSITION_CONTROL_MISSING_OR_DUPLICATE',{f['code'] for f in self.check(d)['findings']})
    def test_wrong_opacity_detected(self):
        d=deepcopy(self.data)
        for n,a in _walk(d['trees'][0]['tree']):
            if n.get('props',{}).get('data-bie-runtime-mode')=='controls':n['props']['style']['opacity']=.123
        self.assertIn('COMPOSITION_OPACITY_MISMATCH',{f['code'] for f in self.check(d)['findings']})
    def test_wrong_visibility_detected(self):
        d=deepcopy(self.data)
        for n,a in _walk(d['trees'][0]['tree']):
            if n.get('props',{}).get('data-bie-runtime-mode')=='controls':n['props']['style']['visibility']='hidden'
        self.assertIn('COMPOSITION_VISIBILITY_MISMATCH',{f['code'] for f in self.check(d)['findings']})
    def test_dropped_graph_track_detected(self):
        d=deepcopy(self.data)
        for n,a in _walk(d['trees'][0]['tree']):n.get('props',{}).pop('data-bie-track-id',None)
        self.assertIn('COMPOSITION_TRACK_MISSING_OR_DUPLICATE',{f['code'] for f in self.check(d)['findings']})
    def test_changed_repeat_output_detected(self):
        d=deepcopy(self.data);d['trees'][-1]['tree']['props']['data-unexpected']='different'
        self.assertIn('COMPOSITION_REVERSE_SEEK_MISMATCH',{f['code'] for f in self.check(d)['findings']})
    def test_report_never_authorizes_release(self):
        r=self.check();self.assertFalse(r['accepted']);self.assertFalse(r['release_authorized']);self.assertFalse(r['actual_render_verified'])
    def test_exhaustive_budget_never_becomes_sampled_success(self):
        with patch('bie.compiler.composition_conformance.MAX_EXECUTIONS',2):self.assertRaisesRegex(ValueError,'BUDGET',verify_composition,self.comp,T)
    def test_noncomposed_source_not_mislabelled_conformance(self):
        from tests.compiler.h9_test_support import shape_scene
        self.assertRaisesRegex(ValueError,'CONTRACT_REQUIRED',verify_composition,compile_h3_scene(shape_scene(),target=T),T)
    def test_record_binds_source_and_emitter_bytes(self):
        r=verify_composition(self.comp,T);self.assertEqual(r['manifest_sha256'],self.comp.codegen.manifest_sha256);self.assertEqual(r['executions'],48);self.assertEqual(len(r['bridge_sha256']),64)
    def test_source_publication_revalidation_with_composed_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'project';r=publish_h3_scene(self.raw,out,target=T);self.assertTrue(r.source_gate_passed);self.assertTrue(require_h3_workspace(out).source_gate_passed)
    def test_tampered_runtime_controls_fail_existing_gate(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'p';publish_h3_scene(self.raw,out,target=T);p=next((out/'src/runtime-layers').glob('RuntimeControls*'));p.write_text(p.read_text()+'\n//tampered');self.assertRaisesRegex(ValueError,'TAMPERED',require_h3_workspace,out)
    def test_missing_required_action_blocks_publication(self):
        p=native_request(composed_scene('static_trace'));p['tracks']=[];p['metadata'].pop('compiler_h10')
        with tempfile.TemporaryDirectory() as td:self.assertRaisesRegex(ValueError,'PUBLICATION_BLOCKED',publish_h3_scene,p,Path(td)/'out',target=T)
    def test_standard_pipeline_remains_not_product_accepted(self):self.assertFalse(self.comp.receipt.accepted)
