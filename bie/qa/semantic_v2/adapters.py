"""Explicit compatibility adapters to preserved canonical KI/RE/DIR producers.

Adapters do not treat legacy CLEAR/passed/objective IDs as semantic acceptance.
Actual rendered-surface caller migration is intentionally a later integration.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from ..release_v2.contracts import ContractError, token, tuple_tokens
from ..source_v2.models import Finding
from .models import Requirement


def legacy_contradiction_hint(left: dict, right: dict) -> dict:
    from bie.knowledge_intelligence.claim_contradiction import detect
    for data in (left, right):
        if type(data) is not dict or set(data) != {'claim_id', 'subject', 'predicate', 'object'}:
            raise ContractError('INVALID_LEGACY_CLAIM')
        for k in data: token(data[k], k)
    actual = detect(left, right)
    return {'legacy_result': actual, 'semantic_status': 'REVIEW_REQUIRED',
        'may_authorize_release': False,
        'reason': 'Legacy comparison lacks governed context, cardinality and polarity; its CLEAR flag is not a consistency assessment.'}


@dataclass(frozen=True, slots=True)
class DirectorInventory:
    lesson_fingerprint: str
    scene_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    requirements: tuple[Requirement, ...]
    requires_review: bool


def director_inventory(lesson, objective_to_concept: tuple[tuple[str, str], ...], *,
                       channels: tuple[str, ...] = ('narration', 'lesson')) -> DirectorInventory:
    from bie.director.lesson_architecture_contract import validate_lesson_architecture
    try: lesson = validate_lesson_architecture(lesson)
    except (TypeError, ValueError, AttributeError) as exc: raise ContractError('INVALID_DIRECTOR_LESSON') from exc
    if type(objective_to_concept) is not tuple or len(objective_to_concept) > 4096:
        raise ContractError('INVALID_DIRECTOR_CONCEPT_MAPPING')
    mapping = {}
    for row in objective_to_concept:
        if type(row) is not tuple or len(row) != 2: raise ContractError('INVALID_DIRECTOR_CONCEPT_MAPPING')
        for item in row: token(item, 'objective-concept')
        if row[0] in mapping: raise ContractError('DUPLICATE_DIRECTOR_OBJECTIVE')
        mapping[row[0]] = row[1]
    if set(mapping) != set(lesson.objective_ids): raise ContractError('DIRECTOR_OBJECTIVE_SCOPE_MISMATCH')
    requirements = tuple(Requirement('objective:' + oid, mapping[oid], oid,
        'Teach the independently reviewed objective ' + oid, 2, 1, True, channels)
        for oid in sorted(mapping))
    return DirectorInventory(lesson.fingerprint(), tuple(s.scene_id for s in lesson.scenes),
        tuple(lesson.source_ids), requirements, lesson.requires_review)


def reasoning_findings(decision, resolutions) -> tuple[Finding, ...]:
    from bie.reasoning.contradiction_resolution_qa import evaluate_contradiction_resolution
    from bie.reasoning.decision_contracts import ReasoningDecision
    if type(decision) is not ReasoningDecision: raise ContractError('INVALID_REASONING_DECISION')
    if type(decision.requires_review) is not bool: raise ContractError('INVALID_REASONING_REVIEW')
    for x in [decision.confidence] + [e.strength for e in decision.evidence_refs]:
        if type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1:
            raise ContractError('INVALID_REASONING_CONFIDENCE')
    try: actual = evaluate_contradiction_resolution(decision, resolutions)
    except (TypeError, ValueError, AttributeError) as exc: raise ContractError('INVALID_REASONING_RESOLUTION') from exc
    findings = []
    for item in actual.invalid_contradiction_ids:
        # Upstream free-form IDs remain in details; stable public subject uses
        # the validated decision identifier rather than unsafe interpolated IDs.
        findings.append(Finding('UPSTREAM_INVALID_CONTRADICTION_RESOLUTION', 'BLOCKER', token(decision.decision_id, 'decision_id'), 'RE_REASONING', str(item)))
    for item in actual.unresolved_contradiction_ids:
        findings.append(Finding('UPSTREAM_UNRESOLVED_CONTRADICTION', 'BLOCKER', token(decision.decision_id, 'decision_id'), 'RE_REASONING', str(item)))
    if actual.requires_review:
        findings.append(Finding('UPSTREAM_REASONING_REVIEW', 'REVIEW', token(decision.decision_id, 'decision_id'), 'RE_REASONING', 'The canonical reasoning producer retains review/escalation.'))
    # Empty findings mean only that this upstream producer raised no blocker.
    # They are not a substitute for semantic_v2.evaluate or assessment receipts.
    return tuple(findings)
