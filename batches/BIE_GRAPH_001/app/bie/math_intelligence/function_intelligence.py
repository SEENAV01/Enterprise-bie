from dataclasses import dataclass
@dataclass(frozen=True)
class FunctionSpec:
 name:str; variables:tuple[str,...]; expression:str; representation:str
def function_spec(name:str,variables:list[str],expression:str,representation="explicit")->FunctionSpec:
 if not name.strip() or not variables or not expression.strip():raise ValueError("incomplete function")
 if len(set(variables))!=len(variables):raise ValueError("duplicate variable")
 if representation not in {"explicit","implicit","parametric","piecewise"}:raise ValueError("unsupported representation")
 return FunctionSpec(name.strip(),tuple(variables),expression.strip(),representation)
