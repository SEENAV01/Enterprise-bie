"""Bounded, closed-world JSON wire codec; unknown fields never become authority."""
from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
from typing import Any

from .contracts import (ArtifactRef, ContractError, EvidenceBundle, GateEvidence,
                        MAX_JSON_BYTES, ReleaseCandidate, canonical_bytes, _check_json)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def _no_float(value: str) -> Any:
    raise ContractError("NON_INTEGER_JSON_NUMBER")


def _shape(value: Any, cls: type) -> dict[str, Any]:
    if type(value) is not dict:
        raise ContractError("EXPECTED_OBJECT", cls.__name__)
    if any(type(key) is not str for key in value):
        raise ContractError("NON_STRING_JSON_KEY", cls.__name__)
    expected = {f.name for f in fields(cls)}
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise ContractError("OBJECT_FIELDS_MISMATCH", f"{cls.__name__}:missing={missing};extra={extra}")
    return dict(value)


def _array(value: Any, name: str) -> tuple:
    if type(value) is not list:
        raise ContractError("EXPECTED_ARRAY", name)
    return tuple(value)


def artifact_from_dict(value: Any) -> ArtifactRef:
    return ArtifactRef(**_shape(value, ArtifactRef))


def bundle_from_dict(value: Any) -> EvidenceBundle:
    data = _shape(value, EvidenceBundle)
    candidate_data = _shape(data["candidate"], ReleaseCandidate)
    candidate_data["artifacts"] = tuple(artifact_from_dict(a) for a in
                                        _array(candidate_data["artifacts"], "artifacts"))
    candidate = ReleaseCandidate(**candidate_data)
    records = []
    for item in _array(data["evidence"], "evidence"):
        record = _shape(item, GateEvidence)
        record["report"] = artifact_from_dict(record["report"])
        for name in ("inspected_artifact_ids", "diagnostics"):
            record[name] = _array(record[name], name)
        records.append(GateEvidence(**record))
    return EvidenceBundle(data["schema_version"], candidate, tuple(records))


def loads(data: bytes) -> EvidenceBundle:
    if type(data) is not bytes or not data or len(data) > MAX_JSON_BYTES:
        raise ContractError("JSON_SIZE_OR_TYPE")
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_object,
                           parse_float=_no_float, parse_constant=_no_float)
        _check_json(value)
        return bundle_from_dict(value)
    except ContractError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ContractError("MALFORMED_JSON") from exc


def load(path: str | Path) -> EvidenceBundle:
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    return loads(data)


def dumps(bundle: EvidenceBundle) -> bytes:
    if type(bundle) is not EvidenceBundle:
        raise ContractError("INVALID_BUNDLE_TYPE")
    data = canonical_bytes(bundle.to_dict())
    if len(data) > MAX_JSON_BYTES:
        raise ContractError("JSON_SIZE_OR_TYPE")
    return data
