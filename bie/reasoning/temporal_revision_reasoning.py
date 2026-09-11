"""RE-TEMP-023 — Track explicit supersession of temporal assertions."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalAssertion:
    assertion_id: str
    value: str
    revision: int
    supersedes: str | None = None

def latest_temporal_assertion(assertions):
    items=tuple(assertions)
    if not items: return None
    ids={a.assertion_id for a in items}
    for a in items:
        if a.supersedes is not None and a.supersedes not in ids:
            raise ValueError("superseded assertion is missing")
    return sorted(items,key=lambda a:(-a.revision,a.assertion_id))[0]
