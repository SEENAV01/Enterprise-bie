from .element_compiler_common import *
def compile_simulation_element(element):
    eid,props,acc,src,rsn=require_type(element,"simulation")
    model_ref=props.get("model_ref")
    if not isinstance(model_ref,str) or not model_ref:
        raise ElementCompilerError("simulation model_ref required")
    execution=props.get("execution_class","conceptual")
    if execution=="verified_observed_execution" and not props.get("receipt_ref"):
        raise ElementCompilerError("verified simulation requires receipt_ref")
    comp=component_name("Simulation",eid)
    source=f"""import React from "react";
import {{Interactive}} from "remotion";

const initialState = {jsx(props.get("initial_state",{}))};

export const {comp}: React.FC = () => {{
  return (
    <Interactive.Div name={{{jsx(eid)}}} role="region" aria-label={{{jsx(acc.get("alt") or "simulation")}}}>
      <pre data-model-ref={{{jsx(model_ref)}}} data-execution-class={{{jsx(execution)}}}>
        {{JSON.stringify(initialState, null, 2)}}
      </pre>
    </Interactive.Div>
  );
}};
"""
    return compile_result(eid,"simulation",comp,source)
