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


def typed_return(outcome="FAILED", code=2, started=True, *, private=MARKER):
    from bie.compiler.build_common import ProcessReceipt
    from bie.compiler.render_process import RenderProcessResult
    p = ProcessReceipt((private,), private, code, private, private, 1234, outcome == "SUCCEEDED")
    result = RenderProcessResult(p, outcome, started, 100, 100)
    boundary = resource_receipt()
    boundary["process_passed"] = p.passed
    return result, {"kernel_enforced": True, "chromium_resource_boundary": boundary}


class TypedReturnPrivacy(unittest.TestCase):
    def project(self, value):
        safe = diag.project_typed_return(value)
        self.assertTrue(diag.is_safe_typed_observation(safe))
        text = json.dumps(safe)
        self.assertNotIn(MARKER, text)
        self.assertLess(len(text), 2048)
        self.assertFalse(safe["accepted"])
        self.assertFalse(safe["render_passed"])
        self.assertFalse(safe["product_accepted"])
        return safe

    def test_frozen_canonical_process_types_and_actual_scalar_values(self):
        value = typed_return()
        self.assertTrue(type(value[0]).__dataclass_params__.frozen)
        self.assertTrue(type(value[0].process).__dataclass_params__.frozen)
        safe = self.project(value)
        self.assertEqual(safe["process"], {"availability": "VALID", "outcome": "FAILED",
            "started": True, "process_passed": False, "exit_code": 2,
            "signal_number": "UNKNOWN", "duration_ms": 1234})
        self.assertFalse(safe["call_origin_verified"])
        self.assertEqual(safe["provenance"], "UNVERIFIED_TEST_RETURN")

    def test_success_remains_observation_not_a_render_or_acceptance_verdict(self):
        safe = self.project(typed_return("SUCCEEDED", 0))
        self.assertTrue(safe["process"]["process_passed"])
        self.assertFalse(safe["render_passed"])

    def test_typed_timeout_cancel_output_limit_and_spawn_are_not_guessed(self):
        for outcome, code, started in (("TIMED_OUT", -15, True), ("CANCELLED", -1, False),
                ("OUTPUT_LIMIT", -9, True), ("SPAWN_ERROR", -1, False)):
            with self.subTest(outcome=outcome):
                p = self.project(typed_return(outcome, code, started))["process"]
                self.assertEqual(p["outcome"], outcome)
                self.assertEqual(p["exit_code"], code)
                self.assertEqual(p["started"], started)

    def test_posix_negative_exit_not_shell_code_or_unstarted_sentinel(self):
        for outcome, code, started, expected in (("FAILED", -9, True, 9),
                ("FAILED", 137, True, "UNKNOWN"), ("SPAWN_ERROR", -1, False, "UNKNOWN")):
            self.assertEqual(self.project(typed_return(outcome, code, started))["process"]["signal_number"], expected)

    def test_unknown_outcome_does_not_read_or_infer_private_failure_text(self):
        safe = self.project(typed_return("NOT_A_KNOWN_OUTCOME"))
        self.assertEqual(safe["process"]["outcome"], "UNKNOWN")
        self.assertNotIn("failure_code", safe["resource"])
        self.assertEqual(self.project(typed_return(MARKER * 10000))["process"]["availability"], "INVALID")

    def test_oversized_private_stdout_stderr_do_not_change_or_leak_observation(self):
        from dataclasses import replace
        base, kernel = typed_return()
        huge = MARKER * (8 * 1024**2 // len(MARKER) + 1)
        changed = replace(base, process=replace(base.process, stdout=huge, stderr=huge),
                          stdout_bytes=2**62, stderr_bytes=2**62)
        self.assertEqual(self.project((changed, kernel)), self.project((base, kernel)))

    def test_private_attributes_are_never_accessed_even_for_validation(self):
        from bie.compiler.build_common import ProcessReceipt
        from bie.compiler.render_process import RenderProcessResult
        value = typed_return()
        old_p, old_r = ProcessReceipt.__getattribute__, RenderProcessResult.__getattribute__
        def read_p(instance, name):
            if name in {"stdout", "stderr", "command", "cwd"}:
                raise AssertionError("PRIVATE_ATTRIBUTE_ACCESS")
            return old_p(instance, name)
        def read_r(instance, name):
            if name in {"stdout_bytes", "stderr_bytes"}:
                raise AssertionError("PRIVATE_ATTRIBUTE_ACCESS")
            return old_r(instance, name)
        with patch.object(ProcessReceipt, "__getattribute__", read_p), patch.object(RenderProcessResult, "__getattribute__", read_r):
            self.assertEqual(self.project(value)["process"]["availability"], "VALID")

    def test_private_values_and_unknown_nested_objects_are_not_serialized_or_traversed(self):
        from dataclasses import replace
        class Forbidden:
            def __repr__(self): raise AssertionError("PRIVATE_REPR")
            def __str__(self): raise AssertionError("PRIVATE_STR")
            def __iter__(self): raise AssertionError("PRIVATE_TRAVERSAL")
        base, kernel = typed_return(private=Forbidden())
        boundary = kernel["chromium_resource_boundary"]
        for key in ("command", "grants", "driver_failure", "driver_stderr", "kernel", "browser_mappings",
                "entry_mapping_diagnostic", "failure", "cleanup_failure"):
            boundary[key] = Forbidden()
        boundary["memory_cgroup"]["events"] = Forbidden()
        changed = replace(base, stdout_bytes=Forbidden(), stderr_bytes=Forbidden())
        self.assertEqual(self.project((changed, kernel))["resource"]["availability"], "VALID")

    def test_no_receipt_file_read_or_broad_serializer_in_typed_projection(self):
        value = typed_return()
        with patch.object(Path, "open", side_effect=AssertionError("NO_FILE_READ")), \
                patch.object(diag, "read_receipt", side_effect=AssertionError("NO_FILE_READ")), \
                patch("dataclasses.asdict", side_effect=AssertionError("NO_BROAD_SERIALIZER")), \
                patch("builtins.repr", side_effect=AssertionError("NO_PRIVATE_REPR")):
            self.assertEqual(diag.project_typed_return(value)["process"]["availability"], "VALID")

    def test_absent_resource_and_missing_counters_are_unknown_not_zero(self):
        base, kernel = typed_return()
        del kernel["chromium_resource_boundary"]
        safe = self.project((base, kernel))["resource"]
        self.assertEqual(safe["availability"], "UNKNOWN")
        self.assertTrue(safe["kernel_enforced"])
        self.assertTrue(all(v == "UNKNOWN" for v in safe["memory_events"].values()))
        base, kernel = typed_return()
        del kernel["chromium_resource_boundary"]["memory_cgroup"]["memory_events"]["oom"]
        self.assertEqual(self.project((base, kernel))["resource"]["memory_events"],
                         {"oom": "UNKNOWN", "oom_kill": 0, "high": 2, "max": 3})

    def test_present_counters_and_enforcement_cleanup_flags_are_exact(self):
        base, kernel = typed_return()
        kernel["chromium_resource_boundary"]["memory_cgroup"]["memory_events"]["oom_kill"] = 1
        safe = self.project((base, kernel))["resource"]
        self.assertEqual(safe["memory_events"], {"oom": 0, "oom_kill": 1, "high": 2, "max": 3})
        self.assertEqual(safe["memory_peak_bytes"], 1024)
        self.assertTrue(safe["kernel_enforced"])
        self.assertFalse(safe["security_policy_weakened"])
        self.assertTrue(safe["owned_processes_reaped"])
        self.assertTrue(safe["owned_cgroup_removed"])

    def test_boolean_as_integer_negative_overflow_and_invalid_process_fields(self):
        from dataclasses import replace
        for key, bad in (("exit_code", True), ("exit_code", -256), ("exit_code", 256),
                ("duration_ms", True), ("duration_ms", -1), ("duration_ms", diag.MAX_DURATION_MS + 1),
                ("passed", 0), ("accepted", True)):
            with self.subTest(field=key):
                base, kernel = typed_return()
                p = self.project((replace(base, process=replace(base.process, **{key: bad})), kernel))["process"]
                self.assertEqual(p["availability"], "INVALID")
                self.assertEqual(p["exit_code"], "UNKNOWN")

    def test_wrong_result_receipt_types_and_subclasses_are_not_introspected(self):
        from dataclasses import replace
        from bie.compiler.build_common import ProcessReceipt
        class Foreign(ProcessReceipt): pass
        base, kernel = typed_return()
        foreign = Foreign((), "", 2, "", "", 1234, False)
        for bad in (object(), replace(base, process=object()), replace(base, process=foreign)):
            self.assertEqual(self.project((bad, kernel))["observation_stage"], "PROCESS_TYPE")

    def test_wrong_return_shape_does_not_traverse_arbitrary_objects(self):
        class Foreign:
            def __iter__(self): raise AssertionError("NO_TRAVERSAL")
        for value in (None, Foreign(), [], (object(),), (object(), object(), object())):
            safe = self.project(value)
            self.assertEqual(safe["observation_stage"], "RETURN_SHAPE")
            self.assertEqual(safe["process"]["exit_code"], "UNKNOWN")

    def test_contradictory_process_outcome_started_and_passed_rejected(self):
        from dataclasses import replace
        for outcome, code, started in (("SUCCEEDED", 2, True), ("FAILED", 0, True),
                ("FAILED", 2, False), ("TIMED_OUT", -1, False), ("SPAWN_ERROR", -1, True)):
            self.assertEqual(self.project(typed_return(outcome, code, started))["process"]["availability"], "INVALID")
        base, kernel = typed_return()
        self.assertEqual(self.project((replace(base, started=1), kernel))["process"]["availability"], "INVALID")
        self.assertEqual(self.project((replace(base, process=replace(base.process, passed=True)), kernel))["process"]["availability"], "INVALID")

    def test_resource_wrong_schema_kind_shape_or_flags_rejected_without_false_leaf_claim(self):
        for key, bad in (("schema", MARKER), ("kind", MARKER), ("memory_cgroup", None),
                ("memory_cgroup", []), ("process_passed", 0), ("accepted", True), ("owned_cgroup_removed", 1)):
            with self.subTest(field=key):
                base, kernel = typed_return(); kernel["chromium_resource_boundary"][key] = bad
                safe = self.project((base, kernel))
                self.assertEqual(safe["resource"]["availability"], "INVALID")
                self.assertEqual(safe["observation_stage"], "RESOURCE_FIELDS")
                self.assertEqual(safe["resource"]["memory_peak_bytes"], "UNKNOWN")
        base, kernel = typed_return(); kernel["chromium_resource_boundary"] = None
        self.assertEqual(self.project((base, kernel))["resource"]["availability"], "INVALID")

    def test_resource_counters_reject_bool_negative_overflow_strings(self):
        for bad in (True, -1, diag.MAX_COUNTER + 1, "0", float("nan")):
            base, kernel = typed_return()
            kernel["chromium_resource_boundary"]["memory_cgroup"]["memory_events"]["oom"] = bad
            safe = self.project((base, kernel))
            self.assertEqual(safe["resource"]["availability"], "INVALID")
            self.assertEqual(safe["resource"]["memory_events"]["oom"], "UNKNOWN")

    def test_wrong_resource_ceilings_peak_or_duplicate_pass_status_rejected(self):
        for key, bad in (("memory_max", 4 * 1024**3), ("swap_max", 1), ("pids_max", True),
                ("memory_peak", -1), ("memory_peak", 1024**4 + 1), ("memory_events", [])):
            base, kernel = typed_return()
            kernel["chromium_resource_boundary"]["memory_cgroup"][key] = bad
            self.assertEqual(self.project((base, kernel))["resource"]["availability"], "INVALID")
        base, kernel = typed_return(); kernel["chromium_resource_boundary"]["process_passed"] = True
        self.assertEqual(self.project((base, kernel))["resource"]["availability"], "INVALID")

    def test_dict_subclass_and_counterfeit_receipt_not_traversed(self):
        class Foreign(dict):
            def get(self, *args): raise AssertionError("NO_FOREIGN_LOOKUP")
            def __getitem__(self, key): raise AssertionError("NO_FOREIGN_LOOKUP")
        base, kernel = typed_return()
        self.assertEqual(self.project((base, Foreign(kernel)))["resource"]["availability"], "INVALID")
        kernel["chromium_resource_boundary"] = Foreign()
        self.assertEqual(self.project((base, kernel))["resource"]["availability"], "INVALID")

    def test_closed_output_rejects_extras_acceptance_unknown_stage_and_counterfeits(self):
        safe = self.project(typed_return())
        for changed in (dict(safe, private=MARKER), dict(safe, accepted=True),
                dict(safe, observation_stage=MARKER), dict(safe, call_origin_verified=True)):
            self.assertFalse(diag.is_safe_typed_observation(changed))
        changed = deepcopy(safe); changed["resource"]["memory_events"]["foreign"] = 0
        self.assertFalse(diag.is_safe_typed_observation(changed))
        changed = deepcopy(safe); changed["process"]["duration_ms"] = "UNKNOWN"
        self.assertFalse(diag.is_safe_typed_observation(changed))
        changed = diag.empty_typed("CALL_RAISED"); changed["process"]["exit_code"] = 0
        self.assertFalse(diag.is_safe_typed_observation(changed))
        changed = deepcopy(safe); changed["resource"]["availability"] = "UNKNOWN"
        self.assertFalse(diag.is_safe_typed_observation(changed))
        changed = deepcopy(safe); changed["observation_stage"] = "RESOURCE_FIELDS"
        self.assertFalse(diag.is_safe_typed_observation(changed))

    def test_malformed_observation_stage_and_origin_flags_cannot_be_retained_or_exported(self):
        safe = diag.empty_typed(MARKER, MARKER)
        self.assertTrue(diag.is_safe_typed_observation(safe))
        self.assertNotIn(MARKER, json.dumps(safe))
        self.assertEqual(safe["observation_stage"], "OBSERVER_ERROR")
        self.assertFalse(safe["call_origin_verified"])
        observer = diag.TypedPaintObserver(verified=MARKER)
        self.assertIs(observer._verified, False)
        self.assertNotIn(MARKER, json.dumps(observer.snapshot()))

    def test_counterfeit_scalar_subclasses_cannot_escape_closed_schema(self):
        class Foreign(str):
            def __eq__(self, other): return True
            __hash__ = str.__hash__
        safe = self.project(typed_return())
        for key in ("schema", "phase", "capture_point", "provenance", "observation_stage"):
            changed = deepcopy(safe); changed[key] = Foreign(MARKER)
            self.assertFalse(diag.is_safe_typed_observation(changed))
        for section, key in (("process", "exit_code"), ("process", "started"),
                ("process", "outcome"), ("resource", "memory_peak_bytes"),
                ("resource", "owned_cgroup_removed")):
            changed = deepcopy(safe); changed[section][key] = Foreign(MARKER)
            self.assertFalse(diag.is_safe_typed_observation(changed))
        changed = deepcopy(safe); changed["resource"]["memory_events"]["oom"] = Foreign(MARKER)
        self.assertFalse(diag.is_safe_typed_observation(changed))


class TypedObserverNoninterference(unittest.TestCase):
    def test_delegate_exactly_once_arguments_and_return_object_identity_preserved(self):
        observer = diag.TypedPaintObserver()
        positional, keyword, returned = object(), object(), typed_return()
        seen = []
        def original(*args, **kwargs):
            seen.append((args, kwargs))
            return returned
        actual = observer.delegate(original, positional, workspace=keyword, timeout_s=192)
        self.assertIs(actual, returned)
        self.assertEqual(len(seen), 1)
        self.assertIs(seen[0][0][0], positional)
        self.assertIs(seen[0][1]["workspace"], keyword)
        self.assertEqual(seen[0][1]["timeout_s"], 192)
        self.assertEqual(observer.snapshot()["process"]["exit_code"], 2)

    def test_native_exception_object_and_cleanup_order_preserved_without_message_access(self):
        class PrivateError(ValueError):
            def __str__(self): raise AssertionError("NO_MESSAGE_ACCESS")
            def __repr__(self): raise AssertionError("NO_MESSAGE_ACCESS")
        original_error = PrivateError()
        observer = diag.TypedPaintObserver(); steps = []
        def original(*args, **kwargs):
            try:
                steps.append("call")
                raise original_error
            finally:
                steps.append("native_cleanup")
        try:
            observer.delegate(original)
        except PrivateError as caught:
            self.assertIs(caught, original_error)
            steps.append("painter_catch")
        self.assertEqual(steps, ["call", "native_cleanup", "painter_catch"])
        safe = observer.snapshot()
        self.assertEqual(safe["observation_stage"], "CALL_RAISED")
        self.assertEqual(safe["process"]["exit_code"], "UNKNOWN")
        self.assertTrue(all(v == "UNKNOWN" for v in safe["resource"]["memory_events"].values()))

    def test_projector_error_and_baseexception_cannot_change_return(self):
        returned = typed_return()
        for error in (RuntimeError(MARKER), KeyboardInterrupt()):
            observer = diag.TypedPaintObserver()
            with patch.object(diag, "project_typed_return", side_effect=error):
                self.assertIs(observer.delegate(lambda: returned), returned)
            self.assertEqual(observer.snapshot()["observation_stage"], "OBSERVER_ERROR")
            self.assertNotIn(MARKER, json.dumps(observer.snapshot()))

    def test_recording_failure_does_not_mask_original_exception(self):
        original_error = ValueError(MARKER)
        observer = diag.TypedPaintObserver()
        def original(): raise original_error
        with patch.object(diag, "empty_typed", side_effect=RuntimeError("OBSERVER_ONLY")):
            try:
                observer.delegate(original)
            except ValueError as caught:
                self.assertIs(caught, original_error)

    def test_result_and_private_payload_not_retained_in_observer_state(self):
        import gc
        import weakref
        observer = diag.TypedPaintObserver()
        returned = typed_return()
        ref = weakref.ref(returned[0]); inner_ref = weakref.ref(returned[0].process)
        observer.delegate(lambda: returned)
        del returned
        gc.collect()
        self.assertIsNone(ref())
        self.assertIsNone(inner_ref())
        self.assertNotIn(MARKER, json.dumps(observer.snapshot()))
        self.assertEqual(set(observer.__dict__), {"_verified", "_called", "_multiple", "_safe"})

    def test_not_called_and_multiple_calls_are_unknown_not_a_chosen_success(self):
        observer = diag.TypedPaintObserver()
        self.assertEqual(observer.snapshot()["observation_stage"], "NOT_CALLED")
        seen = []
        def original():
            seen.append(1)
            return typed_return()
        observer.delegate(original); observer.delegate(original)
        self.assertEqual(len(seen), 2)
        self.assertEqual(observer.snapshot()["observation_stage"], "MULTIPLE_CALLS")
        self.assertEqual(observer.snapshot()["process"]["outcome"], "UNKNOWN")

    def test_snapshot_is_closed_detached_safe_record_not_a_sidecar_reference(self):
        observer = diag.TypedPaintObserver()
        observer.delegate(typed_return)
        first = observer.snapshot()
        first["process"]["exit_code"] = 0; first["resource"]["memory_events"]["oom"] = 99
        self.assertEqual(observer.snapshot()["process"]["exit_code"], 2)
        self.assertEqual(observer.snapshot()["resource"]["memory_events"]["oom"], 0)
        observer._safe["private"] = MARKER
        self.assertEqual(observer.snapshot()["observation_stage"], "OBSERVER_ERROR")

    def test_canonical_binding_origin_and_scope_restoration_without_worker_execution(self):
        worker, original = diag.canonical_paint_binding()
        with diag.observe_paint_process() as observer:
            self.assertIsNot(worker.run_chromium_isolated, original)
            self.assertTrue(observer.snapshot()["call_origin_verified"])
            self.assertEqual(observer.snapshot()["observation_stage"], "NOT_CALLED")
        self.assertIs(worker.run_chromium_isolated, original)

    def test_binding_unavailable_does_not_change_painter_execution_or_exception(self):
        original_error = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED")
        seen = []
        with patch.object(diag, "canonical_paint_binding", side_effect=RuntimeError(MARKER)):
            try:
                with diag.observe_paint_process() as observer:
                    seen.append(1)
                    raise original_error
            except ValueError as caught:
                self.assertIs(caught, original_error)
        self.assertEqual(seen, [1])
        self.assertEqual(observer.snapshot()["observation_stage"], "BINDING_UNAVAILABLE")

    def test_observer_construction_failure_still_executes_unmodified_painter_scope(self):
        original_error = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED")
        seen = []
        with patch.object(diag, "TypedPaintObserver", side_effect=RuntimeError(MARKER)):
            try:
                with diag.observe_paint_process() as observer:
                    self.assertIsNone(observer)
                    seen.append(1)
                    raise original_error
            except ValueError as caught:
                self.assertIs(caught, original_error)
        self.assertEqual(seen, [1])

    def test_foreign_binding_is_not_wrapped_or_certified_and_original_remains(self):
        worker, original = diag.canonical_paint_binding()
        def foreign(*args, **kwargs): return object()
        with patch.object(worker, "run_chromium_isolated", foreign):
            with diag.observe_paint_process() as observer:
                self.assertIs(worker.run_chromium_isolated, foreign)
                self.assertFalse(observer.snapshot()["call_origin_verified"])
                self.assertEqual(observer.snapshot()["observation_stage"], "BINDING_UNAVAILABLE")
        self.assertIs(worker.run_chromium_isolated, original)

    def test_scope_delegates_once_returns_original_and_restores_after_painter_failure(self):
        worker, actual = diag.canonical_paint_binding()
        returned = typed_return(); seen = []
        def original(*args, **kwargs):
            seen.append((args, kwargs))
            return returned
        error = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED")
        with patch.object(diag, "canonical_paint_binding", return_value=(worker, original)):
            try:
                with diag.observe_paint_process() as observer:
                    from bie.compiler.chromium_resource_worker import run_chromium_isolated
                    self.assertIs(run_chromium_isolated("private-call", kind="actual-paint"), returned)
                    raise error
            except ValueError as caught:
                self.assertIs(caught, error)
            finally:
                self.assertIs(worker.run_chromium_isolated, original)
                worker.run_chromium_isolated = actual
        self.assertEqual(len(seen), 1)
        self.assertEqual(observer.snapshot()["process"]["outcome"], "FAILED")


class TypedWrapperRetention(unittest.TestCase):
    def block(self):
        tree = ast.parse((ROOT / "tests/compiler/run_motion_m1.py").read_text(encoding="utf-8"))
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.With) and
                    any(isinstance(i.context_expr, ast.Call) and isinstance(i.context_expr.func, ast.Name)
                        and i.context_expr.func.id == "observe_paint_process" for i in n.items))
        return compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "typed-call-site", "exec")

    def namespace(self, root, painter):
        ns = WrapperFailureRetention.namespace(self, root, painter)
        ns.update(observe_paint_process=diag.observe_paint_process,
                  is_safe_typed_observation=diag.is_safe_typed_observation)
        return ns

    def test_typed_observation_survives_original_failure_and_temporary_cleanup(self):
        worker, actual = diag.canonical_paint_binding()
        returned = typed_return(); error = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED:" + MARKER)
        def original(*args, **kwargs): return returned
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            def painter(*args, **kwargs):
                from bie.compiler.chromium_resource_worker import run_chromium_isolated
                self.assertIs(run_chromium_isolated("synthetic-private", workspace=root), returned)
                raise error
            ns = self.namespace(root, painter)
            with patch.object(diag, "canonical_paint_binding", return_value=(worker, original)):
                try:
                    with self.assertRaises(ValueError) as caught: exec(self.block(), ns)
                    self.assertIs(caught.exception, error)
                    self.assertEqual(ns["phase"]["paint_process_typed_observation"]["process"]["exit_code"], 2)
                    self.assertEqual(ns["phase"]["paint_process_diagnostic"]["process"]["receipt_state"], "ABSENT")
                finally:
                    worker.run_chromium_isolated = actual
        self.assertFalse(root.exists())
        self.assertNotIn(MARKER, json.dumps(ns["phase"]))
        self.assertFalse(ns["phase"]["render_passed"])

    def test_existing_too_large_invalid_states_not_reinterpreted_by_typed_return(self):
        worker, actual = diag.canonical_paint_binding()
        returned = typed_return(); error = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); output = root / "paint-standard"; output.mkdir()
            (output / "PROCESS.json").write_bytes(b" " * (diag.MAX_INPUT_BYTES + 1))
            (output / "CHROMIUM_RESOURCE.json").write_text('{"bad":true}')
            def painter(*args, **kwargs):
                from bie.compiler.chromium_resource_worker import run_chromium_isolated
                run_chromium_isolated("synthetic-private")
                raise error
            ns = self.namespace(root, painter)
            with patch.object(diag, "canonical_paint_binding", return_value=(worker, lambda *a, **k: returned)):
                try:
                    with self.assertRaises(ValueError): exec(self.block(), ns)
                finally:
                    worker.run_chromium_isolated = actual
            raw = ns["phase"]["paint_process_diagnostic"]
            self.assertEqual(raw["process"]["receipt_state"], "TOO_LARGE")
            self.assertEqual(raw["resource"]["receipt_state"], "INVALID")
            self.assertEqual(raw["resource"]["memory_events"]["oom"], "UNKNOWN")
            self.assertEqual(ns["phase"]["paint_process_typed_observation"]["process"]["outcome"], "FAILED")

    def test_snapshot_failure_and_counterfeit_do_not_mask_painter_exception(self):
        from contextlib import contextmanager
        error = ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED")
        def painter(*args, **kwargs): raise error
        for mode in ("ERROR", "COUNTERFEIT", "INTERRUPT"):
            class Broken:
                def snapshot(self):
                    if mode == "COUNTERFEIT": return {"private": MARKER}
                    if mode == "INTERRUPT": raise KeyboardInterrupt()
                    raise RuntimeError(MARKER)
            @contextmanager
            def scope(): yield Broken()
            with tempfile.TemporaryDirectory() as temp:
                ns = self.namespace(Path(temp).resolve(), painter)
                ns["observe_paint_process"] = scope
                with self.assertRaises(ValueError) as caught: exec(self.block(), ns)
                self.assertIs(caught.exception, error)
                self.assertNotIn("paint_process_typed_observation", ns["phase"])

    def test_success_phase_and_existing_receipt_behavior_unchanged(self):
        witness = object()
        with tempfile.TemporaryDirectory() as temp:
            ns = self.namespace(Path(temp).resolve(), lambda *a, **k: witness)
            before = deepcopy(ns["phase"])
            exec(self.block(), ns)
            self.assertIs(ns["witness"], witness)
            self.assertEqual(ns["phase"], before)


if __name__ == "__main__":
    unittest.main()
