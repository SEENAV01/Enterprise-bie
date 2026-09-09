def concept(concept_id,name,concept_type="CONCEPT",
            definition=None,source_refs=None,prerequisites=None):
    return {"concept_id":concept_id,"name":name,"concept_type":concept_type,
            "definition":definition,"source_refs":source_refs or [],
            "prerequisites":prerequisites or []}

def definition_record(concept_id,text,source_refs=None):
    return {"concept_id":concept_id,"text":text,
            "source_refs":source_refs or []}
