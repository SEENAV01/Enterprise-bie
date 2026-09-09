def objective(objective_id,text,level="UNDERSTAND",standards=None):
    return {"objective_id":objective_id,"text":text,"level":level,
            "standards":standards or []}
def map_objective(o,standards):
    ids={s["standard_id"] for s in standards}
    return {"objective_id":o["objective_id"],
            "mapped_standards":[x for x in o.get("standards",[]) if x in ids],
            "aligned":any(x in ids for x in o.get("standards",[]))}
