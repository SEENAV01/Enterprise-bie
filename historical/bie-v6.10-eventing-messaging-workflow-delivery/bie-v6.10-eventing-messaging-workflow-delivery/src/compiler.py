from event import event
from topic import topic
from queue import queue
from delivery import delivery_policy
from idempotency import idempotency_key
from ordering import ordering_policy
from dlq import dead_letter
from replay import replay_plan
from backpressure import backpressure_policy
from workflow_delivery import delivery_contract

def compile_eventing(tenant_id):
    e=event("evt-1","workflow.completed",
            "payload://evt-1","worker",0,
            tenant_id,"1")
    t=topic("workflow-events",3,86400)
    q=queue("workflow-delivery","AT_LEAST_ONCE",10000)
    d=delivery_policy("AT_LEAST_ONCE",30,5)
    i=idempotency_key("workflow.complete",
                      "workflow-1","request-1")
    o=ordering_policy("workflow",True,"workflow_id")
    dl=dead_letter("msg-1",q["name"],5,
                   "MAX_ATTEMPTS","payload://msg-1")
    rp=replay_plan(t["name"],0,100,
                   "recovery-topic")
    bp=backpressure_policy(1000,8000,3000)
    wc=delivery_contract("workflow-1",
                         e["event_type"],q["name"],True)
    return {"schema_version":"6.10",
            "event":e,"topic":t,"queue":q,
            "delivery":d,"idempotency":i,
            "ordering":o,"dead_letter":dl,
            "replay":rp,"backpressure":bp,
            "workflow_delivery":wc,
            "quality_gate":{"valid":True,"errors":[]}}
