def plan_coverage(target_refs,coverage_records,gaps):
    by_target={r["target_ref"]:r for r in coverage_records}
    actions=[]
    for target in target_refs:
        c=by_target.get(target)
        if c is None:
            actions.append({"target_ref":target,"action":"RETRIEVE"})
        elif c.get("status") in ["MISSING","INSUFFICIENT_EVIDENCE"]:
            actions.append({"target_ref":target,"action":"RETRIEVE_OR_GENERATE"})
        elif c.get("status")=="GENERATE":
            actions.append({"target_ref":target,"action":"GENERATE"})
    for g in gaps:
        if g.get("status")=="OPEN":
            actions.append({"target_ref":g["target_ref"],
                            "action":"ADDRESS_GAP",
                            "gap_type":g.get("gap_type")})
    return actions
