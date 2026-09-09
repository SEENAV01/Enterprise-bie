from dataclasses import dataclass
from typing import Protocol
@dataclass(frozen=True)
class SolverRequest:
 operation:str; expression:str; assumptions:tuple[str,...]=()
@dataclass(frozen=True)
class SolverResult:
 result:str; verified:bool; provider:str; evidence:str
class SolverAdapter(Protocol):
 def solve(self,request:SolverRequest)->SolverResult: ...
ALLOWED={"simplify","solve","differentiate","integrate","factor","expand","equivalence"}
def governed_solve(adapter:SolverAdapter,request:SolverRequest)->SolverResult:
 if request.operation not in ALLOWED:raise ValueError("operation not allowed")
 if not request.expression.strip():raise ValueError("empty expression")
 r=adapter.solve(request)
 if not r.provider.strip() or not r.evidence.strip():raise ValueError("solver provenance/evidence required")
 return r
