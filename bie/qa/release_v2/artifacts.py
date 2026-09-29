"""Read-only, bounded artifact verification relative to a trusted directory FD.

No shell, network, media execution or archive extraction. The POSIX implementation
rejects symlinks, hard links and non-regular files. Unsupported platforms fail
closed. Deployments must additionally supply an immutable, operator-owned store.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat

from .contracts import ArtifactRef, ContractError, MAX_FILE_BYTES, safe_relative_path


@dataclass(frozen=True, slots=True)
class ArtifactCheck:
    artifact_id: str
    path: str
    status: str
    diagnostic: str
    expected_sha256: str
    actual_sha256: str = ""
    bytes_read: int = 0


class ArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._fd: int | None = None

    def __enter__(self) -> "ArtifactStore":
        if self._fd is not None:
            raise ContractError("STORE_ALREADY_OPEN")
        if not all(hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")) or (
            os.open not in os.supports_dir_fd
        ):
            raise ContractError("SECURE_ARTIFACT_IO_UNSUPPORTED")
        try:
            self._fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise ContractError("ARTIFACT_ROOT_UNAVAILABLE") from exc
        return self

    def __exit__(self, *_: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def check(self, reference: ArtifactRef) -> ArtifactCheck:
        if type(reference) is not ArtifactRef:
            raise ContractError("INVALID_ARTIFACT_TYPE")
        if self._fd is None:
            raise ContractError("ARTIFACT_STORE_CLOSED")
        # Revalidate even if a caller bypassed dataclass construction.
        parts = safe_relative_path(reference.path).split("/")
        directory_fd = os.dup(self._fd)
        file_fd: int | None = None
        actual = ""
        count = 0
        code = "VERIFIED"
        try:
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                  dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                              dir_fd=directory_fd)
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode):
                raise ContractError("NOT_REGULAR_FILE")
            if before.st_nlink != 1:
                raise ContractError("HARD_LINK_REJECTED")
            if before.st_size != reference.size:
                raise ContractError("ARTIFACT_SIZE_MISMATCH")
            digest = hashlib.sha256()
            while True:
                chunk = os.read(file_fd, 1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > reference.size or count > MAX_FILE_BYTES:
                    raise ContractError("ARTIFACT_READ_LIMIT")
                digest.update(chunk)
            after = os.fstat(file_fd)
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
            if any(getattr(before, name) != getattr(after, name) for name in fields):
                raise ContractError("ARTIFACT_CHANGED_DURING_READ")
            if count != reference.size:
                raise ContractError("ARTIFACT_SIZE_MISMATCH")
            actual = digest.hexdigest()
            if actual != reference.sha256:
                raise ContractError("ARTIFACT_HASH_MISMATCH")
        except ContractError as exc:
            code = exc.code
        except OSError:
            code = "ARTIFACT_OPEN_OR_READ_FAILED"
        finally:
            if file_fd is not None:
                os.close(file_fd)
            os.close(directory_fd)
        return ArtifactCheck(reference.artifact_id, reference.path,
                             "PASS" if code == "VERIFIED" else "ERROR", code,
                             reference.sha256, actual, count)
