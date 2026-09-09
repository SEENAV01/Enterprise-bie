def knowledge_snapshot(snapshot_id,dataset_snapshot,
                       retrieval_evidence,created_at):
    return {"snapshot_id":snapshot_id,
            "dataset":dataset_snapshot,
            "retrieval_evidence":retrieval_evidence,
            "created_at":created_at}

def evidence_refs(snapshot):
    refs=[]
    for hit in snapshot.get("retrieval_evidence",{}).get("hits",[]):
        c=hit.get("chunk",{})
        if c.get("chunk_id"): refs.append(c["chunk_id"])
    return refs
