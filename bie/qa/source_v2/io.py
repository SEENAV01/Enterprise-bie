"""Bounded, one-descriptor snapshot reads; verifies the bytes actually consumed.

Additive reader: leaves Batch001 ArtifactStore untouched. POSIX-only fail-closed
confinement. An immutable operator-owned root is still a deployment requirement.
"""
from __future__ import annotations
import hashlib, os, stat
from pathlib import Path
from ..release_v2.contracts import ArtifactRef, ContractError, safe_relative_path
from .models import MAX_SOURCE_BYTES, MAX_TOTAL_BYTES

class SnapshotStore:
    def __init__(self, root: str | Path):
        self.root = Path(root); self._fd = None; self.total = 0

    def __enter__(self):
        if self._fd is not None: raise ContractError('STORE_ALREADY_OPEN')
        if not all(hasattr(os, x) for x in ('O_NOFOLLOW', 'O_DIRECTORY', 'O_NONBLOCK')) or os.open not in os.supports_dir_fd:
            raise ContractError('SECURE_ARTIFACT_IO_UNSUPPORTED')
        try: self._fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc: raise ContractError('ARTIFACT_ROOT_UNAVAILABLE') from exc
        self.total = 0
        return self

    def __exit__(self, *_):
        if self._fd is not None: os.close(self._fd); self._fd = None

    def read(self, ref: ArtifactRef) -> bytes:
        if type(ref) is not ArtifactRef: raise ContractError('INVALID_ARTIFACT_TYPE')
        if self._fd is None: raise ContractError('ARTIFACT_STORE_CLOSED')
        if ref.size > MAX_SOURCE_BYTES: raise ContractError('SOURCE_SIZE_LIMIT')
        if self.total + ref.size > MAX_TOTAL_BYTES: raise ContractError('TOTAL_SOURCE_IO_LIMIT')
        parts = safe_relative_path(ref.path).split('/')
        directory = os.dup(self._fd); fd = None
        try:
            for part in parts[:-1]:
                new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory); directory = new
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode): raise ContractError('NOT_REGULAR_FILE')
            if before.st_nlink != 1: raise ContractError('HARD_LINK_REJECTED')
            if before.st_size != ref.size: raise ContractError('ARTIFACT_SIZE_MISMATCH')
            chunks=[]; count=0
            while True:
                chunk = os.read(fd, min(1024*1024, ref.size-count+1))
                if not chunk: break
                count += len(chunk)
                if count > ref.size: raise ContractError('ARTIFACT_READ_LIMIT')
                chunks.append(chunk)
            after = os.fstat(fd)
            if any(getattr(before,x)!=getattr(after,x) for x in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_nlink')):
                raise ContractError('ARTIFACT_CHANGED_DURING_READ')
            payload=b''.join(chunks)
            if len(payload) != ref.size: raise ContractError('ARTIFACT_SIZE_MISMATCH')
            if hashlib.sha256(payload).hexdigest()!=ref.sha256: raise ContractError('ARTIFACT_HASH_MISMATCH')
            self.total += len(payload)
            return payload
        except OSError as exc:
            raise ContractError('ARTIFACT_OPEN_OR_READ_FAILED') from exc
        finally:
            if fd is not None: os.close(fd)
            os.close(directory)
