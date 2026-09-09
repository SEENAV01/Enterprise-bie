def leader_term(term, leader_id, epoch_id):
    return {"term":term,"leader_id":leader_id,
            "epoch_id":epoch_id,"status":"ACTIVE"}

def is_leader(record, participant_id):
    return record["leader_id"]==participant_id and record["status"]=="ACTIVE"
