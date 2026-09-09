def leadership(term, node_id, lease_until=None):
    return {"term":term,"node_id":node_id,
            "lease_until":lease_until,"status":"LEADER"}

def valid(record,current_term):
    return record["status"]=="LEADER" and record["term"]==current_term
