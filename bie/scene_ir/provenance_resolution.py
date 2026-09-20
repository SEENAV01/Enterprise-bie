from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class ProvenanceResolutionReceipt:
    scene_id:str
    resolved_source_refs:tuple[str,...]
    resolved_reasoning_refs:tuple[str,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    passed:bool
    accepted:bool=False

def _all_refs(document):
    source=set(document.source_refs)
    reasoning=set(document.reasoning_refs)
    for e in document.elements:
        source.update(e.source_refs);reasoning.update(e.reasoning_refs)
    for t in document.tracks:
        source.update(t.source_refs);reasoning.update(t.reasoning_refs)
    return tuple(sorted(source)),tuple(sorted(reasoning))

def _check_record(ref, record, kind, min_confidence, blockers, warnings):
    if not isinstance(record, dict):
        blockers.append(f"{kind}_record_invalid:{ref}")
        return
    if record.get("current") is not True:
        blockers.append(f"{kind}_stale:{ref}")
    confidence=record.get("confidence")
    if isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not isfinite(float(confidence)) or not 0<=float(confidence)<=1:
        blockers.append(f"{kind}_confidence_invalid:{ref}")
    elif float(confidence)<min_confidence:
        blockers.append(f"{kind}_confidence_below_threshold:{ref}")
    if not record.get("evidence_hash"):
        blockers.append(f"{kind}_evidence_hash_missing:{ref}")
    if record.get("review_required"):
        warnings.append(f"{kind}_review_required:{ref}")

def resolve_provenance(document, source_registry, reasoning_registry, min_confidence=0.5):
    if isinstance(min_confidence,bool) or not isinstance(min_confidence,(int,float)) or not 0<=float(min_confidence)<=1:
        raise ValueError("min_confidence must be in [0,1]")
    sources,reasons=_all_refs(document)
    blockers=[];warnings=[]
    for ref in sources:
        record=source_registry.get(ref)
        if record is None:
            blockers.append("source_ref_unresolved:"+ref)
        else:
            _check_record(ref,record,"source",float(min_confidence),blockers,warnings)
    for ref in reasons:
        record=reasoning_registry.get(ref)
        if record is None:
            blockers.append("reasoning_ref_unresolved:"+ref)
        else:
            _check_record(ref,record,"reasoning",float(min_confidence),blockers,warnings)
    return ProvenanceResolutionReceipt(
        document.scene_id,
        sources,reasons,
        tuple(sorted(set(blockers))),
        tuple(sorted(set(warnings))),
        not blockers,
        False
    )

def require_provenance(receipt):
    if not receipt.passed:
        raise ValueError("provenance resolution failed")
    return True
