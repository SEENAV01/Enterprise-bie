from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Iterable
@dataclass(frozen=True)
class ImplicitPrerequisite:
    prerequisite_id: str
    dependent_id: str
    confidence: float
    shared_features: tuple[str,...]
def infer_implicit_prerequisites(dependent_id: str, dependent_features: Iterable[str],
                                 concept_features: Mapping[str, Iterable[str]], minimum_overlap: int=1) -> list[ImplicitPrerequisite]:
    target={x.casefold() for x in dependent_features if x}
    if minimum_overlap < 1: raise ValueError("minimum_overlap must be >= 1")
    out=[]
    for cid,features in concept_features.items():
        if cid==dependent_id: continue
        f={x.casefold() for x in features if x}; shared=tuple(sorted(target & f))
        if len(shared)>=minimum_overlap:
            conf=round(len(shared)/max(1,len(target)),6)
            out.append(ImplicitPrerequisite(cid,dependent_id,conf,shared))
    return sorted(out,key=lambda x:(-x.confidence,x.prerequisite_id))
