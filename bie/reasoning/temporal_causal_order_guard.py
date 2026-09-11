"""RE-TEMP-037 — Prevent causal assertions that violate known temporal order."""
from dataclasses import dataclass
@dataclass(frozen=True)
class CausalTemporalCheck:
    allowed:bool
    status:str
def validate_causal_temporal_order(cause_latest:float|None,effect_earliest:float|None):
    if cause_latest is None or effect_earliest is None:
        return CausalTemporalCheck(False,"ABSTAIN_UNKNOWN_TEMPORAL_ORDER")
    if cause_latest>effect_earliest:
        return CausalTemporalCheck(False,"REJECT_CAUSE_AFTER_EFFECT")
    return CausalTemporalCheck(True,"TEMPORALLY_ADMISSIBLE_NOT_CAUSALLY_PROVEN")
