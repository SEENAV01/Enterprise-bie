from dataclasses import replace
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from bie.qa.release_v2 import ContractError
from bie.qa.release_v2.artifacts import ArtifactStore
from helpers import CaseTest


class ArtifactTests(CaseTest):
    def test_read_real_fixture_bytes(self):
        ref = self.bundle.candidate.artifacts[0]
        with ArtifactStore(self.root) as store:
            check = store.check(ref)
        self.assertEqual(check.status, "PASS")
        self.assertEqual(check.actual_sha256, ref.sha256)
        self.assertEqual(check.bytes_read, ref.size)

    def test_missing_artifact_fails(self):
        ref = self.bundle.candidate.artifacts[0]
        (self.root / ref.path).unlink()
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).status, "ERROR")

    def test_same_size_tampering_detected(self):
        ref = self.bundle.candidate.artifacts[0]
        (self.root / ref.path).write_bytes(b"X" * ref.size)
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).diagnostic, "ARTIFACT_HASH_MISMATCH")

    def test_size_mismatch_detected(self):
        ref = self.bundle.candidate.artifacts[0]
        (self.root / ref.path).write_bytes(b"short")
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).diagnostic, "ARTIFACT_SIZE_MISMATCH")

    def test_path_traversal_and_platform_escape_rejected(self):
        paths = ("../secret", "/etc/passwd", "subjects/../../secret", "a//b", "a/./b", "a/../b",
                 "C:/secret", "C:\\secret", "\\\\server\\share", "file://secret", "https://example/x",
                 "a\x00b", "a\nb", "a/", "", ".", "..", "a/%2e%2e/b", "a\uff0fb", "a/\u202eb")
        for path in paths:
            with self.subTest(path=path), self.assertRaises(ContractError):
                replace(self.bundle.candidate.artifacts[0], path=path)

    def test_leaf_symlink_rejected(self):
        ref = self.bundle.candidate.artifacts[0]
        target = self.root / ref.path
        moved = self.root / "actual-source"
        target.rename(moved)
        target.symlink_to(moved)
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).status, "ERROR")

    def test_parent_directory_symlink_rejected(self):
        ref = self.bundle.candidate.artifacts[0]
        (self.root / "subjects").rename(self.root / "actual-subjects")
        (self.root / "subjects").symlink_to(self.root / "actual-subjects", target_is_directory=True)
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).status, "ERROR")

    def test_symlink_root_rejected(self):
        link = self.root / "root-link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ContractError):
            with ArtifactStore(link):
                pass

    def test_hard_link_rejected(self):
        ref = self.bundle.candidate.artifacts[0]
        os.link(self.root / ref.path, self.root / "source-hardlink")
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).diagnostic, "HARD_LINK_REJECTED")

    def test_directory_is_not_artifact(self):
        ref = replace(self.bundle.candidate.artifacts[0], path="subjects")
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).diagnostic, "NOT_REGULAR_FILE")

    def test_fifo_rejected_without_blocking(self):
        ref = replace(self.bundle.candidate.artifacts[0], path="pipe")
        os.mkfifo(self.root / "pipe")
        with ArtifactStore(self.root) as store:
            self.assertEqual(store.check(ref).diagnostic, "NOT_REGULAR_FILE")

    def test_store_use_after_close_rejected(self):
        store = ArtifactStore(self.root)
        with store:
            pass
        with self.assertRaisesRegex(ContractError, "ARTIFACT_STORE_CLOSED"):
            store.check(self.bundle.candidate.artifacts[0])

    def test_unsupported_platform_fails_closed(self):
        with patch("bie.qa.release_v2.artifacts.os.supports_dir_fd", set()):
            with self.assertRaisesRegex(ContractError, "SECURE_ARTIFACT_IO_UNSUPPORTED"):
                with ArtifactStore(self.root):
                    pass

    def test_file_change_during_read_rejected(self):
        ref = self.bundle.candidate.artifacts[0]
        real_read = os.read
        changed = False
        def change_after_read(fd, size):
            nonlocal changed
            data = real_read(fd, size)
            if data and not changed:
                changed = True
                (self.root / ref.path).write_bytes(b"Y" * ref.size)
            return data
        with ArtifactStore(self.root) as store, patch("bie.qa.release_v2.artifacts.os.read", change_after_read):
            self.assertEqual(store.check(ref).diagnostic, "ARTIFACT_CHANGED_DURING_READ")

    def test_failed_read_returns_no_pass(self):
        with ArtifactStore(self.root) as store, patch("bie.qa.release_v2.artifacts.os.read", side_effect=OSError("test")):
            self.assertEqual(store.check(self.bundle.candidate.artifacts[0]).status, "ERROR")

    def test_root_error_blocks_whole_release(self):
        from bie.qa.release_v2 import ReleaseEvaluator
        from helpers import NOW
        result = ReleaseEvaluator(self.policy, self.verifier).evaluate(self.bundle, self.root / "missing", as_of=NOW)
        self.assertBlocked(result)
        self.assertIn("ARTIFACT_ROOT_UNAVAILABLE", result.global_diagnostics)


if __name__ == "__main__":
    unittest.main()
