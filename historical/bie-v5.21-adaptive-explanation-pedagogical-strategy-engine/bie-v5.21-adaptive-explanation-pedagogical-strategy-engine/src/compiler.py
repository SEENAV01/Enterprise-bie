from selection import select_strategy
from explanations import explanation_plan
from practice import practice_plan
from interventions import misconception_intervention,choose_intervention

def compile_adaptive_plan(learner,concept,difficulty_level,
                          misconception_id=None,misconception_risk=0.0):
    s=select_strategy(learner,concept,difficulty_level,misconception_risk)
    intervention=choose_intervention(misconception_risk)
    return {"schema_version":"5.21",
            "learner_id":learner.get("learner_id"),
            "concept_id":concept,
            "strategy":s,
            "explanation":explanation_plan(
                concept,s["explanation_depth"],
                example_count=2 if s["explanation_depth"]=="FOUNDATIONAL" else 1),
            "practice":practice_plan(concept,s["practice_density"]),
            "misconception_intervention":
                misconception_intervention(concept,misconception_id,
                                           intervention) if misconception_id else None,
            "quality_gate":{"valid":True,"errors":[]}}
