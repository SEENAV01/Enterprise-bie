from trace import trace_id,span,duration
from metrics import Metrics
from logging import log
from audit import audit_event,valid as audit_valid
from diagnostics import diagnose
from retention import retention_policy,valid as retention_valid
from trace_context import context

def build_observability():
    tid=trace_id()
    ctx=context(tid,"lesson-job-1","lesson-2")
    m=Metrics()
    s1=span("span-1","lesson.build",attributes={"job_id":"lesson-job-1"})
    s1["end"]=s1["start"]+2.5
    s2=span("span-2","render",parent_id=s1["span_id"])
    s2["end"]=s2["start"]+1.5
    s2["status"]="OK"
    m.inc("lessons.completed")
    m.observe("lesson.duration_seconds",duration(s1))
    m.observe("render.duration_seconds",duration(s2))
    m.set("workers.active",2)
    logs=[log("INFO","lesson completed",tid,"span-2",
              "lesson-job-1","lesson-2",{"duration":duration(s1)})]
    audits=[audit_event("audit-1","orchestrator","VERIFY",
                        "lesson-job-1","PASS",tid)]
    policy=retention_policy()
    diag=diagnose(logs,[s1,s2],m.snapshot())
    return {"schema_version":"6.65","trace_context":ctx,
            "spans":[s1,s2],"logs":logs,"metrics":m.snapshot(),
            "audit_log":audits,"retention_policy":policy,
            "diagnostics":diag,
            "observability_gate":{"valid":(
                ctx["trace_id"]==tid and duration(s1)==2.5
                and m.counters["lessons.completed"]==1
                and audit_valid(audits[0])
                and retention_valid(policy)
                and diag["health"]=="HEALTHY"
            ),"errors":[]}}
