from .element_compiler_common import *
def compile_equation_element(element):
    eid,props,acc,src,rsn=require_type(element,"equation")
    expr=props.get("expression")
    if not isinstance(expr,str) or not expr:
        raise ElementCompilerError("equation expression required")
    fmt=props.get("format","latex")
    if fmt not in {"latex","mathml","plain"}:
        raise ElementCompilerError("unsupported equation format")
    comp=component_name("Equation",eid)
    side=props.get("side_conditions",())
    label=acc.get("alt") or expr
    source=f"""import React from "react";
import {{Interactive}} from "remotion";

export const {comp}: React.FC = () => {{
  const expression = {jsx(expr)};
  const sideConditions = {jsx(list(side))};
  return (
    <Interactive.Div name={{{jsx(eid)}}} role="math" aria-label={{{jsx(label)}}}>
      <div data-equation-format={{{jsx(fmt)}}}>{{expression}}</div>
      {{sideConditions.length > 0 ? (
        <div aria-label="side conditions">{{sideConditions.join(", ")}}</div>
      ) : null}}
    </Interactive.Div>
  );
}};
"""
    warnings=() if fmt=="mathml" else ("equation_renderer_dependency_may_be_required_for_typeset_output",)
    return compile_result(eid,"equation",comp,source,warnings=warnings)
