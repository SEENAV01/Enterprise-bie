import json, sys
from pathlib import Path

def build(manifest_path,out_path):
    m=json.loads(Path(manifest_path).read_text())
    jobs=[]
    for u in m["units"]:
        jobs.append({
            "composition_id":u["unit_id"],
            "status":"READY_FOR_SCENE_QC",
            "source_refs":u["source_refs"]
        })
    result={
        "lesson_id":m["lesson_id"],
        "final_gate":"BLOCK_ON_CRITICAL_QC",
        "jobs":jobs
    }
    Path(out_path).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    build(sys.argv[1],sys.argv[2])
