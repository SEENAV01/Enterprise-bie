"""Equation element backed by real bounded typesetting; no raw equation fallback."""
from .element_compiler_common import *
from .equation_typesetting import typeset_latex, mathml_tree
from .hardening_contracts import known_properties, text_value, literal_js_string, sequence, reject


def compile_equation_element(element, *, typesetter=None):
    eid, props, acc, src, rsn = require_type(element, "equation")
    known_properties(props, {"expression", "format", "side_conditions", "renderer", "font_size"})
    expr = text_value(props.get("expression"), "equation expression", maximum=12000)
    fmt = props.get("format", "latex")
    expected_renderer = {"latex": "mathtext-svg", "mathml": "native-mathml", "plain": "plain-text"}
    if not isinstance(fmt,str) or fmt not in expected_renderer:
        reject("EQUATION_FORMAT_UNSUPPORTED", "supported: latex mathtext subset, safe MathML, plain")
    if props.get("renderer", expected_renderer[fmt]) != expected_renderer[fmt]:
        reject("EQUATION_RENDERER_UNSUPPORTED", "no silent typesetter substitution")
    if fmt != "latex" and "font_size" in props:
        reject("UNCONSUMED_ELEMENT_PROPERTY", "font_size is currently a LaTeX layout input only")
    side = sequence(props.get("side_conditions", []), "side_conditions", minimum=0, maximum=32)
    side = [text_value(v, "side condition", maximum=1000) for v in side]
    label = text_value(acc.get("alt") or expr, "equation alternative", maximum=12000)
    comp = component_name("Equation", eid)
    layout = (typesetter or typeset_latex)(expr, element_id=eid, font_size=props.get("font_size", 32)) if fmt == "latex" else (mathml_tree(expr) if fmt == "mathml" else None)
    layout_source = jsx(layout) if layout else "null"
    source = f'''import React from "react";

type EquationNode = {{tag: string; attrs: Record<string, unknown>; children: (EquationNode | string)[]}};
const equationLayout = {layout_source};
const renderMathNode = (node: EquationNode | string, key: string): React.ReactNode => {{
  if (typeof node === "string") return node;
  return React.createElement(node.tag, {{...node.attrs, key}}, ...node.children.map((child, i) => renderMathNode(child, key + "-" + i)));
}};
export const {comp}: React.FC = () => {{
  const expression = {literal_js_string(expr)};
  const sideConditions: string[] = {jsx(side)};
  return (
    <div role="math" aria-label={{{literal_js_string(label)}}} data-bie-element-id={{{jsx(eid)}}} data-equation-format={{{jsx(fmt)}}} style={{{{width: "100%", height: "100%", display: "flex", flexDirection: "column", minWidth: 0}}}}>
      <div style={{{{flex: 1, minHeight: 0, width: "100%", display: "grid", placeItems: "center"}}}}>
        {('{renderMathNode(equationLayout.tree as EquationNode, "equation")}' if layout else '{expression}')}
      </div>
      {{sideConditions.length > 0 ? <div aria-label="side conditions">{{sideConditions.join(", ")}}</div> : null}}
    </div>
  );
}};
'''
    return compile_result(eid, "equation", comp, source)
