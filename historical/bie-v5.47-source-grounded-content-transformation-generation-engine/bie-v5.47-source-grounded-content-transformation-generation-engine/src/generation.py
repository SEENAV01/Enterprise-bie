def generation_request(request_id,output_type,objective_refs=None,
                      source_fragment_refs=None,allow_generation=True,
                      constraints=None):
    return {"request_id":request_id,"output_type":output_type,
            "objective_refs":objective_refs or [],
            "source_fragment_refs":source_fragment_refs or [],
            "allow_generation":allow_generation,
            "constraints":constraints or {}}

def classify_content(source_refs,generated_refs):
    if source_refs and generated_refs: return "MIXED"
    if source_refs: return "SOURCE_DERIVED"
    if generated_refs: return "GENERATED"
    return "UNATTRIBUTED"
