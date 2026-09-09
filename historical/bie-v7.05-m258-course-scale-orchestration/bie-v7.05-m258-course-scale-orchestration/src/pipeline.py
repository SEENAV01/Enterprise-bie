from dag import build_course_dag,topo_order
from batch import create_batch,update_batch
from incremental import fingerprint,plan_incremental
from progress import course_progress,lesson_progress
from scheduler import schedule_course

def build_m258_runtime():
    nodes=[{"id":"lesson-1"},{"id":"lesson-2"},{"id":"lesson-3"}]
    edges=[{"source":"lesson-1","target":"lesson-2"},
           {"source":"lesson-2","target":"lesson-3"}]
    dag=build_course_dag(nodes,edges)
    order=topo_order(dag)
    scheduling=schedule_course(dag,["lesson-1"],capacity=2)
    batch=create_batch(["scene-1","scene-2"],"batch-001")
    update_batch(batch,"SUCCEEDED"); update_batch(batch,"SUCCEEDED")
    previous={"lesson-1":{"fingerprint":fingerprint({"topic":"field"})}}
    current=[{"id":"lesson-1","inputs":{"topic":"field"}},
             {"id":"lesson-2","inputs":{"topic":"charge"}}]
    incremental=plan_incremental(previous,current)
    lessons=[{"id":"lesson-1","status":"SUCCEEDED"},
             {"id":"lesson-2","status":"RUNNING"},{"id":"lesson-3","status":"QUEUED"}]
    progress=course_progress(lessons)
    scene_progress=lesson_progress([{"status":"SUCCEEDED"},{"status":"SUCCEEDED"}])
    valid=dag["valid"] and order["valid"] and bool(scheduling["selected"]) and batch["status"]=="SUCCEEDED"
    return {"schema_version":"7.05","dag":dag,"topological_order":order,
            "schedule":scheduling,"batch":batch,"incremental_plan":incremental,
            "course_progress":progress,"lesson_progress":scene_progress,
            "course_orchestration_gate":{"valid":valid,"errors":[] if valid else ["ORCHESTRATION_FAILURE"]}}
