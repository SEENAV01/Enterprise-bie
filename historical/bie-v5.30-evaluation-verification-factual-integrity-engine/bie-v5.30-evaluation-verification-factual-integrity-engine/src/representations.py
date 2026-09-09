def representation(rep_id,concept_id,rep_type,value,
                   source_claim_refs=None):
    return {"rep_id":rep_id,"concept_id":concept_id,
            "rep_type":rep_type,"value":value,
            "source_claim_refs":source_claim_refs or []}

def consistency_check(representations):
    if not representations: return {"valid":True,"reason":"NO_REPRESENTATIONS"}
    values={str(r.get("value")) for r in representations}
    return {"valid":len(values)<=1,
            "values":list(values),
            "error":"CROSS_REPRESENTATION_MISMATCH" if len(values)>1 else None}
