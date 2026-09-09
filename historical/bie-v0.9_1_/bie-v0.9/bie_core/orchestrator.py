
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import json, hashlib, traceback

class Status(str, Enum):
    PENDING="PENDING"; RUNNING="RUNNING"; PASS="PASS"
    REVIEW="REVIEW"; FAILED="FAILED"; SKIPPED="SKIPPED"

@dataclass
class StageRecord:
    name:str
    status:str=Status.PENDING
    attempts:int=0
    input_hash:str|None=None
    output_hash:str|None=None
    error:str|None=None
    started_at:str|None=None
    finished_at:str|None=None
    metadata:dict=field(default_factory=dict)

@dataclass
class Job:
    job_id:str
    source_path:str
    created_at:str
    stages:dict[str,StageRecord]
    artifacts:dict[str,str]=field(default_factory=dict)

def sha256_obj(obj):
    raw=json.dumps(obj,sort_keys=True,default=str).encode()
    return hashlib.sha256(raw).hexdigest()

class StateStore:
    def __init__(self, root=".bie_state"):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def save(self,job):
        (self.root/f"{job.job_id}.json").write_text(json.dumps(asdict(job),indent=2,default=str))
    def load(self,job_id):
        return json.loads((self.root/f"{job_id}.json").read_text())

class Pipeline:
    STAGES=("M1","M2","M3","M4","M5","M6","M7","M8")
    def __init__(self, store=None):
        self.store=store or StateStore()
        self.handlers={}
    def register(self,name,handler): self.handlers[name]=handler
    def create_job(self,source_path,job_id=None):
        jid=job_id or "job_"+hashlib.sha256(str(source_path).encode()).hexdigest()[:12]
        stages={s:StageRecord(s) for s in self.STAGES}
        job=Job(jid,str(source_path),datetime.now(timezone.utc).isoformat(),stages)
        self.store.save(job); return job
    def can_run(self,job,stage):
        idx=self.STAGES.index(stage)
        if idx==0:return True
        prev=self.STAGES[idx-1]
        return job.stages[prev].status in {Status.PASS,Status.REVIEW}
    def run_stage(self,job,stage,input_obj):
        rec=job.stages[stage]
        if not self.can_run(job,stage):
            rec.status=Status.SKIPPED; self.store.save(job); return None
        if stage not in self.handlers: raise KeyError(f"No handler registered for {stage}")
        rec.status=Status.RUNNING; rec.attempts+=1
        rec.started_at=datetime.now(timezone.utc).isoformat()
        rec.input_hash=sha256_obj(input_obj); self.store.save(job)
        try:
            output=self.handlers[stage](input_obj,job)
            rec.output_hash=sha256_obj(output)
            rec.status=Status.PASS
            rec.finished_at=datetime.now(timezone.utc).isoformat()
            job.artifacts[stage]=f"memory:{rec.output_hash}"
            self.store.save(job); return output
        except Exception as e:
            rec.status=Status.FAILED
            rec.error="".join(traceback.format_exception_only(type(e),e)).strip()
            rec.finished_at=datetime.now(timezone.utc).isoformat()
            self.store.save(job); raise
    def run(self,source_path,initial=None,job_id=None):
        job=self.create_job(source_path,job_id)
        current=initial if initial is not None else {"source_path":str(source_path)}
        outputs={}
        for s in self.STAGES:
            out=self.run_stage(job,s,current)
            if out is None: break
            outputs[s]=out; current=out
        return job,outputs
