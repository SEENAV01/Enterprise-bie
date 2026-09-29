"""Explicit adapters for preserved canonical PR/RE contracts; never a trust upgrade."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from fractions import Fraction
import math,hashlib,json
from ...prerequisite_intelligence.graph import PrerequisiteGraph
from ...reasoning.decision_contracts import ReasoningDecision,ReasoningDecisionGraph
from ..release_v2.contracts import ContractError,token
from .models import PrerequisiteRule


def import_prerequisite_graph(graph:PrerequisiteGraph):
    if type(graph) is not PrerequisiteGraph:raise ContractError('INVALID_LEGACY_PR_GRAPH')
    if type(graph.nodes) is not set or not 1<=len(graph.nodes)<=1024:raise ContractError('INVALID_LEGACY_PR_NODES')
    for n in graph.nodes:token(n,'legacy.node')
    for edges in (graph.outgoing,graph.incoming):
        if type(edges) is not dict or set(edges)!=graph.nodes:raise ContractError('LEGACY_PR_KEY_MISMATCH')
        for n,children in edges.items():
            if type(children) is not set or not children<=graph.nodes or n in children:raise ContractError('INVALID_LEGACY_PR_EDGE')
    pairs=sorted((a,b) for a in graph.nodes for b in graph.outgoing[a])
    if set(pairs)!={(a,b) for b in graph.nodes for a in graph.incoming[b]}:raise ContractError('ASYMMETRIC_LEGACY_PR_GRAPH')
    return tuple(sorted(graph.nodes)),tuple(PrerequisiteRule(f'pr-edge-{i:04d}',a,b) for i,(a,b) in enumerate(pairs,1))


def exact_ppm(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:raise ContractError('INVALID_LEGACY_CONFIDENCE')
    f=Fraction(str(value))*1000000
    if f.denominator!=1:raise ContractError('LEGACY_CONFIDENCE_PRECISION_LOSS')
    return f.numerator

@dataclass(frozen=True,slots=True)
class LegacyInspection:
    decision_id: str
    canonical_payload_sha256: str
    confidence_ppm: int
    evidence_artifact_ids: tuple[str,...]
    dependency_ids: tuple[str,...]
    requires_review: bool
    normalized_proof_available: bool = False
    trusted_evidence_available: bool = False


def inspect_legacy_decisions(decisions:tuple[ReasoningDecision,...]):
    if type(decisions) is not tuple or not 1<=len(decisions)<=256 or any(type(x) is not ReasoningDecision for x in decisions):
        raise ContractError('INVALID_LEGACY_DECISIONS')
    for d in decisions:
        token(d.decision_id,'decision_id');exact_ppm(d.confidence)
        if type(d.requires_review) is not bool:raise ContractError('INVALID_LEGACY_REVIEW_FLAG')
        for e in d.evidence_refs:exact_ppm(e.strength)
        if len(set(d.depends_on_decisions))!=len(d.depends_on_decisions):raise ContractError('DUPLICATE_LEGACY_DEPENDENCY')
    try:ReasoningDecisionGraph(list(decisions)).validate()
    except (ValueError,TypeError,RecursionError) as exc:raise ContractError('LEGACY_DECISION_VALIDATION_FAILED') from exc
    out=[]
    for d in sorted(decisions,key=lambda x:x.decision_id):
        # Hash original canonical decision shape, including its native numbers;
        # no trust, proof, signature or source support is manufactured.
        data=json.dumps(asdict(d),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
        out.append(LegacyInspection(d.decision_id,hashlib.sha256(data).hexdigest(),exact_ppm(d.confidence),
            tuple(sorted(e.artifact_id for e in d.evidence_refs)),tuple(sorted(d.depends_on_decisions)),d.requires_review))
    return tuple(out)
