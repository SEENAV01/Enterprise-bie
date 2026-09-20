from dataclasses import dataclass, field
from typing import Mapping, Any
from math import isfinite

class InteractionIRError(ValueError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise InteractionIRError(f"{n} must be nonblank")
    return v.strip()

def finite(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):
        raise InteractionIRError(f"{n} must be finite numeric")
    return float(v)

def unique_ids(values,n):
    out=tuple(tok(v,n) for v in values)
    if not out or len(set(out))!=len(out):
        raise InteractionIRError(f"{n} must be nonempty unique")
    return out
