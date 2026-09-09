from dataclasses import dataclass
from typing import List, Optional

class QueueError(ValueError): pass

@dataclass
class Msg:
    task_id:str; run_id:str; stage_id:str; attempt:int; idempotency_key:str
    required_capability_tags:List[str]; input_artifact_refs:List[str]; max_deliveries:int=3

@dataclass
class Delivery:
    task:Msg; delivery_count:int; state:str="DELIVERED"; consumer_id:Optional[str]=None

class FakeDurableQueue:
    def __init__(self,messages=None):
        self.messages={m.task_id:{"msg":m,"state":"READY","count":0,"consumer":None} for m in (messages or [])}
        self.events=[]
    def poll(self,consumer_id,visibility_timeout,capability_tags):
        caps=set(capability_tags)
        for tid,r in self.messages.items():
            if r["state"]=="READY" and set(r["msg"].required_capability_tags).issubset(caps):
                r["state"]="DELIVERED";r["count"]+=1;r["consumer"]=consumer_id
                self.events.append((tid,"DELIVERED"))
                return Delivery(r["msg"],r["count"],"DELIVERED",consumer_id)
        return None
    def ack(self,task_id,consumer_id):
        r=self.messages[task_id]
        if r["state"]!="DELIVERED" or r["consumer"]!=consumer_id: raise QueueError("bad ack")
        r["state"]="ACKED";self.events.append((task_id,"ACKED"))
    def nack(self,task_id,consumer_id,delay_seconds=0,reason="nack"):
        r=self.messages[task_id]
        if r["state"]!="DELIVERED" or r["consumer"]!=consumer_id: raise QueueError("bad nack")
        if r["count"]>=r["msg"].max_deliveries:r["state"]="DEAD_LETTER"
        else:r["state"]="READY"
        r["consumer"]=None;self.events.append((task_id,"NACK"))
    def dead_letter(self,task_id,reason):
        self.messages[task_id]["state"]="DEAD_LETTER";self.events.append((task_id,"DEAD_LETTER"))
    def get(self,task_id):
        r=self.messages[task_id]
        return type("R",(),{"state":r["state"]})()
