from dataclasses import dataclass
from math import isfinite

class SpaceIRError(ValueError): pass

def num(v,n):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)):
        raise SpaceIRError(f"{n} must be finite numeric")
    return float(v)

def unit(v,n):
    x=num(v,n)
    if not 0.0<=x<=1.0:
        raise SpaceIRError(f"{n} must be in [0,1]")
    return x

def tok(v,n):
    if not isinstance(v,str) or not v.strip():
        raise SpaceIRError(f"{n} must be nonblank")
    return v.strip()

@dataclass(frozen=True)
class NormalizedBox:
    x:float
    y:float
    width:float
    height:float
    def __post_init__(self):
        object.__setattr__(self,"x",unit(self.x,"x"))
        object.__setattr__(self,"y",unit(self.y,"y"))
        object.__setattr__(self,"width",unit(self.width,"width"))
        object.__setattr__(self,"height",unit(self.height,"height"))
        if self.width<=0 or self.height<=0:
            raise SpaceIRError("width/height must be >0")
        if self.x+self.width>1.0+1e-9 or self.y+self.height>1.0+1e-9:
            raise SpaceIRError("box exceeds normalized canvas")
