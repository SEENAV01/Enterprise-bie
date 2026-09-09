def lesson_plan(lesson_id, title, objective_ids, strategy_ids,
                assessment_ids, prerequisite_ids=None, duration_min=None):
    if not objective_ids:
        raise ValueError("LESSON_REQUIRES_OBJECTIVES")
    return {"lesson_id": lesson_id, "title": title,
            "objective_ids": objective_ids,
            "strategy_ids": strategy_ids,
            "assessment_ids": assessment_ids,
            "prerequisite_ids": prerequisite_ids or [],
            "duration_min": duration_min}

def aligned(plan):
    return (bool(plan["objective_ids"]) and
            bool(plan["strategy_ids"]) and
            bool(plan["assessment_ids"]))
