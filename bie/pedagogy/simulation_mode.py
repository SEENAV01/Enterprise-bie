from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class SimulationVariable:
    name: str
    minimum: float
    maximum: float
    initial: float
    unit: str

@dataclass(frozen=True)
class SimulationPlan:
    phenomenon: str
    variables: tuple[SimulationVariable,...]
    observable: str
    prediction_prompt: str
    evidence_ids: tuple[str,...]

def plan_simulation(
    phenomenon: str,
    variables: Iterable[SimulationVariable],
    observable: str,
    evidence_ids,
) -> SimulationPlan:
    variables=tuple(variables)
    if not phenomenon.strip() or not observable.strip() or not evidence_ids or not variables:
        raise ValueError("grounded simulation input required")
    names=set()
    for v in variables:
        if not v.name.strip() or not v.unit.strip() or v.minimum>v.maximum or not v.minimum<=v.initial<=v.maximum:
            raise ValueError("invalid variable")
        if v.name in names:
            raise ValueError("duplicate variable")
        names.add(v.name)
    return SimulationPlan(
        phenomenon, tuple(sorted(variables,key=lambda v:v.name)), observable,
        f"Predict how {observable} changes when you manipulate the variables.",
        tuple(sorted(set(evidence_ids)))
    )
