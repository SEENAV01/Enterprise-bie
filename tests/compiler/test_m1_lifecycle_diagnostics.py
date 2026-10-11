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


if __name__ == "__main__": unittest.main()
