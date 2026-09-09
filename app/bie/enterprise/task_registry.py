
from dataclasses import dataclass, field
from typing import List, Dict
VALID_STATUSES={"PLANNED","READY","IN_PROGRESS","IMPLEMENTED","UNIT_TESTED","INTEGRATION_TESTED","GOLDEN_TESTED","QA_VERIFIED","ACCEPTED","BLOCKED","INVALIDATED"}
class TaskRegistryError(ValueError): pass

@dataclass(frozen=True)
class AtomicTask:
    task_id:str
    title:str
    system:str
    purpose:str
    dependencies:List[str]=field(default_factory=list)
    status:str="PLANNED"
    acceptance:List[str]=field(default_factory=list)
    evidence_refs:List[str]=field(default_factory=list)
    version:int=1

    def validate(self):
        if not self.task_id.startswith("BIE-"): raise TaskRegistryError("invalid task id")
        if not self.title or not self.system or not self.purpose: raise TaskRegistryError("missing core fields")
        if self.status not in VALID_STATUSES: raise TaskRegistryError("invalid status")
        if self.version<1: raise TaskRegistryError("invalid version")
        if len(set(self.dependencies))!=len(self.dependencies): raise TaskRegistryError("duplicate dependency")
        if self.task_id in self.dependencies: raise TaskRegistryError("self dependency")
        if self.status=="ACCEPTED" and (not self.acceptance or not self.evidence_refs):
            raise TaskRegistryError("accepted task requires acceptance criteria and evidence")

class TaskRegistry:
    def __init__(self): self.tasks:Dict[str,AtomicTask]={}
    def add(self,t:AtomicTask):
        t.validate()
        if t.task_id in self.tasks: raise TaskRegistryError("duplicate task id")
        self.tasks[t.task_id]=t
    def get(self,task_id): return self.tasks[task_id]
    def by_system(self,system): return [t for t in self.tasks.values() if t.system==system]
    def to_dict(self):
        return {k:vars(v) for k,v in sorted(self.tasks.items())}
