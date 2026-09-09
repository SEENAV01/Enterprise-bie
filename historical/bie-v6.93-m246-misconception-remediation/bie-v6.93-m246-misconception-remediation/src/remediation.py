def remediation_plan(concept,error_types):
    actions=[]
    for e in error_types:
        actions.append({"concept_id":concept,"error_type":e,
                        "action":"RETEACH_AND_PRACTICE",
                        "hint_required":True,"reassessment_required":True})
    return actions

def prioritize(plans):
    return sorted(plans,key=lambda x:x["error_type"])
