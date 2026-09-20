from .element_compiler_common import *
def compile_chart_element(element):
    eid,props,acc,src,rsn=require_type(element,"chart")
    kind=props.get("chart_kind")
    cats=props.get("categories");vals=props.get("values")
    if kind not in {"bar","line","scatter","area","pie"}:
        raise ElementCompilerError("unsupported chart_kind")
    if not isinstance(cats,(list,tuple)) or not isinstance(vals,(list,tuple)) or len(cats)!=len(vals) or not cats:
        raise ElementCompilerError("chart categories/values mismatch")
    vals=[float(v) for v in vals]
    comp=component_name("Chart",eid)
    if kind!="bar":
        warnings=("generic_chart_renderer_uses_bar_fallback_for_non_bar_kind",)
    else:warnings=()
    source=f"""import React from "react";

const labels = {jsx(list(cats))};
const values = {jsx(vals)};
const maxValue = Math.max(1, ...values.map((value) => Math.abs(value)));

export const {comp}: React.FC = () => {{
  return (
    <div role="img" aria-label={{{jsx(acc.get("alt") or "chart")}}} data-chart-kind={{{jsx(kind)}}}
      style={{{{display: "flex", alignItems: "end", gap: 12, height: 240}}}}>
      {{values.map((value, index) => (
        <div key={{labels[index]}} style={{{{display: "grid", gap: 4, justifyItems: "center"}}}}>
          <div style={{{{width: 28, height: `${{Math.abs(value) / maxValue * 180}}px`, background: "currentColor"}}}} />
          <span>{{labels[index]}}</span>
        </div>
      ))}}
    </div>
  );
}};
"""
    return compile_result(eid,"chart",comp,source,warnings=warnings)
