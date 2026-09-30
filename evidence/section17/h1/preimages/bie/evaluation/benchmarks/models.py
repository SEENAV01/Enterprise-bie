"""Strict, immutable, content-addressed benchmark records (BIE-EVAL-REG-001).

JSON is data, never a program. Source references are explicitly distinguished
from captured source bytes; an authored fixture is never a hidden golden set.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json
import math
import re
import unicodedata
from typing import Any

class BenchmarkError(ValueError):
    """Stable fail-closed error used at all untrusted-data boundaries."""
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
SPLITS = frozenset({"DEVELOPMENT", "CALIBRATION", "HOLDOUT"})
MAX_BYTES = 2_000_000


def ident(value: Any) -> str:
    if type(value) is not str or ID.fullmatch(value) is None:
        raise BenchmarkError("INVALID_ID")
    return value


def text(value: Any, maximum: int = 20000) -> str:
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise BenchmarkError("INVALID_TEXT")
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        raise BenchmarkError("CONTROL_CHARACTER")
    return value


def number(value: Any, *, maximum: float = 1e100) -> float:
    if type(value) not in (int, float):
        raise BenchmarkError("INVALID_NUMBER")
    try:
        n = float(value)
    except (OverflowError, ValueError) as exc:
        raise BenchmarkError("INVALID_NUMBER") from exc
    if not math.isfinite(n) or abs(n) > maximum:
        raise BenchmarkError("NONFINITE_OR_OUT_OF_RANGE")
    return n


def digest_string(value: Any) -> str:
    if type(value) is not str or SHA.fullmatch(value) is None:
        raise BenchmarkError("INVALID_DIGEST")
    return value


def version_tuple(value: Any) -> tuple[int, int, int]:
    if type(value) is not str or len(value) > 50 or VERSION.fullmatch(value) is None:
        raise BenchmarkError("INVALID_VERSION")
    return tuple(int(x) for x in value.split("."))  # type: ignore[return-value]


def _validate_json(value: Any, depth: int = 0) -> None:
    if depth > 24:
        raise BenchmarkError("JSON_DEPTH_LIMIT")
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        number(value)
    elif type(value) is str:
        if len(value) > MAX_BYTES:
            raise BenchmarkError("JSON_SIZE_LIMIT")
    elif type(value) is list:
        if len(value) > 10000:
            raise BenchmarkError("JSON_COLLECTION_LIMIT")
        for item in value:
            _validate_json(item, depth + 1)
    elif type(value) is dict:
        if len(value) > 10000 or any(type(k) is not str for k in value):
            raise BenchmarkError("INVALID_JSON_OBJECT")
        for k, v in value.items():
            _validate_json(k, depth + 1)
            _validate_json(v, depth + 1)
    else:
        raise BenchmarkError("INVALID_JSON_TYPE")


def canonical_json(value: Any) -> str:
    _validate_json(value)
    out = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False)
    if len(out.encode("utf-8")) > MAX_BYTES:
        raise BenchmarkError("JSON_SIZE_LIMIT")
    return out


def strict_loads(raw: str | bytes) -> Any:
    if type(raw) not in (str, bytes) or len(raw) > MAX_BYTES:
        raise BenchmarkError("JSON_SIZE_LIMIT")
    def pairs(items: list[tuple[str, Any]]) -> dict:
        out: dict = {}
        for k, v in items:
            if k in out:
                raise BenchmarkError("DUPLICATE_JSON_KEY", k)
            out[k] = v
        return out
    def reject_constant(value: str) -> None:
        raise BenchmarkError("NONFINITE_JSON", value)
    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)
        canonical_json(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, BenchmarkError):
            raise
        raise BenchmarkError("INVALID_JSON") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def exact_fields(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    if type(value) is not dict or not required <= value.keys() or value.keys() - required - optional:
        raise BenchmarkError("INVALID_FIELDS")
    return value


@dataclass(frozen=True)
class SourceReference:
    reference_id: str
    title: str
    locator: str
    url: str
    rights: str
    evidence_kind: str = "REFERENCE_ONLY"

    def __post_init__(self) -> None:
        ident(self.reference_id)
        for s in (self.title, self.locator, self.rights):
            text(s)
        if type(self.url) is not str or not self.url.startswith("https://") or len(self.url) > 2048:
            raise BenchmarkError("INVALID_SOURCE_URL")
        if self.evidence_kind != "REFERENCE_ONLY":
            raise BenchmarkError("UNSUPPORTED_SOURCE_EVIDENCE_KIND")

    @classmethod
    def from_dict(cls, value: dict) -> SourceReference:
        exact_fields(value, {"reference_id", "title", "locator", "url", "rights", "evidence_kind"})
        return cls(**value)


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    task_id: str
    domain: str
    title: str
    prompt: str
    inputs_json: str
    expected_json: str
    split: str
    leakage_group: str
    author_id: str
    derivation: str
    sources: tuple[SourceReference, ...]
    tags: tuple[str, ...]
    absolute_tolerance: float = 1e-9
    relative_tolerance: float = 1e-9
    evidence_grade: str = "AUTHORED_DIAGNOSTIC"

    def __post_init__(self) -> None:
        for value in (self.case_id, self.task_id, self.domain, self.leakage_group, self.author_id):
            ident(value)
        if not self.task_id.startswith("BIE-EVAL-"):
            raise BenchmarkError("INVALID_TASK_ID")
        for value in (self.title, self.prompt, self.derivation):
            text(value)
        if self.split not in SPLITS:
            raise BenchmarkError("INVALID_SPLIT")
        if self.evidence_grade not in {"AUTHORED_DIAGNOSTIC", "REFERENCE_CANDIDATE"}:
            raise BenchmarkError("INVALID_EVIDENCE_GRADE")
        if type(self.sources) is not tuple or not self.sources or any(type(x) is not SourceReference for x in self.sources):
            raise BenchmarkError("SOURCE_REQUIRED")
        if len({s.reference_id for s in self.sources}) != len(self.sources):
            raise BenchmarkError("DUPLICATE_SOURCE")
        if type(self.tags) is not tuple or not self.tags or len(set(self.tags)) != len(self.tags):
            raise BenchmarkError("INVALID_TAGS")
        for tag in self.tags:
            ident(tag)
        for tol in (self.absolute_tolerance, self.relative_tolerance):
            if not 0 <= number(tol) <= 0.01:
                raise BenchmarkError("INVALID_TOLERANCE")
        for raw in (self.inputs_json, self.expected_json):
            if type(raw) is not str:
                raise BenchmarkError("INVALID_JSON_TEXT")
            obj = strict_loads(raw)
            if type(obj) is not dict or canonical_json(obj) != raw:
                raise BenchmarkError("NONCANONICAL_PAYLOAD")

    @classmethod
    def create(cls, *, inputs: dict, expected: dict, **kwargs: Any) -> BenchmarkCase:
        return cls(inputs_json=canonical_json(inputs), expected_json=canonical_json(expected), **kwargs)

    def to_dict(self) -> dict:
        value = asdict(self)
        value["sources"] = [asdict(s) for s in self.sources]
        value["tags"] = list(self.tags)
        return value

    @classmethod
    def from_dict(cls, value: dict) -> BenchmarkCase:
        exact_fields(value, set(cls.__dataclass_fields__))
        data = dict(value)
        if type(data["sources"]) is not list or type(data["tags"]) is not list:
            raise BenchmarkError("INVALID_COLLECTION")
        data["sources"] = tuple(SourceReference.from_dict(s) for s in data["sources"])
        data["tags"] = tuple(data["tags"])
        return cls(**data)

    @property
    def content_sha256(self) -> str:
        return digest(self.to_dict())

    @property
    def inputs(self) -> dict:
        return strict_loads(self.inputs_json)

    @property
    def expected(self) -> dict:
        return strict_loads(self.expected_json)

    @property
    def problem_fingerprint(self) -> str:
        # Identity/wording/split/expected answer cannot hide an identical problem.
        return digest({"task_id": self.task_id, "inputs": self.inputs})

    @property
    def prompt_fingerprint(self) -> str:
        normalized = " ".join(unicodedata.normalize("NFKC", self.prompt).casefold().split())
        return digest(normalized)

    def candidate_view(self) -> dict:
        # No reference answers, derivation, reviewer notes or source answer text.
        return {"case_id": self.case_id, "task_id": self.task_id,
                "prompt": self.prompt, "inputs": self.inputs}
