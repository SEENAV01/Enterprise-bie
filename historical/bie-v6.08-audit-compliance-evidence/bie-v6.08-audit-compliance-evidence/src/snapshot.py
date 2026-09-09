def compliance_snapshot(snapshot_id,
                       period,controls,
                       generated_at):
    return {"snapshot_id":snapshot_id,
            "period":period,
            "controls":controls,
            "generated_at":generated_at,
            "status":"GENERATED"}

def summary(snapshot):
    controls=snapshot.get("controls",[])
    return {"total":len(controls),
            "pass":sum(x.get("status")=="PASS" for x in controls),
            "fail":sum(x.get("status")=="FAIL" for x in controls),
            "review":sum(x.get("status")=="REVIEW" for x in controls)}
