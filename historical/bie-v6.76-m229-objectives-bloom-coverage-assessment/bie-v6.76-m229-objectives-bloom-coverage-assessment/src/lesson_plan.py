from objectives import objective
from bloom import assign_bloom
from coverage import concept_coverage
from assessment import assessment_map

def generate_lesson_plan(lesson_id,concepts,action_verbs=None):
    action_verbs=action_verbs or ["explain"]
    level=assign_bloom(action_verbs)
    objectives=[]
    for i,c in enumerate(concepts):
        objectives.append(objective(
            f"{lesson_id}-O{i+1}",
            f"{action_verbs[0].lower()} {c['title']}",
            [c["concept_id"]],level))
    coverage=concept_coverage([c["concept_id"] for c in concepts],objectives)
    return {"lesson_id":lesson_id,"objectives":objectives,
            "coverage":coverage,"assessments":assessment_map(objectives)}

def validate_plan(plan):
    errors=[]
    if not plan["objectives"]: errors.append("NO_OBJECTIVES")
    if plan["coverage"]["missing"]: errors.append("UNCOVERED_CONCEPTS")
    return {"passed":not errors,"errors":errors}
