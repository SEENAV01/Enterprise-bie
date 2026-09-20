from .element_compiler_common import *
from .hardening_contracts import literal_child, literal_js_string, text_value
def compile_annotation_callout_element(element):
    eid,etype,props,acc,src,rsn=normalize_element(element)
    if etype not in {"annotation","callout"}:
        raise ElementCompilerError("expected annotation or callout")
    target=props.get("target_element_id")
    if not isinstance(target,str) or not target:
        raise ElementCompilerError("target_element_id required")
    text=props.get("text") if etype=="annotation" else props.get("content")
    if not isinstance(text,str) or not text:
        raise ElementCompilerError("annotation/callout content required")
    text_value(text, "annotation/callout content")
    comp=component_name("Annotation" if etype=="annotation" else "Callout",eid)
    source=f"""import React from "react";
import {{Interactive}} from "remotion";

export const {comp}: React.FC = () => {{
  return (
    <Interactive.Div
      name={{{jsx(eid)}}}
      data-target-element-id={{{jsx(target)}}}
      role="note"
      aria-label={{{literal_js_string(acc.get("alt") or text)}}}
      style={{{{padding: 12, border: "1px solid currentColor", borderRadius: 8, whiteSpace: "pre-wrap", overflowWrap: "anywhere"}}}}
    >
      {literal_child(text)}
    </Interactive.Div>
  );
}};
"""
    return compile_result(eid,etype,comp,source)
