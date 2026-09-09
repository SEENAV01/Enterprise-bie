from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import heapq, time

class QueueError(ValueError): pass

@dataclass(frozen=True)
class TaskMessage:
    task_id:str
    run_id:str
    stage_id:str
    attempt:int
    idempotency_key:str
    required_capability_tags:List[str]
    input_artifact_refs:List[str]
    priority:int=100
    max_deliveries:int=5
    created_at:float=0.0

    def validate(self):
        if not self.task_id or not self.run_id or not self.stage_id or not self.idempotency_key:
            raise QueueError("task identity fields required")
        if self.attempt<1: raise QueueError("attempt must be >=1")
        if self.max_deliveries<1: raise QueueError("max_deliveries must be >=1")
        if self.priority<0: raise QueueError("priority must be >=0")

@dataclass
class DeliveryRecord:
    task:TaskMessage
    delivery_count:int=0
    state:str="READY"
    consumer_id:Optional[str]=None
    visible_at:float=0.0
    delivered_at:Optional[float]=None
    acked_at:Optional[float]=None
    last_reason:str=""

class InMemoryDurableQueue:
    def __init__(self,clock:Optional[Callable[[],float]]=None,max_queued:int=10000,max_in_flight:int=1000):
        if max_queued<1 or max_in_flight<1: raise QueueError("queue limits must be >=1")
        self.clock=clock or time.time
        self.max_queued=max_queued
        self.max_in_flight=max_in_flight
        self.records:Dict[str,DeliveryRecord]={}
        self._seq=0

    def _now(self): return float(self.clock())

    def _counts(self):
        queued=sum(1 for r in self.records.values() if r.state=="READY")
        inflight=sum(1 for r in self.records.values() if r.state=="DELIVERED")
        return queued,inflight

    def enqueue(self,msg:TaskMessage)->None:
        msg.validate()
        if msg.task_id in self.records:
            existing=self.records[msg.task_id].task
            same_identity = (
                existing.task_id==msg.task_id and
                existing.run_id==msg.run_id and
                existing.stage_id==msg.stage_id and
                existing.attempt==msg.attempt and
                existing.idempotency_key==msg.idempotency_key and
                existing.required_capability_tags==msg.required_capability_tags and
                existing.input_artifact_refs==msg.input_artifact_refs and
                existing.priority==msg.priority and
                existing.max_deliveries==msg.max_deliveries
            )
            if not same_identity: raise QueueError("task_id conflict")
            return
        queued,_=self._counts()
        if queued>=self.max_queued: raise QueueError("queue backpressure: max queued reached")
        created=msg.created_at or self._now()
        msg=TaskMessage(msg.task_id,msg.run_id,msg.stage_id,msg.attempt,msg.idempotency_key,
                        list(msg.required_capability_tags),list(msg.input_artifact_refs),
                        msg.priority,msg.max_deliveries,created)
        self.records[msg.task_id]=DeliveryRecord(msg,0,"READY",None,self._now())

    def _requeue_expired(self):
        now=self._now()
        for r in self.records.values():
            if r.state=="DELIVERED" and r.visible_at<=now:
                r.consumer_id=None
                if r.delivery_count>=r.task.max_deliveries:
                    r.state="DEAD_LETTER"; r.last_reason="visibility timeout: max deliveries exceeded"
                else:
                    r.state="READY"; r.last_reason="visibility timeout"

    def poll(self,consumer_id:str,visibility_timeout:float=30.0,capability_tags:Optional[List[str]]=None)->Optional[DeliveryRecord]:
        if not consumer_id: raise QueueError("consumer_id required")
        if visibility_timeout<=0: raise QueueError("visibility_timeout must be >0")
        self._requeue_expired()
        _,inflight=self._counts()
        if inflight>=self.max_in_flight: return None
        caps=set(capability_tags or [])
        candidates=[]
        for r in self.records.values():
            if r.state!="READY": continue
            if r.visible_at>self._now(): continue
            req=set(r.task.required_capability_tags)
            if not req.issubset(caps): continue
            candidates.append((r.task.priority,r.task.created_at,r.task.task_id,r))
        if not candidates: return None
        candidates.sort(key=lambda x:(x[0],x[1],x[2]))
        r=candidates[0][3]
        r.delivery_count+=1
        r.state="DELIVERED"
        r.consumer_id=consumer_id
        r.delivered_at=self._now()
        r.visible_at=self._now()+visibility_timeout
        return r

    def ack(self,task_id:str,consumer_id:str)->None:
        r=self._get(task_id)
        if r.state!="DELIVERED": raise QueueError("task not delivered")
        if r.consumer_id!=consumer_id: raise QueueError("consumer ownership mismatch")
        r.state="ACKED"; r.acked_at=self._now(); r.last_reason="acked"

    def nack(self,task_id:str,consumer_id:str,delay_seconds:float=0.0,reason:str="nack")->None:
        if delay_seconds<0: raise QueueError("delay must be >=0")
        r=self._get(task_id)
        if r.state!="DELIVERED": raise QueueError("task not delivered")
        if r.consumer_id!=consumer_id: raise QueueError("consumer ownership mismatch")
        r.consumer_id=None
        if r.delivery_count>=r.task.max_deliveries:
            r.state="DEAD_LETTER"; r.last_reason=f"{reason}: max deliveries exceeded"
        else:
            r.state="READY"; r.visible_at=self._now()+delay_seconds; r.last_reason=reason

    def dead_letter(self,task_id:str,reason:str)->None:
        r=self._get(task_id)
        if r.state=="ACKED": raise QueueError("cannot dead-letter acked task")
        r.state="DEAD_LETTER"; r.consumer_id=None; r.last_reason=reason

    def redrive(self,task_id:str)->None:
        r=self._get(task_id)
        if r.state!="DEAD_LETTER": raise QueueError("only dead-letter task can redrive")
        r.state="READY"; r.consumer_id=None; r.visible_at=self._now(); r.last_reason="manual redrive"

    def _get(self,task_id:str)->DeliveryRecord:
        if task_id not in self.records: raise QueueError("task not found")
        return self.records[task_id]

    def state(self,task_id:str)->str:
        self._requeue_expired()
        return self._get(task_id).state

    def stats(self)->Dict[str,int]:
        self._requeue_expired()
        out={"READY":0,"DELIVERED":0,"ACKED":0,"DEAD_LETTER":0}
        for r in self.records.values():
            out[r.state]=out.get(r.state,0)+1
        return out
