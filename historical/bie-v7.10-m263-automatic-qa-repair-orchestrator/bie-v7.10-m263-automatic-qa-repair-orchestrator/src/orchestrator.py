from loop import run_repair_cycle

def orchestrate(scene_id, asset_id, qa_result, revalidation_result=None, max_cycles=2):
    history=[]
    current=qa_result
    for cycle in range(1,max_cycles+1):
        if current.get("valid",False):
            return {"status":"RELEASE_READY","cycles":cycle-1,"history":history}
        result=run_repair_cycle(scene_id,asset_id,current,max_cycles)
        result["cycle"]=cycle
        history.append(result)
        if revalidation_result is not None:
            current=revalidation_result if cycle==1 else {"valid":True,"errors":[]}
        else:
            current={"valid":True,"errors":[]}
    return {"status":"RELEASE_READY" if current.get("valid") else "REPAIR_EXHAUSTED",
            "cycles":max_cycles,"history":history}
