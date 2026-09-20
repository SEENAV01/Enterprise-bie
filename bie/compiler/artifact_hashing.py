"""BUILD-010: deterministic, root-confined artifact integrity (not acceptance)."""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json
import os
import re
import stat
from typing import Any, Iterable, Iterator
from .build_common import BuildError

_HEX = re.compile(r"^[0-9a-f]{64}$")

def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BuildError("value is not finite canonical JSON") from exc

def require_sha256(value: str, name: str = "sha256") -> str:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise BuildError(f"{name} must be a lowercase SHA-256 digest")
    return value

def safe_relative(value: str) -> str:
    if (not isinstance(value, str) or not value or "\\" in value
            or any(ord(c) < 32 for c in value)):
        raise BuildError("invalid relative path")
    parts = value.split("/")
    if any(p in {"", ".", ".."} for p in parts) or ":" in parts[0]:
        raise BuildError("path must be normalized and relative")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise BuildError("absolute path rejected")
    return path.as_posix()

def confined_path(root: str | Path, relative: str, *, must_exist: bool = False) -> Path:
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise BuildError("root must be an existing non-symlink directory")
    root = root.resolve()
    relative = safe_relative(relative)
    current = root
    for part in relative.split("/"):
        current = current / part
        if current.is_symlink():
            raise BuildError("symlink paths rejected")
    if not current.resolve().is_relative_to(root):
        raise BuildError("path escapes root")
    if must_exist and not current.is_file():
        raise BuildError(f"required regular file missing: {relative}")
    return current

@contextmanager
def _open_confined(root: Path, relative: str) -> Iterator[Any]:
    """On POSIX, walk each directory using O_NOFOLLOW, not a check/open pair."""
    target = confined_path(root, relative, must_exist=True)
    if os.name != "posix":
        # Hashing remains usable elsewhere; the render process adapter is POSIX-only.
        with target.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise BuildError("not a regular file")
            yield stream
        return
    descriptors: list[int] = []
    try:
        fd = os.open(root.resolve(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(fd)
        parts = safe_relative(relative).split("/")
        for part in parts[:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            descriptors.append(fd)
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        with os.fdopen(file_fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise BuildError("not a regular file")
            yield stream
    except OSError as exc:
        raise BuildError("confined artifact read failed") from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)

@dataclass(frozen=True)
class ArtifactDigest:
    path: str
    size_bytes: int
    sha256: str

@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: str
    binding_sha256: str
    artifacts: tuple[ArtifactDigest, ...]
    manifest_sha256: str
    accepted: bool = False

@dataclass(frozen=True)
class ArtifactVerification:
    passed: bool
    checked: int
    errors: tuple[str, ...]
    accepted: bool = False

def hash_artifact(root: str | Path, relative: str, *, allow_empty: bool = False) -> ArtifactDigest:
    root = Path(root)
    relative = safe_relative(relative)
    hasher = sha256()
    total = 0
    with _open_confined(root, relative) as stream:
        before = os.fstat(stream.fileno())
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(chunk)
            hasher.update(chunk)
        after = os.fstat(stream.fileno())
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    latest = confined_path(root, relative, must_exist=True).stat()
    if signature(before) != signature(after) or signature(after) != signature(latest) or total != after.st_size:
        raise BuildError("artifact changed during hashing")
    if not total and not allow_empty:
        raise BuildError("empty artifact rejected")
    return ArtifactDigest(relative, total, hasher.hexdigest())

def _manifest_body(binding: str, artifacts: Iterable[ArtifactDigest]) -> dict:
    return {"schema_version": "bie.artifacts.v1", "binding_sha256": binding,
            "artifacts": [asdict(a) for a in artifacts], "accepted": False}

def hash_artifacts(root: str | Path, paths: Iterable[str], *, binding_sha256: str,
                   allow_empty: bool = False) -> ArtifactManifest:
    require_sha256(binding_sha256, "binding_sha256")
    paths = tuple(safe_relative(p) for p in paths)
    if not paths or len(paths) != len(set(paths)):
        raise BuildError("artifact paths must be nonempty and unique")
    artifacts = tuple(hash_artifact(root, p, allow_empty=allow_empty) for p in sorted(paths))
    digest = sha256(canonical_json(_manifest_body(binding_sha256, artifacts))).hexdigest()
    return ArtifactManifest("bie.artifacts.v1", binding_sha256, artifacts, digest)

def verify_artifacts(root: str | Path, manifest: ArtifactManifest) -> ArtifactVerification:
    errors: list[str] = []
    try:
        require_sha256(manifest.binding_sha256)
        require_sha256(manifest.manifest_sha256)
        paths = [safe_relative(a.path) for a in manifest.artifacts]
        if (manifest.schema_version != "bie.artifacts.v1" or manifest.accepted
                or not paths or paths != sorted(set(paths))):
            raise BuildError("invalid manifest structure")
        for item in manifest.artifacts:
            require_sha256(item.sha256)
            if type(item.size_bytes) is not int or item.size_bytes < 0:
                raise BuildError("invalid artifact size")
        expected = sha256(canonical_json(_manifest_body(manifest.binding_sha256, manifest.artifacts))).hexdigest()
        if expected != manifest.manifest_sha256:
            errors.append("MANIFEST_DIGEST_MISMATCH")
    except (BuildError, AttributeError, TypeError) as exc:
        return ArtifactVerification(False, 0, (f"INVALID_MANIFEST: {exc}",))
    checked = 0
    for item in manifest.artifacts:
        try:
            actual = hash_artifact(root, item.path, allow_empty=True)
            checked += 1
            if actual != item:
                errors.append(f"ARTIFACT_MISMATCH: {item.path}")
        except (BuildError, OSError) as exc:
            errors.append(f"ARTIFACT_UNREADABLE: {item.path}: {exc}")
    return ArtifactVerification(not errors, checked, tuple(errors))

def manifest_from_dict(value: dict) -> ArtifactManifest:
    try:
        if set(value) != {"schema_version", "binding_sha256", "artifacts", "manifest_sha256", "accepted"}:
            raise BuildError("unexpected manifest fields")
        return ArtifactManifest(value["schema_version"], value["binding_sha256"],
                                tuple(ArtifactDigest(**a) for a in value["artifacts"]),
                                value["manifest_sha256"], value["accepted"])
    except (KeyError, TypeError) as exc:
        raise BuildError("invalid artifact manifest") from exc
