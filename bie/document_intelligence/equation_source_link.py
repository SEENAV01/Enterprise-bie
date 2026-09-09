from dataclasses import dataclass
class EquationLinkError(ValueError): pass
@dataclass(frozen=True)
class EquationSourceLink:
    equation_id:str; source_hash:str; page:int; region_id:str; latex:str; confidence:float
def validate(x):
    if not x.equation_id or len(x.source_hash)!=64 or x.page<1 or not x.region_id or not x.latex.strip() or not 0<=x.confidence<=1:
        raise EquationLinkError("invalid source link")
    return True
