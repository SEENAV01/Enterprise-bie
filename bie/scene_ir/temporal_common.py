from dataclasses import dataclass, field
from typing import Mapping, Any

class TemporalIRError(ValueError): pass

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise TemporalIRError(f"{n} must be nonblank")
    return v.strip()

def posint(v,n,allow_zero=False):
    if isinstance(v,bool) or not isinstance(v,int):
        raise TemporalIRError(f"{n} must be int")
    if (v<0 if allow_zero else v<1):
        raise TemporalIRError(f"{n} out of range")
    return v
