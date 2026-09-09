from error_taxonomy import classify_error
from misconceptions import detect_misconception,misconception_gate
from hints import generate_hint
from remediation import remediation_plan,prioritize
from reassessment import reassessment_decision,close_loop

def build_misconception_runtime():
    concept="Electric Field"
    questions=[
      {"question_id":"q1","error_hint":"DEFINITION_CONFUSION"},
      {"question_id":"q2","error_hint":"UNIT_ERROR"}]
    responses=[
      {"question_id":"q1","error":{"type":"DEFINITION_CONFUSION"}},
      {"question_id":"q2","error":{"type":"UNIT_ERROR"}}]
    detected=detect_misconception(responses)
    gate=misconception_gate(detected)
    hints=[{"error_type":x["type"],"hint":generate_hint(x["type"],concept)} for x in detected]
    plans=prioritize(remediation_plan(concept,[x["type"] for x in detected]))
    decision=reassessment_decision(.45,.78)
    loop=close_loop(decision)
    return {"schema_version":"6.93","concept":concept,
            "detected_misconceptions":detected,"misconception_gate":gate,
            "hints":hints,"remediation_plan":plans,
            "reassessment":decision,"mastery_loop":loop,
            "remediation_gate":{"valid":gate["passed"] and bool(plans) and decision["passed"],
                                "errors":[]}}
