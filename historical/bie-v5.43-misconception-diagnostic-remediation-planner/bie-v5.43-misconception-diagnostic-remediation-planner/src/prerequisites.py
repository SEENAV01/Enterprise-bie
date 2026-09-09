def prerequisite(concept_ref,required_for,reason=None,
                 priority=0.5):
    return {"concept_ref":concept_ref,"required_for":required_for,
            "reason":reason,"priority":priority}

def rank_prerequisites(prereqs):
    return sorted(prereqs,key=lambda x:x.get("priority",0),reverse=True)
