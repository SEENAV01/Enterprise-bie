from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class DerivationTeachingStep:
    index: int
    expression: str
    justification: str
    evidence_ids: tuple[str,...]

@dataclass(frozen=True)
class DerivationPlan:
    steps: tuple[DerivationTeachingStep,...]
    assumptions: tuple[str,...]
    requires_review: bool

def plan_derivation(steps: Iterable[tuple[str,str,tuple[str,...]]], assumptions=()) -> DerivationPlan:
    steps=tuple(steps)
    if len(steps)<2:
        raise ValueError("derivation requires at least two steps")
    out=[]
    for i,(expr,why,evidence_ids) in enumerate(steps,1):
        if not expr.strip() or not why.strip() or not evidence_ids:
            raise ValueError("every derivation step must be grounded and justified")
        out.append(DerivationTeachingStep(i,expr,why,tuple(sorted(set(evidence_ids)))))
    assumptions=tuple(a for a in assumptions if str(a).strip())
    return DerivationPlan(tuple(out),assumptions,bool(assumptions))
