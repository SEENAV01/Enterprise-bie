def scene_intent(scene_id,objective_id,representation_refs=None,
                 explanation_goal=None):
    return {"scene_id":scene_id,"objective_id":objective_id,
            "representation_refs":representation_refs or [],
            "explanation_goal":explanation_goal}
