def reconstruction_spec(asset):
    return {
        "asset_id":asset["asset_id"],
        "input":"SOURCE_ASSET",
        "mode":"STRUCTURED_RECONSTRUCTION",
        "extract":["text_labels","shapes","arrows","relationships","colors","regions"],
        "output":"EDITABLE_VECTOR_SCENE",
        "human_review_if_confidence_low":True
    }

def fallback_spec(scene_objective):
    return {
        "mode":"GENERATED_VISUAL_FALLBACK",
        "objective":scene_objective,
        "must_preserve":["scientific_relationships","labels","quantities","directionality"],
        "source_status":"EXTERNAL_GENERATED",
        "review_required":True
    }
