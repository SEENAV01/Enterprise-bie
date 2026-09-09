from items import assessment_item,validate_item
from rubrics import rubric
from difficulty import calibrate_difficulty
from distractors import distractors,validate_distractors
from evaluation import evaluation_plan,coverage

def build_assessment_runtime():
    bloom="APPLY"
    difficulty=calibrate_difficulty(bloom,steps=2,abstraction=1)
    correct="12 N"
    choices=[correct]+distractors(correct,["10 N","6 N","24 N"])
    item=assessment_item("a1","s1-L1-O1","MCQ",
        "Calculate the electric force.",correct,difficulty,choices)
    item["bloom"]=bloom; item["steps"]=2; item["abstraction"]=1
    open_item=assessment_item("a2","s1-L1-O2","OPEN",
        "Explain the result using the governing relationship.",
        difficulty=difficulty)
    checks={"item":validate_item(item),
            "distractors":validate_distractors(correct,choices),
            "open_item":validate_item(open_item)}
    rub=[rubric("s1-L1-O2",["accuracy","reasoning","clarity"])]
    plan=evaluation_plan([item,open_item])
    cov=coverage([item,open_item],["s1-L1-O1","s1-L1-O2"])
    return {"schema_version":"6.77","items":[item,open_item],
            "rubrics":rub,"checks":checks,"evaluation_plan":plan,
            "coverage":cov,
            "assessment_gate":{"valid":all(v["passed"] for v in checks.values())
                and cov["coverage"]==1,"errors":[]}}
