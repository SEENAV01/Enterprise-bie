from .element_compiler_common import *
def compile_particle_element(element):
    eid,props,acc,src,rsn=require_type(element,"particle_system")
    count=props.get("particle_count")
    if isinstance(count,bool) or not isinstance(count,int) or count<1 or count>2000:
        raise ElementCompilerError("particle_count must be 1..2000")
    physical=bool(props.get("physical_claim",False))
    if physical and not props.get("receipt_ref"):
        raise ElementCompilerError("physical particle claim requires receipt_ref")
    comp=component_name("Particles",eid)
    source=f"""import React from "react";

const count = {count};

export const {comp}: React.FC = () => {{
  return (
    <div role="img" aria-label={{{jsx(acc.get("alt") or "particle system")}}}
      style={{{{position: "relative", width: "100%", height: "100%"}}}}>
      {{Array.from({{length: count}}, (_, index) => {{
        const x = (index * 37) % 100;
        const y = (index * 61) % 100;
        return <div key={{index}} style={{{{
          position: "absolute",
          left: `${{x}}%`,
          top: `${{y}}%`,
          width: 6,
          height: 6,
          borderRadius: 999,
          background: "currentColor",
        }}}} />;
      }})}}
    </div>
  );
}};
"""
    return compile_result(eid,"particle_system",comp,source)
