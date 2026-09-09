def curriculum_concept(concept_id,label,domain=None,description=None):
    return {"concept_id":concept_id,"label":label,"domain":domain,
            "description":description,"prerequisites":[],"objectives":[],
            "misconceptions":[],"learning_events":[]}
