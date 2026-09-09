def beat(beat_id,kind,objective_ref=None,scene_ref=None,
         trigger=None,importance=0.5):
    return {"beat_id":beat_id,"kind":kind,"objective_ref":objective_ref,
            "scene_ref":scene_ref,"trigger":trigger,
            "importance":importance}

def beat_types():
    return ["INTRO","ATTENTION","EXPLAIN","DEMONSTRATE","PREDICT",
            "INTERACT","PRACTICE","FEEDBACK","REFLECT","ASSESS",
            "TRANSITION","SUMMARY"]
