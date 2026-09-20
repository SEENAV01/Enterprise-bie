"""Shared contracts for COMP-QA-001..005; no acceptance or baseline auto-blessing."""
from __future__ import annotations
from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable
import json
from .artifact_hashing import canonical_json, safe_relative, confined_path, require_sha256
from .build_common import BuildError

class CompilerQAError(BuildError):
    """An invalid QA contract, unsafe path, or incomplete evidence was supplied."""


def token(value: str, name: str = "identifier") -> str:
    if (not isinstance(value, str) or not value.strip() or
            any(ord(c) < 32 for c in value)):
        raise CompilerQAError(f"{name} must be nonblank text without control characters")
    return value


def digest(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


def positive_int(value: int, name: str) -> int:
    if type(value) is not int or value < 1:
        raise CompilerQAError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class QAFinding:
    code: str
    severity: str
    message: str
    path: str = "$"
    owner: str = "COMP"
    def __post_init__(self) -> None:
        for name in ("code", "message", "path", "owner"):
            token(getattr(self, name), name)
        if self.severity not in {"ERROR", "WARNING", "INFO"}:
            raise CompilerQAError("invalid QA severity")


def ordered_findings(items: Iterable[QAFinding]) -> tuple[QAFinding, ...]:
    return tuple(sorted(set(items), key=lambda f: (
        {"ERROR": 0, "WARNING": 1, "INFO": 2}[f.severity], f.path, f.code, f.message, f.owner)))


def source_files(files: Iterable[Any]) -> tuple[tuple[str, str, str], ...]:
    """Validate both names and content hashes; never trust a supplied hash alone."""
    result = []
    seen: set[str] = set()
    for f in files:
        if isinstance(f, tuple) and len(f) == 2:
            path, content = f
            supplied = None
        else:
            path, content = f.path, f.content
            supplied = getattr(f, "sha256", None)
        path = safe_relative(path)
        if path in seen:
            raise CompilerQAError("duplicate source path: " + path)
        if not isinstance(content, str):
            raise CompilerQAError("source content must be UTF-8 text")
        actual = sha256(content.encode("utf-8")).hexdigest()
        if supplied is not None and supplied != actual:
            raise CompilerQAError("source content hash mismatch: " + path)
        seen.add(path)
        result.append((path, content, actual))
    if not result:
        raise CompilerQAError("empty source tree is not a passing QA input")
    return tuple(sorted(result))


def write_json(path: Path, value: Any, *, exclusive: bool = True) -> None:
    """Write local receipts; callers choose a fresh evidence directory."""
    if is_dataclass(value):
        value = asdict(value)
    # Validate finite values before touching output.
    canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False,
                                sort_keys=True, indent=2) + "\n")
