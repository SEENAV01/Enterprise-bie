from worker import create_worker_run,ingest_event,validate_worker_run
from log_capture import summarize_output

def build_m256_runtime():
    job={"composition_id":"scene-c-field","output":"dist/lesson.mp4",
         "fps":30,"duration_in_frames":120}
    run=create_worker_run(job,"remotion-project")
    events=[
      {"kind":"stdout","stream":"stdout","text":"Remotion render started"},
      {"kind":"progress","frame":60,"total_frames":120,"status":"RENDERING"},
      {"kind":"progress","frame":120,"total_frames":120,"status":"RENDERING"},
      {"kind":"completed","output":"dist/lesson.mp4","duration_frames":120}]
    for e in events: ingest_event(run,e)
    run["log_summary"]=summarize_output(run["logs"])
    validation=validate_worker_run(run)
    return {"schema_version":"7.03","worker_run":run,
            "worker_validation":validation,
            "execution_gate":{"valid":validation["valid"],"errors":validation["errors"]}}
