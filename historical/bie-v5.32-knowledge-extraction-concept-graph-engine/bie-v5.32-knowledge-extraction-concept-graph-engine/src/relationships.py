def relationship(rel_id,source,target,relation_type,
                 source_refs=None,confidence=None):
    return {"rel_id":rel_id,"source":source,"target":target,
            "relation_type":relation_type,"source_refs":source_refs or [],
            "confidence":confidence}

def relation_types():
    return ["PREREQUISITE_OF","PART_OF","RELATED_TO","CAUSES",
            "DEPENDS_ON","EXAMPLE_OF","USES","CONTRASTS_WITH"]
