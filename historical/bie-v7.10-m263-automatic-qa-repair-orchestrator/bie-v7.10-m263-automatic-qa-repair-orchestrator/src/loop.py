from diagnosis import diagnose
from strategy import select_strategies
from repair import create_repair_job,apply_repair_result
from rerender import targeted_rerender

def run_repair_cycle(scene_id, asset_id, qa_result, max_cycles=2):
    errors=qa_result.get("errors",[])
    diagnosis=diagnose(errors)
    strategies=select_strategies(diagnosis["actions"])
    jobs=[create_repair_job(asset_id,s["action"],s["target"],s["mode"],errors) for s in strategies]
    for j in jobs: apply_repair_result(j,f"repaired/{asset_id}-{j['target']}.bin")
    rerender=targeted_rerender(scene_id,[j["target"] for j in jobs])
    return {"diagnosis":diagnosis,"strategies":strategies,"repair_jobs":jobs,
            "targeted_rerender":rerender,"cycle":1,"max_cycles":max_cycles}
