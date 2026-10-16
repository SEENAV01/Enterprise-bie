"""Synthetic runner/privacy contracts, not execution of inherited H4 fixtures."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.compiler import run_m1_tests as runner

SECRET = "PRIVATE_TOKEN_book_content_C:/private/input argv stderr"


class LifecycleDiagnosticControls(unittest.TestCase):
    def fixture(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "tests/compiler/test_comp_h4_005.py"
            path.parent.mkdir(parents=True)
            (root / "tests/__init__.py").write_text("")
            (root / "tests/compiler/__init__.py").write_text("")
            path.write_text(source, encoding="utf-8")
            # Real package loading in a separate synthetic root, never native mocks.
            previous = {k: v for k, v in sys.modules.items() if k == "tests" or k.startswith("tests.")}
            for key in previous: sys.modules.pop(key)
            try:
                row = runner.run_file("tests/compiler/test_comp_h4_005.py", set(), root)
            finally:
                for key in list(sys.modules):
                    if key == "tests" or key.startswith("tests."): sys.modules.pop(key)
                sys.modules.update(previous)
            self.assertNotIn(SECRET, json.dumps(row))
            self.assertNotIn(directory, json.dumps(row))
            return row

    def lifecycle(self, expression):
        return self.fixture("import unittest\nclass Example(unittest.TestCase):\n"
            "    @classmethod\n    def setUpClass(cls): raise AssertionError(" + expression + ")\n"
            "    def test_one(self): pass\n    def test_two(self): pass\n")

    def payload(self, **changes):
        value = {"schema_version": "bie.layout-repair-run.v1", "status": "ENVIRONMENT_OR_VALIDATOR_BLOCKED",
            "source_published": False, "local_fit_passed": False,
            "attempts": [{"source_gate_passed": True, "local_fit_passed": False, "codes": ["LAYOUT_BRIDGE_FAILED"]}],
            "runtime_block": SECRET, "error": SECRET, "stdout": SECRET, "stderr": SECRET,
            "target": {"private": SECRET}, "command": SECRET}
        value.update(changes)
        return repr(value)  # Only synthetic fixture construction, never private receipt formatting.

    def observation(self, expression):
        row = self.lifecycle(expression)
        self.assertFalse(row["passed"])
        self.assertEqual((row["selected"], row["executed"], row["errors"]), (2, 0, 1))
        self.assertEqual(row["collection_errors"], 0)
        self.assertEqual(row["failed_methods"], ["M1_TEST_LIFECYCLE_ERROR"])
        self.assertEqual(len(row["failure_diagnostics"]), 1)
        return row["failure_diagnostics"][0]

    def test_setup_failure_preserves_zero_execution_and_error(self):
        diagnostic = self.observation(repr(SECRET))
        self.assertEqual(diagnostic["exception_class"], "AssertionError")
        self.assertEqual(diagnostic["lifecycle"], "LIFECYCLE")
        self.assertIsNone(diagnostic["repair_observation"])

    def test_fixed_repair_status_and_codes_only(self):
        diagnostic = self.observation(self.payload())
        self.assertEqual(diagnostic["schema"], runner.FAILURE_DIAGNOSTIC_SCHEMA)
        value = diagnostic["repair_observation"]
        self.assertFalse(value["source_published"])
        self.assertTrue(value["attempts_available"])
        self.assertEqual(value["attempts"][0]["codes"], ["LAYOUT_BRIDGE_FAILED"])
        self.assertTrue(value["attempts"][0]["source_gate_passed"])

    def test_private_codes_are_unclassified(self):
        value = self.observation(self.payload(attempts=[{"codes": [SECRET, 7, True, {}]}]))["repair_observation"]
        self.assertEqual(value["attempts"][0]["codes"], ["UNCLASSIFIED"] * 4)

    def test_absence_not_false_or_zero(self):
        value = self.observation(self.payload(source_published=None, local_fit_passed=0, attempts=None))["repair_observation"]
        self.assertIsNone(value["source_published"])
        self.assertIsNone(value["local_fit_passed"])
        self.assertFalse(value["attempts_available"])

    def test_invalid_status_not_exported(self):
        value = self.observation(self.payload(status=SECRET))["repair_observation"]
        self.assertEqual(value["status"], "UNKNOWN")

    def test_wrong_schema_has_no_repair_observation(self):
        self.assertIsNone(self.observation(self.payload(schema_version=SECRET))["repair_observation"])

    def test_boolean_boundaries(self):
        value = self.observation(self.payload(source_published=1, local_fit_passed="true",
            attempts=[{"source_gate_passed": 1, "local_fit_passed": "true", "codes": True}]))["repair_observation"]
        self.assertIsNone(value["source_published"])
        self.assertIsNone(value["attempts"][0]["source_gate_passed"])
        self.assertFalse(value["attempts"][0]["codes_available"])

    def test_oversized_attempt_inventory_not_read(self):
        value = self.observation(self.payload(attempts=[{}] * 33))["repair_observation"]
        self.assertFalse(value["attempts_available"])
        self.assertEqual(value["attempts"], [])

    def test_oversized_codes_not_read(self):
        value = self.observation(self.payload(attempts=[{"codes": [SECRET] * 33}]))["repair_observation"]
        self.assertFalse(value["attempts"][0]["codes_available"])
        self.assertEqual(value["attempts"][0]["codes"], [])

    def test_invalid_attempt_row_unavailable(self):
        value = self.observation(self.payload(attempts=[True]))["repair_observation"]
        self.assertFalse(value["attempts_available"])

    def test_success_behavior_and_identity_unchanged(self):
        row = self.fixture("import unittest\nclass Example(unittest.TestCase):\n    def test_one(self): pass\n")
        self.assertTrue(row["passed"])
        self.assertEqual((row["selected"], row["executed"], row["errors"]), (1, 1, 0))
        self.assertEqual(row["logical_identities"], ["tests/compiler/test_comp_h4_005.py::Example.test_one"])
        self.assertEqual(row["failure_diagnostics"], [])

    def test_method_failure_does_not_inflate_count(self):
        row = self.fixture("import unittest\nclass Example(unittest.TestCase):\n    def test_one(self): self.fail(" + repr(SECRET) + ")\n")
        self.assertEqual((row["executed"], row["failures"], row["errors"]), (1, 1, 0))
        self.assertEqual(row["failure_diagnostics"][0]["lifecycle"], "TEST")

    def test_subtest_failure_observed_once(self):
        row = self.fixture("import unittest\nclass Example(unittest.TestCase):\n    def test_one(self):\n        with self.subTest(private=" + repr(SECRET) + "): self.fail(" + repr(SECRET) + ")\n")
        self.assertEqual((row["executed"], row["failures"]), (1, 1))
        self.assertEqual(len(row["failure_diagnostics"]), 1)

    def test_observer_failure_cannot_mask_original_verdict(self):
        with patch.object(runner, "failure_diagnostic", side_effect=RuntimeError(SECRET)):
            diagnostic = self.observation(repr(SECRET))
        self.assertFalse(diagnostic["observation_complete"])

    def test_no_exception_formatting_or_unknown_object_traversal(self):
        class PrivateError(Exception):
            def __str__(self): raise AssertionError("formatted")
            def __repr__(self): raise AssertionError("formatted")
        diagnostic = runner.failure_diagnostic((PrivateError, PrivateError(object()), None), runner.ROOT, "TEST")
        self.assertEqual(diagnostic["exception_class"], "OTHER")
        self.assertIsNone(diagnostic["repair_observation"])

    def test_hostile_exception_metaclass_cannot_export_name(self):
        class PrivateMeta(type):
            def __getattribute__(cls, key):
                if key == "__name__": raise AssertionError("name access")
                return super().__getattribute__(key)
        class PrivateError(Exception, metaclass=PrivateMeta): pass
        diagnostic = runner.failure_diagnostic((PrivateError, PrivateError(SECRET), None), runner.ROOT, "TEST")
        self.assertEqual(diagnostic["exception_class"], "OTHER")
        self.assertTrue(diagnostic["observation_complete"])
        self.assertNotIn(SECRET, json.dumps(diagnostic))

    def test_failed_diagnostic_sink_cannot_terminate_error_or_failure(self):
        class BrokenSink:
            def append(self, value): raise RuntimeError(SECRET)
        for failure in (False, True):
            result = runner.SafeFailureResult(io.StringIO(), True, 0)
            result.safe_diagnostics = BrokenSink()
            case = unittest.FunctionTestCase(lambda: None)
            error = (AssertionError, AssertionError(SECRET), None)
            if failure: result.addFailure(case, error)
            else: result.addError(case, error)
            self.assertEqual(len(result.failures) + len(result.errors), 1)
            self.assertFalse(result.wasSuccessful())

    def test_lifecycle_schema_rejects_non_plain_values(self):
        class PrivateString(str):
            def __hash__(self): raise AssertionError("must not hash")
        value = runner.failure_diagnostic((ValueError, ValueError(SECRET), None), runner.ROOT, PrivateString("TEST"))
        self.assertEqual(value["lifecycle"], "UNKNOWN")
        self.assertNotIn(SECRET, json.dumps(value))

    def test_inventory_retains_214_original_files_and_assigns_once(self):
        before = sys.path[:]
        lanes, inherited = runner.inventory()
        path = "tests/compiler/test_m1_lifecycle_diagnostics.py"
        self.assertEqual(len(lanes["native-extra"]), 214)
        self.assertEqual(lanes["new"].count(path), 1)
        self.assertNotIn(path, lanes["native-extra"])
        self.assertNotIn(path, lanes["safety"])
        self.assertNotIn(path, inherited)
        self.assertEqual(sys.path, before)


class CollectionDiagnosticPrivacyControls(unittest.TestCase):
    def check(self, error):
        result = runner.collection_diagnostic(error, runner.ROOT)
        self.assertEqual(set(result), {"class", "code", "location", "package_aware"})
        self.assertNotIn(SECRET, json.dumps(result))
        return result

    def test_changing_metaclass_name_never_read(self):
        calls = []
        class ChangingMeta(type):
            def __getattribute__(cls, key):
                if key == "__name__":
                    calls.append(key)
                    return "ValueError" if len(calls) == 1 else SECRET
                return super().__getattribute__(key)
        class ForeignError(Exception, metaclass=ChangingMeta): pass
        self.assertEqual(self.check(ForeignError())["class"], "OTHER")
        self.assertEqual(calls, [])

    def test_raising_metaclass_name_contained(self):
        class RaisingMeta(type):
            def __getattribute__(cls, key):
                if key == "__name__": raise RuntimeError(SECRET)
                return super().__getattribute__(key)
        class ForeignError(Exception, metaclass=RaisingMeta): pass
        self.assertEqual(self.check(ForeignError())["class"], "OTHER")

    def test_collection_subclass_stateful_string_never_formatted(self):
        calls = []
        class ForeignError(runner.CollectionError):
            def __str__(self):
                calls.append(True)
                return "M1_COLLECTION_EMPTY_SUITE" if len(calls) == 1 else SECRET
        result = self.check(ForeignError())
        self.assertEqual((result["class"], result["code"]), ("OTHER", "M1_COLLECTION_EXCEPTION"))
        self.assertEqual(calls, [])

    def test_exact_collection_code_and_trusted_import_preserved(self):
        self.assertEqual(self.check(runner.CollectionError("M1_COLLECTION_EMPTY_SUITE"))["code"], "M1_COLLECTION_EMPTY_SUITE")
        for error, label in ((ImportError(SECRET), "ImportError"), (ModuleNotFoundError(SECRET), "ModuleNotFoundError")):
            result = self.check(error)
            self.assertEqual((result["class"], result["code"]), (label, "M1_COLLECTION_IMPORT_ERROR"))

    def test_malformed_and_private_exact_collection_args_rejected(self):
        for args in ((), (SECRET,), (True,), (1,), ({"private": SECRET},), ("M1_COLLECTION_EMPTY_SUITE", SECRET)):
            with self.subTest(boundary=len(args)):
                self.assertEqual(self.check(runner.CollectionError(*args))["code"], "M1_COLLECTION_EXCEPTION")

    def test_string_subclass_is_not_code_authority(self):
        class PrivateString(str):
            def __hash__(self): raise AssertionError("must not hash")
        self.assertEqual(self.check(runner.CollectionError(PrivateString("M1_COLLECTION_EMPTY_SUITE")))["code"], "M1_COLLECTION_EXCEPTION")

    def test_foreign_traceback_getter_never_read(self):
        class ForeignError(Exception):
            @property
            def __traceback__(self): raise AssertionError("foreign getter")
        self.assertIsNone(self.check(ForeignError(SECRET))["location"])

    def test_unregistered_identifier_filename_is_not_exported(self):
        filename = runner.ROOT / "tests/compiler/PRIVATE_SYNTHETIC_FILENAME.py"
        try:
            exec(compile("raise ValueError('synthetic')", str(filename), "exec"), {})
        except ValueError as error:
            result = self.check(error)
        self.assertIsNone(result["location"])
        self.assertNotIn("PRIVATE_SYNTHETIC_FILENAME", json.dumps(result))

    def test_fixed_runner_boundary_and_actual_line_are_preserved(self):
        filename = runner.ROOT / "tests/compiler/run_m1_tests.py"
        try:
            exec(compile("\nraise ValueError('synthetic')", str(filename), "exec"), {})
        except ValueError as error:
            result = self.check(error)
        self.assertEqual(result["location"], {"file": "tests/compiler/run_m1_tests.py", "line": 2})

    def test_formatter_failure_preserves_collection_error_and_closed_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(runner, "collection_diagnostic", side_effect=RuntimeError(SECRET)):
                row = runner.run_file("missing.py", set(), root)
            self.assertFalse(row["passed"])
            self.assertEqual((row["selected"], row["executed"], row["collection_errors"]), (0, 0, 1))
            self.assertEqual(row["collector_error"]["code"], "M1_COLLECTION_EXCEPTION")
            self.assertNotIn(SECRET, json.dumps(row))


if __name__ == "__main__": unittest.main()
