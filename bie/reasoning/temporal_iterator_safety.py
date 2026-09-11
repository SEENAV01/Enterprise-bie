"""RE-TEMP-039 — Materialize single-pass temporal iterables once for deterministic reuse."""
from dataclasses import dataclass
@dataclass(frozen=True)
class MaterializedTemporalInputs:
    events:tuple
    constraints:tuple
    evidence:tuple
def materialize_temporal_inputs(events=(),constraints=(),evidence=()):
    return MaterializedTemporalInputs(tuple(events),tuple(constraints),tuple(evidence))
def temporal_input_counts(inputs:MaterializedTemporalInputs):
    return {"events":len(inputs.events),"constraints":len(inputs.constraints),"evidence":len(inputs.evidence)}
