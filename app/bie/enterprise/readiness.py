
from typing import Dict,List
READY_DEP_STATES={"ACCEPTED"}
class ReadinessError(ValueError): pass
def compute_ready(tasks:Dict[str,dict])->List[str]:
    out=[]
    for tid,t in tasks.items():
        if t.get("status") not in {"PLANNED","BLOCKED"}: continue
        deps=t.get("dependencies",[])
        if all(d in tasks and tasks[d].get("status") in READY_DEP_STATES for d in deps):
            out.append(tid)
    return sorted(out)
def blockers(tasks:Dict[str,dict],task_id:str)->List[str]:
    if task_id not in tasks: raise ReadinessError("unknown task")
    out=[]
    for d in tasks[task_id].get("dependencies",[]):
        if d not in tasks or tasks[d].get("status") not in READY_DEP_STATES: out.append(d)
    return sorted(out)
def mark_ready(tasks:Dict[str,dict])->Dict[str,dict]:
    import copy
    new=copy.deepcopy(tasks)
    for tid in compute_ready(new): new[tid]["status"]="READY"
    return new
