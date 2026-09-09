from dataclasses import dataclass
import math
@dataclass(frozen=True)
class NumericalQA:
 passed:bool; error:float; failures:tuple[str,...]
def assess_numeric(expected:float,actual:float,tolerance:float=1e-8,finite_required=True)->NumericalQA:
 if tolerance<0:raise ValueError("negative tolerance")
 f=[]
 if finite_required and (not math.isfinite(expected) or not math.isfinite(actual)):f.append("non_finite")
 err=abs(expected-actual) if math.isfinite(expected) and math.isfinite(actual) else float("inf")
 if err>tolerance:f.append("outside_tolerance")
 return NumericalQA(not f,err,tuple(f))
