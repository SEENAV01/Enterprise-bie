from dataclasses import dataclass
@dataclass(frozen=True)
class Rearrangement:
 valid:bool; operation:str; reason:str
def validate_linear_step(a:tuple[float,float],b:tuple[float,float],operation:str,value:float)->Rearrangement:
 # tuple represents lhs,rhs numeric probes; validate same operation both sides
 la,ra=a;lb,rb=b
 ops={"add":lambda x:x+value,"subtract":lambda x:x-value,"multiply":lambda x:x*value}
 if operation=="divide":
  if value==0:return Rearrangement(False,operation,"division_by_zero")
  fn=lambda x:x/value
 elif operation in ops:fn=ops[operation]
 else:raise ValueError("unsupported operation")
 ok=abs(fn(la)-lb)<1e-9 and abs(fn(ra)-rb)<1e-9
 return Rearrangement(ok,operation,"same_operation_both_sides" if ok else "invalid_transformation")
