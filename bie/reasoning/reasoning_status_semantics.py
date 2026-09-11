from __future__ import annotations
from dataclasses import dataclass

STATUSES=("RESOLVED","AMBIGUOUS","CONFLICT","UNREACHABLE","ABSTAINED","INSUFFICIENT_EVIDENCE")
# Match the established GroundedResult critical review boundary.
REVIEW_CONFIDENCE_THRESHOLD = 0.75
_PRIORITY={"RESOLVED":0,"AMBIGUOUS":1,"INSUFFICIENT_EVIDENCE":2,"ABSTAINED":3,"UNREACHABLE":4,"CONFLICT":5}

@dataclass(frozen=True)
class ReasoningStatus:
    status: str
    reason_code: str
    requires_review: bool
    releasable: bool

def normalize_status(status:str, reason_code:str="") -> ReasoningStatus:
    # TEMP-047's published contract uses ABSTAIN; central output stays canonical.
    if status == "ABSTAIN": status = "ABSTAINED"
    if status not in STATUSES: raise ValueError("unsupported status")
    if not reason_code.strip(): reason_code=status
    review=status!="RESOLVED"
    return ReasoningStatus(status,reason_code,review,status=="RESOLVED")

def aggregate_status(*statuses:str) -> ReasoningStatus:
    if not statuses: return normalize_status("INSUFFICIENT_EVIDENCE")
    statuses = tuple(normalize_status(s).status for s in statuses)
    for s in statuses:
        if s not in STATUSES: raise ValueError("unsupported status")
    worst=max(statuses,key=lambda s:(_PRIORITY[s],s))
    return normalize_status(worst,"AGGREGATED_"+worst)
