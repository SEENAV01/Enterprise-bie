def interaction(interaction_id,interaction_type,objective_id,
                prompt=None,inputs=None,outputs=None,feedback=None):
    return {"interaction_id":interaction_id,"interaction_type":interaction_type,
            "objective_id":objective_id,"prompt":prompt,
            "inputs":inputs or [],"outputs":outputs or [],
            "feedback":feedback}

def interaction_types():
    return ["EXPLANATION","DEMONSTRATION","PREDICTION","EXPLORATION",
            "QUESTION","PRACTICE","SIMULATION","REFLECTION","ASSESSMENT"]
