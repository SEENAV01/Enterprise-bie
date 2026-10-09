"""Synthetic private-receipt/privacy tests, NOT native paint execution evidence."""
import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.compiler import m1_safe_paint_diagnostics as diag

ROOT = Path(__file__).resolve().parents[2]
MARKER = "SYNTHETIC_PRIVATE_CREDENTIAL_TEXT_DO_NOT_EXPORT"


def process_receipt(outcome="FAILED", code=2, started=True):
    return {"command": ["synthetic-private-command", MARKER],
        "process": {"process": {"command": [MARKER], "cwd": "/private/synthetic-fixture",
            "exit_code": code, "stdout": MARKER, "stderr": MARKER,
            "duration_ms": 1234, "passed": outcome == "SUCCEEDED", "accepted": False},
            "outcome": outcome, "started": started, "stdout_bytes": 100, "stderr_bytes": 100,
            "accepted": False},
        "kernel_policy": {"kernel_enforced": True, "private_path": MARKER, "pid": 991}}


def resource_receipt():
    return {"schema": "bie.chromium-resource-boundary/1", "kind": "actual-paint",
        "command": [MARKER], "physical_memory_bytes": 2 * 1024**3, "swap_max": 0,
        "grants": [{"pid": 991, "browser_argv": [MARKER], "readonly_executable_mappings": [MARKER]}],
        "driver_stderr": MARKER, "driver_failure": {"diagnostic": MARKER},
        "browser_mappings": {"991": [{"private_source": MARKER}]},
        "entry_mapping_diagnostic": {"maps": MARKER}, "cleanup_failure": MARKER,
        "kernel": {"kernel_enforced": True, "private_path": MARKER},
        "security_policy_weakened": False, "accepted": False, "process_passed": False,
        "owned_processes_reaped": True, "owned_cgroup_removed": True, "failure": None,
        "memory_cgroup": {"memory_max": 2 * 1024**3, "swap_max": 0, "pids_max": 128,
            "memory_peak": 1024, "memory_events": {"oom": 0, "oom_kill": 0, "high": 2, "max": 3},
            "events": {"populated": 0}, "controller_configuration_changed": False,
            "host_supervisor_inside_workload": False}}


class SafePaintDiagnostics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="m1-safe-receipt-")
        self.root = Path(self.tmp.name).resolve()
        self.output = self.root / "paint-standard"
        self.output.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        path = self.output / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def capture(self, **changes):
        options = dict(family="cellular", preference="standard", frame_count=48,
                       duration_ms=2000, fps=24)
        options.update(changes)
        value = diag.capture_paint_diagnostic(self.root, **options)
        self.assertTrue(diag.is_safe_diagnostic(value))
        self.assertNotIn(MARKER, json.dumps(value))
        self.assertFalse(value["render_passed"])
        self.assertFalse(value["accepted"])
        self.assertFalse(value["product_accepted"])
        return value

    def test_valid_failed_outcome_actual_nested_exit_duration(self):
        self.write("PROCESS.json", process_receipt())
        value = self.capture()
        self.assertEqual(value["process"], {"receipt_state": "VALID", "outcome": "FAILED",
            "started": True, "process_passed": False, "exit_code": 2,
            "signal_number": "UNKNOWN", "duration_ms": 1234, "kernel_enforced": True})
        self.assertEqual(value["configured_timeout_s"], 192)

    def test_timeout_cancelled_and_output_limit_not_inferred(self):
        for outcome in ("TIMED_OUT", "CANCELLED", "OUTPUT_LIMIT"):
            with self.subTest(outcome=outcome):
                self.write("PROCESS.json", process_receipt(outcome, -15))
                value = self.capture()["process"]
                self.assertEqual(value["outcome"], outcome)
                self.assertEqual(value["signal_number"], 15)

    def test_negative_exit_signal_and_shell_128_plus_signal_distinct(self):
        for code, signal in ((-9, 9), (137, "UNKNOWN")):
            self.write("PROCESS.json", process_receipt(code=code))
            self.assertEqual(self.capture()["process"]["signal_number"], signal)

    def test_spawn_and_unstarted_cancel_sentinel_not_signal(self):
        for outcome in ("SPAWN_ERROR", "CANCELLED"):
            self.write("PROCESS.json", process_receipt(outcome, -1, False))
            p = self.capture()["process"]
            self.assertFalse(p["started"])
            self.assertEqual(p["signal_number"], "UNKNOWN")

    def test_unknown_outcome_not_guessed_from_passed_or_failure_labels(self):
        raw = process_receipt("not-an-enum")
        self.write("PROCESS.json", raw)
        value = self.capture()["process"]
        self.assertEqual(value["receipt_state"], "VALID")
        self.assertEqual(value["outcome"], "UNKNOWN")

    def test_missing_both_not_zero_or_false(self):
        value = self.capture()
        self.assertEqual(value["process"]["receipt_state"], "ABSENT")
        self.assertEqual(value["resource"]["receipt_state"], "ABSENT")
        self.assertTrue(all(v == "UNKNOWN" for v in value["resource"]["memory_events"].values()))

    def test_resource_only_early_failure_does_not_invent_exit(self):
        raw = resource_receipt(); raw["failure"] = "CHROMIUM_RESOURCE_DRIVER_RESULT"
        self.write("CHROMIUM_RESOURCE.json", raw)
        value = self.capture()
        self.assertEqual(value["process"]["exit_code"], "UNKNOWN")
        self.assertEqual(value["resource"]["failure_code"], "DRIVER_RESULT")

    def test_process_only_missing_resource_stays_unknown(self):
        self.write("PROCESS.json", process_receipt())
        self.assertEqual(self.capture()["resource"]["kernel_enforced"], "UNKNOWN")

    def test_corrupt_partial_and_invalid_utf8(self):
        path = self.output / "PROCESS.json"
        for raw in (b"{", b'{"process":', b"\xff"):
            path.write_bytes(raw)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_oversize_not_read(self):
        path = self.output / "PROCESS.json"
        path.write_bytes(b" " * (diag.MAX_INPUT_BYTES + 1))
        with patch.object(diag.os, "open", side_effect=AssertionError("must not open")):
            self.assertEqual(self.capture()["process"]["receipt_state"], "TOO_LARGE")

    def test_symlink_receipt_foreign_target_not_read(self):
        foreign = self.root / "foreign.json"; foreign.write_text(MARKER)
        path = self.output / "PROCESS.json"
        try:
            path.symlink_to(foreign)
        except OSError:
            # Platform-independent lstat rejection in addition to real links
            # where the host allows their creation. No skip or weakened gate.
            path.write_text(MARKER)
            with patch.object(Path, "is_symlink", return_value=True):
                self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")
        else:
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_linked_directory_and_foreign_relative_root_rejected(self):
        with patch.object(Path, "is_symlink", return_value=True):
            self.assertEqual(self.capture()["resource"]["receipt_state"], "INVALID")
        value = diag.capture_paint_diagnostic(Path("../foreign"), family="cellular", preference="standard",
                                             frame_count=48, duration_ms=2000, fps=24)
        self.assertEqual(value["process"]["receipt_state"], "INVALID")

    def test_nonregular_file_rejected(self):
        (self.output / "PROCESS.json").mkdir()
        self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_duplicate_keys_at_any_depth_rejected(self):
        path = self.output / "PROCESS.json"
        for text in ('{"process":{},"process":{}}', '{"process":{"outcome":"FAILED","outcome":"SUCCEEDED"}}'):
            path.write_text(text)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_nonfinite_float_and_overflow_rejected(self):
        path = self.output / "PROCESS.json"
        for text in ('{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}'):
            path.write_text(text)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_bool_exit_duration_and_byte_counts_rejected(self):
        for owner, key in (("inner", "exit_code"), ("inner", "duration_ms"), ("result", "stdout_bytes")):
            raw = process_receipt()
            (raw["process"]["process"] if owner == "inner" else raw["process"])[key] = True
            self.write("PROCESS.json", raw)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_exit_duration_and_counter_ranges_rejected(self):
        for key, bad in (("exit_code", -256), ("exit_code", 256), ("duration_ms", -1),
                         ("duration_ms", diag.MAX_DURATION_MS + 1)):
            raw = process_receipt(); raw["process"]["process"][key] = bad
            self.write("PROCESS.json", raw)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_invalid_nested_process_and_kernel_types_rejected(self):
        for key in ("process", "kernel_policy"):
            raw = process_receipt(); raw[key] = []
            self.write("PROCESS.json", raw)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")
        raw = process_receipt(); raw["kernel_policy"]["kernel_enforced"] = 1
        self.write("PROCESS.json", raw)
        self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_unknown_top_shape_or_extra_process_field_rejected(self):
        for raw in ([], {"outcome": "FAILED"}, dict(process_receipt(), private_extra=MARKER)):
            self.write("PROCESS.json", raw)
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_private_strings_commands_paths_pid_and_mapping_never_exported(self):
        self.write("PROCESS.json", process_receipt())
        self.write("CHROMIUM_RESOURCE.json", resource_receipt())
        value = self.capture()
        banned = {"command", "argv", "cwd", "stdout", "stderr", "driver_stderr", "driver_failure",
                  "pid", "grants", "browser_mappings", "entry_mapping_diagnostic", "cleanup_failure"}
        def keys(v):
            return set(v) | set().union(*(keys(x) for x in v.values() if type(x) is dict))
        self.assertFalse(keys(value) & banned)

    def test_command_injection_and_unused_private_data_has_no_effect(self):
        a = process_receipt(); self.write("PROCESS.json", a)
        before = self.capture()
        a["command"] = [MARKER, "never-executed-synthetic-command"]
        a["process"]["process"]["stdout"] = "synthetic source snippet " + MARKER
        self.write("PROCESS.json", a)
        self.assertEqual(self.capture(), before)

    def test_present_memory_counters_distinct_from_unknown(self):
        raw = resource_receipt(); raw["memory_cgroup"]["memory_events"]["oom_kill"] = 1
        self.write("CHROMIUM_RESOURCE.json", raw)
        value = self.capture()["resource"]
        self.assertEqual(value["memory_events"], {"oom": 0, "oom_kill": 1, "high": 2, "max": 3})
        self.assertEqual(value["failure_code"], "NONE_RECORDED")  # no inferred OOM verdict

    def test_bad_memory_counter_types_and_ranges_rejected(self):
        for bad in (True, -1, diag.MAX_COUNTER + 1, "0"):
            raw = resource_receipt(); raw["memory_cgroup"]["memory_events"]["oom"] = bad
            self.write("CHROMIUM_RESOURCE.json", raw)
            r = self.capture()["resource"]
            self.assertEqual(r["receipt_state"], "INVALID")
            self.assertEqual(r["memory_events"]["oom"], "UNKNOWN")

    def test_malformed_resource_kernel_group_and_boolean_rejected(self):
        for key, bad in (("kernel", []), ("memory_cgroup", []), ("owned_processes_reaped", 1)):
            raw = resource_receipt(); raw[key] = bad
            self.write("CHROMIUM_RESOURCE.json", raw)
            self.assertEqual(self.capture()["resource"]["receipt_state"], "INVALID")

    def test_resource_schema_kind_unknown_fields_and_wrong_ceilings_rejected(self):
        for key, bad in (("schema", "foreign"), ("kind", "renderer"), ("private_extra", MARKER),
                         ("physical_memory_bytes", 4 * 1024**3), ("swap_max", True)):
            raw = resource_receipt(); raw[key] = bad
            self.write("CHROMIUM_RESOURCE.json", raw)
            self.assertEqual(self.capture()["resource"]["receipt_state"], "INVALID")

    def test_exact_failure_code_only_no_prefix_or_private_suffix_matching(self):
        for text, expected in (("CHROMIUM_RESOURCE_HOST_DEADLINE", "HOST_DEADLINE"),
                ("MEMORY_EXHAUSTED", "MEMORY_EXHAUSTED"), ("CLEANUP_FAILED", "CLEANUP_FAILED"),
                ("CHROMIUM_RESOURCE_HOST_DEADLINE:" + MARKER, "UNCLASSIFIED"), (MARKER, "UNCLASSIFIED")):
            raw = resource_receipt(); raw["failure"] = text
            self.write("CHROMIUM_RESOURCE.json", raw)
            self.assertEqual(self.capture()["resource"]["failure_code"], expected)

    def test_frame_count_policy_requires_actual_duration_fps_consistency(self):
        for changes in (dict(frame_count=49), dict(frame_count=True), dict(fps=0), dict(duration_ms=-1)):
            value = self.capture(**changes)
            self.assertEqual(value["configured_timeout_s"], "UNKNOWN")
            self.assertEqual(value["planned_frame_count"], "UNKNOWN")

    def test_invalid_cli_enums_never_export_free_form_content(self):
        for changes in (dict(family=MARKER), dict(preference="../foreign")):
            value = self.capture(**changes)
            self.assertEqual(value["configured_timeout_s"], "UNKNOWN")

    def test_stat_race_and_permission_error_do_not_export_or_claim_success(self):
        self.write("PROCESS.json", process_receipt())
        with patch.object(diag, "signature", side_effect=lambda _: object()):
            self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")
        with patch.object(diag.os, "open", side_effect=PermissionError(MARKER)):
            self.assertEqual(self.capture()["process"]["receipt_state"], "UNKNOWN")

    def test_excessive_depth_and_nested_size_rejected(self):
        raw = {}; current = raw
        for _ in range(22): current["x"] = {}; current = current["x"]
        self.write("PROCESS.json", raw)
        self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")
        self.write("PROCESS.json", {"x": [0] * 2049})
        self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_output_closed_shape_no_counterfeit_receipt_or_acceptance(self):
        value = self.capture()
        for mutated in (dict(value, source=MARKER), dict(value, accepted=True),
                        dict(value, configured_timeout_s=True)):
            self.assertFalse(diag.is_safe_diagnostic(mutated))

    def test_invalid_receipt_state_cannot_claim_observed_fields(self):
        value = self.capture()
        value["process"]["exit_code"] = 0
        self.assertFalse(diag.is_safe_diagnostic(value))
        value = self.capture()
        value["resource"]["memory_events"]["oom"] = 0
        self.assertFalse(diag.is_safe_diagnostic(value))

    def test_counterfeit_signal_or_contradictory_outcome_rejected(self):
        self.write("PROCESS.json", process_receipt())
        value = self.capture()
        value["process"]["signal_number"] = 9
        self.assertFalse(diag.is_safe_diagnostic(value))
        raw = process_receipt(); raw["process"]["process"]["passed"] = True
        self.write("PROCESS.json", raw)
        self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")

    def test_stat_path_and_handle_times_each_stable_without_cross_api_ctime_assumption(self):
        info = (self.output / "PROCESS.json")
        self.write("PROCESS.json", process_receipt())
        before = info.lstat()
        fields = {name: getattr(before, name) for name in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")}
        changed = SimpleNamespace(**dict(fields, st_ctime_ns=fields["st_ctime_ns"] + 100))
        self.assertEqual(diag.file_identity(before), diag.file_identity(changed))
        self.assertNotEqual(diag.signature(before), diag.signature(changed))

    def test_total_json_node_budget_rejected(self):
        self.write("PROCESS.json", {"x": [[0] * 2048 for _ in range(5)]})
        self.assertEqual(self.capture()["process"]["receipt_state"], "INVALID")


class WrapperFailureRetention(unittest.TestCase):
    def block(self):
        tree = ast.parse((ROOT / "tests/compiler/run_motion_m1.py").read_text(encoding="utf-8"))
        candidates = [n for n in ast.walk(tree) if isinstance(n, ast.Try) and
            any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "produce_actual_paint"
                for statement in n.body for c in ast.walk(statement))]
        # The innermost exact call-site try, not the whole synthetic pipeline.
        node = min(candidates, key=lambda n: n.end_lineno - n.lineno)
        return compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "m1-call-site", "exec")

    def namespace(self, root, painter, collector=diag.capture_paint_diagnostic):
        return dict(produce_actual_paint=painter, capture_paint_diagnostic=collector,
            is_safe_diagnostic=diag.is_safe_diagnostic, root=root, project=root / "project-standard",
            output=root / "paint-standard", family="cellular", preference="standard",
            phase={"phase": "REAL_GENERATED_CONSUMER", "layer_frames": 48, "render_passed": False},
            raw={"duration_ms": 2000}, target=SimpleNamespace(fps=24), args=SimpleNamespace(browser=None), shutil=shutil)

    def test_failure_snapshot_before_cleanup_original_exception_identity_preserved(self):
        from bie.compiler.qa_common import CompilerQAError
        from tests.compiler.run_motion_m1 import safe_error
        original = CompilerQAError("ACTUAL_PAINT_EXECUTION_BLOCKED:" + MARKER)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            def painter(*args, **kwargs):
                output = root / "paint-standard"; output.mkdir()
                (output / "PROCESS.json").write_text(json.dumps(process_receipt()))
                raise original
            ns = self.namespace(root, painter)
            with self.assertRaises(CompilerQAError) as captured:
                exec(self.block(), ns)
            self.assertIs(captured.exception, original)
            self.assertEqual(ns["phase"]["paint_process_diagnostic"]["process"]["outcome"], "FAILED")
            self.assertEqual(safe_error(original), {"exception_class": "CompilerQAError",
                                                   "safe_code": "ACTUAL_PAINT_EXECUTION_BLOCKED"})
            self.assertTrue((root / "paint-standard/PROCESS.json").exists())
        self.assertFalse(root.exists())

    def test_sanitizer_exception_cannot_mask_original_failure(self):
        original = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED:" + MARKER)
        def painter(*args, **kwargs): raise original
        def collector(*args, **kwargs): raise RuntimeError(MARKER)
        with tempfile.TemporaryDirectory() as temp:
            ns = self.namespace(Path(temp).resolve(), painter, collector)
            with self.assertRaises(ValueError) as captured: exec(self.block(), ns)
            self.assertIs(captured.exception, original)
            self.assertNotIn("paint_process_diagnostic", ns["phase"])

    def test_counterfeit_diagnostic_not_forwarded_and_failure_not_downgraded(self):
        original = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED")
        def painter(*args, **kwargs): raise original
        with tempfile.TemporaryDirectory() as temp:
            ns = self.namespace(Path(temp).resolve(), painter, lambda *a, **k: {"private": MARKER})
            with self.assertRaises(ValueError): exec(self.block(), ns)
            self.assertNotIn("paint_process_diagnostic", ns["phase"])
            self.assertFalse(ns["phase"]["render_passed"])

    def test_success_call_and_existing_phase_unchanged_no_diagnostic_read(self):
        witness = object()
        def collector(*args, **kwargs): raise AssertionError("success must not collect")
        with tempfile.TemporaryDirectory() as temp:
            ns = self.namespace(Path(temp).resolve(), lambda *a, **k: witness, collector)
            original = deepcopy(ns["phase"])
            exec(self.block(), ns)
            self.assertIs(ns["witness"], witness)
            self.assertEqual(ns["phase"], original)

    def test_owned_supervisor_and_workflow_require_failure_gate_unchanged(self):
        owner = (ROOT / "tests/compiler/run_m1_owned_render.py").read_text()
        self.assertLess(owner.index('result["proof"]=receipt'), owner.index('"CHILD_GATE"'))
        workflow = (ROOT / ".github/workflows/task036-motion-capability.yml").read_text()
        self.assertIn("needs: [verify, task035-affected, native-extra]", workflow)
        self.assertIn("family: [quantitative, chronology, cellular, cellular_reduced]", workflow)
        self.assertIn("preference: [standard, reduced]", workflow)
        self.assertNotIn("continue-on-error", workflow)

    def test_new_file_owned_once_native_extra_no_original_inventory_overlap(self):
        from tests.compiler.run_m1_tests import inventory
        selected, inherited = inventory()
        name = "tests/compiler/test_m1_safe_paint_diagnostics.py"
        self.assertEqual(selected["new"].count(name), 1)
        self.assertNotIn(name, inherited)
        self.assertNotIn(name, selected["native-extra"] + selected["safety"])


if __name__ == "__main__":
    unittest.main()
