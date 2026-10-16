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


class SequentialChildControls(unittest.TestCase):
    """Synthetic cut/receipt guards, NOT real eleven-stage Linux execution."""
    def setUp(self):
        from apps.operator import scene_ir_worker_child as worker
        from scripts import smoke_bie_scene_ir as smoke
        from bie.productization.contracts import ProducerError
        self.worker, self.smoke, self.error = worker, smoke, ProducerError
        self.stages = probe.STAGES

    def fixture(self, completed=10, blocked=False):
        from contextlib import contextmanager
        expected = self.worker._split_expected(self.stages, completed, blocked)
        records = {ref: SimpleNamespace(stage_id="SOURCE", blob_digest="0"*64)
                   for ref in ("run-config", "run-source")}
        saved, messages = {"stages": {}}, {}
        for stage, state in expected.items():
            refs = [stage + "-output"] if state == "SUCCEEDED" else []
            saved["stages"][stage] = {"attempts": [dict(attempt=1, state=state,
                output_artifact_refs=refs, evidence_refs=[])]}
            if refs:
                records[refs[0]] = SimpleNamespace(stage_id=stage, blob_digest="1"*64)
            if state in ("SUCCEEDED", "BLOCKED"):
                messages[stage] = SimpleNamespace(state="ACKED" if state == "SUCCEEDED" else "DEAD_LETTER")
        counts = dict(ACKED=sum(v == "SUCCEEDED" for v in expected.values()),
                      DEAD_LETTER=sum(v == "BLOCKED" for v in expected.values()))
        service = SimpleNamespace(persistence=SimpleNamespace(load_run_state=lambda _: saved,
            artifacts_for_run=lambda _: list(records)), queue=SimpleNamespace(get=messages.get, stats=lambda: counts),
            task_id=lambda run, stage, attempt: stage, record=lambda run, ref: records[ref])
        @contextmanager
        def native(*args):
            self.assertEqual(args, ("principal", "run", "read"))
            yield service
        port = SimpleNamespace(native=native)
        return expected, saved, messages, records, counts, port

    def inventory(self, fixture):
        return self.worker._partition_inventory(fixture[-1], "principal", "run", fixture[0])

    def test_cut_has_ten_succeeded_and_only_scene_ready(self):
        expected = self.fixture()[0]
        self.assertEqual(list(expected.values()), ["SUCCEEDED"]*10 + ["READY"])
        self.assertEqual(len(self.inventory(self.fixture())), 64)

    def test_empty_first_cut_requires_no_precompleted_stage(self):
        f = self.fixture(0)
        self.assertEqual(list(f[0].values()), ["READY"] + ["PENDING"]*10)
        f[1]["stages"]["SOURCE"]["attempts"][0]["state"] = "SUCCEEDED"
        with self.assertRaises(self.error): self.inventory(f)

    def test_missing_stage_rejected(self):
        f = self.fixture(); del f[1]["stages"]["VISUAL"]
        with self.assertRaises(self.error): self.inventory(f)

    def test_extra_stage_rejected(self):
        f = self.fixture(); f[1]["stages"]["VIDEO_CODE"] = {}
        with self.assertRaises(self.error): self.inventory(f)

    def test_missing_executed_stage_cannot_pass_with_fake_ack(self):
        f = self.fixture(); f[1]["stages"]["VISUAL"]["attempts"][0]["state"] = "PENDING"
        with self.assertRaises(self.error): self.inventory(f)

    def test_missing_ack_rejected(self):
        f = self.fixture(); del f[2]["ANIMATION"]
        with self.assertRaises(self.error): self.inventory(f)

    def test_nonterminal_queue_rejected(self):
        f = self.fixture(); f[2]["ANIMATION"].state = "DELIVERED"
        with self.assertRaises(self.error): self.inventory(f)

    def test_surplus_fake_ack_rejected(self):
        f = self.fixture(); f[4]["ACKED"] += 1
        with self.assertRaises(self.error): self.inventory(f)

    def test_missing_output_rejected_even_with_ack(self):
        f = self.fixture(); f[1]["stages"]["ANIMATION"]["attempts"][0]["output_artifact_refs"] = []
        with self.assertRaises(self.error): self.inventory(f)

    def test_forged_record_uses_native_validation_not_record_count(self):
        f = self.fixture()
        with patch.object(f[3]["ANIMATION-output"], "stage_id", "VISUAL"):
            with self.assertRaises(self.error): self.inventory(f)

    def test_missing_cas_record_cannot_become_success(self):
        f = self.fixture(); del f[3]["ANIMATION-output"]
        with self.assertRaises(KeyError): self.inventory(f)

    def test_duplicate_output_rejected(self):
        f = self.fixture(); f[1]["stages"]["ANIMATION"]["attempts"][0]["output_artifact_refs"] *= 2
        with self.assertRaises(self.error): self.inventory(f)

    def test_preseeded_scene_output_rejected(self):
        f = self.fixture(); f[1]["stages"]["SCENE_IR"]["attempts"][0]["output_artifact_refs"] = ["fake"]
        with self.assertRaises(self.error): self.inventory(f)

    def test_preseeded_private_artifact_without_output_ref_rejected(self):
        f = self.fixture(); f[3]["fake"] = SimpleNamespace(stage_id="SCENE_IR", blob_digest="2"*64)
        with self.assertRaises(self.error): self.inventory(f)

    def test_preseeded_first_stage_private_artifact_rejected(self):
        f = self.fixture(0); f[3]["fake"] = SimpleNamespace(stage_id="SOURCE", blob_digest="2"*64)
        with self.assertRaises(self.error): self.inventory(f)

    def test_missing_original_admission_rejected(self):
        f = self.fixture(); del f[3]["run-source"]
        with self.assertRaises(self.error): self.inventory(f)

    def test_retry_or_precompleted_attempt_rejected(self):
        f = self.fixture(); f[1]["stages"]["SOURCE"]["attempts"] *= 2
        with self.assertRaises(self.error): self.inventory(f)

    def test_real_private_supporting_artifacts_are_retained_and_bound(self):
        f = self.fixture(); original = self.inventory(f)
        f[3]["visual-private"] = SimpleNamespace(stage_id="VISUAL", blob_digest="2"*64)
        self.assertNotEqual(self.inventory(f), original)

    def test_scene_publication_does_not_change_upstream_identity(self):
        self.assertEqual(self.inventory(self.fixture(10)), self.inventory(self.fixture(11)))

    def test_changed_upstream_bytes_change_cut_identity(self):
        f = self.fixture(); original = self.inventory(f)
        f[3]["ANIMATION-output"].blob_digest = "2"*64
        self.assertNotEqual(self.inventory(f), original)

    def test_blocked_math_requires_four_acks_and_no_later_output(self):
        f = self.fixture(blocked=True)
        self.assertEqual(f[4], dict(ACKED=4, DEAD_LETTER=1))
        self.assertEqual(f[0]["SCENE_IR"], "PENDING")
        self.assertEqual(len(self.inventory(f)), 64)
        f[3]["fake"] = SimpleNamespace(stage_id="ANIMATION", blob_digest="2"*64)
        with self.assertRaises(self.error): self.inventory(f)

    def reply(self, segment="through-animation", blocked=False):
        return dict(enforcement="LINUX_RLIMIT", run_id="run", status_sha256="a"*64,
            stages=self.worker._split_expected(self.stages, 10 if segment == "through-animation" else 11, blocked),
            scene_ir=None, product_accepted=False, partition=dict(segment=segment,
                executed_stages=list(self.stages[:5] if blocked else self.stages[:10]) if segment == "through-animation" else ([] if blocked else ["SCENE_IR"]),
                input_prefix_sha256="b"*64, output_prefix_sha256="b"*64))

    def check_reply(self, row, segment="through-animation", blocked=False):
        return self.smoke._partition_reply(row, segment, self.stages, blocked, "run")

    def test_actual_partition_reply_preserves_original_restart_projection(self):
        row = self.reply("scene-ir")
        original, _ = self.check_reply(row, "scene-ir")
        self.assertEqual(original, {k: v for k, v in row.items() if k != "partition"})
        self.assertIn("partition", row)

    def test_missing_or_reordered_executions_rejected(self):
        for order in ([], list(reversed(self.stages[:10])), list(self.stages[:9])):
            row = self.reply(); row["partition"]["executed_stages"] = order
            with self.assertRaises(self.smoke.SmokeFailure): self.check_reply(row)

    def test_blocked_math_cannot_claim_scene_execution(self):
        row = self.reply("scene-ir", True)
        self.check_reply(row, "scene-ir", True)
        row["partition"]["executed_stages"] = ["SCENE_IR"]
        with self.assertRaises(self.smoke.SmokeFailure): self.check_reply(row, "scene-ir", True)

    def test_changed_prefix_at_scene_exit_rejected(self):
        row = self.reply("scene-ir"); row["partition"]["output_prefix_sha256"] = "c"*64
        with self.assertRaises(self.smoke.SmokeFailure): self.check_reply(row, "scene-ir")

    def test_unknown_reply_fields_and_malformed_identity_rejected(self):
        for key, value in (("private", "sentinel"), ("status_sha256", "sentinel"), ("run_id", "foreign")):
            row = self.reply(); row[key] = value
            with self.assertRaises(self.smoke.SmokeFailure): self.check_reply(row)

    def test_supervisor_timeout_or_output_overflow_cannot_pass(self):
        from apps.operator.process_supervision import ChildOutcome
        self.assertFalse(self.smoke._child_passed(ChildOutcome(0, b"{}", False)))

    def test_cpu_kill_or_nonzero_exit_cannot_pass(self):
        from apps.operator.process_supervision import ChildOutcome
        for code in (-9, -24, 1, 2):
            self.assertFalse(self.smoke._child_passed(ChildOutcome(code, b"{}", True)))

    def test_nonboolean_completion_and_boolean_exit_are_not_success(self):
        from apps.operator.process_supervision import ChildOutcome
        self.assertFalse(self.smoke._child_passed(ChildOutcome(False, b"{}", True)))
        self.assertFalse(self.smoke._child_passed(ChildOutcome(0, b"{}", 1)))

    def test_every_child_uses_unchanged_budget_and_direct_entry(self):
        from apps.operator.process_limits import PdfProcessBudget
        budget = PdfProcessBudget()
        self.assertEqual((budget.cpu_seconds, budget.wall_seconds, budget.memory_bytes), (30, 45, 1024**3))
        for module in (self.worker, self.smoke):
            source = Path(module.__file__).read_text()
            tree = ast.parse(source)
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Name) and n.func.id == "PdfProcessBudget"]
            self.assertEqual(len(calls), 1)
            self.assertTrue(all(not n.args and not n.keywords for n in calls))
            self.assertNotIn("runpy", source)
        self.assertIn('"apps/operator/scene_ir_worker_child.py"', Path(self.smoke.__file__).read_text())


if __name__ == "__main__": unittest.main()
