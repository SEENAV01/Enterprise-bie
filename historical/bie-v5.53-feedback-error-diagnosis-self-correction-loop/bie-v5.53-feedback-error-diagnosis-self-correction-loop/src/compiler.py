from loop import correction_plan,next_iteration
from guardrails import loop_guard,should_escalate

def compile_correction(diagnosis,causes,previous_result,
                       iteration=0,max_iterations=3):
    plan=correction_plan(diagnosis,causes)
    guard=loop_guard(iteration,max_iterations)
    escalation=should_escalate(diagnosis)
    return {"schema_version":"5.53",
            "diagnosis":diagnosis,"causes":causes,
            "correction_plan":plan,
            "guard":guard,"escalate":escalation,
            "next_iteration":next_iteration(
                previous_result,diagnosis,causes),
            "quality_gate":{"valid":guard["allowed"] and
                                   not escalation,
                            "errors":(
                              [] if guard["allowed"] and not escalation
                              else ["HUMAN_REVIEW_OR_LOOP_STOP"])}}}
