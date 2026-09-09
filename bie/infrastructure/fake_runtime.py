from dataclasses import dataclass
from typing import List

class RuntimeErrorX(ValueError): pass

@dataclass(frozen=True)
class Result:
    output_artifact_refs:List[str]
    evidence_refs:List[str]

class FakeWorkerRuntime:
    def __init__(self,fail=False,commit_fail=False,events=None):
        self.fail=fail;self.commit_fail=commit_fail;self.events=events if events is not None else []
    def execute(self,task,req,executor,commit,owner):
        self.events.append("RUNTIME_START")
        if self.fail:
            self.events.append("RUNTIME_FAIL")
            raise RuntimeErrorX("runtime failed")
        result=executor(type("Ctx",(),{})())
        self.events.append("EXECUTOR_DONE")
        if not getattr(result,"output_artifact_refs",None) or not getattr(result,"evidence_refs",None):
            raise RuntimeErrorX("invalid result")
        if self.commit_fail:
            self.events.append("COMMIT_FAIL")
            raise RuntimeErrorX("fenced commit failed")
        commit(None,result)
        self.events.append("COMMIT_DONE")
        return result
