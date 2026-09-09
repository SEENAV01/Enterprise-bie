from events import event,normalize_event
from metrics import counters,render_metrics
from tracing import start_span,finish_span
from analytics import failure_summary,scope_summary
from audit import audit_record,verify_audit

def build_m264_runtime():
    run="course-001"
    events=[
      event("RENDER_STARTED",run,{"lesson_id":"lesson-1","scene_id":"scene-1"}),
      event("RENDER_RETRY",run,{"lesson_id":"lesson-1","scene_id":"scene-1","code":"RENDER_TIMEOUT"}, "WARN"),
      event("RENDER_SUCCEEDED",run,{"lesson_id":"lesson-1","scene_id":"scene-1"}),
      event("RENDER_STARTED",run,{"lesson_id":"lesson-2","scene_id":"scene-3"}),
      event("RENDER_FAILED",run,{"lesson_id":"lesson-2","scene_id":"scene-3","code":"AUDIO_MISSING"},"ERROR")
    ]
    events=[normalize_event(e) for e in events]
    span=finish_span(start_span("trace-001","span-001","course-render"),
                     "ERROR",{"run_id":run})
    audit=[audit_record(run,"system","RENDER","scene-1","SUCCEEDED"),
           audit_record(run,"system","RENDER","scene-3","FAILED","AUDIO_MISSING")]
    result={"schema_version":"7.11","events":events,"counters":counters(events),
            "render_metrics":render_metrics(events),"trace":span,
            "failure_analytics":failure_summary(events),
            "lesson_summary":scope_summary(events,"lesson_id"),
            "scene_summary":scope_summary(events,"scene_id"),
            "audit":audit,"audit_validation":verify_audit(audit)}
    result["observability_gate"]={"valid":result["audit_validation"]["valid"] and
                                  bool(result["counters"]),
                                  "errors":[] if result["audit_validation"]["valid"] else ["AUDIT_INVALID"]}
    return result
