def remediation_path(concept_id,mastery,prerequisites=None):
    prerequisites=prerequisites or []
    if mastery>=0.85:
        return {"concept_id":concept_id,"action":"ADVANCE","prerequisites":prerequisites}
    if mastery>=0.60:
        return {"concept_id":concept_id,"action":"TARGETED_PRACTICE",
                "prerequisites":prerequisites}
    return {"concept_id":concept_id,"action":"RETEACH_AND_PRACTICE",
            "prerequisites":prerequisites}

def prioritize(concept_masteries):
    return sorted(concept_masteries.items(),key=lambda x:x[1])
