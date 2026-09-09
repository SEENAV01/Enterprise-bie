from dataclasses import dataclass
import math
@dataclass(frozen=True)
class NumericalEquivalence:
 equivalent:bool; absolute_error:float; relative_error:float
def compare(a:float,b:float,abs_tol:float=1e-9,rel_tol:float=1e-9)->NumericalEquivalence:
 if abs_tol<0 or rel_tol<0:raise ValueError("negative tolerance")
 err=abs(a-b); scale=max(abs(a),abs(b),1e-300); rel=err/scale
 return NumericalEquivalence(math.isclose(a,b,abs_tol=abs_tol,rel_tol=rel_tol),err,rel)
