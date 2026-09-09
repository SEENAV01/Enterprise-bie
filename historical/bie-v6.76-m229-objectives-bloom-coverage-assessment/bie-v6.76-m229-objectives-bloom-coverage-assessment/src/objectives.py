def objective(objective_id,text,concept_ids=None,bloom="UNDERSTAND",
             evidence=None):
    return {"objective_id":objective_id,"text":text,
            "concept_ids":concept_ids or [],"bloom":bloom,
            "evidence":evidence or []}

BLOOM_LEVELS=["REMEMBER","UNDERSTAND","APPLY","ANALYZE","EVALUATE","CREATE"]

def valid_bloom(level):
    return level in BLOOM_LEVELS
