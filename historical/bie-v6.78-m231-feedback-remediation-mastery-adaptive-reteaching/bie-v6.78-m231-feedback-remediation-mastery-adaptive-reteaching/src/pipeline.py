from feedback import feedback,feedback_level
from mastery import estimate_mastery,concept_mastery
from remediation import remediation_path
from adaptive import adaptive_plan

def build_adaptive_runtime():
    results=[
      {"item_id":"a1","concept_id":"charge","score":1.0},
      {"item_id":"a2","concept_id":"field","score":0.55},
      {"item_id":"a3","concept_id":"force","score":0.35}]
    feedback_items=[
      feedback("a1",True,1.0,"Correct: the relationship was applied correctly."),
      feedback("a2",False,0.55,"Review electric-field definition.","definition_confusion"),
      feedback("a3",False,0.35,"Revisit the force calculation step by step.","formula_confusion")]
    overall=estimate_mastery(results)
    cm=concept_mastery(results)
    remediation={c:remediation_path(c,m) for c,m in cm.items()}
    plan=adaptive_plan(list(cm),cm,{"field":["charge"],"force":["field"]})
    return {"schema_version":"6.78","results":results,
            "feedback":feedback_items,"feedback_levels":[feedback_level(x["score"]) for x in results],
            "overall_mastery":overall,"concept_mastery":cm,
            "remediation":remediation,"adaptive_plan":plan,
            "mastery_gate":{"valid":overall["sample_count"]>0 and
                all(0<=v<=1 for v in cm.values()),"errors":[]}}
