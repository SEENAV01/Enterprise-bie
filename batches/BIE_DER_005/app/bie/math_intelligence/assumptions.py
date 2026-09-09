from dataclasses import dataclass
@dataclass(frozen=True)
class Assumption:
 statement:str; required_by:str; explicit:bool; source:str|None
def infer_assumptions(operation:str,operand:str,source=None)->tuple[Assumption,...]:
 op=operation.casefold();out=[]
 if op=="divide":out.append(Assumption(f"{operand} != 0","division",False,source))
 elif op=="sqrt":out.append(Assumption(f"{operand} >= 0","real square root",False,source))
 elif op=="log":out.append(Assumption(f"{operand} > 0","real logarithm",False,source))
 return tuple(out)
def mark_explicit(a:Assumption)->Assumption:return Assumption(a.statement,a.required_by,True,a.source)
