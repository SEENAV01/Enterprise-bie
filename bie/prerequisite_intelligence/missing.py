from dataclasses import dataclass
@dataclass(frozen=True)
class MissingPrerequisite:
 prerequisite:str; required_by:tuple[str,...]; severity:float
def find_missing_prerequisites(available:set[str], requirements:dict[str,set[str]], strength:dict[tuple[str,str],float]|None=None)->list[MissingPrerequisite]:
 strength=strength or {}; uses={}
 for dep,reqs in requirements.items():
  for pre in reqs:
   if pre not in available: uses.setdefault(pre,[]).append(dep)
 out=[]
 for pre,deps in uses.items():
  sev=max([strength.get((pre,d),.5) for d in deps] or [.5])
  out.append(MissingPrerequisite(pre,tuple(sorted(deps)),round(sev,6)))
 return sorted(out,key=lambda x:(-x.severity,x.prerequisite))
