"""Separate CI-R1 diagnostic safety tests; not part of the 129/4,972 lanes."""
from copy import deepcopy
from hashlib import sha1
import importlib.util
import json
from pathlib import Path
import re
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SUPPORT = Path(__file__).with_name("diagnose_post_dir.py")
spec = importlib.util.spec_from_file_location("task035_ci_r1_diagnostics", SUPPORT)
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)
SECRET = "PRIVATE_DIAGNOSTIC_SENTINEL"


def blob_identity(relative):
    # Git's committed Python files use LF. Ignore only checkout CRLF translation,
    # not path, content, tests, assertions or inventory changes.
    data = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def workflow_steps():
    text = (ROOT / ".github/workflows/animation-producer.yml").read_text(encoding="utf-8")
    return text, {match.group(1): match.group(2) for match in re.finditer(
        r"^      - name: ([^\n]+)\n(.*?)(?=^      - |\Z)", text, re.M | re.S)}


def valid_child_receipt():
    return {
        "observation_valid": True, "outcome": "PASS", "tests": 1,
        "failures": 0, "errors": 0, "skips": 0, "diagnostics": [],
        "canonical_module_origins": {
            "checked_locations": 1, "foreign_locations": 0, "valid": True,
        },
    }


class DiagnosticSafety(unittest.TestCase):
    def test_exception_classes_codes_and_messages_are_finite_allowlisted(self):
        unknown = type(SECRET, (Exception,), {})(SECRET)
        result = diagnostics.safe_exception(unknown, ROOT)
        self.assertEqual(result["chain"][0]["class"], "OTHER_EXCEPTION")
        self.assertEqual(result["chain"][0]["codes"], ["UNCLASSIFIED"])
        self.assertNotIn(SECRET, json.dumps(result))
        known = RuntimeError("HOST_TOOLCHAIN_UNAVAILABLE: " + SECRET)
        result = diagnostics.safe_exception(known, ROOT)
        self.assertEqual(result["chain"][0]["codes"], ["HOST_TOOLCHAIN_UNAVAILABLE"])
        self.assertNotIn(SECRET, json.dumps(result))

    def test_missing_module_names_are_allowlisted_not_exception_arguments(self):
        for name, expected in (("matplotlib", "matplotlib"), (SECRET, None)):
            with self.subTest(allowed=expected is not None):
                result = diagnostics.safe_exception(ModuleNotFoundError(SECRET, name=name), ROOT)
                self.assertEqual(result["chain"][0]["missing_module"], expected)
                self.assertNotIn(SECRET, json.dumps(result))

    def test_stack_frames_never_export_source_or_unapproved_paths(self):
        for relative in ("bie/compiler/host_toolchain.py", "bie/" + SECRET + ".py"):
            with self.subTest(canonical=relative in diagnostics.BLOBS):
                try:
                    exec(compile("raise RuntimeError('" + SECRET + "')", str(ROOT / relative), "exec"), {})
                except RuntimeError as exc:
                    result = diagnostics.safe_exception(exc, ROOT)
                encoded = json.dumps(result)
                self.assertNotIn(SECRET, encoded)
                self.assertNotIn(str(ROOT), encoded)
                frames = result["chain"][0]["canonical_frames"]
                if relative in diagnostics.BLOBS:
                    self.assertTrue(any(frame["path"] == relative for frame in frames))
                else:
                    self.assertEqual(frames, [])
                self.assertTrue(all("source" not in frame and "locals" not in frame for frame in frames))

    def test_dependency_versions_reject_paths_messages_and_arbitrary_suffixes(self):
        for value in ("3.13.5", "3.10.8", "2.9.0.post0"):
            self.assertEqual(diagnostics.safe_version(value), value)
        for value in (SECRET, "1" + SECRET, "1.0.0+" + SECRET,
                      str(ROOT / SECRET), "3.13.5\n" + SECRET):
            with self.subTest(kind=type(value).__name__):
                self.assertEqual(diagnostics.safe_version(value), "UNKNOWN")

    def test_import_origin_requires_selected_root_and_at_least_one_location(self):
        local = types.ModuleType("bie")
        local.__file__ = str(ROOT / "bie/__init__.py")
        foreign = types.ModuleType("bie.foreign")
        foreign.__file__ = str(ROOT.parent / "foreign-ci-root/bie/foreign.py")
        with patch.dict(sys.modules, {"bie": local}, clear=True):
            self.assertTrue(diagnostics.canonical_origins(ROOT)["valid"])
        with patch.dict(sys.modules, {"bie": local, "bie.foreign": foreign}, clear=True):
            result = diagnostics.canonical_origins(ROOT)
            self.assertFalse(result["valid"])
            self.assertEqual(result["foreign_locations"], 1)
            self.assertNotIn("foreign-ci-root", json.dumps(result))
        with patch.dict(sys.modules, {}, clear=True):
            self.assertFalse(diagnostics.canonical_origins(ROOT)["valid"])

    def test_malformed_or_inconsistent_child_receipts_cannot_claim_pass(self):
        selection = diagnostics.METHODS[0]
        good = valid_child_receipt()
        self.assertTrue(diagnostics.validate_child_receipt(good, selection))
        invalid = [None, [], {}, {"observation_valid": True, "outcome": "PASS"}]
        for key, value in (("observation_valid", "true"), ("tests", True),
                           ("tests", 0), ("errors", 1), ("skips", 1),
                           ("outcome", "SUCCESS"), ("private_response", SECRET)):
            changed = deepcopy(good)
            changed[key] = value
            invalid.append(changed)
        changed = deepcopy(good)
        changed["canonical_module_origins"]["foreign_locations"] = 1
        invalid.append(changed)
        failed = deepcopy(good)
        failed.update(outcome="FAIL", errors=1, diagnostics=[{
            "kind": "ERROR", "method": selection,
            "exception": {"chain": [{
                "class": "CompilerQAError", "codes": ["HOST_TOOLCHAIN_UNAVAILABLE"],
                "missing_module": None,
                "canonical_frames": [{"path": "bie/compiler/host_toolchain.py", "line": 59}],
            }]},
        }])
        self.assertTrue(diagnostics.validate_child_receipt(failed, selection))
        for target, key, value in (("entry", "message", SECRET),
                                   ("entry", "codes", [SECRET]),
                                   ("entry", "class", SECRET),
                                   ("entry", "missing_module", SECRET),
                                   ("frame", "path", str(ROOT / SECRET)),
                                   ("frame", "source", SECRET),
                                   ("frame", "line", True)):
            changed = deepcopy(failed)
            entry = changed["diagnostics"][0]["exception"]["chain"][0]
            location = entry if target == "entry" else entry["canonical_frames"][0]
            location[key] = value
            invalid.append(changed)
        for value in invalid:
            with self.subTest(payload_type=type(value).__name__):
                self.assertFalse(diagnostics.validate_child_receipt(value, selection))

    def test_private_verbose_buffer_remains_bounded(self):
        buffer = diagnostics.PrivateVerboseBuffer()
        try:
            self.assertEqual(buffer.write(SECRET * 10000), len(SECRET) * 10000)
            self.assertLessEqual(len(buffer.getvalue()), 64 * 1024)
            self.assertEqual(buffer.write(SECRET), len(SECRET))
            self.assertLessEqual(len(buffer.getvalue()), 64 * 1024)
        finally:
            buffer.close()


class OriginalGatePreservation(unittest.TestCase):
    def test_original_129_and_4972_test_selection_remains_unchanged(self):
        expected = {
            "tools/run_task029_tests.py": "da56e97f97109e4efdf0fdf832d49591755ad5b5",
            "tools/run_task030_tests.py": "9f7b6d35578fb27d6eab860080eda3c8fb5cffce",
            "tools/run_task031_tests.py": "ca402ad2a161d51857d8e08936e467882a5bc46b",
            "tools/run_task032_tests.py": "69d1754619cd2cf7d940c689e279cc022b4d23eb",
            "tools/run_task033_tests.py": "333b433da7ae9396e04d94b0a28016d7283dab1d",
            "tools/run_task034_tests.py": "ade2fd031b3bb08588edc7f285ef532d7fb643b0",
            "tools/run_task035_tests.py": "6765852995760f629e702f9bda24aaf3600f1c53",
            "tests/productization/animation/test_animation_producer.py": "ce6fb2c5bb38af9dc6ea94a7336526493d6dfe1e",
            "tests/productization/animation/test_animation_recovery.py": "f841c5f195f196e54346c8e32dcd3acca6144c7a",
            "tests/post_dir/test_canonical_adoption.py": "6801194add84de0f752a18aaac86c8c4005bebce",
        }
        for relative, identity in expected.items():
            with self.subTest(file=relative):
                self.assertEqual(blob_identity(relative), identity)

    def test_original_dependency_setup_is_retained_without_hypothesized_fix(self):
        text, steps = workflow_steps()
        self.assertEqual(steps["Install unchanged approved API DI and Section16 profiles"],
            "        run: |\n"
            "          python -m pip install -e '.[document-intelligence,document-intelligence-layout,api,api-test]'\n"
            "          python -m pip install -r requirements-qa-section16-validation.txt\n"
            "          python -m pip check\n")
        # R1's before observation must retain its original provisioning even
        # when the separately authorized R2 repair follows that observation.
        before_name = "Diagnose unchanged Post-DIR tests without changing provisioning"
        self.assertEqual(text.count("      - name: " + before_name + "\n"), 1)
        before_end = text.index(steps[before_name]) + len(steps[before_name])
        before = text[:before_end]
        self.assertEqual(before.count("pip install"), 2)
        self.assertNotIn("setup_ci_environment.sh", before)
        self.assertNotIn("requirements-comp-h3.txt", before)
        self.assertIn("python-version: '3.13.5'", text)
        self.assertIn("runs-on: ubuntu-24.04", text)

    def test_every_original_gate_is_mandatory_with_unchanged_command(self):
        text, steps = workflow_steps()
        gates = {
            "Governed current Visual Animation synchronization grounding QA and recovery":
                'python -B tools/run_task035_tests.py --lane new --output "$RUNNER_TEMP/task035-evidence/new.json"',
            "Complete inherited producers native Animation QA and store preservation":
                'python -B tools/run_task035_tests.py --lane affected --output "$RUNNER_TEMP/task035-evidence/affected.json"',
            "Preserved Task029 three-stage process": "smoke_bie_di_knowledge.py|task029-process.json",
            "Preserved Task030 five-stage process and historical Math block": "smoke_bie_pr_reasoning.py|task030-process.json",
            "Preserved Task031 Math applicability and six-stage process": "smoke_bie_math_evidence.py|task031-process.json",
            "Preserved Task032 seven-stage process and Director compatibility": "smoke_bie_pedagogy.py|task032-process.json",
            "Preserved Task033 eight-stage native Director and review boundary": "smoke_bie_director.py|task033-process.json",
            "Preserved Task034 nine-stage multiple-domain Visual and restart": "smoke_bie_visual.py|task034-process.json",
            "Actual ten-stage multiple-domain Animation planning and second-process restart": "smoke_bie_animation.py|process.json",
            "Full canonical source preservation": "audit_canonical.py|source-preservation.json",
        }
        positions = []
        for name, command in gates.items():
            if "|" in command:
                script, receipt = command.split("|")
                command = f'python -B scripts/{script} --output "$RUNNER_TEMP/task035-evidence/{receipt}"'
            with self.subTest(gate=name):
                self.assertEqual(steps[name], "        run: " + command + "\n")
                self.assertEqual(text.count("      - name: " + name + "\n"), 1)
                positions.append(text.index("      - name: " + name + "\n"))
        self.assertEqual(positions, sorted(positions))

    def test_process_and_workflow_resource_limits_are_unchanged(self):
        expected = {
            "scripts/smoke_bie_animation.py": "587b77b1822320ddbbad27a85904caae8833f2a2",
            "apps/operator/process_supervision.py": "a2a6986be82f9f461f508450f45f58a13c8b851d",
            "apps/operator/process_limits.py": "58e339bafcf2cf307974efe7d51639ae2163d846",
        }
        for relative, identity in expected.items():
            with self.subTest(file=relative):
                self.assertEqual(blob_identity(relative), identity)
        text, _ = workflow_steps()
        self.assertEqual(re.findall(r"^\s*timeout-minutes: (.+)$", text, re.M), ["45"])
        self.assertNotIn("continue-on-error", text)
        self.assertNotIn("|| true", text)

    def test_diagnostic_tests_are_separate_and_do_not_replace_required_gates(self):
        text, steps = workflow_steps()
        separate = "Task035 CI-R1 diagnostic safety controls only"
        self.assertEqual(steps[separate],
            "        run: python -I -B -m unittest discover -s tests/productization/animation -p test_ci_r1_diagnostics.py -v\n")
        runner = (ROOT / "tools/run_task035_tests.py").read_text(encoding="utf-8")
        self.assertNotIn("test_ci_r1_diagnostics.py", runner)
        self.assertNotIn("diagnose_post_dir.py", runner)
        self.assertLess(text.index("Diagnose unchanged Post-DIR tests"),
                        text.index("Complete inherited producers native Animation QA"))
        self.assertEqual(set(diagnostics.METHODS), {
            "test_actual_cross_section_source_publication",
            "test_actual_dsl_output_compiles_to_source",
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
