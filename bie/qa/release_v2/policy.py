"""Trusted release policy: every critical gate is a hard floor, never an average.

These rules describe evidence requirements. They are NOT implementations of the
source, math, pedagogy, cinematic-quality, video, game or EVAL evaluators.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from .contracts import (ContractError, VERSION, choice, digest, integer, token, tuple_tokens)

_ALL = ("source", "video", "game")
_EXECUTION = ("execution",)
_REVIEW = ("execution", "review")
# Existing gate IDs are retained where possible. New mandatory floors are explicit.
_CATALOG = (
    ("lineage_integrity", "INFRA", _ALL, _REVIEW),
    ("source_grounding", "BI.KI.QA", ("source",), _REVIEW),
    ("citation_provenance", "BI.QA", ("source",), _REVIEW),
    ("semantic_correctness", "KI.RE.QA", _ALL, _REVIEW),
    ("prerequisite_correctness", "PR.PED", _ALL, _REVIEW),
    ("reasoning_validity", "RE.QA", _ALL, _REVIEW),
    ("mathematical_correctness", "MATH.QA", _ALL, _REVIEW),
    ("pedagogical_correctness", "PED", _ALL, _REVIEW),
    ("director_quality", "DIR", ("video",), _REVIEW),
    ("visual_quality", "VIS", ("video",), _REVIEW),
    ("animation_quality", "ANI", ("video",), _REVIEW),
    ("timing_audio_sync", "AUDIO.COMP", ("video",), _EXECUTION),
    ("code_compile", "COMP", ("video",), _EXECUTION),
    ("video_render", "COMP", ("video",), _EXECUTION),
    ("rendered_frame_inspection", "QA.VIS", ("video",), _EXECUTION),
    ("game_build", "GAME", ("game",), _EXECUTION),
    ("game_runtime", "GAME.QA", ("game",), _EXECUTION),
    ("game_interactions", "GAME.QA", ("game",), _EXECUTION),
    ("game_learning_alignment", "GAME.PED", ("source", "game"), _REVIEW),
    ("regression", "QA", _ALL, _EXECUTION),
    ("reproducibility", "INFRA.QA", _ALL, _EXECUTION),
    ("rights_and_asset_provenance", "INFRA.VIS", _ALL, _REVIEW),
    ("security", "INFRA", _ALL, _EXECUTION),
    ("accessibility", "QA.VIS.GAME", ("video", "game"), _REVIEW),
    ("performance", "INFRA.COMP", ("video", "game"), _EXECUTION),
    ("benchmark", "EVAL", _ALL, _REVIEW),
    ("real_book_e2e", "QA.EVAL", _ALL, _EXECUTION),
    ("canonical_integration", "INFRA.QA", _ALL, _EXECUTION),
)


@dataclass(frozen=True, slots=True)
class GateRule:
    gate_id: str
    owner: str
    required_roles: tuple[str, ...]
    allowed_kinds: tuple[str, ...]
    min_distinct_evaluators: int = 1

    def __post_init__(self) -> None:
        token(self.gate_id, "gate_id")
        token(self.owner, "owner")
        tuple_tokens(self.required_roles, "required_roles", 1, 4)
        tuple_tokens(self.allowed_kinds, "allowed_kinds", 1, 2)
        for role in self.required_roles:
            choice(role, ("source", "video", "game", "support"), "required_roles")
        for kind in self.allowed_kinds:
            choice(kind, _REVIEW, "allowed_kinds")
        integer(self.min_distinct_evaluators, "min_distinct_evaluators", 1, 8)


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    policy_id: str
    policy_version: str
    gates: tuple[GateRule, ...]
    max_evidence_lifetime_seconds: int = 604800

    def __post_init__(self) -> None:
        token(self.policy_id, "policy_id")
        if self.policy_version != VERSION:
            raise ContractError("UNSUPPORTED_POLICY_VERSION")
        if type(self.gates) is not tuple or not self.gates or len(self.gates) > 128:
            raise ContractError("INVALID_GATES")
        if any(type(g) is not GateRule for g in self.gates):
            raise ContractError("INVALID_GATE_TYPE")
        by_id = {g.gate_id: g for g in self.gates}
        if len(by_id) != len(self.gates):
            raise ContractError("DUPLICATE_GATE_ID")
        integer(self.max_evidence_lifetime_seconds, "max_evidence_lifetime_seconds", 1, 604800)
        # Custom policies may strengthen, but not silently remove or weaken floors.
        for gid, owner, roles, kinds in _CATALOG:
            current = by_id.get(gid)
            if current is None or not set(roles).issubset(current.required_roles) or not set(
                current.allowed_kinds
            ).issubset(kinds):
                raise ContractError("WEAKENED_REQUIRED_GATE", gid)
            if current.owner != owner:
                raise ContractError("OWNER_ROUTING_CHANGED", gid)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["gates"] = []
        for rule in sorted(self.gates, key=lambda r: r.gate_id):
            item = asdict(rule)
            item["required_roles"] = sorted(rule.required_roles)
            item["allowed_kinds"] = sorted(rule.allowed_kinds)
            data["gates"].append(item)
        return data

    @property
    def content_digest(self) -> str:
        return digest(self.to_dict())


def enterprise_policy() -> ReleasePolicy:
    return ReleasePolicy("bie-enterprise-evidence-v2", VERSION,
                         tuple(GateRule(*row) for row in _CATALOG))
