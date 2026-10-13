"""Actual independent review admission and adversarial read controls, not renderer proof."""
from pathlib import Path
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bie.productization import scene_ir_m1_review as admission
from bie.productization.contracts import ProducerError, strict_json, sha

ROOT = Path(__file__).resolve().parents[3]


class CurrentM1ReviewControls(unittest.TestCase):
    def test_actual_hardlinked_identical_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.py"
            first.write_bytes(b"# fixed synthetic bytes\n")
            os.link(first, root / "second.py")
            with self.assertRaises(ProducerError):
                admission.read_regular(root, "first.py")

    def test_reader_rejects_resolved_path_escape(self):
        actual = Path.resolve
        target = ROOT / admission.FINAL
        def resolved(path, *args, **kwargs):
            return ROOT.parent / "foreign-review.json" if path == target else actual(path, *args, **kwargs)
        with patch.object(Path, "resolve", resolved), self.assertRaises(ProducerError):
            admission.read_regular(ROOT, admission.FINAL)

    def test_reader_rejects_opened_descriptor_identity_disagreement(self):
        actual = admission.os.fstat
        def changed(fd):
            info = actual(fd)
            return SimpleNamespace(st_mode=info.st_mode, st_nlink=info.st_nlink,
                st_dev=info.st_dev, st_ino=info.st_ino + 1, st_size=info.st_size, st_mtime_ns=info.st_mtime_ns)
        with patch.object(admission.os, "fstat", changed), self.assertRaises(ProducerError):
            admission.read_regular(ROOT, admission.FINAL)

    def test_reader_rejects_hardlink_added_during_read(self):
        actual = admission.os.fstat
        calls = []
        def changed(fd):
            info = actual(fd); calls.append(fd)
            return SimpleNamespace(st_mode=info.st_mode, st_nlink=1 if len(calls) == 1 else 2,
                st_dev=info.st_dev, st_ino=info.st_ino, st_size=info.st_size, st_mtime_ns=info.st_mtime_ns)
        with patch.object(admission.os, "fstat", changed), self.assertRaises(ProducerError):
            admission.read_regular(ROOT, admission.FINAL)

    def test_native_subset_known_valid_reads_are_all_in_complete_fixed_chain(self):
        from scripts import compiler_pr_source_contract_amendment as native
        original_reader = native.reader
        regular, unique, manifest, manifest_sha = original_reader()
        requested = []
        def observed(root, relative, limit):
            requested.append(relative)
            return regular(root, relative, limit)
        with patch.object(native, "reader", return_value=(observed, unique, manifest, manifest_sha)):
            document = native.validate(ROOT)
        chain = strict_json((ROOT / admission.CHAIN).read_bytes())
        covered = {r["path"] for r in chain["files"]} | {chain["ledger"]["path"]}
        self.assertTrue(requested)
        self.assertLessEqual(set(requested), covered)
        self.assertEqual(document["original_m1_sha256"], native.M1_SHA256)
        self.assertEqual(document["previous_amendment_sha256"], native.PREVIOUS_SHA256)

    def test_each_current_admission_authenticates_ledger_once_no_cross_call_cache(self):
        actual = admission.read_regular
        calls = []
        def read(root, relative, limit=262144):
            calls.append(relative)
            return actual(root, relative, limit)
        with patch.object(admission, "read_regular", read):
            admission.verified_m1_review(ROOT)
            admission.verified_m1_review(ROOT)
        self.assertEqual(calls.count("manifests/post_dir_integration_004.json"), 2)
        self.assertEqual(calls.count(admission.CHAIN), 2)

    def tamper(self, target, replacement=None):
        actual = admission.read_regular
        def read(root, relative, limit=262144):
            value = actual(root, relative, limit)
            return (value + b"\n" if replacement is None else replacement) if relative == target else value
        with patch.object(admission, "read_regular", read), self.assertRaises(ProducerError):
            admission.verified_m1_review(ROOT)

    def test_actual_current_source_and_review_chain_authenticate(self):
        self.assertEqual(admission.verified_m1_review(ROOT),
            dict(m1_review=admission.HISTORICAL_SHA, m1_current_review=admission.FINAL_SHA,
                 m1_current_source_bindings=admission.ADDENDUM_SHA, m1_source_chain=admission.CHAIN_SHA))

    def test_original_review_exact_bytes_still_immutable(self):
        self.assertEqual(sha((ROOT / admission.HISTORICAL).read_bytes()), admission.HISTORICAL_SHA)

    def test_complete_historical_set_only_four_reviewed_changes(self):
        old = strict_json((ROOT / admission.HISTORICAL).read_bytes())
        new = strict_json((ROOT / admission.ADDENDUM).read_bytes())
        rows = {r["path"]: r for r in old["cumulative_source_review"]["exact_reviewed_file_bindings"]
                if r["path"].startswith(admission.PREFIXES)}
        current = {r["path"]: r for r in new["exact_reviewed_file_bindings"]}
        self.assertEqual(set(rows), set(current))
        self.assertEqual(len(rows), 52)
        self.assertEqual(sum(rows[p] != current[p] for p in rows), 4)
        self.assertEqual(len(new["authenticated_followon_file_bindings"]), 11)

    def test_latest_review_tamper_rejected(self): self.tamper(admission.FINAL)
    def test_historical_review_tamper_rejected(self): self.tamper(admission.HISTORICAL)
    def test_binding_addendum_tamper_rejected(self): self.tamper(admission.ADDENDUM)
    def test_changed_compiler_source_tamper_rejected(self):
        self.tamper("bie/compiler/qa_support/remotion_raster_capture.cjs")
    def test_unchanged_native_source_tamper_rejected(self):
        self.tamper("bie/compiler/animation_behavior.py")
    def test_new_audit_resolver_tamper_rejected(self):
        self.tamper("scripts/compiler_pr_source_contract_amendment.py")
    def test_sealed_amendment_tamper_rejected(self):
        self.tamper("docs/productization/task036-motion-amendment/AMENDMENT.json")
    def test_original_preimage_tamper_rejected(self):
        self.tamper("docs/productization/task036-pr-source-contract-amendment/remotion_raster_capture.cjs.before")
    def test_ci_authority_tamper_rejected(self):
        self.tamper(".github/workflows/post-dir-canonical-catchup.yml")

    def crlf_tamper(self, target):
        raw = admission.read_regular(ROOT, target)
        replacement = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        self.assertNotEqual(raw, replacement)
        self.tamper(target, replacement)

    def test_ci_workflow_preimage_crlf_only_tamper_rejected(self):
        self.crlf_tamper("docs/productization/task036-ci-history-amendment/post-dir-canonical-catchup.yml.before")

    def test_ci_guard_preimage_crlf_only_tamper_rejected(self):
        self.crlf_tamper("docs/productization/task036-ci-history-amendment/verify_post_dir_provisioning.py.before")

    def test_original_native_preimage_crlf_only_tamper_rejected(self):
        self.crlf_tamper("docs/productization/task036-motion-amendment/reduced_motion.py.before")

    def test_followon_native_preimage_crlf_only_tamper_rejected(self):
        self.crlf_tamper("docs/productization/task036-pr-source-contract-amendment/remotion_raster_capture.cjs.before")

    def test_original_seal_crlf_only_tamper_rejected(self):
        self.crlf_tamper("docs/productization/task036-motion-amendment/AMENDMENT.json")

    def test_followon_seal_crlf_only_tamper_rejected(self):
        self.crlf_tamper("docs/productization/task036-ci-history-amendment/REPLACEMENTS.json")

    def test_portable_source_crlf_only_conversion_is_not_a_raw_seal(self):
        actual = admission.read_regular
        def read(root, relative, limit=262144):
            raw = actual(root, relative, limit)
            if relative == "bie/compiler/animation_behavior.py":
                return raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            return raw
        with patch.object(admission, "read_regular", read):
            self.assertEqual(admission.verified_m1_review(ROOT)["m1_current_review"], admission.FINAL_SHA)

    def test_documents_use_exact_reviewed_lengths_inside_original_reader_bound(self):
        actual = admission.read_regular
        calls = []
        def read(root, relative, limit=262144):
            calls.append((relative, limit))
            return actual(root, relative, limit)
        with patch.object(admission, "read_regular", read):
            admission.verified_m1_review(ROOT)
        for path, length in admission.DOCUMENT_BYTES.items():
            self.assertEqual(calls.count((path, length)), 1)
            self.assertLessEqual(length, 262144)

    def test_unregistered_document_cannot_expand_read_authority(self):
        with self.assertRaises(ProducerError):
            admission.authenticated_document(ROOT, "docs/foreign-review.json", admission.FINAL_SHA)

    def test_chain_identity_index_tamper_cannot_self_bless(self): self.tamper(admission.CHAIN)

    def test_unlisted_baseline_worker_bytes_rejected(self):
        self.tamper("bie/compiler/chromium_resource_worker.py")

    def test_unlisted_baseline_render_runtime_bytes_rejected(self):
        self.tamper("bie/compiler/render_runtime.py")

    def test_unlisted_baseline_codec_dependency_bytes_rejected(self):
        self.tamper("bie/compiler/scene_ir_loader.py")

    def test_section18_original_native_seal_tamper_rejected(self):
        self.tamper("docs/section18/compiler-native-source-amendment/AMENDMENT.json")

    def test_section18_original_cache_preimage_tamper_rejected(self):
        self.tamper("docs/section18/compiler-bundle-source-amendment/remotion_raster_capture.cjs.before")

    def test_section18_original_caller_preimage_tamper_rejected(self):
        self.tamper("docs/section18/compiler-caller-source-amendment/test_comp_h7_007.py.before")

    def test_original_ledger_tamper_rejected(self):
        self.tamper("manifests/post_dir_integration_004.json")

    def test_empty_known_compiler_initializer_is_exactly_authenticated(self):
        chain = strict_json((ROOT / admission.CHAIN).read_bytes())
        row, = [r for r in chain["files"] if r["path"] == "bie/compiler/__init__.py"]
        self.assertEqual(row["bytes"], 0)
        self.assertEqual(admission.read_regular(ROOT, row["path"]), b"")
        self.tamper(row["path"], b"# unreviewed initializer\n")

    def test_missing_predecessor_does_not_admit_current_only(self):
        actual = admission.read_regular
        def read(root, relative, limit=262144):
            if relative == "docs/section18/compiler-paint-source-amendment/real_paint.py.before":
                raise ProducerError("scene_ir_m1_source_identity")
            return actual(root, relative, limit)
        with patch.object(admission, "read_regular", read), self.assertRaises(ProducerError):
            admission.verified_m1_review(ROOT)

    def test_extra_compiler_path_rejected_by_exact_census(self):
        actual = Path.rglob
        def paths(folder, pattern):
            yield from actual(folder, pattern)
            if folder == ROOT / "bie/compiler":
                # A real existing noncompiler file is still an unlisted result;
                # no native file mutation is needed for the census control.
                yield ROOT / "tools/run_task036_tests.py"
        with patch.object(Path, "rglob", paths), self.assertRaises(ProducerError):
            admission.verified_m1_review(ROOT)

    def test_removed_compiler_path_rejected_by_exact_census(self):
        actual = Path.rglob
        def paths(folder, pattern):
            for path in actual(folder, pattern):
                if path != ROOT / "bie/compiler/chromium_resource_worker.py":
                    yield path
        with patch.object(Path, "rglob", paths), self.assertRaises(ProducerError):
            admission.verified_m1_review(ROOT)

    def test_partial_rollback_cannot_fall_back_to_old_review(self):
        before = ROOT / "docs/productization/task036-pr-source-contract-amendment/remotion_raster_capture.cjs.before"
        self.tamper("bie/compiler/qa_support/remotion_raster_capture.cjs", before.read_bytes())

    def test_missing_current_record_does_not_admit_historical_only(self):
        actual = admission.read_regular
        def read(root, relative, limit=262144):
            if relative == admission.FINAL:
                raise ProducerError("scene_ir_m1_source_identity")
            return actual(root, relative, limit)
        with patch.object(admission, "read_regular", read), self.assertRaises(ProducerError):
            admission.verified_m1_review(ROOT)

    def test_path_traversal_and_absolute_paths_fail_closed(self):
        for value in ("../outside", "/absolute", "C:/outside", "docs\\outside"):
            with self.subTest(value=value), self.assertRaises(ProducerError):
                admission.read_regular(ROOT, value)

    def test_configuration_binds_helper_and_both_review_identities(self):
        from bie.productization.scene_ir_contract import code_identity_scope, engine_identity
        with code_identity_scope():
            current = engine_identity()
        self.assertEqual(current["m1_current_review"], admission.FINAL_SHA)
        self.assertEqual(current["m1_current_source_bindings"], admission.ADDENDUM_SHA)
        self.assertIn("bie.productization.scene_ir_m1_review", current)

    def test_review_record_commit_does_not_claim_to_be_reviewed_source(self):
        record = strict_json((ROOT / admission.FINAL).read_bytes())
        self.assertEqual(record["exact_source"]["candidate"], admission.CANDIDATE)
        self.assertFalse(record["reviewer"]["PR_review_submission"])
        self.assertFalse(record["reviewer"]["human_signature"])

    def test_new_case_ownership_disjoint_and_once(self):
        from tools.run_task036_tests import NEW
        from tests.compiler.run_m1_tests import NEW as m1, SAFETY, inventory
        own = "tests/productization/scene_ir/test_current_m1_review.py"
        lanes, inherited = inventory()
        self.assertEqual(NEW.count(own), 1)
        self.assertNotIn(own, set(m1) | set(SAFETY) | set(lanes["native-extra"]) | inherited)
