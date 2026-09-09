from process import create_process_spec,validate_process_spec
from progress import progress_snapshot
from log_capture import capture_output,summarize_output
from artifact import verify_artifact

def create_worker_run(job, project_dir):
    spec=create_process_spec("npx",["remotion","render",job["composition_id"],job["output"]],
                             project_dir)
    return {"status":"QUEUED","process":spec,"progress":progress_snapshot([]),
            "logs":[],"artifact":None}

def ingest_event(run,event):
    kind=event.get("kind")
    if kind=="progress":
        run["progress"]=progress_snapshot([event])
    elif kind in ("stdout","stderr"):
        run["logs"].append(capture_output(event["stream"],event.get("text",""),
                                          event.get("level","INFO")))
    elif kind=="completed":
        run["status"]="SUCCEEDED"
        run["artifact"]=verify_artifact(event.get("output"),"mp4","h264",
                                        event.get("duration_frames"))
    elif kind=="failed":
        run["status"]="FAILED"
        run["logs"].append(capture_output("stderr",event.get("error",""),"ERROR"))
    return run

def validate_worker_run(run):
    p=validate_process_spec(run["process"])
    errors=list(p["errors"])
    if run["status"]=="SUCCEEDED" and not run.get("artifact",{}).get("valid",False):
        errors.append("ARTIFACT_VERIFICATION_FAILED")
    return {"valid":not errors,"errors":errors}
