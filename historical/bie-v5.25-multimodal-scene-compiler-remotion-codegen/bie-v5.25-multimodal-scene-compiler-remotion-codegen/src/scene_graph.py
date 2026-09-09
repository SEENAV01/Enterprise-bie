def scene(scene_id,concept_refs=None,objective_refs=None,
         visual_refs=None,audio_refs=None,children=None):
    return {"scene_id":scene_id,"concept_refs":concept_refs or [],
            "objective_refs":objective_refs or [],
            "visual_refs":visual_refs or [],
            "audio_refs":audio_refs or [],
            "children":children or []}

def node(node_id,node_type,props=None,children=None):
    return {"node_id":node_id,"node_type":node_type,
            "props":props or {},"children":children or []}
