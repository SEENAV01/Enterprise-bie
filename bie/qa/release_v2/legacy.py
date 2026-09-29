"""Explicit diagnostic bridge; legacy SUCCESS never becomes v2 authorization."""
from __future__ import annotations
from dataclasses import asdict
from typing import Any
from bie.qa.release_contracts import GateEvidence, ReleaseEvaluator, ReleasePolicy
from .contracts import ContractError


def preview_legacy(policy: ReleasePolicy, evidence: list[GateEvidence]) -> dict[str, Any]:
    """Retain original API behavior, but label its missing v2 evidence bindings.

    This is a preview only. There is intentionally no automatic PASS migration.
    """
    if type(policy) is not ReleasePolicy or type(evidence) is not list:
        raise ContractError("INVALID_LEGACY_INPUT")
    if any(type(item) is not GateEvidence for item in evidence):
        raise ContractError("INVALID_LEGACY_INPUT")
    original = ReleaseEvaluator.evaluate(policy, evidence)
    return {
        "schema_version": "2.0.0",
        "legacy_decision": asdict(original),
        "release_status": "BLOCKED",
        "release_authorized": False,
        "product_accepted": False,
        "migration_required": True,
        "diagnostics": ["LEGACY_CONTENT_BINDING_UNVERIFIED", "LEGACY_PRODUCER_AUTHORIZATION_UNVERIFIED",
                        "REGENERATE_CANDIDATE_BOUND_EVIDENCE"],
    }
