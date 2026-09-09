def prepare(coordination_id, participant_id,
            term, proposal_hash):
    return {"coordination_id":coordination_id,
            "participant_id":participant_id,"term":term,
            "proposal_hash":proposal_hash,"status":"PREPARED"}

def prepared(record):
    return record["status"]=="PREPARED"
