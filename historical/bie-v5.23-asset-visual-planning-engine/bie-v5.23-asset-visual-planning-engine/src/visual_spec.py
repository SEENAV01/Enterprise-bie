def visual_spec(spec_id,concept_id,modality,
               objective_id=None,primitives=None,animation=None,
               narration_cues=None,source_refs=None):
    return {"spec_id":spec_id,"concept_id":concept_id,
            "objective_id":objective_id,"modality":modality,
            "primitives":primitives or [],
            "animation":animation or {},
            "narration_cues":narration_cues or [],
            "source_refs":source_refs or [],
            "render_target":"REMOTION"}
