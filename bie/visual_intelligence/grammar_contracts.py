from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from typing import Any, Iterable, Mapping, Sequence
import json


class GrammarValidationError(ValueError):
    """Base class for deterministic visual-grammar validation failures."""


class GrammarElementError(GrammarValidationError):
    pass


class GrammarRelationError(GrammarValidationError):
    pass


def _clean_token(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise GrammarValidationError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise GrammarValidationError(f"{field_name} must not be blank")
    return value


def clean_ids(values: Iterable[Any], *, field_name: str, allow_empty: bool = False) -> tuple[str, ...]:
    if values is None:
        values = ()
    cleaned = tuple(_clean_token(v, field_name=field_name) for v in values)
    if not allow_empty and not cleaned:
        raise GrammarValidationError(f"{field_name} must contain at least one id")
    if len(set(cleaned)) != len(cleaned):
        raise GrammarValidationError(f"{field_name} contains duplicate ids")
    return cleaned


def finite_number(value: Any, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GrammarValidationError(f"{field_name} must be numeric")
    number = float(value)
    if not isfinite(number):
        raise GrammarValidationError(f"{field_name} must be finite")
    return number


def optional_finite_number(value: Any, *, field_name: str) -> float | None:
    if value is None:
        return None
    return finite_number(value, field_name=field_name)


def canonical_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): canonical_payload(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (list, tuple)):
        return [canonical_payload(v) for v in value]
    if isinstance(value, set):
        return sorted(canonical_payload(v) for v in value)
    if isinstance(value, float):
        if not isfinite(value):
            raise GrammarValidationError("payload contains non-finite float")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise GrammarValidationError(f"unsupported payload type: {type(value).__name__}")


def stable_fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(canonical_payload(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VisualGrammar:
    grammar_id: str
    version: str
    domains: tuple[str, ...]
    representations: tuple[str, ...]
    allowed_primitives: tuple[str, ...]
    required_roles: tuple[str, ...] = ()
    semantic_constraints: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "grammar_id", _clean_token(self.grammar_id, field_name="grammar_id"))
        object.__setattr__(self, "version", _clean_token(self.version, field_name="version"))
        for field_name in ("domains", "representations", "allowed_primitives"):
            value = clean_ids(getattr(self, field_name), field_name=field_name)
            object.__setattr__(self, field_name, value)
        for field_name in ("required_roles", "semantic_constraints", "aliases", "tags"):
            raw = getattr(self, field_name)
            value = clean_ids(raw, field_name=field_name, allow_empty=True)
            object.__setattr__(self, field_name, value)
        if self.grammar_id in self.aliases:
            raise GrammarValidationError("grammar_id cannot also be an alias")

    def snapshot(self) -> dict[str, Any]:
        return {
            "grammar_id": self.grammar_id,
            "version": self.version,
            "domains": list(self.domains),
            "representations": list(self.representations),
            "allowed_primitives": list(self.allowed_primitives),
            "required_roles": list(self.required_roles),
            "semantic_constraints": list(self.semantic_constraints),
            "aliases": list(self.aliases),
            "tags": list(self.tags),
            "description": self.description,
        }


@dataclass(frozen=True)
class GrammarPlan:
    grammar_id: str
    grammar_version: str
    evidence_refs: tuple[str, ...]
    reasoning_refs: tuple[str, ...]
    elements: tuple[dict[str, Any], ...]
    relations: tuple[dict[str, Any], ...]
    constraints: tuple[str, ...]
    warnings: tuple[str, ...]
    review_required: bool = True
    accepted: bool = False
    fingerprint: str = field(default="")

    def to_dict(self) -> dict[str, Any]:
        return {
            "grammar_id": self.grammar_id,
            "grammar_version": self.grammar_version,
            "evidence_refs": list(self.evidence_refs),
            "reasoning_refs": list(self.reasoning_refs),
            "elements": [canonical_payload(e) for e in self.elements],
            "relations": [canonical_payload(r) for r in self.relations],
            "constraints": list(self.constraints),
            "warnings": list(self.warnings),
            "review_required": self.review_required,
            "accepted": self.accepted,
            "fingerprint": self.fingerprint,
        }


def _normalize_element(element: Mapping[str, Any], grammar: VisualGrammar, evidence_refs: set[str]) -> dict[str, Any]:
    if not isinstance(element, Mapping):
        raise GrammarElementError("element must be a mapping")
    element_id = _clean_token(element.get("id"), field_name="element.id")
    role = _clean_token(element.get("role"), field_name=f"element[{element_id}].role")
    primitive = _clean_token(element.get("primitive"), field_name=f"element[{element_id}].primitive")
    if primitive not in grammar.allowed_primitives:
        raise GrammarElementError(f"primitive {primitive!r} is not allowed by {grammar.grammar_id}")
    source_ids = clean_ids(element.get("source_ids", ()), field_name=f"element[{element_id}].source_ids")
    unknown = set(source_ids) - evidence_refs
    if unknown:
        raise GrammarElementError(f"element {element_id} has unbound source ids: {sorted(unknown)}")
    label = element.get("label")
    if label is not None:
        label = _clean_token(label, field_name=f"element[{element_id}].label")
    payload = canonical_payload(element.get("payload", {}))
    if not isinstance(payload, dict):
        raise GrammarElementError(f"element {element_id} payload must be a mapping")
    return {
        "id": element_id,
        "role": role,
        "primitive": primitive,
        "label": label,
        "source_ids": list(source_ids),
        "payload": payload,
    }


def _normalize_relation(relation: Mapping[str, Any], element_ids: set[str], evidence_refs: set[str]) -> dict[str, Any]:
    if not isinstance(relation, Mapping):
        raise GrammarRelationError("relation must be a mapping")
    relation_id = _clean_token(relation.get("id"), field_name="relation.id")
    source = _clean_token(relation.get("source"), field_name=f"relation[{relation_id}].source")
    target = _clean_token(relation.get("target"), field_name=f"relation[{relation_id}].target")
    kind = _clean_token(relation.get("kind"), field_name=f"relation[{relation_id}].kind")
    if source not in element_ids or target not in element_ids:
        raise GrammarRelationError(f"relation {relation_id} references unknown elements")
    source_ids = clean_ids(relation.get("source_ids", ()), field_name=f"relation[{relation_id}].source_ids")
    unknown = set(source_ids) - evidence_refs
    if unknown:
        raise GrammarRelationError(f"relation {relation_id} has unbound source ids: {sorted(unknown)}")
    payload = canonical_payload(relation.get("payload", {}))
    if not isinstance(payload, dict):
        raise GrammarRelationError(f"relation {relation_id} payload must be a mapping")
    return {
        "id": relation_id,
        "source": source,
        "target": target,
        "kind": kind,
        "source_ids": list(source_ids),
        "payload": payload,
    }


def make_plan(
    grammar: VisualGrammar,
    *,
    evidence_refs: Sequence[str],
    reasoning_refs: Sequence[str],
    elements: Sequence[Mapping[str, Any]],
    relations: Sequence[Mapping[str, Any]] = (),
    constraints: Sequence[str] = (),
    warnings: Sequence[str] = (),
) -> GrammarPlan:
    evidence = clean_ids(evidence_refs, field_name="evidence_refs")
    reasoning = clean_ids(reasoning_refs, field_name="reasoning_refs")
    normalized_elements = tuple(_normalize_element(e, grammar, set(evidence)) for e in elements)
    if not normalized_elements:
        raise GrammarElementError("plan must contain at least one element")
    element_ids = [e["id"] for e in normalized_elements]
    if len(set(element_ids)) != len(element_ids):
        raise GrammarElementError("element ids must be unique")
    roles = {e["role"] for e in normalized_elements}
    missing_roles = set(grammar.required_roles) - roles
    if missing_roles:
        raise GrammarElementError(f"missing required roles: {sorted(missing_roles)}")
    normalized_relations = tuple(_normalize_relation(r, set(element_ids), set(evidence)) for r in relations)
    relation_ids = [r["id"] for r in normalized_relations]
    if len(set(relation_ids)) != len(relation_ids):
        raise GrammarRelationError("relation ids must be unique")
    constraint_values = clean_ids(constraints, field_name="constraints", allow_empty=True)
    warning_values = clean_ids(warnings, field_name="warnings", allow_empty=True)
    payload = {
        "grammar_id": grammar.grammar_id,
        "grammar_version": grammar.version,
        "evidence_refs": evidence,
        "reasoning_refs": reasoning,
        "elements": normalized_elements,
        "relations": normalized_relations,
        "constraints": constraint_values,
        "warnings": warning_values,
        "review_required": True,
        "accepted": False,
    }
    return GrammarPlan(
        grammar_id=grammar.grammar_id,
        grammar_version=grammar.version,
        evidence_refs=evidence,
        reasoning_refs=reasoning,
        elements=normalized_elements,
        relations=normalized_relations,
        constraints=constraint_values,
        warnings=warning_values,
        review_required=True,
        accepted=False,
        fingerprint=stable_fingerprint(payload),
    )
