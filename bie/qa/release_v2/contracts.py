"""BIE-QA-RELEASE-001: strict, immutable evidence contracts (additive v2).

This module deliberately does not alter bie.qa.release_contracts. Hashes provide
content identity, not factual correctness. Evaluators and signer authorization are
separate trust boundaries. All time inputs are supplied explicitly for replay.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any

VERSION = "2.0.0"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_ARTIFACTS = 2048
MAX_EVIDENCE = 1024
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z", re.ASCII)
_SHA = re.compile(r"[a-f0-9]{64}\Z", re.ASCII)
_REV = re.compile(r"[a-f0-9]{40}\Z", re.ASCII)
_PATH_PART = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z", re.ASCII)


class ContractError(ValueError):
    """Stable diagnostic code plus a non-secret contract field location."""

    def __init__(self, code: str, field: str = "") -> None:
        self.code = code
        self.field = field
        super().__init__(f"{code}: {field}" if field else code)


def token(value: Any, field: str) -> str:
    if type(value) is not str or not _TOKEN.fullmatch(value):
        raise ContractError("INVALID_TOKEN", field)
    return value


def sha256(value: Any, field: str) -> str:
    if type(value) is not str or not _SHA.fullmatch(value):
        raise ContractError("INVALID_SHA256", field)
    return value


def integer(value: Any, field: str, minimum: int = 0, maximum: int = 2**53 - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ContractError("INVALID_INTEGER", field)
    return value


def choice(value: Any, choices: tuple[str, ...], field: str) -> str:
    if type(value) is not str or value not in choices:
        raise ContractError("INVALID_ENUM", field)
    return value


def version(value: Any) -> None:
    if type(value) is not str or value != VERSION:
        raise ContractError("UNSUPPORTED_SCHEMA", "schema_version")


def revision(value: Any) -> None:
    if type(value) is not str or not _REV.fullmatch(value):
        raise ContractError("INVALID_REVISION", "revision")


def tuple_tokens(value: Any, field: str, minimum: int = 0, maximum: int = MAX_ARTIFACTS) -> None:
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        raise ContractError("INVALID_TUPLE", field)
    for item in value:
        token(item, field)
    if len(set(value)) != len(value):
        raise ContractError("DUPLICATE_VALUE", field)


def safe_relative_path(value: Any) -> str:
    # Portable ASCII storage keys, not user-facing titles. URLs and platform drive
    # syntax are intentionally unsupported. Unicode titles belong in metadata.
    if type(value) is not str or not 1 <= len(value) <= 512:
        raise ContractError("UNSAFE_PATH", "path")
    parts = value.split("/")
    if any(part in ("", ".", "..") or not _PATH_PART.fullmatch(part) for part in parts):
        raise ContractError("UNSAFE_PATH", "path")
    return value


def _check_json(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ContractError("JSON_TOO_DEEP")
    if value is None or type(value) in (str, bool, int):
        if type(value) is str:
            try:
                value.encode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise ContractError("INVALID_UNICODE") from exc
        return
    if type(value) in (list, tuple):
        for item in value:
            _check_json(item, depth + 1)
        return
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            raise ContractError("NON_STRING_JSON_KEY")
        for key, item in value.items():
            _check_json(key, depth + 1)
            _check_json(item, depth + 1)
        return
    raise ContractError("NON_CANONICAL_JSON_TYPE")


def canonical_bytes(value: Any) -> bytes:
    """Versioned project encoding: UTF-8, sorted keys, integers only, no coercion.

    This is not claimed to implement an external canonical-JSON standard.
    """
    _check_json(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    path: str
    sha256: str
    size: int
    role: str

    def __post_init__(self) -> None:
        token(self.artifact_id, "artifact_id")
        safe_relative_path(self.path)
        sha256(self.sha256, "artifact.sha256")
        integer(self.size, "artifact.size", 1, MAX_FILE_BYTES)
        choice(self.role, ("source", "video", "game", "support", "report"), "artifact.role")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    schema_version: str
    candidate_id: str
    run_id: str
    revision: str
    artifacts: tuple[ArtifactRef, ...]

    def __post_init__(self) -> None:
        version(self.schema_version)
        token(self.candidate_id, "candidate_id")
        token(self.run_id, "run_id")
        revision(self.revision)
        if type(self.artifacts) is not tuple or not 3 <= len(self.artifacts) <= MAX_ARTIFACTS:
            raise ContractError("INVALID_ARTIFACT_COLLECTION")
        if any(type(a) is not ArtifactRef for a in self.artifacts):
            raise ContractError("INVALID_ARTIFACT_TYPE")
        if len({a.artifact_id for a in self.artifacts}) != len(self.artifacts):
            raise ContractError("DUPLICATE_ARTIFACT_ID")
        if len({a.path for a in self.artifacts}) != len(self.artifacts):
            raise ContractError("DUPLICATE_ARTIFACT_PATH")
        roles = {a.role for a in self.artifacts}
        if not {"source", "video", "game"}.issubset(roles) or "report" in roles:
            raise ContractError("INCOMPLETE_PRODUCT_SCOPE")
        if sum(a.size for a in self.artifacts) > MAX_TOTAL_BYTES:
            raise ContractError("ARTIFACT_TOTAL_LIMIT")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["artifacts"] = [a.to_dict() for a in sorted(self.artifacts, key=lambda a: a.artifact_id)]
        return data

    @property
    def content_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class GateEvidence:
    schema_version: str
    evidence_id: str
    gate_id: str
    candidate_digest: str
    policy_digest: str
    run_id: str
    revision: str
    status: str
    evaluator_id: str
    evaluator_version: str
    kind: str
    inspected_artifact_ids: tuple[str, ...]
    report: ArtifactRef
    created_at: int
    expires_at: int
    diagnostics: tuple[str, ...]
    signer_key_id: str
    signature: str = ""

    def __post_init__(self) -> None:
        version(self.schema_version)
        for name in ("evidence_id", "gate_id", "run_id", "evaluator_id", "evaluator_version", "signer_key_id"):
            token(getattr(self, name), name)
        sha256(self.candidate_digest, "candidate_digest")
        sha256(self.policy_digest, "policy_digest")
        revision(self.revision)
        choice(self.status, ("PASS", "FAIL", "ERROR", "SKIPPED", "NOT_RUN"), "status")
        choice(self.kind, ("execution", "review", "fixture", "declaration", "historical"), "kind")
        tuple_tokens(self.inspected_artifact_ids, "inspected_artifact_ids", 1)
        if type(self.report) is not ArtifactRef or self.report.role != "report":
            raise ContractError("INVALID_REPORT")
        integer(self.created_at, "created_at")
        integer(self.expires_at, "expires_at", self.created_at + 1)
        tuple_tokens(self.diagnostics, "diagnostics", 0, 128)
        if self.status != "PASS" and not self.diagnostics:
            raise ContractError("MISSING_FAILURE_DIAGNOSTIC")
        if self.signature != "":
            sha256(self.signature, "signature")
        elif type(self.signature) is not str:
            raise ContractError("INVALID_SIGNATURE")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["inspected_artifact_ids"] = sorted(self.inspected_artifact_ids)
        data["diagnostics"] = sorted(self.diagnostics)
        return data

    def signing_bytes(self) -> bytes:
        data = self.to_dict()
        del data["signature"]
        return b"BIE-QA-EVIDENCE-V2\x00" + canonical_bytes(data)


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    schema_version: str
    candidate: ReleaseCandidate
    evidence: tuple[GateEvidence, ...]

    def __post_init__(self) -> None:
        version(self.schema_version)
        if type(self.candidate) is not ReleaseCandidate:
            raise ContractError("INVALID_CANDIDATE_TYPE")
        if type(self.evidence) is not tuple or len(self.evidence) > MAX_EVIDENCE:
            raise ContractError("INVALID_EVIDENCE_COLLECTION")
        if any(type(e) is not GateEvidence for e in self.evidence):
            raise ContractError("INVALID_EVIDENCE_TYPE")
        if len({e.evidence_id for e in self.evidence}) != len(self.evidence):
            raise ContractError("DUPLICATE_EVIDENCE_ID")
        # An ID or path cannot secretly refer to two different content versions.
        by_id = {a.artifact_id: a for a in self.candidate.artifacts}
        by_path = {a.path: a for a in self.candidate.artifacts}
        for ev in self.evidence:
            ref = ev.report
            if (ref.artifact_id in by_id and by_id[ref.artifact_id] != ref) or (
                ref.path in by_path and by_path[ref.path] != ref
            ):
                raise ContractError("AMBIGUOUS_ARTIFACT_BINDING")
            by_id[ref.artifact_id] = ref
            by_path[ref.path] = ref
        if sum(a.size for a in by_id.values()) > MAX_TOTAL_BYTES:
            raise ContractError("ARTIFACT_TOTAL_LIMIT")

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "candidate": self.candidate.to_dict(),
                "evidence": [e.to_dict() for e in sorted(self.evidence, key=lambda e: e.evidence_id)]}

    @property
    def content_digest(self) -> str:
        return digest(self.to_dict())
