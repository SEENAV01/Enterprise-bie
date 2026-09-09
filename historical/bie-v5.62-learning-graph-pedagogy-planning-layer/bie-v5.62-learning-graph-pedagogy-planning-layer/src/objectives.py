def objective(objective_id,statement,domain=None,
              mastery_criteria=None,priority=0):
    return {"objective_id":objective_id,"statement":statement,
            "domain":domain,"mastery_criteria":mastery_criteria or {},
            "priority":priority}
