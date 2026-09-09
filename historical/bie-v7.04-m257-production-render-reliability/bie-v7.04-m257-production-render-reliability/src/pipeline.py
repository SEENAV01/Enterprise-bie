from queue import create_job,enqueue,dequeue
from scheduler import schedule
from checkpoint import save_checkpoint,resume_command
from retry import retry_job
from cache import cache_key,lookup,store
from cancellation import cancel,can_resume

def build_m257_runtime():
    queue=[]
    job=create_job("lesson-001",{"composition_id":"scene-c-field",
        "resources":{"cpu":2,"ram_mb":2048}},priority=100)
    queue=enqueue(queue,job)
    plan=schedule(queue,{"cpu":8,"ram_mb":8192},concurrency=2)
    running=plan["selected"][0]
    running["status"]="RUNNING"
    save_checkpoint(running,60)
    resume=resume_command(running)
    retry_job(running,"RENDER_TIMEOUT",max_attempts=3)
    cache={}
    key=cache_key("scene-c-field",{"version":"7.04","checkpoint":60})
    cached=lookup(cache,key)
    artifact={"path":"dist/lesson.mp4","verified":True}
    store(cache,key,artifact)
    cached_after=lookup(cache,key)
    cancel(running,"TEST_CANCEL")
    return {"schema_version":"7.04","queue":queue,"schedule":plan,
            "running_job":running,"resume_command":resume,"cache_key":key,
            "cache_before":cached,"cache_after":cached_after,
            "resume_available":can_resume(running),
            "reliability_gate":{"valid":bool(plan["selected"] and cached_after),
                                "errors":[] if plan["selected"] and cached_after else ["RELIABILITY_FAILURE"]}}
