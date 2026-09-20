from .element_compiler_common import *
def compile_model2d_element(element):
    eid,props,acc,src,rsn=require_type(element,"model2d")
    vertices=props.get("vertices")
    if not isinstance(vertices,(list,tuple)) or len(vertices)<2:
        raise ElementCompilerError("model2d vertices required")
    verts=[(float(p[0]),float(p[1])) for p in vertices]
    edges=props.get("edges",())
    comp=component_name("Model2D",eid)
    source=f"""import React from "react";

const vertices = {jsx(verts)} as const;
const edges = {jsx(list(edges))} as const;

export const {comp}: React.FC = () => {{
  return (
    <svg viewBox="0 0 400 300" role="img" aria-label={{{jsx(acc.get("alt") or "2D model")}}}>
      {{edges.map(([a,b],index) => (
        <line key={{index}}
          x1={{vertices[a][0] * 400}} y1={{vertices[a][1] * 300}}
          x2={{vertices[b][0] * 400}} y2={{vertices[b][1] * 300}}
          stroke="currentColor" strokeWidth={{2}} />
      ))}}
    </svg>
  );
}};
"""
    return compile_result(eid,"model2d",comp,source)
