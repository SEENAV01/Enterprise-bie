from events import make_event
from bus import publish,subscribe,poll
from delivery import deliver_once
from ordering import ordered,ordering_errors
from dlq import dead_letter,retryable
from workflow import trigger_workflow

def build_m269_runtime():
    bus={}; deliveries={}; dlq=[]
    e1=make_event("evt-1","SCENE_COMPLETED","scene-1",1,{"scene_id":"scene-1"})
    e2=make_event("evt-2","QA_PASSED","scene-1",2,{"score":96})
    publish(bus,e1); publish(bus,e2)
    subscribe(bus,"workflow-engine","SCENE_COMPLETED")
    received=poll(bus,"workflow-engine","SCENE_COMPLETED")
    d1=deliver_once(deliveries,e1,"workflow-engine")
    d2=deliver_once(deliveries,e1,"workflow-engine")
    order=ordered([e2,e1])
    errors=ordering_errors([e1,e2])
    failed=dead_letter(dlq,e2,"DOWNSTREAM_UNAVAILABLE",3)
    workflows=trigger_workflow(e1,[{"event_type":"SCENE_COMPLETED","workflow":"START_QA"}])
    return {"schema_version":"7.16","published":[e1,e2],"received":received,
            "delivery":{"first":d1,"duplicate":d2},"ordered":order,
            "ordering_errors":errors,"dead_letter":failed,
            "retryable_after_3":retryable(3),
            "workflow_triggers":workflows,
            "event_bus_gate":{"valid":d1["delivered"] and d2["duplicate"] and
                              not errors and not retryable(3),"errors":[]}}
