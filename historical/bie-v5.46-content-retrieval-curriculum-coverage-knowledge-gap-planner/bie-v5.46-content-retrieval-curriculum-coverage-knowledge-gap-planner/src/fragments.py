def content_fragment(fragment_id,source_ref,text=None,
                    locator=None,concept_refs=None,objective_refs=None,
                    provenance=None):
    return {"fragment_id":fragment_id,"source_ref":source_ref,
            "text":text,"locator":locator,
            "concept_refs":concept_refs or [],
            "objective_refs":objective_refs or [],
            "provenance":provenance or {}}
