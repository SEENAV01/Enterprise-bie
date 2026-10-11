"""Synthetic closed checkpoint controls; not actual Linux worker proof."""
import json
import ast
import builtins
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tests.productization.scene_ir import positive_process_observations as probe


class PositiveCheckpointControls(unittest.TestCase):
    def row(self):
        return dict(schema=probe.SCHEMA, mode="RUN", phase="BEFORE_WORK", requested_stage="SCENE_IR",
            boundary="UNKNOWN", operation_index=11, process_cpu_ms=20000, accepted=False, product_accepted=False)

    def test_roundtrip_closed_shape(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertTrue(probe.write(root, self.row()))
            self.assertEqual(probe.read(root), ("VALID", self.row()))

    def test_absent_is_not_zero_or_success(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(probe.read(root), ("ABSENT", None))

    def test_unknown_cpu_is_distinct_from_zero(self):
        for cpu in (None, 0):
            row = self.row(); row["process_cpu_ms"] = cpu
            self.assertIs(probe.validate(row)["process_cpu_ms"], cpu)

    def test_boolean_cpu_rejected(self):
        row = self.row(); row["process_cpu_ms"] = True
        with self.assertRaises(ValueError): probe.validate(row)

    def test_nonfinite_negative_overflow_cpu_rejected(self):
        for cpu in (-1, 60001, float("inf"), float("nan"), 1.2):
            row = self.row(); row["process_cpu_ms"] = cpu
            with self.assertRaises(ValueError): probe.validate(row)

    def test_unknown_enum_rejected(self):
        for key in ("mode", "phase", "requested_stage", "boundary"):
            row = self.row(); row[key] = "PRIVATE_SYNTHETIC_SENTINEL"
            with self.assertRaises(ValueError): probe.validate(row)

    def test_unknown_fields_rejected(self):
        row = self.row(); row["stderr"] = "PRIVATE_SYNTHETIC_SENTINEL"
        with self.assertRaises(ValueError): probe.validate(row)

    def test_schema_subclass_cannot_impersonate_or_leak(self):
        class Foreign(str):
            def __eq__(self, _): return True
        row = self.row(); row["schema"] = Foreign("PRIVATE_SYNTHETIC_SENTINEL")
        with self.assertRaises(ValueError): probe.validate(row)

    def test_nonfinite_json_rejected_before_admission(self):
        with tempfile.TemporaryDirectory() as root:
            raw = json.dumps(self.row()).replace('20000', 'NaN')
            (Path(root)/probe.NAME).write_text(raw, encoding="utf-8")
            self.assertEqual(probe.read(root), ("INVALID", None))

    def test_boolean_negative_overflow_index_rejected(self):
        for index in (True, -1, 12, 1.1):
            row = self.row(); row["operation_index"] = index
            with self.assertRaises(ValueError): probe.validate(row)

    def test_acceptance_promotion_rejected(self):
        for key in ("accepted", "product_accepted"):
            row = self.row(); row[key] = True
            with self.assertRaises(ValueError): probe.validate(row)

    def test_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            raw = json.dumps(self.row())[:-1] + ',"accepted":false}'
            (Path(root)/probe.NAME).write_text(raw, encoding="utf-8")
            self.assertEqual(probe.read(root), ("INVALID", None))

    def test_partial_write_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/probe.NAME).write_bytes(b'{"schema":')
            self.assertEqual(probe.read(root), ("INVALID", None))

    def test_oversize_rejected_without_unbounded_read(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/probe.NAME).write_bytes(b"x" * (probe.MAX_BYTES + 1))
            self.assertEqual(probe.read(root), ("TOO_LARGE", None))

    def test_symlink_root_rejected_before_io(self):
        with patch.object(Path, "is_symlink", return_value=True):
            self.assertFalse(probe.write("synthetic", self.row()))
            self.assertEqual(probe.read("synthetic"), ("INVALID", None))

    def test_nonregular_target_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/probe.NAME).mkdir()
            self.assertFalse(probe.write(root, self.row()))
            self.assertEqual(probe.read(root), ("INVALID", None))

    def test_private_values_never_enter_valid_guard(self):
        with tempfile.TemporaryDirectory(prefix="PRIVATE_SYNTHETIC_SENTINEL") as root:
            marker = probe.Checkpoints(root, "RUN")
            with patch.object(probe.time, "process_time", return_value=1.0):
                marker.mark("BEFORE_WORK", "SCENE_IR", 11)
            self.assertEqual(probe.read(root)[0], "VALID")
            self.assertNotIn("PRIVATE_SYNTHETIC_SENTINEL", json.dumps(probe.read(root)))

    def test_actual_clock_is_projected_not_elapsed_estimate(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(probe.time, "process_time", return_value=12.345):
                probe.Checkpoints(root, "RUN").mark("INITIAL_STATUS")
            self.assertEqual(probe.read(root)[1]["process_cpu_ms"], 12345)

    def test_clock_error_is_optional(self):
        with patch.object(probe.time, "process_time", side_effect=RuntimeError("private")):
            probe.Checkpoints("synthetic", "RUN").mark("INITIAL_STATUS")

    def test_write_failure_cannot_escape(self):
        with patch.object(probe, "write", side_effect=RuntimeError("private")):
            probe.Checkpoints("synthetic", "RUN").mark("INITIAL_STATUS")

    def test_unrecognized_fault_is_not_formatted(self):
        class Foreign:
            def __str__(self): raise AssertionError("private")
        with tempfile.TemporaryDirectory() as root:
            probe.Checkpoints(root, "RUN").fault(Foreign())
            self.assertEqual(probe.read(root), ("ABSENT", None))

    def test_native_boundary_retains_current_requested_stage(self):
        with tempfile.TemporaryDirectory() as root:
            marker = probe.Checkpoints(root, "RUN")
            with patch.object(probe.time, "process_time", return_value=1.0):
                marker.mark("BEFORE_WORK", "SCENE_IR", 11)
                marker.fault("after_SCENE_IR_terminal")
            row = probe.read(root)[1]
            self.assertEqual((row["phase"], row["requested_stage"], row["operation_index"], row["boundary"]),
                ("NATIVE_BOUNDARY", "SCENE_IR", 11, "after_SCENE_IR_terminal"))

    def test_out_of_range_clock_is_unavailable_without_state_change(self):
        with tempfile.TemporaryDirectory() as root:
            marker = probe.Checkpoints(root, "RUN")
            with patch.object(probe.time, "process_time", return_value=61.0):
                self.assertIsNone(marker.mark("BEFORE_WORK", "SCENE_IR", 11))
                self.assertIsNone(marker.fault("after_SCENE_IR_terminal"))
            self.assertEqual(probe.read(root), ("ABSENT", None))
            self.assertEqual((marker.stage, marker.index), ("UNKNOWN", 0))

    def test_existing_temporary_collision_is_not_removed(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root)/(probe.NAME+".new")
            target.write_bytes(b"private")
            self.assertFalse(probe.write(root, self.row()))
            self.assertEqual(target.read_bytes(), b"private")

    def test_atomic_replacement_preserves_latest_safe_record(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertTrue(probe.write(root, self.row()))
            row = self.row(); row["phase"] = "AFTER_WORK"
            self.assertTrue(probe.write(root, row))
            self.assertEqual(probe.read(root), ("VALID", row))

    def test_validated_result_is_not_caller_dictionary(self):
        row = self.row(); result = probe.validate(row)
        row["schema"] = "PRIVATE_SYNTHETIC_SENTINEL"
        self.assertEqual(result["schema"], probe.SCHEMA)


class WorkerCheckpointNoninterference(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3]
        tree = ast.parse((root/"apps/operator/scene_ir_worker_child.py").read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
            and n.name in ("_checkpoints", "_mark", "_checkpoint_fault")]
        self.assertEqual(len(nodes), 3)
        self.scope = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "synthetic-safe-wrapper", "exec"), self.scope)
        self.args = SimpleNamespace(technical_test_providers=True, verify_only=False, data_root="synthetic")

    def test_optional_import_failure_cannot_abort_native_work(self):
        with patch.object(builtins, "__import__", side_effect=RuntimeError("private")):
            self.assertIsNone(self.scope["_checkpoints"](self.args))

    def test_optional_constructor_failure_cannot_abort_native_work(self):
        with patch.object(probe, "Checkpoints", side_effect=RuntimeError("private")):
            self.assertIsNone(self.scope["_checkpoints"](self.args))

    def test_non_test_mode_never_imports_optional_observer(self):
        self.args.technical_test_providers = False
        with patch.object(builtins, "__import__", side_effect=AssertionError("must not import")):
            self.assertIsNone(self.scope["_checkpoints"](self.args))

    def test_optional_mark_exception_is_contained(self):
        observer = SimpleNamespace(mark=lambda *_: (_ for _ in ()).throw(RuntimeError("private")))
        self.assertIsNone(self.scope["_mark"](observer, "INITIAL_STATUS"))

    def test_optional_fault_exception_is_contained(self):
        observer = SimpleNamespace(fault=lambda *_: (_ for _ in ()).throw(RuntimeError("private")))
        self.assertIsNone(self.scope["_checkpoint_fault"](observer)("after_SCENE_IR_terminal"))

    def test_optional_calls_are_exactly_once_with_unchanged_arguments(self):
        calls = []; value = object()
        observer = SimpleNamespace(mark=lambda *a: calls.append(a), fault=lambda *a: calls.append(a))
        self.scope["_mark"](observer, "BEFORE_WORK", "SCENE_IR", 11)
        self.scope["_checkpoint_fault"](observer)(value)
        self.assertEqual(calls[0], ("BEFORE_WORK", "SCENE_IR", 11))
        self.assertIs(calls[1][0], value)

    def checkpoint_reader(self):
        root = Path(__file__).resolve().parents[3]
        tree = ast.parse((root/"scripts/smoke_bie_scene_ir.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_read_checkpoint")
        scope = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "synthetic-safe-reader", "exec"), scope)
        return scope["_read_checkpoint"]

    def test_optional_reader_import_failure_preserves_failed_child_path(self):
        read = self.checkpoint_reader()
        with patch.object(builtins, "__import__", side_effect=RuntimeError("private")):
            self.assertEqual(read("synthetic"), ("UNAVAILABLE", None))

    def test_optional_reader_exception_preserves_failed_child_path(self):
        read = self.checkpoint_reader()
        with patch.object(probe, "read", side_effect=RuntimeError("private")):
            self.assertEqual(read("synthetic"), ("UNAVAILABLE", None))


if __name__ == "__main__": unittest.main()
