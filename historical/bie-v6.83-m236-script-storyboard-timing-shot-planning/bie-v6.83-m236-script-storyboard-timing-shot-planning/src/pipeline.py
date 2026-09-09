from script import build_script
from storyboard import storyboard
from timing import assign_timing
from sync import sync_narration,validate_sync
from shots import shot_plan,validate_shots

def build_video_planning_runtime():
    concepts=[{"concept_id":"c1","title":"electric charge"},
              {"concept_id":"c2","title":"electric field"}]
    objectives=[{"objective_id":"o1","text":"Explain electric charge","concept_ids":["c1"]},
                {"objective_id":"o2","text":"Explain electric field","concept_ids":["c2"]}]
    script=build_script(objectives,concepts)
    board=storyboard(script)
    timings=assign_timing(script)
    narration=sync_narration(script,timings)
    shots=shot_plan(board,timings)
    sync_check=validate_sync(narration)
    shot_check=validate_shots(shots)
    return {"schema_version":"6.83","script":script,"storyboard":board,
            "timings":timings,"narration_sync":narration,"shot_plan":shots,
            "sync_validation":sync_check,"shot_validation":shot_check,
            "video_planning_gate":{"valid":sync_check["passed"] and shot_check["passed"],
                                   "errors":[]}}
