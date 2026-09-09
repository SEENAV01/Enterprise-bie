def scaffold_steps(example,completed_steps=0):
    steps=example.get("steps",[])
    completed=max(0,min(completed_steps,len(steps)))
    return {"example_id":example.get("example_id"),"visible_steps":steps[:completed+1],
            "next_step":steps[completed] if completed<len(steps) else None,
            "completed_steps":completed,"total_steps":len(steps)}

def validate_step_order(scaffold):
    return {"passed":scaffold["completed_steps"]<=scaffold["total_steps"],
            "errors":[] if scaffold["completed_steps"]<=scaffold["total_steps"] else ["INVALID_STEP_INDEX"]}
