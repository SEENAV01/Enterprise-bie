def election_candidate(node_id,term,
                      priority=0):
    return {"node_id":node_id,"term":term,
            "priority":priority}

def elect(candidates):
    if not candidates: return None
    return max(candidates,
               key=lambda x:(x.get("term",0),
                             x.get("priority",0),
                             x.get("node_id","")))
