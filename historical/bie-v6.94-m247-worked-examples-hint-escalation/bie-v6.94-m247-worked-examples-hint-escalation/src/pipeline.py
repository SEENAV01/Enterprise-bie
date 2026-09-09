from examples import worked_example,validate_example
from scaffolding import scaffold_steps,validate_step_order
from hints import hint_for,escalate_hint
from reveal import reveal_policy

def build_scaffolding_runtime():
    ex=worked_example("EX-1","c-field",
        "Find the electric field from force and charge.",
        ["Identify E = F/q.","Substitute the known force and charge.",
         "Compute the quotient and attach the correct unit."],"E = F/q.")
    validation=validate_example(ex)
    scaffold=scaffold_steps(ex,1)
    scaffold_check=validate_step_order(scaffold)
    hint_level="STEP"
    hint=hint_for(ex,hint_level,1)
    next_level=escalate_hint(hint_level,correct=False)
    reveal=reveal_policy(False,False,next_level)
    return {"schema_version":"6.94","worked_example":ex,
            "example_validation":validation,"scaffold":scaffold,
            "scaffold_validation":scaffold_check,"hint_level":hint_level,
            "hint":hint,"next_hint_level":next_level,
            "answer_reveal_policy":reveal,
            "scaffolding_gate":{"valid":validation["passed"] and scaffold_check["passed"] and
                               reveal["allowed"],"errors":[]}}
