from diagram import create_diagram,validate_diagram
from equation import create_equation,apply_equation_step,validate_equation_step
from visual_validation import validate_visual_step
from animation_state import create_animation_state,transition,sync_state

def build_visual_animation_runtime():
    d=create_diagram("D1",
      [{"id":"charge","type":"POINT_CHARGE","x":0,"y":0},
       {"id":"field","type":"VECTOR_FIELD","visible":False}],
      [{"source":"charge","target":"field","relation":"GENERATES"}])
    eq=create_equation("E1","E = F / q",{"E":"field","F":"force","q":"charge"})
    step=apply_equation_step(eq,"substitute","E = 10 / 2")
    eqcheck=validate_equation_step(step,"E = 10 / 2")
    state=create_animation_state("S1",d,eq)
    transition(state,"INTRO",0); transition(state,"ACTIVE",30)
    sync_state(state,equation={"expression":step["to"],"step":"substitute"})
    visual=validate_visual_step({"expression":"E = 10 / 2"},
                                state["equation"])
    gate=validate_diagram(d)
    return {"schema_version":"6.96","diagram":d,"diagram_validation":gate,
            "equation":eq,"equation_step":step,"equation_validation":eqcheck,
            "animation_state":state,"visual_step_validation":visual,
            "animation_gate":{"valid":gate["passed"] and eqcheck["valid"] and visual["valid"],
                              "errors":[]}}
