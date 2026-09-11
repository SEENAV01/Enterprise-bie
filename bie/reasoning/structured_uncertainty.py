from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable
import json
from math import isfinite

KINDS={"SOURCE","MEASUREMENT","TEMPORAL","SPATIAL","MODEL","AMBIGUITY","CONFLICT","INFERENCE"}

@dataclass(frozen=True)
class UncertaintyComponent:
    component_id: str
    kind: str
    description: str
    evidence_ids: tuple[str,...] = ()
    lower: float | None = None
    upper: float | None = None
    weight: float = 1.0

    def validate(self):
        if not self.component_id.strip() or not self.description.strip(): raise ValueError("id/description required")
        if self.kind not in KINDS: raise ValueError("unsupported uncertainty kind")
        if not 0 <= self.weight <= 1: raise ValueError("weight must be in [0,1]")
        if (self.lower is None) != (self.upper is None): raise ValueError("bounds must be both present or absent")
        if self.lower is not None and any(isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x)
                                          for x in (self.lower, self.upper)):
            raise ValueError("uncertainty bounds must be finite numbers")
        if self.lower is not None and self.lower > self.upper: raise ValueError("lower > upper")

@dataclass(frozen=True)
class UncertaintyAssessment:
    components: tuple[UncertaintyComponent,...]
    conservative_confidence_ceiling: float
    requires_review: bool
    policy: str = "min_weight"

    def canonical_json(self) -> str:
        return json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

def assess_uncertainty(components: Iterable[UncertaintyComponent], *, review_threshold: float=.75) -> UncertaintyAssessment:
    if not 0 <= review_threshold <= 1: raise ValueError("review_threshold")
    components=tuple(components)
    ids=[c.component_id for c in components]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate component_id")
    for c in components: c.validate()
    ceiling=min((c.weight for c in components),default=1.0)
    review=bool(components) and (ceiling < review_threshold or any(c.kind in {"CONFLICT","AMBIGUITY"} for c in components))
    return UncertaintyAssessment(tuple(sorted(components,key=lambda c:c.component_id)),ceiling,review)
