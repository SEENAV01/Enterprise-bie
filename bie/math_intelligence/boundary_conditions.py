from dataclasses import dataclass
@dataclass(frozen=True)
class BoundaryCondition:
 variable:str; location:str; value:str; kind:str
def make_boundary(variable:str,location:str,value:str,kind="value")->BoundaryCondition:
 if not variable.strip() or not location.strip() or not value.strip():raise ValueError("incomplete boundary condition")
 if kind not in {"value","derivative","initial","periodic","asymptotic"}:raise ValueError("unsupported boundary kind")
 return BoundaryCondition(variable.strip(),location.strip(),value.strip(),kind)
def complete(required:set[tuple[str,str]],conditions:list[BoundaryCondition])->bool:
 return required <= {(c.variable,c.location) for c in conditions}
