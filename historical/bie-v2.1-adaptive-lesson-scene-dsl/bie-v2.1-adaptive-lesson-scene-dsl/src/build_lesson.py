import json,sys
from pathlib import Path
from lesson_planner import plan
from scene_dsl import compile_lesson

def run(path,out):
    d=json.loads(Path(path).read_text())
    units=plan(d["graph"],d.get("evidence",[]))
    lesson=compile_lesson(units,d["graph"].get("edges",[]))
    result={
      "schema_version":"2.1",
      "lesson_id":"LESSON_AUTO_001",
      "learning_units":lesson,
      "adaptive_policy":{
        "below_0.60":"RETEACH",
        "0.60_to_0.80":"PRACTICE",
        "0.80_to_0.90":"APPLY",
        "above_0.90":"ADVANCE_OR_SKIP"
      }
    }
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    run(sys.argv[1],sys.argv[2])
