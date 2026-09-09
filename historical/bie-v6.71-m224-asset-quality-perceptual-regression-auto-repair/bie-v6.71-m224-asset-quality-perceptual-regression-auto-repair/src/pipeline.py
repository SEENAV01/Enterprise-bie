from quality_score import quality_score,classify
from perceptual import perceptual_similarity,above_threshold
from regression import regression_check
from repair import repair_plan
from regeneration import regeneration_policy,next_action
from diff import visual_diff

def build_quality_runtime():
    reference={"features":["field","charge","lines","label"]}
    candidate={"asset_id":"asset-field-002",
                "features":["field","charge","lines","label"],
                "technical_score":0.98,"semantic_score":0.95,
                "visual_score":0.94,"consistency_score":0.92}
    q=quality_score(candidate)
    sim=perceptual_similarity(reference,candidate)
    reg=regression_check(
        {"technical":0.98,"semantic":0.95,"visual":0.94,"consistency":0.92},
        {"technical":candidate["technical_score"],
         "semantic":candidate["semantic_score"],
         "visual":candidate["visual_score"],
         "consistency":candidate["consistency_score"]})
    diff=visual_diff(reference,candidate)
    failures=[k for k,v in q["components"].items() if v<0.75]
    repair=repair_plan(failures,candidate)
    policy=regeneration_policy(0,2)
    action=next_action(repair,policy)
    return {"schema_version":"6.71","quality":q,
            "quality_class":classify(q["score"]),
            "perceptual_similarity":sim,
            "visual_regression":reg,"visual_diff":diff,
            "repair_plan":repair,"regeneration_policy":policy,
            "next_action":action,
            "quality_gate":{"valid":(
                q["score"]>=0.75 and above_threshold(sim,0.8)
                and reg["passed"] and action=="ACCEPT"
            ),"errors":[]}}
