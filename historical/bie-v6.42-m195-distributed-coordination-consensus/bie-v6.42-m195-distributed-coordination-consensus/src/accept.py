def accept(coordination_id, participant_id,
           term, proposal_hash):
    return {"coordination_id":coordination_id,
            "participant_id":participant_id,"term":term,
            "proposal_hash":proposal_hash,"status":"ACCEPTED"}

def accepted(record):
    return record["status"]=="ACCEPTED"
