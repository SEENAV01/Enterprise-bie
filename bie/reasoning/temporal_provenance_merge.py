"""RE-TEMP-028 — Merge temporal evidence while retaining source-level provenance."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalEvidence:
    source_id:str
    claim:str
    confidence:float

@dataclass(frozen=True)
class ProvenanceMerge:
    claim:str
    source_ids:tuple[str,...]
    confidence:float

def merge_temporal_evidence(items):
    xs=tuple(items)
    if not xs: raise ValueError("evidence required")
    claims={x.claim for x in xs}
    if len(claims)!=1: raise ValueError("cannot merge different claims")
    if any(not 0<=x.confidence<=1 for x in xs): raise ValueError("invalid confidence")
    sources=tuple(sorted({x.source_id for x in xs}))
    # conservative aggregation: strongest supported observation, never > 1
    conf=max(x.confidence for x in xs)
    return ProvenanceMerge(xs[0].claim,sources,conf)
