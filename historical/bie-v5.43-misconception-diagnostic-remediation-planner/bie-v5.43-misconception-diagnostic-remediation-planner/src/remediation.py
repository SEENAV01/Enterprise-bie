def remediation(remediation_id,target_type,target_refs=None,
                 strategy=None,activities=None,check=None):
    return {"remediation_id":remediation_id,"target_type":target_type,
            "target_refs":target_refs or [],
            "strategy":strategy,
            "activities":activities or [],
            "check":check}

def remediation_types():
    return ["REEXPLAIN","CONCRETE_EXAMPLE","COUNTEREXAMPLE",
            "VISUAL_REPRESENTATION","GUIDED_PRACTICE",
            "PREREQUISITE_REVIEW","MISCONCEPTION_CONTRAST",
            "SCAFFOLDED_PROBLEM","RETEACH_AND_RETRY"]
