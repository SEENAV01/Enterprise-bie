from questions import generate_diagnostic_questions
from scoring import score_response,aggregate_mastery
from diagnostics import diagnostic_report
from feedback import feedback_batch
from adaptation import adapt_from_diagnosis

def build_assessment_runtime():
    questions=generate_diagnostic_questions("c-field","Electric Field")
    responses={"c-field-D1":"Definition","c-field-D2":"Core principle"}
    results=[score_response(q,responses.get(q["question_id"])) for q in questions]
    mastery=aggregate_mastery(results)
    report=diagnostic_report(results)
    feedback=feedback_batch(results,questions)
    adaptation=adapt_from_diagnosis(report)
    return {"schema_version":"6.92","questions":questions,"results":results,
            "mastery":mastery,"diagnostic_report":report,"feedback":feedback,
            "adaptation":adaptation,
            "assessment_gate":{"valid":bool(questions) and all("score" in r for r in results),
                               "errors":[]}}
