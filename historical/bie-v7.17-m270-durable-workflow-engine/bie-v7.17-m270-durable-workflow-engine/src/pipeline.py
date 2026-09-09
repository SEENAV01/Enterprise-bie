from definition import workflow_definition
from engine import start,transition
from timeouts import set_timeout,timeout_due,fire_timeout
from compensation import compensate
from persistence import persist,resume
from recovery import recover,is_resumable

def build_m270_runtime():
    definition=workflow_definition(
        "course-render-v1",
        ["RUNNING","QA","COMPLETED","FAILED","CANCELLED"],
        {"RUNNING:RENDER_DONE":"QA","QA:QA_PASS":"COMPLETED",
         "QA:QA_FAIL":"FAILED","RUNNING:CANCEL":"CANCELLED"},
        "RUNNING")
    instance=start(definition,"workflow-001",{"course_id":"course-001"})
    transition(definition,instance,"RENDER_DONE",{"artifact":"render.mp4"})
    transition(definition,instance,"QA_PASS",{"score":98})
    store={}
    persisted=persist(instance,store)
    restored=resume("workflow-001",store)
    timer=set_timeout("workflow-001","QA",200)
    due=timeout_due(timer,201)
    fired=fire_timeout(timer)
    recovered=recover(restored["instance"],instance["history"])
    compensation=compensate(["RENDER","UPLOAD","INDEX"])
    return {"schema_version":"7.17","definition":definition,"instance":instance,
            "persistence":persisted,"resume":restored,"timeout":{"due":due,"timer":fired},
            "recovery":{"resumable":is_resumable(recovered),"instance":recovered},
            "compensation":compensation,
            "workflow_gate":{"valid":instance["state"]=="COMPLETED" and
                             persisted["ok"] and restored["ok"] and due,
                             "errors":[]}}
