from dataclasses import dataclass
from hashlib import sha256
import json

class DSLMigrationError(ValueError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise DSLMigrationError(f"{n} must be nonblank")
    return v.strip()

def fp(payload):
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=list)
    return sha256(raw.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class MigrationEvidence:
    adapter_id:str
    source_format:str
    target_format:str
    input_fingerprint:str
    output_fingerprint:str
    preserved_source_refs:bool
    preserved_reasoning_refs:bool
    lossy:bool
    warnings:tuple[str,...]=()
    accepted:bool=False

def require_lossless_lineage(e):
    if e.lossy:
        raise DSLMigrationError("lossy migration prohibited")
    if not e.preserved_source_refs or not e.preserved_reasoning_refs:
        raise DSLMigrationError("lineage not preserved")
    return True
