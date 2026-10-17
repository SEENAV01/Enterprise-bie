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
    def test_lf_source_preserves_all_non_crlf_bytes(self):
        import itertools
        # Include isolated CR, LF, NUL and non-UTF8; no universal newline or
        # text decoding may erase a source change. Exercise adjacent pairs.
        for length in range(7):
            for sequence in itertools.product((0, 10, 13, 65, 255), repeat=length):
                raw = bytes(sequence)
                self.assertEqual(admission.lf_source(raw), raw.replace(b"\r\n", b"\n"))

    def test_lf_source_complete_real_ledger_retains_fixed_identity(self):
        raw = admission.read_regular(ROOT, "manifests/post_dir_integration_004.json", 42 * 1024**2)
        normalized = admission.lf_source(raw)
        self.assertEqual(len(normalized), 40505121)
        self.assertEqual(sha(normalized), "33c579d83186d0a11319984e6d047cb41bfea804a6477e5902b77f0432d71c7f")

    def test_lf_source_mixed_crlf_ledger_retains_fixed_identity(self):
        raw = admission.read_regular(ROOT, "manifests/post_dir_integration_004.json", 42 * 1024**2)
        original = admission.lf_source(raw)
        windows = original.replace(b"\n", b"\r\n")
        self.assertEqual(admission.lf_source(windows), original)
        # A content mutation still cannot be normalized into reviewed bytes.
        self.assertNotEqual(sha(admission.lf_source(windows + b"\r")), sha(original))

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


class CanonicalDeadlineReviewControls(unittest.TestCase):
    """Synthetic authority-schema controls are not an independent review.

    Historical positive admission tests above remain unchanged and fail closed
    in Commit A, until actual review records and fixed constants are installed B.
    """

    def fixture(self):
        rows = admission.deadline_source_bindings(ROOT)
        review = dict(schema="bie.task036.canonical-deadline-independent-review/1",
            role="INDEPENDENT_TECHNICAL_REVIEW_NOT_PRODUCT_ACCEPTANCE", owner_decision="D6",
            reviewer=dict(execution_identity="synthetic-reviewer-not-approval",
                implementation_execution="/root", type="GENUINELY_SEPARATE_AI_ASSISTED_EXECUTION",
                provenance="SYNTHETIC_SCHEMA_TEST_ONLY", human_signature=False, codeowner_approval=False),
            candidate="1" * 40, tree="2" * 40, base=admission.DEADLINE_BASE,
            base_tree=admission.DEADLINE_BASE_TREE, decision=admission.DEADLINE_DECISION,
            blocking_findings_remaining=0, timestamp_utc="2026-10-17T00:00:00Z",
            amendment_sha256=next(r["sha256"] for r in rows if r["path"] == admission.DEADLINE_DIRECTORY + "AMENDMENT.json"),
            replacements_sha256=admission.DEADLINE_REPLACEMENTS_SHA,
            approved_binding_rows=rows, findings=[], checks_performed=["Synthetic schema only"],
            checks_not_performed=["Actual independent review"], residual_risks=["Not approval"], product_accepted=False)
        bindings = dict(schema="bie.task036.canonical-deadline-reviewed-bindings/1",
            role="EXACT_REVIEWED_BINDINGS_NOT_AN_APPROVAL", candidate=review["candidate"], tree=review["tree"],
            review_sha256="3" * 64, amendment_sha256=review["amendment_sha256"],
            replacements_sha256=admission.DEADLINE_REPLACEMENTS_SHA, approved_binding_rows=rows,
            product_accepted=False)
        return review, bindings, rows

    def validate(self, review, bindings, rows):
        with patch.multiple(admission, DEADLINE_CANDIDATE="1" * 40, DEADLINE_TREE="2" * 40,
                DEADLINE_REVIEWER="synthetic-reviewer-not-approval", DEADLINE_REVIEW_SHA="3" * 64):
            admission.deadline_review_documents(review, bindings, rows)

    def test_missing_review_constants_fail_closed_after_integrity(self):
        rows = admission.deadline_source_bindings(ROOT)
        self.assertEqual(len(rows), 12)
        with patch.object(admission, "DEADLINE_REVIEW_SHA", "PENDING"), self.assertRaisesRegex(
                ProducerError, "scene_ir_m1_deadline_approval_missing"):
            admission.verified_m1_review(ROOT)

    def test_synthetic_closed_review_schema_only_accepts_complete_rows(self):
        self.validate(*self.fixture())

    def test_missing_extra_duplicate_or_foreign_binding_rows_reject(self):
        from copy import deepcopy
        for mutate in (lambda r: r.pop(), lambda r: r.append(deepcopy(r[0])),
                       lambda r: r[0].update(path="bie/compiler/foreign.py")):
            review, bindings, rows = self.fixture()
            review["approved_binding_rows"] = deepcopy(rows)
            mutate(review["approved_binding_rows"])
            with self.assertRaises(ProducerError): self.validate(review, bindings, rows)

    def test_review_schema_unknown_missing_and_coercion_reject(self):
        for key, value in (("schema", "unknown/2"), ("product_accepted", 0),
                           ("blocking_findings_remaining", False), ("extra", "foreign"),
                           ("timestamp_utc", "invalid"), ("checks_performed", [])):
            review, bindings, rows = self.fixture()
            review[key] = value
            with self.assertRaises(ProducerError): self.validate(review, bindings, rows)
        for key in admission.DEADLINE_REVIEW_FIELDS:
            review, bindings, rows = self.fixture()
            del review[key]
            with self.assertRaises(ProducerError): self.validate(review, bindings, rows)

    def test_changes_requested_pending_or_wrong_candidate_cannot_admit(self):
        for key, value in (("decision", "CHANGES_REQUESTED"), ("decision", "REVIEW_INCOMPLETE"),
                           ("decision", "REVIEW_AUTHORITY_UNRESOLVED"), ("decision", "PENDING"),
                           ("candidate", "4" * 40), ("tree", "4" * 40), ("base", "4" * 40),
                           ("replacements_sha256", "0" * 64), ("amendment_sha256", "0" * 64)):
            review, bindings, rows = self.fixture()
            review[key] = value
            with self.assertRaises(ProducerError): self.validate(review, bindings, rows)

    def test_self_approval_human_claim_or_wrong_reviewer_rejected(self):
        for key, value in (("execution_identity", "/root"), ("execution_identity", "foreign"),
                           ("human_signature", True), ("codeowner_approval", True),
                           ("type", "ROLE_PLAY"), ("provenance", "")):
            review, bindings, rows = self.fixture()
            review["reviewer"][key] = value
            with self.assertRaises(ProducerError): self.validate(review, bindings, rows)

    def test_unresolved_blocking_finding_or_duplicate_id_rejected(self):
        finding = dict(id="F1", severity="HIGH", blocking=True, disposition="OPEN", location="synthetic",
            requirement_or_risk="synthetic", correction_or_reason="synthetic", verification="synthetic")
        review, bindings, rows = self.fixture()
        review["findings"] = [finding]
        with self.assertRaises(ProducerError): self.validate(review, bindings, rows)
        finding["disposition"] = "NON_BLOCKING"
        with self.assertRaises(ProducerError): self.validate(review, bindings, rows)
        finding["disposition"] = "RESOLVED"
        self.validate(review, bindings, rows)
        review["findings"].append(dict(finding))
        with self.assertRaises(ProducerError): self.validate(review, bindings, rows)

    def test_binding_container_not_an_independent_approval(self):
        for key, value in (("review_sha256", "0" * 64), ("candidate", "0" * 40),
                           ("tree", "0" * 40), ("approved_binding_rows", []),
                           ("product_accepted", 0), ("extra", True), ("schema", "unknown")):
            review, bindings, rows = self.fixture()
            bindings[key] = value
            with self.assertRaises(ProducerError): self.validate(review, bindings, rows)

    def test_source_tamper_repin_and_rollback_rejected_before_approval(self):
        actual = admission.read_regular
        for target in sorted(admission.DEADLINE_ACTIVE_PATHS | admission.DEADLINE_RECORD_PATHS |
                             {admission.DEADLINE_DIRECTORY + "REPLACEMENTS.json"}):
            def read(root, relative, limit=262144):
                data = actual(root, relative, limit)
                return data + b"\n" if relative == target else data
            with patch.object(admission, "read_regular", read), self.assertRaisesRegex(
                    ProducerError, "scene_ir_m1_deadline_source_identity"):
                admission.deadline_source_bindings(ROOT)
        for target in sorted(admission.DEADLINE_ACTIVE_PATHS):
            def read(root, relative, limit=262144):
                return actual(root, admission.DEADLINE_DIRECTORY + admission.DEADLINE_PREIMAGES[relative], limit) if relative == target else actual(root, relative, limit)
            with patch.object(admission, "read_regular", read), self.assertRaises(ProducerError):
                admission.deadline_source_bindings(ROOT)

    def test_unlisted_v2_member_rejected(self):
        actual = Path.rglob
        def paths(folder, pattern):
            yield from actual(folder, pattern)
            if folder == ROOT / admission.DEADLINE_DIRECTORY:
                yield ROOT / "tools/run_task036_tests.py"
        with patch.object(Path, "rglob", paths), self.assertRaises(ProducerError):
            admission.deadline_source_bindings(ROOT)

    def test_v2_preimages_require_raw_bytes_not_normalized_seals(self):
        actual = admission.read_regular
        for target in (admission.DEADLINE_DIRECTORY + p for p in admission.DEADLINE_PREIMAGES.values()):
            def read(root, relative, limit=262144):
                data = actual(root, relative, limit)
                return data.replace(b"\n", b"\r\n") if relative == target else data
            with patch.object(admission, "read_regular", read), self.assertRaises(ProducerError):
                admission.deadline_source_bindings(ROOT)

    def test_fixed_review_bytes_reject_tamper_without_recomputing_expected_hash(self):
        import json
        from hashlib import sha256
        review, bindings, rows = self.fixture()
        raw = json.dumps(review).encode()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / admission.DEADLINE_DIRECTORY
            folder.mkdir(parents=True)
            (folder / "REVIEW.json").write_bytes(raw + b" ")
            with patch.multiple(admission, DEADLINE_REVIEW_SHA=sha256(raw).hexdigest(),
                    DEADLINE_BINDINGS_SHA="5" * 64, DEADLINE_REVIEW_BYTES=len(raw) + 1,
                    DEADLINE_BINDINGS_BYTES=100, DEADLINE_CANDIDATE="1" * 40,
                    DEADLINE_TREE="2" * 40, DEADLINE_REVIEWER="synthetic-reviewer-not-approval"):
                with self.assertRaisesRegex(ProducerError, "scene_ir_m1_deadline_review_identity"):
                    admission.verified_deadline_review(root, rows)

    def test_review_json_duplicate_keys_and_nonfinite_are_rejected(self):
        for raw in (b'{"decision":"x","decision":"x"}', b'{"blocking_findings_remaining":NaN}'):
            with self.assertRaises(ProducerError): strict_json(raw)

    def test_synthetic_fixed_record_reader_requires_both_exact_documents(self):
        import json
        from hashlib import sha256
        review, bindings, rows = self.fixture()
        raw_review = json.dumps(review, sort_keys=True).encode()
        bindings["review_sha256"] = sha256(raw_review).hexdigest()
        raw_bindings = json.dumps(bindings, sort_keys=True).encode()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / admission.DEADLINE_DIRECTORY
            folder.mkdir(parents=True)
            with patch.multiple(admission, DEADLINE_REVIEW_SHA=sha256(raw_review).hexdigest(),
                    DEADLINE_BINDINGS_SHA=sha256(raw_bindings).hexdigest(),
                    DEADLINE_REVIEW_BYTES=len(raw_review), DEADLINE_BINDINGS_BYTES=len(raw_bindings),
                    DEADLINE_CANDIDATE="1" * 40, DEADLINE_TREE="2" * 40,
                    DEADLINE_REVIEWER="synthetic-reviewer-not-approval"):
                with self.assertRaisesRegex(ProducerError, "scene_ir_m1_deadline_approval_missing"):
                    admission.verified_deadline_review(root, rows)
                (folder / "REVIEW.json").write_bytes(raw_review)
                with self.assertRaisesRegex(ProducerError, "scene_ir_m1_deadline_approval_missing"):
                    admission.verified_deadline_review(root, rows)
                (folder / "BINDINGS.json").write_bytes(raw_bindings)
                admission.verified_deadline_review(root, rows)
                (folder / "BINDINGS.json").write_bytes(raw_bindings.replace(b"1" * 40, b"4" * 40))
                with self.assertRaisesRegex(ProducerError, "scene_ir_m1_deadline_review_identity"):
                    admission.verified_deadline_review(root, rows)

    def test_v2_old_auxiliary_row_cannot_be_silently_retired(self):
        from copy import deepcopy
        actual = admission.authenticated_document
        def document(root, relative, expected):
            value = actual(root, relative, expected)
            if relative == admission.ADDENDUM:
                value = deepcopy(value)
                value["auxiliary_reviewed_authority_bindings"][0]["sha256"] = "0" * 64
            return value
        with patch.object(admission, "authenticated_document", document), self.assertRaisesRegex(
                ProducerError, "^scene_ir_m1_source_identity$"):
            admission.verified_m1_review(ROOT)

    def test_v2_unknown_authority_paths_never_expand_reader_bounds(self):
        for review_bytes, bindings_bytes in ((0, 100), (True, 100), (262145, 100), (100, -1)):
            with patch.multiple(admission, DEADLINE_REVIEW_SHA="3" * 64, DEADLINE_BINDINGS_SHA="4" * 64,
                    DEADLINE_CANDIDATE="1" * 40, DEADLINE_TREE="2" * 40,
                    DEADLINE_REVIEWER="synthetic-reviewer-not-approval",
                    DEADLINE_REVIEW_BYTES=review_bytes, DEADLINE_BINDINGS_BYTES=bindings_bytes), self.assertRaisesRegex(
                        ProducerError, "scene_ir_m1_deadline_approval_missing"):
                admission.verified_deadline_review(ROOT, [])
