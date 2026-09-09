def leadership(group,
              leader_id=None,
              epoch=0):
    return {"group":group,
            "leader_id":leader_id,
            "epoch":epoch,
            "status":"ELECTED" if leader_id else "NO_LEADER"}

def is_leader(record,worker_id):
    return record["status"]=="ELECTED" and record["leader_id"]==worker_id
