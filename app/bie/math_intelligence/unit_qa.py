from dataclasses import dataclass
@dataclass(frozen=True)
class UnitQA:
 passed:bool; failures:tuple[str,...]
def assess_units(expected:tuple[int,...],actual:tuple[int,...],declared:bool=True)->UnitQA:
 if len(expected)!=7 or len(actual)!=7:raise ValueError("SI dimension vectors require 7 entries")
 f=[]
 if expected!=actual:f.append("dimension_mismatch")
 if not declared:f.append("unit_not_declared")
 return UnitQA(not f,tuple(f))
