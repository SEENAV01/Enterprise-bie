"""Pure configuration regression tests, NOT real-render evidence.

Execute the actual capture-configuration statements from produce_actual_paint.
No fake compiler, renderer or ActualPaintWitness is used or returned.
"""
import ast
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def configuration_nodes(root=ROOT):
    source = (root / 'bie/compiler/real_paint.py').read_text()
    tree = ast.parse(source)
    producer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'produce_actual_paint')
    stage = next(n for n in ast.walk(producer) if isinstance(n, ast.With))
    start = next(i for i, n in enumerate(stage.body)
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'stage_cfg' for t in n.targets))
    end = next(i for i in range(start + 1, len(stage.body))
               if isinstance(stage.body[i], ast.Expr) and isinstance(stage.body[i].value, ast.Call)
               and isinstance(stage.body[i].value.func, ast.Attribute)
               and stage.body[i].value.func.attr == 'write_bytes')
    return stage.body[start + 1:end], source


def capture_config(original):
    nodes, _ = configuration_nodes()
    scope = {'stage_cfg': copy.deepcopy(original)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual-capture-config>', 'exec'), scope)
    return scope['stage_cfg']


class CaptureCoverageTests(unittest.TestCase):
    def config(self):
        return {'compilerOptions': {'strict': True, 'noImplicitAny': True,
                                    'strictNullChecks': True, 'noEmit': True,
                                    'skipLibCheck': False},
                'include': ['src/**/*.ts', 'src/**/*.tsx'], 'exclude': ['node_modules']}

    def test_executable_helper_is_explicitly_in_program(self):
        self.assertIn('qa-paint-helper.js', capture_config(self.config())['files'])

    def test_existing_explicit_members_remain_in_order(self):
        value = self.config(); value['files'] = ['existing.ts', 'another.ts']
        self.assertEqual(capture_config(value)['files'], ['existing.ts', 'another.ts', 'qa-paint-helper.js'])

    def test_existing_helper_is_not_duplicated(self):
        value = self.config(); value['files'] = ['existing.ts', 'qa-paint-helper.js']
        self.assertEqual(capture_config(value)['files'], value['files'])

    def test_all_original_include_patterns_remain(self):
        value = self.config()
        self.assertEqual(capture_config(value)['include'], value['include'] + [
            'qa-capture-entry.tsx', 'qa-paint-helper.js', 'qa-paint-helper.d.ts'])

    def test_strict_ts_options_are_unchanged(self):
        value = self.config(); expected = dict(value['compilerOptions'], allowJs=True, checkJs=False)
        self.assertEqual(capture_config(value)['compilerOptions'], expected)

    def test_exclusion_rules_are_not_bypassed(self):
        value = self.config(); value['exclude'].append('src/excluded.ts')
        self.assertEqual(capture_config(value)['exclude'], value['exclude'])

    def test_original_config_is_not_rewritten(self):
        value = self.config(); saved = copy.deepcopy(value)
        capture_config(value); self.assertEqual(value, saved)

    def test_fail_closed_typecheck_precedes_capture_process(self):
        _, source = configuration_nodes()
        check = source.index("tc=isolated_typecheck(stage,node=node,evidence_directory=out/'typecheck')")
        guard = source.index("if tc.status!='PASS':raise CompilerQAError('ACTUAL_PAINT_TYPECHECK_BLOCKED:'+tc.status)", check)
        process = source.index('process,kernel=run_isolated(', guard)
        self.assertLess(check, guard); self.assertLess(guard, process)
        self.assertIn('expected_sources', (ROOT / 'bie/compiler/generated_code_regression.py').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
