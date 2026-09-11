"""RE-TEMP-056 — Deterministic migration manifest for TEMP atomic ZIP integration."""
from dataclasses import dataclass, asdict
import hashlib, json

@dataclass(frozen=True)
class MigrationEntry:
    task_id: str
    source_path: str
    target_path: str
    sha256: str

def build_manifest(entries):
    xs=tuple(sorted(entries,key=lambda e:(e.task_id,e.target_path,e.source_path)))
    seen=set()
    for e in xs:
        key=(e.task_id,e.target_path)
        if key in seen:
            raise ValueError("duplicate task/target mapping")
        seen.add(key)
        if len(e.sha256)!=64:
            raise ValueError("sha256 must be 64 hex chars")
        int(e.sha256,16)
    payload=[asdict(e) for e in xs]
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    return {
        "entries": payload,
        "manifest_sha256": hashlib.sha256(raw.encode()).hexdigest(),
    }
