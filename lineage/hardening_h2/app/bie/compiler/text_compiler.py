from .element_compiler_common import *
from .hardening_contracts import literal_child, literal_js_string, text_value
def compile_text_element(element):
    eid,props,acc,src,rsn=require_type(element,"text")
    text=props.get("text")
    if not isinstance(text,str) or not text:
        raise ElementCompilerError("text prop required")
    text_value(text, "text")
    role=props.get("role","body")
    comp=component_name("Text",eid)
    source=f"""import React from "react";
import {{Interactive}} from "remotion";

export const {comp}: React.FC = () => {{
  return (
    <Interactive.Div
      name={{{jsx(eid)}}}
      role="text"
      aria-label={{{literal_js_string(acc.get("alt") or text)}}}
      data-role={{{jsx(role)}}}
      style={{{{whiteSpace: "pre-wrap", overflowWrap: "anywhere"}}}}
    >
      {literal_child(text)}
    </Interactive.Div>
  );
}};
"""
    return compile_result(eid,"text",comp,source)
