from mastery import mastery_score,mastery_level
from readiness import prerequisite_readiness,readiness_gate
from difficulty import choose_difficulty,adapt_unit
from path_selection import select_path

def build_adaptive_runtime():
    signals={
      "c-charge":{"assessment":0.92,"practice":0.9,"completion":1,"confidence":0.85},
      "c-field":{"assessment":0.72,"practice":0.7,"completion":0.9,"confidence":0.65},
      "c-force":{"assessment":0.45,"practice":0.5,"completion":0.7,"confidence":0.4}}
    mastery={k:mastery_score(v) for k,v in signals.items()}
    levels={k:mastery_level(v) for k,v in mastery.items()}
    prereq={"c-field":["c-charge"],"c-force":["c-field"]}
    readiness=[prerequisite_readiness("c-field",prereq["c-field"],mastery),
               prerequisite_readiness("c-force",prereq["c-force"],mastery)]
    path=select_path("c-force",prereq,mastery,{"c-force":{"recent_failures":0}})
    diff={c:choose_difficulty(s) for c,s in mastery.items()}
    units=[adapt_unit({"concept_id":c},d) for c,d in diff.items()]
    gate=readiness_gate(readiness)
    return {"schema_version":"6.91","mastery_scores":mastery,
            "mastery_levels":levels,"readiness":readiness,
            "readiness_gate":gate,"path_selection":path,
            "difficulty":diff,"adapted_units":units,
            "adaptive_learning_gate":{"valid":gate["passed"],"errors":[]}}
