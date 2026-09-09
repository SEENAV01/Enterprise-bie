def provenance_record(output_id,operation,input_ids,source_ids=None):
    return {"output_id":output_id,"operation":operation,
            "input_ids":input_ids,"source_ids":source_ids or []}

def provenance_chain(records,output_id):
    return [r for r in records if r.get("output_id")==output_id]
