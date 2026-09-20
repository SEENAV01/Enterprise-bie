from .element_compiler_common import *
def compile_vector_element(element):
    eid,props,acc,src,rsn=require_type(element,"vector")
    comps=props.get("components")
    if not isinstance(comps,(list,tuple)) or len(comps) not in {2,3}:
        raise ElementCompilerError("vector components must be 2D/3D")
    try:x=float(comps[0]);y=float(comps[1])
    except Exception as exc:raise ElementCompilerError("vector components numeric") from exc
    comp=component_name("Vector",eid)
    scale=40
    x2=100+x*scale;y2=100-y*scale
    source=f"""import React from "react";

export const {comp}: React.FC = () => {{
  return (
    <svg viewBox="0 0 200 200" role="img" aria-label={{{jsx(acc.get("alt") or props.get("label") or "vector")}}}>
      <defs>
        <marker id="arrow-{comp}" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
          <path d="M0,0 L0,6 L9,3 z" />
        </marker>
      </defs>
      <line x1={{100}} y1={{100}} x2={{{x2}}} y2={{{y2}}} stroke="currentColor" strokeWidth={{3}} markerEnd="url(#arrow-{comp})" />
    </svg>
  );
}};
"""
    return compile_result(eid,"vector",comp,source)
