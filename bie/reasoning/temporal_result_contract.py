from dataclasses import dataclass, asdict
import json, hashlib

_ALLOWED={"RESOLVED","AMBIGUOUS","CONFLICT","UNREACHABLE","ABSTAIN"}

@dataclass(frozen=True)
class TemporalResultContract:
    status: str
    conclusion: str | None
    evidence_ids: tuple[str,...]
    assumptions: tuple[str,...] = ()
    uncertainty: tuple[str,...] = ()

def validate_temporal_result(r):
    if r.status not in _ALLOWED:
        raise ValueError("unsupported status")
    if r.status == "RESOLVED" and not r.conclusion:
        raise ValueError("resolved result requires conclusion")
    if r.status != "RESOLVED" and r.conclusion == "":
        raise ValueError("use None for absent conclusion")
    return r

def canonical_temporal_json(r):
    validate_temporal_result(r)
    payload=asdict(r)
    payload["evidence_ids"]=sorted(set(payload["evidence_ids"]))
    payload["assumptions"]=sorted(set(payload["assumptions"]))
    payload["uncertainty"]=sorted(set(payload["uncertainty"]))
    return json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def temporal_result_id(r):
    return hashlib.sha256(canonical_temporal_json(r).encode()).hexdigest()
