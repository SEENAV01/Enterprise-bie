"""Actual isolated TypeScript positive and seeded-negative coverage controls.

These are technical synthetic compile tests, not book/render acceptance. No
fake compiler runner or modified source-coverage guard is used.
"""
from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from bie.compiler.real_paint import isolated_typecheck


class NativePaintTypecheck(unittest.TestCase):
    def setUp(self):
        if sys.platform!='linux':raise RuntimeError('native Linux required; no compiler fallback')
        prepared=os.environ.get('BIE_SECTION18_RENDER_PROJECT')
        if not prepared:raise RuntimeError('prepared pinned render project required')
        self.temp=tempfile.TemporaryDirectory(prefix='bie-paint-ts-regression-')
        self.root=Path(self.temp.name)
        self.project=self.root/'project'
        shutil.copytree(Path(prepared),self.project,symlinks=True,
                        ignore=shutil.ignore_patterns('out','render-evidence','validation-runs'))
        self.node=shutil.which('node')
        self.assertIsNotNone(self.node)
        (self.project/'qa-paint-helper.js').write_text('export const baseMeasure = options => [];\n')
        self.observer=self.project/'qa-capture-entry.tsx'
        self.observer.write_text('''import {baseMeasure as rawBaseMeasure} from "./qa-paint-helper";
const baseMeasure: (options:{frame:number;equationFonts:Record<string,number>}) => unknown[] = rawBaseMeasure;
export const observed = baseMeasure({frame:0,equationFonts:{}});
''')
        self.config=json.loads((self.project/'tsconfig.json').read_text())
        self.config['compilerOptions'].update(allowJs=True,checkJs=False)
        self.config['include']+=['qa-paint-helper.js','qa-capture-entry.tsx']
        self.write_config()

    def tearDown(self):self.temp.cleanup()

    def write_config(self):
        (self.project/'tsconfig.json').write_text(json.dumps(self.config))

    def check(self):
        return isolated_typecheck(self.project,node=self.node,evidence_directory=self.root/'evidence')

    def test_same_basename_declaration_reproduces_coverage_block(self):
        (self.project/'qa-paint-helper.d.ts').write_text(
            'export function baseMeasure(options:{frame:number;equationFonts:Record<string,number>}):unknown[];\n')
        self.config['include'].append('qa-paint-helper.d.ts');self.write_config()
        result=self.check()
        self.assertEqual(result.status,'BLOCKED_INPUT_COVERAGE')
        self.assertIn('qa-paint-helper.d.ts',result.stdout)
        self.assertNotIn(str(self.project/'qa-paint-helper.js'),result.stdout.splitlines())

    def test_executable_helper_with_typed_observer_passes_real_tsc(self):
        result=self.check();self.assertEqual(result.status,'PASS')
        evidence=json.loads((self.root/'evidence/TYPECHECK.json').read_text())
        self.assertEqual(len(evidence['executions']),2)
        self.assertTrue(all(row['process']['process']['passed'] for row in evidence['executions']))
        coverage=evidence['executions'][0]['process']['process']['stdout']
        self.assertIn('/work/qa-paint-helper.js',coverage)
        self.assertNotIn('qa-paint-helper.d.ts',coverage)

    def test_strict_observer_type_error_still_fails(self):
        self.observer.write_text(self.observer.read_text()+'const invalid: number = "wrong";\n')
        result=self.check();self.assertEqual(result.status,'FAIL')
        self.assertIn('TS2322',result.stdout+result.stderr)

    def test_uninspected_excluded_source_still_blocks_coverage(self):
        (self.project/'excluded-source.ts').write_text('export const orphan = 1;\n')
        result=self.check();self.assertEqual(result.status,'BLOCKED_INPUT_COVERAGE')
        self.assertNotIn(str(self.project/'excluded-source.ts'),result.stdout.splitlines())


if __name__=='__main__':unittest.main(verbosity=2)
