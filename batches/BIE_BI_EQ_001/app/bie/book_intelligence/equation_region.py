from dataclasses import dataclass
class EquationRegionError(ValueError): pass
@dataclass(frozen=True)
class EquationRegion:
    equation_id:str; page:int; box:tuple; confidence:float
def validate(e):
    if not e.equation_id or e.page<1 or len(e.box)!=4 or not 0<=e.confidence<=1: raise EquationRegionError("invalid equation region")
    x1,y1,x2,y2=e.box
    if not (0<=x1<x2<=1 and 0<=y1<y2<=1): raise EquationRegionError("invalid box")
    return True
