def concept(concept_id,label,definition=None,source_refs=None,
            aliases=None):
    return {"concept_id":concept_id,"label":label,
            "definition":definition,"source_refs":source_refs or [],
            "aliases":aliases or []}
def concept_mapping(chunk_id,concept_id,relation="MENTIONS",
                    confidence=None):
    return {"chunk_id":chunk_id,"concept_id":concept_id,
            "relation":relation,"confidence":confidence}
