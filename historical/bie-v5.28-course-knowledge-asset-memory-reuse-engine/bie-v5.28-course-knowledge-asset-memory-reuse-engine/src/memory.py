def memory_store(records=None,index=None):
    return {"records":records or [],"semantic_index":index or []}

def find_by_concept(records,concept_id):
    return [r for r in records if concept_id in r.get("concept_refs",[])]

def find_by_type(records,record_type):
    return [r for r in records if r.get("record_type")==record_type]
