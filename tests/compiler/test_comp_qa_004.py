from dataclasses import asdict, replace
from pathlib import Path
import json
import shutil
import tempfile
import unittest
from bie.compiler.generated_code_regression import *
from tests.compiler.qa_test_support import context, bundle, FIXTURES

class GeneratedCodeRegressionTests(unittest.TestCase):
    def probe(self,code,extra=()):return probe_typescript_sources((('src/a.tsx',code),)+extra)
    def codes(self,r):return {f.code for f in r.findings}
    def test_real_typescript_parser_accepts_syntax(self):
        r=self.probe('export const A=()=> <div>Hello</div>;')
        self.assertEqual(r.status,'PASS');self.assertEqual(r.execution_kind,'REAL_TYPESCRIPT_AST_PARSER');self.assertFalse(r.full_typecheck)
    def test_actual_parser_detects_invalid_jsx(self):
        r=self.probe('export const A=()=> <div>{broken;</div>;')
        self.assertEqual(r.status,'FAIL');self.assertTrue(any(d.code.startswith('TS') for d in r.diagnostics))
    def test_math_random_is_rejected(self):self.assertIn('QA_UNSEEDED_RANDOM',self.codes(self.probe('const x=Math.random();')))
    def test_computed_random_call_rejected(self):self.assertIn('QA_UNSEEDED_RANDOM',self.codes(self.probe('const x=Math["random"]();')))
    def test_remotion_random_null_rejected(self):
        self.assertIn('QA_UNSEEDED_RANDOM',self.codes(self.probe('import {random as r} from "remotion";const x=r(null);')))
    def test_seeded_random_permitted_by_ast(self):
        self.assertEqual(self.probe('import {random} from "remotion";const x=random("fixed");').status,'PASS')
    def test_wallclock_calls_rejected(self):
        self.assertIn('QA_WALL_CLOCK',self.codes(self.probe('const x=Date.now();const y=new Date();')))
    def test_fixed_date_not_wallclock(self):self.assertNotIn('QA_WALL_CLOCK',self.codes(self.probe('const x=new Date(0);')))
    def test_timers_rejected(self):self.assertIn('QA_REALTIME_SCHEDULER',self.codes(self.probe('setInterval(()=>{},10);')))
    def test_eval_rejected(self):self.assertIn('QA_EXECUTABLE_EVAL',self.codes(self.probe('eval("1");')))
    def test_function_constructor_rejected(self):self.assertIn('QA_EXECUTABLE_EVAL',self.codes(self.probe('new Function("return 1");')))
    def test_strings_and_comments_not_mistaken_for_executable_random(self):
        self.assertNotIn('QA_UNSEEDED_RANDOM',self.codes(self.probe('const text="Math.random()"; // Math.random()\n')))
    def test_node_prefixed_import_rejected(self):
        self.assertIn('QA_NODE_RUNTIME_IMPORT',self.codes(self.probe('import fs from "node:fs";')))
    def test_require_node_capability_rejected(self):
        self.assertIn('QA_NODE_RUNTIME_IMPORT',self.codes(self.probe('const fs=require("fs");')))
    def test_dynamic_import_target_requires_static_governance(self):
        self.assertIn('QA_DYNAMIC_IMPORT_UNBOUNDED',self.codes(self.probe('const x=import(userChoice);')))
    def test_network_calls_rejected(self):self.assertIn('QA_NETWORK_SIDE_EFFECT',self.codes(self.probe('fetch("https://example.invalid");')))
    def test_environment_dependency_rejected(self):self.assertIn('QA_ENVIRONMENT_DEPENDENCY',self.codes(self.probe('const x=process.env.MODE;')))
    def test_css_realtime_animation_rejected(self):self.assertIn('QA_CSS_REALTIME_ANIMATION',self.codes(self.probe('const x={transition:"all 1s"};')))
    def test_typecheck_suppression_rejected(self):self.assertIn('QA_TYPECHECK_SUPPRESSION',self.codes(self.probe('// @ts-ignore\nconst x=1;')))
    def test_string_mention_typecheck_comment_not_rejected(self):self.assertNotIn('QA_TYPECHECK_SUPPRESSION',self.codes(self.probe('const x="@ts-ignore";')))
    def test_missing_relative_import_detected(self):self.assertIn('GENERATED_IMPORT_MISSING',self.codes(self.probe('import {B} from "./Missing";')))
    def test_existing_relative_import_allowed(self):
        self.assertEqual(self.probe('import {B} from "./b";',(('src/b.ts','export const B=1;'),)).status,'PASS')
    def test_escaping_relative_import_rejected(self):self.assertIn('GENERATED_IMPORT_ESCAPES_ROOT',self.codes(self.probe('import x from "../../secret";')))
    def test_undeclared_package_detected(self):self.assertIn('GENERATED_DEPENDENCY_UNDECLARED',self.codes(self.probe('import x from "unlisted-package";')))
    def test_no_parser_is_blocked_not_simulated(self):
        r=probe_typescript_sources((('a.ts','const a=1;'),),typescript_library='/no/such/typescript.js')
        self.assertEqual(r.status,'BLOCKED')
    def test_empty_code_scan_not_pass(self):self.assertEqual(probe_typescript_sources((('readme.txt','not code'),)).status,'FAIL')
    def regression(self,files,baseline=None):
        return evaluate_generated_regression(files=files,context=context(),baseline=baseline,require_full_typecheck=False)
    def baseline(self,files):return record_generated_baseline(baseline_id='b',fixture_id='f',approval_ref='test:initial-golden',files=files,context=context())
    def test_matching_explicit_baseline(self):
        f=(('a.ts','export const a=1;'),);r=self.regression(f,self.baseline(f));self.assertTrue(r.passed);self.assertFalse(r.compile_verified)
    def test_missing_baseline_never_auto_blessed(self):
        r=self.regression((('a.ts','export const a=1;'),))
        self.assertFalse(r.passed);self.assertEqual(r.baseline_status,'MISSING')
    def test_changed_source_requires_baseline_review(self):
        old=(('a.ts','export const a=1;'),);r=self.regression((('a.ts','export const a=2;'),),self.baseline(old))
        self.assertFalse(r.passed);self.assertEqual(r.baseline_status,'DIFF')
    def test_tampered_baseline_rejected(self):
        b=self.baseline((('a.ts','export const a=1;'),))
        with self.assertRaises(ValueError):validate_baseline(replace(b,baseline_sha256='f'*64))
    def test_acceptance_escalation_rejected(self):
        b=self.baseline((('a.ts','export const a=1;'),))
        with self.assertRaises(ValueError):validate_baseline(replace(b,accepted=True))
    def test_existing_bie_generated_project_baseline_and_imports(self):
        b=bundle('biology-structure');base=baseline_from_dict(json.loads((FIXTURES/'baselines/biology-structure.json').read_text()))
        r=evaluate_generated_regression(files=b.codegen.files,context=b.context,baseline=base,require_full_typecheck=False)
        self.assertTrue(r.source_checks_passed)
    def test_missing_remotion_dependencies_block_full_compile(self):
        b=bundle();base=baseline_from_dict(json.loads((FIXTURES/'baselines/math-plain.json').read_text()))
        r=evaluate_generated_regression(files=b.codegen.files,context=b.context,baseline=base)
        self.assertTrue(r.source_checks_passed);self.assertFalse(r.passed)
        self.assertEqual(r.full_typecheck.status,'BLOCKED_DEPENDENCIES');self.assertFalse(r.compile_verified)
    def test_real_tsc_compiles_selfcontained_typed_fixture(self):
        self.assertIsNotNone(shutil.which('tsc'))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'src').mkdir();(root/'src/a.ts').write_text('export const x:number=1;')
            (root/'tsconfig.json').write_text(json.dumps({'compilerOptions':{'strict':True,'skipLibCheck':True},'include':['src/**/*.ts']}))
            r=typecheck_generated_workspace(root,tsc_bin=shutil.which('tsc'))
            self.assertEqual(r.status,'PASS');self.assertEqual(r.execution_kind,'REAL_TSC_PROCESS')
    def test_real_tsc_rejects_incompatible_type(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a.ts').write_text('export const x:number="not-number";')
            (root/'tsconfig.json').write_text(json.dumps({'compilerOptions':{'strict':True,'skipLibCheck':True},'include':['a.ts']}))
            r=typecheck_generated_workspace(root,tsc_bin=shutil.which('tsc'))
            self.assertEqual(r.status,'FAIL');self.assertTrue(any(d.code=='TS2322' for d in r.diagnostics))
    def test_wrong_workspace_source_rejected(self):
        files=(('src/a.ts','export const a=1;'),)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'src').mkdir();(root/'src/a.ts').write_text('different')
            with self.assertRaises(ValueError):evaluate_generated_regression(files=files,context=context(),baseline=self.baseline(files),workspace=root,require_full_typecheck=False)
    def test_alias_to_random_is_still_rejected(self):
        self.assertIn('QA_UNSEEDED_RANDOM',self.codes(self.probe('const r=Math.random;const x=r();')))
    def test_source_regression_does_not_accept_product(self):
        files=(('a.ts','export const a=1;'),);self.assertFalse(self.regression(files,self.baseline(files)).accepted)

if __name__=='__main__':unittest.main()
