"""Separate CI-R2 provisioning/receipt controls, never product-lane counts.

Synthetic receipts exercise fail-closed validation only. They do not replace
the unchanged Post-DIR tests, real compiler calls or hosted after gate.
"""
from copy import deepcopy
from hashlib import sha1
import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
SUPPORT = Path(__file__).with_name("verify_post_dir_provisioning.py")
spec = importlib.util.spec_from_file_location("task035_ci_r2_provisioning", SUPPORT)
provisioning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provisioning)
SECRET = "PRIVATE_CI_R2_SENTINEL"
HEAD = "2" * 40
IDENTITY = "1" * 64


def valid_runtime():
    """Validator input only: not a toolchain observation or uploaded receipt."""
    return {
        "os": "Linux", "os_id": "ubuntu", "os_version": "24.04",
        "python": {"version": "3.13.5", "executable_sha256": IDENTITY,
                   "role": "SAME_INTERPRETER_AS_MANDATORY_WORKFLOW_STEPS",
                   "path_python_matches": True, "isolated": True},
        "profile_blobs": dict(provisioning.PROFILE_BLOBS), "requirements_identical": True,
        "packages": {module: {"distribution": distribution, "expected_version": version,
                               "distribution_version": version, "importable": True,
                               "origin_in_interpreter": True, "origin_sha256": IDENTITY}
                     for module, (distribution, version) in provisioning.APPROVED_PACKAGES.items()},
        "pip_check_passed": True,
        "node": {"version": "22.16.0", "executable_sha256": IDENTITY,
                 "path_executable_matches": True, "tsc_version": "5.8.3",
                 "typescript_version": "5.8.3", "typescript_library_sha256": IDENTITY,
                 "library_resolution_matches": True, "sanitized_environment_used": True,
                 "parser_library_loaded": True},
        "provisioning_phase": "approved_after", "provisioning_changed": True,
    }


def valid_comparison():
    """Six synthetic validation rows; real workflow probes are not mocked."""
    diagnostics = provisioning.diagnostics
    probes = []
    for root in ("candidate", "base"):
        for selection in (*diagnostics.METHODS, "whole_file"):
            probes.append({
                "root": root, "selection": selection, "observation_valid": True,
                "outcome": "PASS", "tests": 22 if selection == "whole_file" else 1,
                "failures": 0, "errors": 0, "skips": 0, "diagnostics": [],
                "canonical_module_origins": {
                    "checked_locations": 1, "foreign_locations": 0, "valid": True,
                },
            })
    return {
        "schema": "bie.task035.post-dir-diagnostic/1", "scope": "SYNTHETIC_TEST_DIAGNOSTICS_ONLY",
        "original_run_traceback_recovered": False, "base": diagnostics.BASE, "candidate": HEAD,
        "unchanged_blobs": {path: {"base_blob": identity, "candidate_blob": identity,
                                    "working_blob": identity, "equal": True}
                            for path, identity in diagnostics.BLOBS.items()},
        "environment": {
            "os": "Linux", "os_id": "ubuntu", "os_version": "24.04", "python_version": "3.13.5",
            "python_executable_role": "SAME_INTERPRETER_AS_MANDATORY_WORKFLOW_STEPS",
            "python_executable_sha256": IDENTITY, "isolated_python": True,
            "dependencies": {module: {"import_spec_available": True, "distribution_version": version}
                             for module, (_, version) in provisioning.APPROVED_PACKAGES.items()},
            "node": {"available": True, "version": "22.16.0"},
            "tsc": {"available": True, "version": "5.8.3"},
            "canonical_typescript_library_present": True,
            "canonical_python_prefix_present": False, "canonical_node_prefix_present": False,
            "unshare_available": True, "bubblewrap_available": False,
            "provisioning_changed": True, "provisioning_phase": "approved_after",
        },
        "probes": probes, "mandatory_regression_substituted": False,
        "product_accepted": False, "diagnostics_complete": True, "test_outcome": "PASS",
    }


def valid_after():
    return {
        "schema": "bie.task035.post-dir-after/1", "scope": "SYNTHETIC_TEST_PROVISIONING_GATE_ONLY",
        "phase": "approved_after", "base": provisioning.diagnostics.BASE, "candidate": HEAD,
        "runtime": valid_runtime(), "comparison": valid_comparison(), "after_gate_passed": True,
        "mandatory_regression_substituted": False, "product_accepted": False,
    }


def workflow_steps():
    text = (ROOT / ".github/workflows/animation-producer.yml").read_text(encoding="utf-8")
    return text, {match.group(1): match.group(2) for match in re.finditer(
        r"^      - name: ([^\n]+)\n(.*?)(?=^      - |\Z)", text, re.M | re.S)}


class StrictAfterReceipt(unittest.TestCase):
    def test_complete_six_probe_comparison_and_bound_runtime_are_required(self):
        value = valid_after()
        self.assertTrue(provisioning.validate_runtime(value["runtime"]))
        self.assertTrue(provisioning.validate_comparison(value["comparison"], HEAD))
        self.assertTrue(provisioning.validate_after_receipt(value, HEAD))
        self.assertEqual([(row["root"], row["tests"]) for row in value["comparison"]["probes"]],
                         [("candidate", 1), ("candidate", 1), ("candidate", 22),
                          ("base", 1), ("base", 1), ("base", 22)])

    def test_missing_duplicate_extra_or_foreign_probe_cannot_pass(self):
        good = valid_comparison()
        variants = []
        for probes in ([], good["probes"][:-1], good["probes"] + [good["probes"][0]],
                       good["probes"][:-1] + [good["probes"][0]]):
            value = deepcopy(good)
            value["probes"] = deepcopy(probes)
            variants.append(value)
        for key, content in (("root", "foreign"), ("selection", "unapproved_test"),
                             ("selection", []), ("root", {})):
            value = deepcopy(good)
            value["probes"][0][key] = content
            variants.append(value)
        for value in variants:
            with self.subTest(probe_count=len(value["probes"])):
                self.assertFalse(provisioning.validate_comparison(value, HEAD))

    def test_independent_methods_and_whole_file_reject_wrong_or_boolean_counts(self):
        for index in range(6):
            for key, value in (("tests", 0), ("tests", 2), ("tests", True),
                               ("failures", False), ("errors", False), ("skips", False)):
                with self.subTest(probe=index, field=key, count=value):
                    receipt = valid_comparison()
                    receipt["probes"][index][key] = value
                    self.assertFalse(provisioning.validate_comparison(receipt, HEAD))

    def test_collector_completion_and_labeled_pass_never_hide_failures_errors_or_skips(self):
        for field in ("failures", "errors", "skips"):
            for outcome in ("PASS", "FAIL", "UNKNOWN"):
                with self.subTest(field=field, outcome=outcome):
                    receipt = valid_comparison()
                    receipt["probes"][0].update({field: 1, "outcome": outcome})
                    self.assertFalse(provisioning.validate_comparison(receipt, HEAD))
        receipt = valid_comparison()
        receipt["probes"][0].update(outcome="FAIL", errors=1, diagnostics=[{
            "kind": "ERROR", "method": provisioning.diagnostics.METHODS[0],
            "exception": {"chain": [{"class": "CompilerQAError", "codes": ["HOST_TOOLCHAIN_UNAVAILABLE"],
                                     "missing_module": None, "canonical_frames": [
                                         {"path": "bie/compiler/host_toolchain.py", "line": 59}]}]},
        }])
        child = {key: value for key, value in receipt["probes"][0].items() if key not in {"root", "selection"}}
        self.assertTrue(provisioning.diagnostics.validate_child_receipt(child, provisioning.diagnostics.METHODS[0]))
        self.assertFalse(provisioning.validate_comparison(receipt, HEAD))

    def test_complete_diagnostics_and_zero_foreign_imports_are_mandatory(self):
        for index in range(6):
            for key, value in (("checked_locations", 0), ("checked_locations", True),
                               ("foreign_locations", 1), ("valid", False)):
                with self.subTest(probe=index, field=key):
                    receipt = valid_comparison()
                    receipt["probes"][index]["canonical_module_origins"][key] = value
                    self.assertFalse(provisioning.validate_comparison(receipt, HEAD))
            receipt = valid_comparison()
            receipt["probes"][index]["observation_valid"] = False
            self.assertFalse(provisioning.validate_comparison(receipt, HEAD))
        for key, value in (("diagnostics_complete", False), ("test_outcome", "UNKNOWN")):
            receipt = valid_comparison()
            receipt[key] = value
            self.assertFalse(provisioning.validate_comparison(receipt, HEAD))

    def test_exact_base_candidate_and_inherited_blob_identities_are_bound(self):
        for key in ("base", "candidate"):
            receipt = valid_comparison()
            receipt[key] = "3" * 40
            self.assertFalse(provisioning.validate_comparison(receipt, HEAD))
        self.assertFalse(provisioning.validate_comparison(valid_comparison(), "UNKNOWN"))
        for path in provisioning.diagnostics.BLOBS:
            for key in ("base_blob", "candidate_blob", "working_blob", "equal"):
                with self.subTest(file=path, identity=key):
                    receipt = valid_comparison()
                    receipt["unchanged_blobs"][path][key] = False if key == "equal" else "3" * 40
                    self.assertFalse(provisioning.validate_comparison(receipt, HEAD))

    def test_after_phase_cannot_claim_original_unchanged_provisioning(self):
        for key, value in (("provisioning_changed", False), ("provisioning_phase", "original")):
            receipt = valid_comparison()
            receipt["environment"][key] = value
            self.assertFalse(provisioning.validate_comparison(receipt, HEAD))
        self.assertEqual(provisioning.diagnostics.collect.__defaults__, ("original",))
        self.assertEqual(provisioning.diagnostics.environment_observation.__defaults__, ("original",))
        with self.assertRaises(ValueError):
            provisioning.diagnostics.environment_observation("unapproved")
        with self.assertRaises(ValueError):
            provisioning.diagnostics.collect("unapproved")

    def test_after_gate_does_not_promote_completion_acceptance_or_wrong_interpreter(self):
        for key, value in (("after_gate_passed", False), ("after_gate_passed", 1),
                           ("mandatory_regression_substituted", True), ("product_accepted", True),
                           ("phase", "original"), ("schema", "UNKNOWN"), ("candidate", "3" * 40)):
            with self.subTest(field=key):
                receipt = valid_after()
                receipt[key] = value
                self.assertFalse(provisioning.validate_after_receipt(receipt, HEAD))
        receipt = valid_after()
        receipt["runtime"]["python"]["executable_sha256"] = "3" * 64
        self.assertFalse(provisioning.validate_after_receipt(receipt, HEAD))
        for receipt in (None, [], {}, {"after_gate_passed": True}):
            self.assertFalse(provisioning.validate_after_receipt(receipt, HEAD))

    def test_private_or_unknown_fields_are_rejected_at_every_receipt_layer(self):
        selectors = (
            lambda value: value,
            lambda value: value["runtime"],
            lambda value: value["runtime"]["python"],
            lambda value: value["runtime"]["node"],
            lambda value: value["runtime"]["packages"]["matplotlib"],
            lambda value: value["comparison"],
            lambda value: value["comparison"]["environment"],
            lambda value: value["comparison"]["probes"][0],
            lambda value: value["comparison"]["probes"][0]["canonical_module_origins"],
        )
        for index, select in enumerate(selectors):
            with self.subTest(layer=index):
                receipt = valid_after()
                select(receipt)["private_response"] = SECRET
                self.assertFalse(provisioning.validate_after_receipt(receipt, HEAD))
        encoded = json.dumps(valid_after())
        self.assertNotIn(SECRET, encoded)
        self.assertNotIn(str(ROOT), encoded)


class RuntimeValidation(unittest.TestCase):
    def test_observed_version_map_is_bound_to_unchanged_approved_profiles(self):
        self.assertEqual(provisioning.approved_profiles(), provisioning.PROFILE_BLOBS)
        self.assertEqual(provisioning.APPROVED_PACKAGES["matplotlib"], ("matplotlib", "3.10.8"))
        self.assertEqual(provisioning.APPROVED_PACKAGES["numpy"], ("numpy", "2.3.5"))
        self.assertEqual(provisioning.APPROVED_PACKAGES["playwright"], ("playwright", "1.57.0"))

    def test_os_interpreter_profile_and_pip_check_fail_closed(self):
        for key, value in (("os", "Windows"), ("os_version", "UNKNOWN"),
                           ("pip_check_passed", False), ("requirements_identical", False),
                           ("provisioning_changed", False), ("provisioning_phase", "original")):
            runtime = valid_runtime()
            runtime[key] = value
            self.assertFalse(provisioning.validate_runtime(runtime))
        for key, value in (("version", "3.13.6"), ("executable_sha256", "UNKNOWN"),
                           ("path_python_matches", False), ("isolated", False), ("role", SECRET)):
            runtime = valid_runtime()
            runtime["python"][key] = value
            self.assertFalse(provisioning.validate_runtime(runtime))
        runtime = valid_runtime()
        runtime["profile_blobs"]["requirements-comp-h3.txt"] = "3" * 40
        self.assertFalse(provisioning.validate_runtime(runtime))

    def test_every_approved_dependency_requires_real_import_version_and_interpreter_origin(self):
        for module in provisioning.APPROVED_PACKAGES:
            for key, value in (("distribution_version", "UNKNOWN"), ("expected_version", "0"),
                               ("importable", False), ("origin_in_interpreter", False),
                               ("origin_sha256", None)):
                with self.subTest(module=module, field=key):
                    runtime = valid_runtime()
                    runtime["packages"][module][key] = value
                    self.assertFalse(provisioning.validate_runtime(runtime))
            runtime = valid_runtime()
            del runtime["packages"][module]
            self.assertFalse(provisioning.validate_runtime(runtime))

    def test_tsc_version_alone_cannot_replace_loaded_parser_or_node_identity(self):
        for key, value in (("version", "22.23.3"), ("tsc_version", "7.0.2"),
                           ("typescript_version", "7.0.2"), ("parser_library_loaded", False),
                           ("executable_sha256", None), ("typescript_library_sha256", None),
                           ("path_executable_matches", False), ("library_resolution_matches", False),
                           ("sanitized_environment_used", False)):
            with self.subTest(field=key):
                runtime = valid_runtime()
                runtime["node"][key] = value
                self.assertFalse(provisioning.validate_runtime(runtime))

    def test_runtime_values_cannot_disclose_user_paths_or_arbitrary_output(self):
        for section, key in (("python", "executable_sha256"), ("node", "executable_sha256"),
                             ("node", "typescript_library_sha256"), ("node", "typescript_version")):
            runtime = valid_runtime()
            runtime[section][key] = str(ROOT / SECRET)
            self.assertFalse(provisioning.validate_runtime(runtime))
        for value in (None, {}, [], SECRET):
            self.assertFalse(provisioning.validate_runtime(value))


class WorkflowProvisioning(unittest.TestCase):
    def test_approved_h3_profile_is_complete_and_identical_to_canonical_setup(self):
        h3 = (ROOT / "requirements-comp-h3.txt").read_bytes()
        canonical = (ROOT / ".integration/tools/requirements-validation.txt").read_bytes()
        self.assertEqual(h3, canonical)
        text, steps = workflow_steps()
        setup = steps["Provision approved H3 source compiler and parser profiles"]
        self.assertIn("cmp requirements-comp-h3.txt .integration/tools/requirements-validation.txt", setup)
        self.assertIn("python -m pip install -r requirements-comp-h3.txt", setup)
        self.assertNotRegex(text, r"pip install (?:matplotlib|numpy)(?:\s|$)")
        self.assertNotIn("--no-deps", text)

    def test_host_node_and_parser_use_exact_approved_versions(self):
        text, steps = workflow_steps()
        self.assertEqual(text.count("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020"), 1)
        self.assertEqual(text.count("node-version: '22.16.0'"), 1)
        setup = steps["Provision approved H3 source compiler and parser profiles"]
        self.assertEqual(setup.count("npm install --global typescript@5.8.3"), 1)
        canonical_workflow = (ROOT / ".github/workflows/post-dir-canonical-catchup.yml").read_text(encoding="utf-8")
        canonical_setup = (ROOT / ".integration/tools/setup_ci_environment.sh").read_text(encoding="utf-8")
        self.assertIn("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020", canonical_workflow)
        self.assertIn("node-version: '22.16.0'", canonical_workflow)
        self.assertIn("npm install --global typescript@5.8.3", canonical_setup)

    def test_final_api_di_section16_and_pip_check_share_the_test_interpreter(self):
        text, steps = workflow_steps()
        setup = steps["Provision approved H3 source compiler and parser profiles"]
        commands = [line.strip() for line in setup.splitlines() if line.startswith("          ")]
        self.assertEqual(commands, [
            "cmp requirements-comp-h3.txt .integration/tools/requirements-validation.txt",
            "python -m pip install -r requirements-comp-h3.txt",
            "npm install --global typescript@5.8.3",
            "python -m pip install -e '.[document-intelligence,document-intelligence-layout,api,api-test]'",
            "python -m pip install -r requirements-qa-section16-validation.txt",
            "python -m pip check",
        ])
        self.assertEqual(text.count("python-version: '3.13.5'"), 1)
        self.assertNotIn("activate", setup)
        self.assertNotIn("venv", setup)
        self.assertNotIn("sudo", setup)

    def test_original_before_evidence_and_strict_after_gate_have_distinct_receipts(self):
        text, steps = workflow_steps()
        before = "Diagnose unchanged Post-DIR tests without changing provisioning"
        setup = "Provision approved H3 source compiler and parser profiles"
        after = "Require actual post-provision compiler passes on candidate and base"
        self.assertIn('diagnose_post_dir.py --output "$RUNNER_TEMP/task035-evidence/ci-r1-diagnostics.json"', steps[before])
        self.assertIn('verify_post_dir_provisioning.py --output "$RUNNER_TEMP/task035-evidence/ci-r2-after.json"', steps[after])
        self.assertLess(text.index(before), text.index("actions/setup-node@"))
        self.assertLess(text.index(before), text.index(setup))
        self.assertLess(text.index(setup), text.index(after))
        self.assertLess(text.index(after), text.index("Governed current Visual Animation synchronization"))
        self.assertLess(text.index(after), text.index("Complete inherited producers native Animation QA"))
        self.assertNotIn("if:", steps[after])

    def test_repair_does_not_add_unrelated_full_runtime_or_render_provisioning(self):
        text, _ = workflow_steps()
        for forbidden in ("setup_ci_environment.sh", "playwright install", "apt-get", "bubblewrap",
                          "/opt/pyvenv", "/opt/nvm", "ffmpeg", "chromium", "--no-sandbox"):
            with self.subTest(command=forbidden):
                self.assertNotIn(forbidden, text)
        self.assertNotIn("continue-on-error", text)
        self.assertNotIn("|| true", text)
        self.assertEqual(re.findall(r"^\s*timeout-minutes: (.+)$", text, re.M), ["45"])

    def test_r2_controls_remain_separate_from_original_product_test_inventory(self):
        _, steps = workflow_steps()
        self.assertEqual(steps["Task035 CI-R2 provisioning receipt safety controls only"],
            "        run: python -I -B -m unittest discover -s tests/productization/animation -p test_ci_r2_provisioning.py -v\n")
        runner = ROOT / "tools/run_task035_tests.py"
        data = runner.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest(),
                         "6765852995760f629e702f9bda24aaf3600f1c53")
        self.assertNotIn("test_ci_r2_provisioning.py", runner.read_text(encoding="utf-8"))
        r1 = Path(__file__).with_name("test_ci_r1_diagnostics.py").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^    def test_", r1, re.M)), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
