"""Synthetic diagnostic privacy controls, not product process proof."""
import json
import ast
import builtins
from copy import deepcopy
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from apps.operator.process_supervision import ChildOutcome
from . import recovery_observations as safe


class RecoveryObservationControls(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / safe.NAME
        self.boundary = 'after_SCENE_IR_private_publication'

    def row(self, **changes):
        row = safe.child_guard('WORK', self.boundary, 'CHILD_EXIT_BOUNDARY_REACHED')
        row.update(changes)
        return row

    def observe(self, result=None, mode='CRASH', elapsed=1.25):
        return safe.observe(result if result is not None else ChildOutcome(73, b'', True),
                            self.root, self.boundary, mode, elapsed)

    def test_valid_guard_roundtrip(self):
        self.assertTrue(safe.write_guard(self.root, self.row()))
        self.assertEqual(safe.read_guard(self.root), ('VALID', self.row()))

    def test_version_one_receipt_is_preserved_not_relabeled(self):
        row = self.row(schema=safe.LEGACY_CHILD_SCHEMA)
        self.assertEqual(safe.validate_guard(row), row)

    def test_operation_started_requires_explicit_version_two(self):
        row = safe.child_guard('RECOVERY', 'UNKNOWN', 'CHILD_OPERATION_STARTED', mode='RECOVER')
        self.assertEqual(row['schema'], 'bie.task036.recovery-child-guard/2')
        self.assertEqual(safe.validate_guard(row), row)
        row['schema'] = safe.LEGACY_CHILD_SCHEMA
        with self.assertRaises(ValueError):
            safe.validate_guard(row)

    def test_actual_worker_has_distinct_pre_recover_and_pre_work_guards(self):
        tree = ast.parse(Path(__file__).with_name('recovery_worker.py').read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        branch = next(n for n in main.body if isinstance(n, ast.If) and ast.unparse(n.test) == 'args.recover')
        calls = [ast.unparse(n.value) for n in branch.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
        self.assertEqual(calls[:3], ["report('CHILD_OPERATION_STARTED')", 'port.recover(p, args.run)',
                                     "report('CHILD_OPERATION_STARTED')"])
        phases = [n.value.value for n in branch.body if isinstance(n, ast.Assign) and
                  any(isinstance(t, ast.Name) and t.id == '_PHASE' for t in n.targets)]
        self.assertEqual(phases, ['RECOVERY', 'WORK'])

    def test_absence_is_not_success(self):
        row = self.observe()
        self.assertEqual(row['guard_state'], 'ABSENT')
        self.assertIsNone(row['guard'])
        self.assertFalse(row['accepted'])
        self.assertFalse(row['product_accepted'])

    def test_zero_exit_is_distinct_from_unknown(self):
        self.assertEqual(self.observe(ChildOutcome(0, b'', True))['exit_code'], 0)
        self.assertIsNone(self.observe(ChildOutcome(None, b'', True))['exit_code'])

    def test_false_completion_is_distinct_from_unknown(self):
        self.assertIs(self.observe(ChildOutcome(2, b'', False))['completed'], False)
        self.assertIsNone(self.observe(ChildOutcome(2, b'', 1))['completed'])

    def test_boolean_exit_not_integer(self):
        self.assertIsNone(self.observe(ChildOutcome(True, b'', True))['exit_code'])

    def test_out_of_range_exit_unknown(self):
        for code in (-256, 256, 2.0, '0'):
            with self.subTest(code=code):
                self.assertIsNone(self.observe(ChildOutcome(code, b'', True))['exit_code'])

    def test_spawn_sentinel_is_not_signal(self):
        self.assertIsNone(self.observe(ChildOutcome(-1, b'', False))['signal_number'])

    def test_actual_negative_exit_without_cause_inference(self):
        with patch.object(safe, 'POSIX_SIGNALS', True):
            row = self.observe(ChildOutcome(-24, b'', True))
        self.assertEqual(row['signal_number'], 24)
        self.assertNotIn('cause', row)
        self.assertNotIn('timeout', row)

    def test_elapsed_invalid_unknown(self):
        for elapsed in (True, -1, 61, float('nan'), float('inf'), '1'):
            with self.subTest(type=type(elapsed).__name__):
                self.assertIsNone(self.observe(elapsed=elapsed)['child_wall_seconds'])

    def test_private_output_is_never_inspected(self):
        class Private:
            def __str__(self): raise AssertionError('private read')
            def __repr__(self): raise AssertionError('private read')
            def __len__(self): raise AssertionError('private read')
        row = self.observe(ChildOutcome(2, Private(), True))
        self.assertNotIn('output', row)
        json.dumps(row)

    def test_oversized_private_output_cannot_leak(self):
        secret = 'SYNTHETIC_PRIVATE_BOOK_TOKEN'
        raw = (secret * 30000).encode()
        row = self.observe(ChildOutcome(2, raw, True))
        self.assertNotIn(secret, json.dumps(row))
        self.assertLess(len(json.dumps(row)), 2048)

    def test_extra_private_guard_fields_rejected(self):
        self.path.write_text(json.dumps(self.row(stderr='SYNTHETIC_PRIVATE', cwd='SYNTHETIC_PATH')))
        row = self.observe()
        self.assertEqual(row['guard_state'], 'INVALID')
        self.assertNotIn('SYNTHETIC_PRIVATE', json.dumps(row))

    def test_unknown_enum_rejected(self):
        for key in ('mode', 'phase', 'last_boundary', 'code', 'exception_class', 'scene_ir_state'):
            with self.subTest(field=key), self.assertRaises(ValueError):
                safe.validate_guard(self.row(**{key: 'UNRECOGNIZED'}))

    def test_non_string_enums_rejected(self):
        for value in (True, [], {}, 1):
            with self.subTest(type=type(value).__name__), self.assertRaises(ValueError):
                safe.child_guard(value, self.boundary, 'CHILD_EXCEPTION')

    def test_acceptance_promotion_rejected(self):
        for key in ('accepted', 'product_accepted'):
            for value in (True, 0, None):
                with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                    safe.validate_guard(self.row(**{key: value}))

    def test_duplicate_keys_rejected(self):
        self.path.write_text('{"schema":"x","schema":"y"}')
        self.assertEqual(safe.read_guard(self.root), ('INVALID', None))

    def test_nonfinite_json_rejected(self):
        for text in ('NaN', 'Infinity', '-Infinity'):
            self.path.write_text('{"phase":' + text + '}')
            self.assertEqual(safe.read_guard(self.root), ('INVALID', None))

    def test_partial_corrupt_json_rejected(self):
        for text in ('{', '[]', 'null', '\ufffd'):
            self.path.write_text(text, encoding='utf-8')
            self.assertEqual(safe.read_guard(self.root), ('INVALID', None))

    def test_oversize_guard_rejected(self):
        self.path.write_bytes(b' ' * 2049)
        self.assertEqual(safe.read_guard(self.root), ('INVALID', None))

    def test_nonregular_guard_rejected(self):
        self.path.mkdir()
        self.assertEqual(safe.read_guard(self.root), ('INVALID', None))
        self.assertFalse(safe.write_guard(self.root, self.row()))

    def test_symlink_guard_rejected_before_read_or_write(self):
        with patch.object(Path, 'is_symlink', return_value=True), patch.object(Path, 'read_bytes', side_effect=AssertionError):
            self.assertEqual(safe.read_guard(self.root), ('INVALID', None))
            self.assertFalse(safe.write_guard(self.root, self.row()))

    def test_file_change_rejected(self):
        safe.write_guard(self.root, self.row())
        original = safe.os.fstat
        def altered(fd):
            value = original(fd)
            class Changed:
                st_mode = value.st_mode
                st_ino = value.st_ino + 1
                st_size = value.st_size
                st_mtime_ns = value.st_mtime_ns
            return Changed()
        with patch.object(safe.os, 'fstat', side_effect=altered):
            self.assertEqual(safe.read_guard(self.root), ('INVALID', None))

    def test_stale_crash_guard_not_recovery_evidence(self):
        safe.write_guard(self.root, self.row())
        row = self.observe(mode='RECOVER')
        self.assertEqual(row['guard_state'], 'INVALID')
        self.assertIsNone(row['guard'])

    def test_recovery_guard_explicit_mode(self):
        row = safe.child_guard('RECOVERY', 'UNKNOWN', 'CHILD_RECOVERED', state='SUCCEEDED', mode='RECOVER')
        safe.write_guard(self.root, row)
        self.assertEqual(self.observe(mode='RECOVER')['guard'], row)

    def test_evidence_write_failure_contained(self):
        with patch.object(safe.os, 'open', side_effect=PermissionError('SYNTHETIC_PRIVATE')):
            self.assertFalse(safe.write_guard(self.root, self.row()))

    def test_observer_failure_cannot_replace_original_result(self):
        result = ChildOutcome(73, b'', True)
        with patch.object(safe, 'observe', side_effect=RuntimeError('SYNTHETIC_PRIVATE')):
            self.assertIsNone(safe.record_observation(result, self.root, self.boundary, 'CRASH', 1))
        self.assertEqual(result.exit_code, 73)
        self.assertTrue(result.completed)

    def test_invalid_observer_inputs_rejected(self):
        for boundary, mode in (('FOREIGN', 'CRASH'), (self.boundary, True), (self.boundary, 'OTHER')):
            with self.assertRaises(ValueError):
                safe.observe(ChildOutcome(73, b'', True), self.root, boundary, mode, 1)

    def test_context_bounded_and_restored(self):
        previous = safe._ROWS.get()
        with safe.capture_observations() as rows:
            for _ in range(10): self.observe()
            self.assertEqual(len(rows), 4)
        self.assertIs(safe._ROWS.get(), previous)

    def test_nested_context_isolated(self):
        with safe.capture_observations() as outer:
            with safe.capture_observations() as inner:
                self.observe()
            self.assertEqual(len(inner), 1)
            self.assertEqual(outer, [])

    def test_exception_restores_context_and_cleanup(self):
        previous = safe._ROWS.get()
        with self.assertRaises(RuntimeError):
            with safe.capture_observations():
                raise RuntimeError('synthetic')
        self.assertIs(safe._ROWS.get(), previous)
        safe.write_guard(self.root, self.row())
        self.temp.cleanup()
        self.assertFalse(self.root.exists())

    def test_package_loader_preserves_observation_binding(self):
        from tests.compiler.run_m1_tests import repository_module, ROOT
        previous = sys.path[:]
        with repository_module('tests/productization/scene_ir/test_scene_ir_recovery.py', ROOT) as (module, origins):
            self.assertIs(module.record_observation, safe.record_observation)
            self.assertEqual(origins[safe.__name__], 'tests/productization/scene_ir/recovery_observations.py')
        self.assertEqual(sys.path, previous)

    def callback_import_failure(self, phase):
        # Compile the actual nested callback, not a copied alternate worker.
        tree = ast.parse(Path(__file__).with_name('recovery_worker.py').read_text(encoding='utf-8'))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        node = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'fault')
        exits, reports = [], []
        def refused(*args, **kwargs):
            raise ImportError('SYNTHETIC_PRIVATE')
        scope = dict(__builtins__={**vars(builtins), '__import__': refused},
                     _BOUNDARY='UNKNOWN', args=SimpleNamespace(phase=self.boundary),
                     os=SimpleNamespace(_exit=exits.append), report=reports.append)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[deepcopy(node)], type_ignores=[])),
                     '<actual-test-worker-callback>', 'exec'), scope)
        scope['fault'](phase)
        self.assertEqual(scope['_BOUNDARY'], 'UNKNOWN')
        return exits, reports

    def test_optional_import_failure_preserves_exact_crash_injection(self):
        exits, reports = self.callback_import_failure(self.boundary)
        self.assertEqual(exits, [73])
        self.assertEqual(reports, ['CHILD_EXIT_BOUNDARY_REACHED'])

    def test_optional_import_failure_preserves_nonmatching_callback(self):
        exits, reports = self.callback_import_failure('after_SCENE_IR_catalog')
        self.assertEqual(exits, [])
        self.assertEqual(reports, [])

    def test_cpu_guard_is_closed_explicit_version_three(self):
        row = safe.child_cpu_guard('RECOVERY', 'UNKNOWN', 'CHILD_OPERATION_STARTED', mode='RECOVER', process_cpu_ms=1234)
        self.assertEqual(row['schema'], 'bie.task036.recovery-child-guard/3')
        self.assertEqual(set(row), safe.CPU_FIELDS)
        self.assertEqual(safe.validate_guard(row), row)

    def test_cpu_unknown_is_not_zero(self):
        args = ('WORK', self.boundary, 'CHILD_EXIT_BOUNDARY_REACHED')
        self.assertIsNone(safe.child_cpu_guard(*args)['process_cpu_ms'])
        self.assertEqual(safe.child_cpu_guard(*args, process_cpu_ms=0)['process_cpu_ms'], 0)

    def test_cpu_bool_negative_and_overflow_fail_closed(self):
        for value in (True, False, -1, 60001, 10**200):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                safe.child_cpu_guard('WORK', self.boundary, 'CHILD_EXIT_BOUNDARY_REACHED', process_cpu_ms=value)

    def test_cpu_float_nonfinite_and_string_are_not_coerced(self):
        for value in (1.0, float('nan'), float('inf'), 'PRIVATE_SYNTHETIC_CPU'):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                safe.child_cpu_guard('WORK', self.boundary, 'CHILD_EXIT_BOUNDARY_REACHED', process_cpu_ms=value)

    def test_cpu_field_cannot_be_smuggled_into_prior_guard_versions(self):
        for schema in (safe.LEGACY_CHILD_SCHEMA, safe.CHILD_SCHEMA):
            row = self.row(schema=schema, process_cpu_ms=1)
            with self.assertRaises(ValueError): safe.validate_guard(row)

    def test_version_three_requires_cpu_field_even_when_unknown(self):
        row = self.row(schema=safe.CPU_CHILD_SCHEMA)
        with self.assertRaises(ValueError): safe.validate_guard(row)

    def test_cpu_private_object_is_not_inspected_or_retained(self):
        class Private:
            def __str__(self): raise AssertionError('PRIVATE_STR')
            def __repr__(self): raise AssertionError('PRIVATE_REPR')
            def __int__(self): raise AssertionError('PRIVATE_INT')
        with self.assertRaises(ValueError):
            safe.child_cpu_guard('WORK', self.boundary, 'CHILD_EXIT_BOUNDARY_REACHED', process_cpu_ms=Private())

    def test_actual_worker_cpu_clock_is_inside_optional_evidence_guard(self):
        tree = ast.parse(Path(__file__).with_name('recovery_worker.py').read_text())
        report = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'report')
        self.assertEqual(len(report.body), 1)
        self.assertIsInstance(report.body[0], ast.Try)
        calls = [ast.unparse(n.func) for n in ast.walk(report) if isinstance(n, ast.Call)]
        self.assertIn('time.process_time', calls)
        self.assertNotIn('str', calls)
        self.assertNotIn('repr', calls)
        self.assertNotIn('vars', calls)


if __name__ == '__main__':
    unittest.main()
