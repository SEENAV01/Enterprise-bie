from claims import claim,validate_claim
from math_check import check_equation,check_relation
from physics_check import check_physics_relation,check_units
from multimodal_check import check_alignment,check_modalities
from educational_qa import check_learning_objective,qa_summary
from review import review

def build_educational_qa():
    claims=[claim("c1","Electric force follows Coulomb relation","PHYSICS","curriculum"),
            claim("c2","F = k q1 q2 / r^2","EQUATION","curriculum")]
    checks={
      "claims":{"passed":all(validate_claim(c) for c in claims)},
      "equation":check_equation(10,10),
      "relation":check_relation(0.98,1.0,0.05),
      "physics":check_physics_relation(9.8,9.8,0.01,True),
      "units":check_units("N","N"),
      "multimodal":check_alignment("electric force acts between charges",
          "electric force diagram between charges","electric force acts between charges"),
      "modalities":check_modalities({"narration","visual","captions"}),
      "objective":check_learning_objective("understand electric force",
          ["understand","electric","force","charges"])
    }
    result=review(checks,claims)
    result["educational_summary"]=qa_summary(checks)
    return {"schema_version":"6.72","claims":claims,"checks":checks,
            "review":result,"educational_qa_gate":{"valid":result["passed"],"errors":[]}}
