from dataclasses import dataclass
@dataclass(frozen=True)
class LoadAssessment: total:float; overload:bool
def assess_load(intrinsic,extraneous,germane,max_total=1.8):
 if any(not 0<=x<=1 for x in (intrinsic,extraneous,germane)): raise ValueError("load")
 t=intrinsic+extraneous+germane; return LoadAssessment(t,t>max_total)
