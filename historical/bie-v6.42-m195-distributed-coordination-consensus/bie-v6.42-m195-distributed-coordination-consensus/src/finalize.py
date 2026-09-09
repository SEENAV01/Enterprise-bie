def finalize(coordination_id, term,
             proposal_hash, decision="COMMITTED"):
    if decision not in {"COMMITTED","REJECTED"}:
        raise ValueError("INVALID_FINAL_DECISION")
    return {"coordination_id":coordination_id,"term":term,
            "proposal_hash":proposal_hash,"decision":decision,
            "status":"FINALIZED"}

def finalized(record):
    return record["status"]=="FINALIZED"
