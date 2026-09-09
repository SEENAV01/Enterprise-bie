def citation_map(claims,grounded,sources):
    source_ids={s["source_id"] for s in sources}
    result=[]
    for g in grounded:
        valid=[e for e in g["evidence_ids"]]
        result.append({"claim_id":g["claim_id"],"evidence_ids":valid,
                       "citation_ready":bool(valid and source_ids)})
    return result
