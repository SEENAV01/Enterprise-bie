from .element_compiler_common import *
def compile_map_element(element):
    eid,props,acc,src,rsn=require_type(element,"map")
    layers=props.get("layers")
    if not isinstance(layers,(list,tuple)) or not layers:
        raise ElementCompilerError("map layers required")
    routes=[]
    for layer in layers:
        if layer.get("kind")=="route":
            pts=layer.get("points",())
            routes.append([(float(p[0]),float(p[1])) for p in pts])
    comp=component_name("Map",eid)
    source=f"""import React from "react";

const routes = {jsx(routes)} as const;

export const {comp}: React.FC = () => {{
  return (
    <svg viewBox="0 0 1000 600" role="img" aria-label={{{jsx(acc.get("alt") or "map")}}} data-crs={{{jsx(props.get("crs","unknown"))}}}>
      <rect x={{0}} y={{0}} width={{1000}} height={{600}} fill="transparent" />
      {{routes.map((points,index) => {{
        const d = points.map(([x,y],i) => `${{i === 0 ? "M" : "L"}} ${{x * 1000}} ${{(1-y) * 600}}`).join(" ");
        return <path key={{index}} d={{d}} fill="none" stroke="currentColor" strokeWidth={{4}} />;
      }})}}
    </svg>
  );
}};
"""
    warnings=() if routes else ("map_has_no_route_geometry; external/static-map provider may be required",)
    return compile_result(eid,"map",comp,source,warnings=warnings)
