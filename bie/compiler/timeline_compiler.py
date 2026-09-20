from .element_compiler_common import *
def compile_timeline_element(element):
    eid,props,acc,src,rsn=require_type(element,"timeline")
    events=props.get("events")
    if not isinstance(events,(list,tuple)) or len(events)<2:
        raise ElementCompilerError("timeline requires >=2 events")
    comp=component_name("Timeline",eid)
    normalized=[{"event_id":str(x.get("event_id","")),"label":str(x.get("label") or x.get("event_id",""))} for x in events]
    source=f"""import React from "react";

const events = {jsx(normalized)};

export const {comp}: React.FC = () => {{
  return (
    <div role="img" aria-label={{{jsx(acc.get("alt") or "timeline")}}}
      style={{{{display: "flex", alignItems: "center", gap: 16}}}}>
      {{events.map((event,index) => (
        <React.Fragment key={{event.event_id}}>
          <div style={{{{display: "grid", justifyItems: "center", gap: 6}}}}>
            <div style={{{{width: 12, height: 12, borderRadius: 999, background: "currentColor"}}}} />
            <span>{{event.label}}</span>
          </div>
          {{index < events.length - 1 ? <div style={{{{height: 2, flex: 1, background: "currentColor"}}}} /> : null}}
        </React.Fragment>
      ))}}
    </div>
  );
}};
"""
    return compile_result(eid,"timeline",comp,source)
