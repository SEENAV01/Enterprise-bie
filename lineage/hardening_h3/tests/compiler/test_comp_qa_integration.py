from dataclasses import asdict,replace
from pathlib import Path
from hashlib import sha256
import json
import tempfile
import unittest
from bie.compiler.qa_scene_compile import compile_scene_for_qa,CompilerQATarget
from bie.compiler.compile_diagnostics_mapping import map_compile_diagnostics,validate_source_map,RawCompileDiagnostic
from bie.compiler.generated_code_regression import baseline_from_dict,evaluate_generated_regression,probe_typescript_sources,typecheck_generated_workspace
from bie.compiler.deterministic_codegen import write_codegen_plan
from bie.compiler.deterministic_output_qa import snapshot_generated
from tests.compiler.qa_test_support import ROOT,FIXTURES,bundle,document,case_raw

class CompilerQAIntegrationTests(unittest.TestCase):
    def test_scene_ir_to_element_to_map_provenance_chain(self):
        b=bundle('biology-structure');validate_source_map(b.source_map,b.codegen.files)
        for e in b.element_results:
            spans=[s for s in b.source_map.spans if s.path==e.source_path]
            self.assertEqual(len(spans),1);self.assertEqual(spans[0].origin.element_id,e.element_id)
    def test_native_original_emitter_bytes_are_used_unmodified(self):
        from bie.compiler.vector_compiler import compile_vector_element
        raw=case_raw('physics-vector')['document'];b=bundle('physics-vector')
        expected=compile_vector_element(raw['elements'][0]);actual=next(f for f in b.codegen.files if f.path==expected.source_path)
        self.assertEqual(actual.content,expected.source_text)
    def test_fixed_literal_no_longer_produces_executable_diagnostic(self):
        b=bundle('reject-jsx-braces');p=probe_typescript_sources(b.codegen.files)
        r=map_compile_diagnostics(p.diagnostics,source_map=b.source_map,files=b.codegen.files)
        self.assertTrue(r.passed);self.assertEqual(r.diagnostics,())
    def test_reveal_now_has_applied_visual_style(self):
        b=bundle('reject-metadata-animation')
        self.assertTrue(b.animation_results);self.assertTrue(b.source_contract_passed)
        self.assertIn('style=',b.animation_results[0].source_text);self.assertIn('clipPath',b.animation_results[0].source_text)
    def test_unknown_emitter_is_failure_not_text_fallback(self):
        raw=case_raw()['document'];raw.pop('fingerprint');raw['elements'][0]['element_type']='shape';raw['elements'][0]['props']={'kind':'circle'}
        with self.assertRaisesRegex(ValueError,'EMITTER_UNAVAILABLE'):compile_scene_for_qa(raw)
    def test_missing_provenance_fails_before_codegen(self):
        raw=case_raw()['document'];raw.pop('fingerprint');raw['elements'][0]['source_refs']=[]
        with self.assertRaises(ValueError):compile_scene_for_qa(raw)
    def test_nan_inputs_rejected(self):
        raw=case_raw('physics-vector')['document'];raw.pop('fingerprint');raw['elements'][0]['props']['components'][0]=float('nan')
        with self.assertRaises(ValueError):compile_scene_for_qa(raw)
    def test_layout_not_invented_when_box_missing(self):
        raw=case_raw()['document'];raw.pop('fingerprint');raw['elements'][0]['normalized_box']=None
        b=compile_scene_for_qa(raw);self.assertIn('LAYOUT_BINDING_NOT_PROVIDED',{f.code for f in b.findings})
    def test_frame_quantization_collapse_detected(self):
        raw=case_raw('reject-metadata-animation')['document'];raw.pop('fingerprint');raw['tracks'][0]['end_ms']=1
        b=compile_scene_for_qa(raw);self.assertIn('ANIMATION_FRAME_RANGE_COLLAPSES',{f.code for f in b.findings})
    def test_declared_target_change_changes_identity(self):
        raw=case_raw()['document'];a=compile_scene_for_qa(raw);b=compile_scene_for_qa(raw,target=CompilerQATarget(width=1280))
        self.assertNotEqual(a.context.dependency_identity,b.context.dependency_identity)
        self.assertNotEqual(a.codegen.manifest_sha256,b.codegen.manifest_sha256)
    def test_codegen_can_be_materialized_and_rechecked(self):
        b=bundle();base=baseline_from_dict(json.loads((FIXTURES/'baselines/math-plain.json').read_text()))
        with tempfile.TemporaryDirectory() as td:
            write_codegen_plan(b.codegen,td)
            r=evaluate_generated_regression(files=b.codegen.files,context=b.context,baseline=base,workspace=Path(td))
            self.assertTrue(r.source_checks_passed);self.assertFalse(r.compile_verified)
    def test_source_maps_change_if_input_lineage_changes(self):
        raw=case_raw()['document'];a=compile_scene_for_qa(raw);raw.pop('fingerprint');raw['elements'][0]['source_refs']=['fixture:different']
        b=compile_scene_for_qa(raw);self.assertNotEqual(a.source_map.map_sha256,b.source_map.map_sha256)
    def test_strict_typecheck_cannot_be_disabled(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a.ts').write_text('let x:any;');(root/'tsconfig.json').write_text('{"compilerOptions":{"strict":false}}')
            r=typecheck_generated_workspace(root,tsc_bin=shutil.which('tsc'))
            self.assertEqual(r.status,'BLOCKED_CONFIG')
    def test_tsc_cannot_exclude_generated_file_to_get_pass(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a.ts').write_text('const x=1;');(root/'hidden.ts').write_text('const y:number="bad";')
            (root/'tsconfig.json').write_text('{"compilerOptions":{"strict":true,"skipLibCheck":true},"files":["a.ts"]}')
            r=typecheck_generated_workspace(root,tsc_bin=shutil.which('tsc'))
            self.assertEqual(r.status,'BLOCKED_INPUT_COVERAGE')
    def test_uninspected_workspace_source_blocked(self):
        b=bundle();base=baseline_from_dict(json.loads((FIXTURES/'baselines/math-plain.json').read_text()))
        with tempfile.TemporaryDirectory() as td:
            write_codegen_plan(b.codegen,td);(Path(td)/'src/uninspected.ts').write_text('const hidden=1;')
            with self.assertRaises(ValueError):evaluate_generated_regression(files=b.codegen.files,context=b.context,baseline=base,workspace=Path(td))
    def test_target_and_task_receipts_never_claim_acceptance(self):
        b=bundle();self.assertFalse(b.accepted);self.assertFalse(b.source_map.accepted);self.assertFalse(b.capability_qa.accepted)

if __name__=='__main__':unittest.main()
