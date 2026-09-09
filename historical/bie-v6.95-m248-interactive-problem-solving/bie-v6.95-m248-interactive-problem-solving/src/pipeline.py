from state import create_state
from session import process_turn,session_summary
from step_validation import validate_sequence

def build_interactive_runtime():
    steps=["Identify E = F/q.","Substitute the known values.","Compute and attach the unit."]
    state=create_state("P-1",steps)
    turn1=process_turn(state,"wrong",steps[0],steps[0])
    turn2=process_turn(state,steps[0],steps[0],steps[0])
    gate=validate_sequence(state)
    return {"schema_version":"6.95","state":state,"turns":[turn1,turn2],
            "summary":session_summary(state),"sequence_validation":gate,
            "interactive_gate":{"valid":gate["passed"],"errors":[]}}
