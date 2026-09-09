
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
import hashlib, json

class E2ERuntimeError(RuntimeError): pass

@dataclass(frozen=True)
class StageTask:
    task_id:str
    run_id:str
    stage_id:str
    attempt:int
    input_artifact_refs:List[str]
    required_capability_tags:List[str]

@dataclass
class Artifact:
    artifact_id:str
    payload:dict
    evidence_refs:List[str]

class InMemoryDurableQueue:
    def __init__(self):
        self._items={}
        self.events=[]
    def enqueue(self,t:StageTask):
        if t.task_id in self._items:
            old=self._items[t.task_id]["task"]
            if old != t: raise E2ERuntimeError("conflicting task id")
            return
        self._items[t.task_id]={"task":t,"state":"READY","delivery_count":0,"consumer":None}
        self.events.append((t.task_id,"ENQUEUED"))
    def poll(self,consumer_id:str,caps:List[str]):
        capset=set(caps)
        for r in self._items.values():
            if r["state"]=="READY" and set(r["task"].required_capability_tags).issubset(capset):
                r["state"]="DELIVERED"; r["delivery_count"]+=1; r["consumer"]=consumer_id
                self.events.append((r["task"].task_id,"DELIVERED"))
                return r
        return None
    def ack(self,task_id,consumer_id):
        r=self._items[task_id]
        if r["state"]!="DELIVERED" or r["consumer"]!=consumer_id: raise E2ERuntimeError("invalid ACK")
        r["state"]="ACKED"; self.events.append((task_id,"ACKED"))
    def nack(self,task_id,consumer_id):
        r=self._items[task_id]
        if r["state"]!="DELIVERED" or r["consumer"]!=consumer_id: raise E2ERuntimeError("invalid NACK")
        r["state"]="READY"; r["consumer"]=None; self.events.append((task_id,"NACKED"))
    def state(self,task_id): return self._items[task_id]["state"]

class InMemoryArtifactStore:
    def __init__(self): self.records={}
    def put(self,run_id,stage_id,payload,evidence_refs):
        body=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        artifact_id=hashlib.sha256(body).hexdigest()
        if artifact_id not in self.records:
            self.records[artifact_id]={"run_id":run_id,"stage_id":stage_id,"payload":payload,"evidence_refs":list(evidence_refs)}
        return artifact_id

class InMemoryStateStore:
    def __init__(self):
        self.stage_states={}
        self.events=[]
    def start(self,run_id,stage_id,attempt):
        self.stage_states[(run_id,stage_id)]={"status":"RUNNING","attempt":attempt,"output_refs":[],"evidence_refs":[]}
        self.events.append((run_id,stage_id,"RUNNING"))
    def succeed(self,run_id,stage_id,attempt,output_refs,evidence_refs):
        if not output_refs or not evidence_refs: raise E2ERuntimeError("success needs output and evidence")
        cur=self.stage_states.get((run_id,stage_id))
        if not cur or cur["status"]!="RUNNING" or cur["attempt"]!=attempt:
            raise E2ERuntimeError("invalid stage success transition")
        cur.update(status="SUCCEEDED",output_refs=list(output_refs),evidence_refs=list(evidence_refs))
        self.events.append((run_id,stage_id,"SUCCEEDED"))

class LeaseFence:
    def __init__(self): self.tokens={}
    def acquire(self,run_id,stage_id,attempt,worker):
        key=(run_id,stage_id,attempt)
        token=self.tokens.get(key,(0,None))[0]+1
        self.tokens[key]=(token,worker)
        return token
    def assert_current(self,run_id,stage_id,attempt,worker,token):
        if self.tokens.get((run_id,stage_id,attempt))!=(token,worker):
            raise E2ERuntimeError("stale fencing token")

class EnterpriseRuntime:
    def __init__(self,queue=None,artifacts=None,state=None,fence=None):
        self.queue=queue or InMemoryDurableQueue()
        self.artifacts=artifacts or InMemoryArtifactStore()
        self.state=state or InMemoryStateStore()
        self.fence=fence or LeaseFence()
    def submit(self,task:StageTask):
        self.queue.enqueue(task)
    def consume_once(self,worker_id,caps,executor:Callable[[StageTask],dict],commit_hook:Optional[Callable]=None):
        delivery=self.queue.poll(worker_id,caps)
        if not delivery: return {"outcome":"IDLE"}
        task=delivery["task"]
        token=self.fence.acquire(task.run_id,task.stage_id,task.attempt,worker_id)
        self.state.start(task.run_id,task.stage_id,task.attempt)
        try:
            produced=executor(task)
            payload=produced["payload"]
            evidence=list(produced["evidence_refs"])
            if not evidence: raise E2ERuntimeError("executor must return evidence")
            self.fence.assert_current(task.run_id,task.stage_id,task.attempt,worker_id,token)
            artifact_id=self.artifacts.put(task.run_id,task.stage_id,payload,evidence)
            self.fence.assert_current(task.run_id,task.stage_id,task.attempt,worker_id,token)
            if commit_hook: commit_hook(task,artifact_id,evidence)
            self.state.succeed(task.run_id,task.stage_id,task.attempt,[artifact_id],evidence)
            self.queue.ack(task.task_id,worker_id)
            return {"outcome":"ACKED","artifact_id":artifact_id,"evidence_refs":evidence}
        except Exception as e:
            self.queue.nack(task.task_id,worker_id)
            return {"outcome":"RETRY","error":f"{type(e).__name__}: {e}"}
