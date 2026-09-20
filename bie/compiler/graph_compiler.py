from .element_compiler_common import *
def compile_graph_element(element):
    eid,props,acc,src,rsn=require_type(element,"graph")
    series=props.get("series")
    if not isinstance(series,(list,tuple)) or not series:
        raise ElementCompilerError("graph series required")
    paths=[]
    for s in series:
        pts=s.get("points",())
        if len(pts)<2:raise ElementCompilerError("graph series needs >=2 points")
        nums=[(float(p[0]),float(p[1])) for p in pts]
        paths.append(nums)
    comp=component_name("Graph",eid)
    source=f"""import React from "react";

const series = {jsx(paths)} as const;

export const {comp}: React.FC = () => {{
  return (
    <svg viewBox="0 0 400 240" role="img" aria-label={{{jsx(acc.get("alt") or "graph")}}}>
      <line x1={{40}} y1={{200}} x2={{380}} y2={{200}} stroke="currentColor" />
      <line x1={{40}} y1={{20}} x2={{40}} y2={{200}} stroke="currentColor" />
      {{series.map((points, index) => {{
        const d = points.map(([x,y],i) => `${{i === 0 ? "M" : "L"}} ${{40 + x * 300}} ${{200 - y * 150}}`).join(" ");
        return <path key={{index}} d={{d}} fill="none" stroke="currentColor" strokeWidth={{2}} />;
      }})}}
    </svg>
  );
}};
"""
    return compile_result(eid,"graph",comp,source)
