def compile_coverage_plan(target_refs,sources,fragments,
                          coverage_records,gaps):
    source_ids={s["source_id"] for s in sources}
    fragment_errors=[]
    for f in fragments:
        if f.get("source_ref") not in source_ids:
            fragment_errors.append("FRAGMENT_SOURCE_MISSING")
    plan=[]
    by_target={r["target_ref"]:r for r in coverage_records}
    for target in target_refs:
        r=by_target.get(target)
        if not r:
            plan.append({"target_ref":target,"action":"RETRIEVE"})
        elif r.get("status") in ["MISSING","INSUFFICIENT_EVIDENCE"]:
            plan.append({"target_ref":target,"action":"RETRIEVE_OR_GENERATE"})
        elif r.get("status")=="GENERATE":
            plan.append({"target_ref":target,"action":"GENERATE"})
    return {"schema_version":"5.46",
            "sources":sources,"fragments":fragments,
            "coverage":coverage_records,"gaps":gaps,
            "next_actions":plan,
            "quality_gate":{"valid":not fragment_errors,
                            "errors":sorted(set(fragment_errors))}}
