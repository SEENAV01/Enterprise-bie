from results import aggregate_status

def quality_gate(results,contract):
    status=aggregate_status(results)
    required=set(contract.get("acceptance",{}).get("required_checks",[]))
    completed={r["check_id"] for r in results if r.get("status")=="PASS"}
    missing=sorted(required-completed)
    if missing: status="FAIL"
    if status=="NEEDS_REVIEW" and not contract.get("acceptance",{}).get(
        "allow_review",True):
        status="FAIL"
    return {"status":status,"missing_required_checks":missing,
            "accepted":status=="PASS"}
