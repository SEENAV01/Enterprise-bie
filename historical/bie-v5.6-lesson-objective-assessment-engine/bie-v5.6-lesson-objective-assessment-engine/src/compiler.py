from assessment import assessment_blueprint
from mastery import mastery_status
from adaptive import next_action

def compile_assessment(objectives, questions, learner_state=None):
    learner_state=learner_state or {}
    ids=[o["objective_id"] for o in objectives]
    blueprint=assessment_blueprint(ids,questions)
    concept_mastery={}
    for o in objectives:
        m=learner_state.get(o["concept_id"],{}).get("mastery",0)
        concept_mastery[o["concept_id"]]={
          "mastery":m,
          "status":mastery_status(m),
          "next_action":next_action(m,True)
        }
    return {
      "schema_version":"5.6",
      "objectives":objectives,
      "questions":questions,
      "assessment_blueprint":blueprint,
      "learner_mastery":concept_mastery,
      "quality_gate":{"valid":blueprint["coverage_complete"],
                     "errors":["OBJECTIVE_COVERAGE_GAP"] if not blueprint["coverage_complete"] else []}
    }
