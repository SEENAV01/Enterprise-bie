import json
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest
from bie.compiler.compile_diagnostics_mapping import *
from bie.compiler.generated_lint import LintReceipt, LintIssue
from bie.compiler.generated_static_analysis import StaticAnalysisReceipt, StaticFinding
from bie.compiler.typescript_compile import compile_typescript
from tests.compiler.qa_test_support import bundle

class DiagnosticsMappingTests(unittest.TestCase):
    def setUp(self):
        self.files=(('src/a.ts','export const x: number = 1;\nexport const y = x;\n'),)
        self.origin=SourceOrigin('scene','$.elements[0]','e0',None,('source:1',),('reason:1',))
        self.span=GeneratedSourceSpan('src/a.ts',1,2,sha256(self.files[0][1].encode()).hexdigest(),self.origin)
        self.mapping=build_source_map(scene_fingerprint='a'*64,files=self.files,spans=(self.span,))
    def map(self,items,**kw):
        return map_compile_diagnostics(items,source_map=self.mapping,files=self.files,**kw)
    def test_maps_file_line_to_actual_source_refs(self):
        r=self.map([RawCompileDiagnostic('TS2322','ERROR','typescript','Type mismatch','src/a.ts',1,14)])
        self.assertEqual(r.diagnostics[0].origin.source_refs,('source:1',));self.assertFalse(r.passed)
    def test_compiled_scene_maps_existing_element_source(self):
        b=bundle();e=b.element_results[0]
        r=map_compile_diagnostics([RawCompileDiagnostic('TS1','ERROR','typescript','x',e.source_path,1,1)],source_map=b.source_map,files=b.codegen.files)
        self.assertEqual(r.diagnostics[0].origin.element_id,e.element_id)
    def test_mapping_preserves_scene_id_not_fabricated_pages(self):
        r=self.map([RawCompileDiagnostic('E','ERROR','build','x','src/a.ts',1)])
        self.assertEqual(r.diagnostics[0].origin.scene_id,'scene')
        self.assertNotIn('page',asdict(r.diagnostics[0].origin))
    def test_stale_source_is_rejected(self):
        with self.assertRaises(ValueError):
            map_compile_diagnostics([],source_map=self.mapping,files=(('src/a.ts','changed'),))
    def test_map_metadata_tampering_is_rejected(self):
        bad=replace(self.mapping,map_sha256='b'*64)
        with self.assertRaises(ValueError):map_compile_diagnostics([],source_map=bad,files=self.files)
    def test_overlapping_spans_rejected(self):
        with self.assertRaises(ValueError):build_source_map(scene_fingerprint='a'*64,files=self.files,spans=(self.span,self.span))
    def test_out_of_file_span_rejected(self):
        with self.assertRaises(ValueError):build_source_map(scene_fingerprint='a'*64,files=self.files,spans=(replace(self.span,end_line=3),))
    def test_missing_generated_file_rejected(self):
        with self.assertRaises(ValueError):build_source_map(scene_fingerprint='a'*64,files=self.files,spans=(replace(self.span,path='src/missing.ts'),))
    def test_no_error_with_failed_process_never_passes(self):
        r=self.map([],process_exit_code=2)
        self.assertFalse(r.passed);self.assertEqual(r.diagnostics[0].code,'COMP_PROCESS_FAILURE')
    def test_warning_does_not_hide_process_failure(self):
        r=self.map([RawCompileDiagnostic('W','WARNING','build','Warning')],process_exit_code=1)
        self.assertEqual(r.error_count,1);self.assertEqual(r.warning_count,1)
    def test_warning_only_can_pass_source_gate(self):
        self.assertTrue(self.map([RawCompileDiagnostic('W','WARNING','lint','Warning','src/a.ts',1)]).passed)
    def test_unknown_file_remains_explicitly_unmapped(self):
        r=self.map([RawCompileDiagnostic('E','ERROR','typescript','x','src/b.ts',1)])
        self.assertEqual(r.diagnostics[0].mapping_status,'UNMAPPED');self.assertIsNone(r.diagnostics[0].origin)
    def test_outside_workspace_not_guessed_by_basename(self):
        r=self.map([RawCompileDiagnostic('E','ERROR','typescript','x','/other/src/a.ts',1)],workspace='/project')
        self.assertEqual(r.diagnostics[0].mapping_status,'OUTSIDE_WORKSPACE')
    def test_absolute_inside_workspace_maps(self):
        r=self.map([RawCompileDiagnostic('E','ERROR','typescript','x','/project/src/a.ts',2)],workspace='/project')
        self.assertEqual(r.diagnostics[0].origin,self.origin)
    def test_windows_drive_and_spaces_are_mapped(self):
        d=parse_compile_output(r'C:\my project\src\a.ts(2,4): error TS2322: mismatch')[0]
        r=self.map([d],workspace=r'C:\my project')
        self.assertEqual(r.diagnostics[0].origin,self.origin)
    def test_relative_traversal_is_not_mapped(self):
        r=self.map([RawCompileDiagnostic('E','ERROR','x','x','../src/a.ts',1)])
        self.assertEqual(r.diagnostics[0].mapping_status,'OUTSIDE_WORKSPACE')
    def test_multiline_tsc_diagnostic_keeps_detail(self):
        d=parse_compile_output('src/a.ts(1,3): error TS2322: Not assignable\n  Inner constraint failed\n')[0]
        self.assertIn('Inner constraint failed',d.message)
    def test_ansi_diagnostics_parsed(self):
        self.assertEqual(parse_compile_output('\x1b[31msrc/a.ts(1,1): error TS1005: x\x1b[0m')[0].code,'TS1005')
    def test_global_tsc_error_preserved(self):
        d=parse_compile_output('error TS18003: No inputs found.')[0]
        self.assertEqual(self.map([d]).diagnostics[0].mapping_status,'GLOBAL')
    def test_colon_format_parsed(self):
        d=parse_compile_output('src/a.ts:1:2 - error TS1005: expected')[0]
        self.assertEqual((d.line,d.column),(1,2))
    def test_identical_diagnostics_deduplicated(self):
        d=RawCompileDiagnostic('E','ERROR','typescript','x','src/a.ts',1)
        self.assertEqual(len(self.map([d,d]).diagnostics),1)
    def test_order_independent_report(self):
        ds=[RawCompileDiagnostic('B','WARNING','lint','b','src/a.ts',2),RawCompileDiagnostic('A','ERROR','build','a','src/a.ts',1)]
        self.assertEqual(self.map(ds),self.map(reversed(ds)))
    def test_bad_boolean_line_rejected(self):
        with self.assertRaises(ValueError):RawCompileDiagnostic('E','ERROR','x','x','src/a.ts',True)
    def test_column_without_line_rejected(self):
        with self.assertRaises(ValueError):RawCompileDiagnostic('E','ERROR','x','x','src/a.ts',None,1)
    def test_source_map_roundtrip(self):
        restored=source_map_from_dict(json.loads(json.dumps(asdict(self.mapping))))
        validate_source_map(restored,self.files);self.assertEqual(restored,self.mapping)
    def test_accepted_source_map_rejected(self):
        raw=asdict(self.mapping);raw['accepted']=True
        with self.assertRaises(ValueError):source_map_from_dict(raw)
    def test_existing_lint_and_static_receipts_adapt(self):
        lint=LintReceipt(1,(LintIssue('LINT_EVAL','ERROR','src/a.ts',1,'Eval'),),1,0,False)
        static=StaticAnalysisReceipt(1,(StaticFinding('STATIC_FS_IMPORT','BLOCKER','src/a.ts',2,'FS'),),1,False)
        r=map_build_receipts(source_map=self.mapping,files=self.files,lint=lint,static_analysis=static)
        self.assertEqual((r.error_count,r.unmapped_count),(2,0))
    def test_real_tsc_error_maps_to_source(self):
        self.assertIsNotNone(shutil.which('tsc'),'real tsc required')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'src').mkdir()
            text='export const x: number = "wrong";\n'
            (root/'src/a.ts').write_text(text)
            (root/'tsconfig.json').write_text(json.dumps({'compilerOptions':{'strict':True,'noEmit':True,'skipLibCheck':True},'include':['src/**/*.ts']}))
            r=compile_typescript(root)
            files=(('src/a.ts',text),)
            m=build_source_map(scene_fingerprint='a'*64,files=files,spans=(GeneratedSourceSpan('src/a.ts',1,1,sha256(text.encode()).hexdigest(),self.origin),))
            out=map_build_receipts(source_map=m,files=files,typescript=r,workspace=root)
            self.assertFalse(out.passed);self.assertTrue(any(d.code=='TS2322' and d.origin==self.origin for d in out.diagnostics))
    def test_no_acceptance_from_no_errors(self):self.assertFalse(self.map([]).accepted)

if __name__=='__main__':unittest.main()
