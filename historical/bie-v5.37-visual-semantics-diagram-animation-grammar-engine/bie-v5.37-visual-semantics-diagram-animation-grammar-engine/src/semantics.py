def semantic_mapping(primitive_id,concept_ref,
                     meaning,source_ref=None):
    return {"primitive_id":primitive_id,"concept_ref":concept_ref,
            "meaning":meaning,"source_ref":source_ref}

def semantic_scene(scene_id,objective_ref,primitives,relations,
                   mappings=None):
    return {"scene_id":scene_id,"objective_ref":objective_ref,
            "primitives":primitives,"relations":relations,
            "mappings":mappings or []}
