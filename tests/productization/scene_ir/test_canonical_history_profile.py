"""Source compatibility controls, distinct from actual Linux compiler probes."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tests.productization.scene_ir import canonical_history_profile as profile
from tests.productization.animation.test_ci_r2_provisioning import provisioning, valid_after, HEAD

ROOT = Path(__file__).resolve().parents[3]
DOCUMENT = profile.DIRECTORY + "AMENDMENT.json"
REPLACEMENTS = {
    "schema": "bie.task036.canonical-history-source-attestation/1",
    "role": "FIXED_SOURCE_GATE_ATTESTATION_NOT_ADMISSION_AUTHORITY",
    "files": {
        profile.GUARD: {"bytes": 23564, "sha256": "2bbd0c6c7df6e5f5d2b98235cb1bceab1c5fcb1024a4d40e6ce870cbecdac517"},
        "tests/productization/scene_ir/canonical_history_profile.py": {
            "bytes": 5828, "sha256": "2ee292eba7bfcb47e39f25a14aa5e8a85af1a316ecb664d4760222fe5e95a92e"},
        DOCUMENT: {"bytes": 1476, "sha256": "639e87119a2cf8f6cf35e8062dbd66df4b021f05b689a5602674e9eb4992df00"},
    },
    "historical_guard_blob": "57d32e0c7b93e2c2c4a71ee05239c3630c21f60f",
    "historical_workflow_blob": "3f95bbff25fa7e9cd18d054eb5bee04d76933655",
    "product_accepted": False,
}


def validate_replacements(root):
    try:
        raw = profile.read_regular(root, profile.DIRECTORY + "REPLACEMENTS.json", 16384)
        value = json.loads(raw, object_pairs_hook=profile.unique, parse_constant=profile.reject_constant)
        if json.dumps(value, sort_keys=True) != json.dumps(REPLACEMENTS, sort_keys=True):
            return False
        for relative, row in REPLACEMENTS["files"].items():
            data = profile.read_regular(root, relative, 65536).replace(b"\r\n", b"\n")
            if len(data) != row["bytes"] or sha256(data).hexdigest() != row["sha256"]:
                return False
        return True
    except (ValueError, OSError):
        return False


class CanonicalHistoryProfileControls(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.paths = [DOCUMENT, profile.DIRECTORY + "REPLACEMENTS.json",
            "tests/productization/scene_ir/canonical_history_profile.py"]
        for row in (profile.EXPECTED["workflow"], profile.EXPECTED["guard"]):
            self.paths.extend((row["path"], row["preimage"]))
        for relative in self.paths:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

    def change_document(self, mutate):
        value = deepcopy(profile.EXPECTED)
        mutate(value)
        (self.root / DOCUMENT).write_text(json.dumps(value), encoding="utf-8")

    def rejected(self):
        with self.assertRaises((ValueError, OSError)):
            profile.authenticate(self.root)

    def test_actual_guard_accepts_exact_compatibility_without_repinning_authority(self):
        self.assertEqual(provisioning.approved_profiles(), provisioning.PROFILE_BLOBS)
        self.assertEqual(provisioning.PROFILE_BLOBS[profile.WORKFLOW], "3f95bbff25fa7e9cd18d054eb5bee04d76933655")
        self.assertEqual(provisioning.current_profile_amendment(), profile.authenticate(ROOT))

    def test_complete_exact_preimages_and_replacements_authenticate(self):
        self.assertEqual(profile.authenticate(self.root), profile.witness())
        self.assertEqual(profile.authenticate(ROOT), profile.witness())
        self.assertTrue(validate_replacements(ROOT))

    def test_actual_after_uses_separate_closed_v2_witness(self):
        value = valid_after()
        value.update(schema="bie.task035.post-dir-after/2", profile_amendment=profile.authenticate(ROOT))
        self.assertTrue(provisioning.validate_after_receipt(value, HEAD))
        self.assertNotEqual(value["profile_amendment"]["actual_workflow_blob"],
                            value["runtime"]["profile_blobs"][profile.WORKFLOW])

    def test_legacy_receipt_shape_and_old_safety_validator_remain_supported(self):
        value = valid_after()
        self.assertTrue(provisioning.validate_after_receipt(value, HEAD))
        value["profile_amendment"] = profile.witness()
        self.assertFalse(provisioning.validate_after_receipt(value, HEAD))

    def test_collector_emits_v2_for_actual_amended_root(self):
        # Synthetic collector assembly control only; real hosted probes remain
        # mandatory and are never replaced by these validator fixtures.
        value = valid_after()
        with patch.object(provisioning.diagnostics, "git_text", return_value=HEAD), patch.object(
                provisioning.diagnostics, "collect", return_value=value["comparison"]), patch.object(
                provisioning, "runtime_preflight", return_value=value["runtime"]):
            receipt = provisioning.collect_after()
        self.assertEqual(receipt["schema"], "bie.task035.post-dir-after/2")
        self.assertEqual(receipt["profile_amendment"], profile.authenticate(ROOT))
        self.assertTrue(receipt["after_gate_passed"])

    def test_original_workflow_without_amendment_keeps_original_admission(self):
        row = profile.EXPECTED["workflow"]
        shutil.copyfile(self.root / row["preimage"], self.root / row["path"])
        (self.root / DOCUMENT).unlink()
        with patch.object(provisioning, "ROOT", self.root), patch.object(provisioning, "__file__", self.root / profile.EXPECTED["guard"]["preimage"]):
            self.assertIsNone(provisioning.current_profile_amendment())

    def test_active_guard_cannot_downgrade_to_legacy_after_partial_rollback(self):
        row = profile.EXPECTED["workflow"]
        shutil.copyfile(self.root / row["preimage"], self.root / row["path"])
        (self.root / DOCUMENT).unlink()
        with patch.object(provisioning, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "APPROVED_PROFILE_PARTIAL_ROLLBACK"):
                provisioning.current_profile_amendment()

    def test_current_candidate_cannot_use_legacy_v1_as_source_evidence(self):
        with patch.object(provisioning.diagnostics, "git_text", return_value=HEAD):
            self.assertFalse(provisioning.validate_after_receipt(valid_after(), HEAD))

    def test_helper_bytes_are_authenticated_before_any_execution(self):
        relative = "tests/productization/scene_ir/canonical_history_profile.py"
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("raise AssertionError('MUST_NOT_EXECUTE')\n", encoding="utf-8")
        with patch.object(provisioning, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "APPROVED_PROFILE_AMENDMENT_MODULE_IDENTITY"):
                provisioning._profile_module()

    def test_checked_helper_bytes_execute_without_second_loader_read(self):
        with patch("importlib.machinery.SourceFileLoader.exec_module", side_effect=AssertionError("MUST_NOT_REREAD")):
            module = provisioning._profile_module()
        self.assertEqual(module.authenticate(ROOT), profile.witness())

    def test_attestation_cannot_repin_tampered_replacement_or_add_paths(self):
        path = self.root / (profile.DIRECTORY + "REPLACEMENTS.json")
        value = deepcopy(REPLACEMENTS)
        value["files"][profile.GUARD]["sha256"] = "0" * 64
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertFalse(validate_replacements(self.root))
        value = deepcopy(REPLACEMENTS)
        value["files"]["bie/compiler/real_paint.py"] = {"bytes": 1, "sha256": "0" * 64}
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertFalse(validate_replacements(self.root))

    def test_v2_without_witness_or_unknown_schema_cannot_pass(self):
        for schema in ("bie.task035.post-dir-after/2", "bie.task035.post-dir-after/3"):
            value = valid_after()
            value["schema"] = schema
            self.assertFalse(provisioning.validate_after_receipt(value, HEAD))

    def test_v2_cannot_substitute_for_runtime_or_six_real_probe_requirements(self):
        for field in ("runtime", "comparison"):
            value = valid_after()
            value.update(schema="bie.task035.post-dir-after/2", profile_amendment=profile.witness())
            value[field] = {}
            self.assertFalse(provisioning.validate_after_receipt(value, HEAD))

    def test_witness_rejects_missing_extra_and_forged_fields(self):
        for key in profile.witness():
            value = profile.witness()
            del value[key]
            self.assertFalse(profile.validate_witness(value))
            value = profile.witness()
            value[key] = "PRIVATE_FAKE_SENTINEL"
            self.assertFalse(profile.validate_witness(value))
        value = profile.witness()
        value["private"] = "PRIVATE_FAKE_SENTINEL"
        self.assertFalse(profile.validate_witness(value))

    def test_boolean_and_integer_equivalence_cannot_spoof_witness(self):
        for key in ("native_source_changed", "requirements_installers_changed", "product_accepted"):
            value = profile.witness()
            value[key] = 0
            self.assertFalse(profile.validate_witness(value))

    def test_extra_path_or_changed_authority_in_manifest_rejected(self):
        for key, value in (("extra_path", "bie/compiler/real_paint.py"),
                           ("base", "0" * 40), ("product_accepted", True)):
            self.change_document(lambda document: document.update({key: value}))
            self.rejected()

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for raw in ('{"schema":"x","schema":"x"}', '{"value":NaN}', '{"value":Infinity}'):
            (self.root / DOCUMENT).write_text(raw, encoding="utf-8")
            self.rejected()

    def test_manifest_bool_as_integer_or_nested_unknown_key_rejected(self):
        self.change_document(lambda value: value.update(native_source_changed=0))
        self.rejected()
        self.change_document(lambda value: value["workflow"].update(unknown="x"))
        self.rejected()

    def test_preimage_tamper_is_not_blessed_by_recomputed_hash(self):
        for name in ("workflow", "guard"):
            with self.subTest(source=name):
                self.setUp()
                row = profile.EXPECTED[name]
                (self.root / row["preimage"]).write_bytes(b"foreign\n")
                self.change_document(lambda value: value[name].update(original_sha256=sha256(b"foreign\n").hexdigest()))
                self.rejected()

    def test_workflow_rollback_requires_original_root_not_new_amendment(self):
        row = profile.EXPECTED["workflow"]
        shutil.copyfile(self.root / row["preimage"], self.root / row["path"])
        self.rejected()

    def test_unlisted_workflow_change_or_new_dependency_cannot_pass(self):
        path = self.root / profile.WORKFLOW
        path.write_bytes(path.read_bytes() + b"# unrelated package addition\n")
        self.rejected()

    def test_guard_source_tamper_rejected_by_fixed_source_attestation(self):
        path = self.root / profile.GUARD
        path.write_bytes(path.read_bytes() + b"# unapproved guard change\n")
        self.assertFalse(validate_replacements(self.root))

    def test_missing_manifest_and_missing_preimage_rejected(self):
        (self.root / DOCUMENT).unlink()
        self.rejected()
        shutil.copyfile(ROOT / DOCUMENT, self.root / DOCUMENT)
        (self.root / profile.EXPECTED["guard"]["preimage"]).unlink()
        self.rejected()

    def test_oversized_or_nonregular_receipt_rejected(self):
        path = self.root / DOCUMENT
        path.write_bytes(b"x" * 16385)
        self.rejected()
        path.unlink()
        path.mkdir()
        self.rejected()

    def test_links_and_path_escape_fail_before_read(self):
        # Synthetic lstat boundary check, not a substituted compiler execution.
        with patch.object(Path, "is_symlink", return_value=True):
            self.rejected()
        for relative in ("../private", str(ROOT / "private")):
            with self.assertRaises(ValueError):
                profile.read_regular(self.root, relative, 1024)

    def test_nonworkflow_profile_still_rejected_by_actual_guard(self):
        for relative in provisioning.PROFILE_BLOBS:
            if relative == profile.WORKFLOW:
                continue
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"foreign\n")
        with patch.object(provisioning, "ROOT", self.root), patch.object(provisioning, "current_profile_amendment", return_value=profile.witness()):
            with self.assertRaisesRegex(ValueError, "APPROVED_PROFILE_IDENTITY_MISMATCH"):
                provisioning.approved_profiles()

    def test_private_content_is_never_returned_in_witness_or_error(self):
        (self.root / DOCUMENT).write_text('{"private":"PRIVATE_FAKE_SENTINEL"}', encoding="utf-8")
        try:
            profile.authenticate(self.root)
        except ValueError as error:
            self.assertEqual(error.args, ("TASK036_PROFILE_AMENDMENT_IDENTITY",))
        encoded = json.dumps(profile.witness())
        self.assertNotIn("PRIVATE_FAKE_SENTINEL", encoded)
        self.assertNotIn(str(self.root), encoded)

    def test_inventory_owns_new_controls_once_without_cross_lane_overlap(self):
        from tools.run_task036_tests import NEW
        from tests.compiler.run_m1_tests import NEW as M1, SAFETY, inventory
        path = "tests/productization/scene_ir/test_canonical_history_profile.py"
        lanes, inherited = inventory()
        self.assertEqual(NEW.count(path), 1)
        self.assertNotIn(path, set(M1) | set(SAFETY) | set(lanes["native-extra"]) | inherited)
        self.assertEqual(len(lanes["native-extra"]), 214)


if __name__ == "__main__":
    unittest.main()
