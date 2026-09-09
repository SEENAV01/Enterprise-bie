def assessment_for_objective(o):
    level=o["bloom"]
    mapping={
      "REMEMBER":"RECALL_CHECK",
      "UNDERSTAND":"EXPLANATION_CHECK",
      "APPLY":"PROBLEM_SOLVING",
      "ANALYZE":"COMPARISON_ANALYSIS",
      "EVALUATE":"JUSTIFICATION_TASK",
      "CREATE":"DESIGN_TASK"}
    return {"objective_id":o["objective_id"],"assessment_type":mapping[level],
            "bloom":level}

def assessment_map(objectives):
    return [assessment_for_objective(o) for o in objectives]
