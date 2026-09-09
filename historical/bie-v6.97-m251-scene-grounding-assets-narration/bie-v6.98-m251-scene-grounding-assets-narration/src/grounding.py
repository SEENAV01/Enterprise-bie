def ground_concept(concept_id, title, learning_goal, modalities=None):
    modalities=modalities or ["visual","equation","narration"]
    return {"concept_id":concept_id,"title":title,"learning_goal":learning_goal,
            "modalities":modalities}

def scene_intent(grounding, visual_intent, narration_intent, equation_intent=None):
    return {"concept_id":grounding["concept_id"],
            "visual_intent":visual_intent,"narration_intent":narration_intent,
            "equation_intent":equation_intent}
