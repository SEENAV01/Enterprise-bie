import React from "react";

type EquationNode = {tag: string; attrs: Record<string, unknown>; children: (EquationNode | string)[]};
const equationLayout = {"accepted": false, "input_sha256": "17ea38a225537f3e72d2e54c8d5b280646fb68e7cbb96c8443ee10792f7dfbb1", "renderer": "native-mathml-core.v1", "tree": {"attrs": {"display": "block"}, "children": [{"attrs": {}, "children": [{"attrs": {}, "children": [{"attrs": {}, "children": ["x"], "tag": "mi"}, {"attrs": {}, "children": ["2"], "tag": "mn"}], "tag": "msup"}, {"attrs": {}, "children": [{"attrs": {}, "children": ["y"], "tag": "mi"}], "tag": "msqrt"}], "tag": "mfrac"}], "tag": "math"}};
const renderMathNode = (node: EquationNode | string, key: string): React.ReactNode => {
  if (typeof node === "string") return node;
  return React.createElement(node.tag, {...node.attrs, key}, ...node.children.map((child, i) => renderMathNode(child, key + "-" + i)));
};
export const Equation_e0_5c88e7a2: React.FC = () => {
  const expression = "\u003cmath>\u003cmfrac>\u003cmsup>\u003cmi>x\u003c\u002fmi>\u003cmn>2\u003c\u002fmn>\u003c\u002fmsup>\u003cmsqrt>\u003cmi>y\u003c\u002fmi>\u003c\u002fmsqrt>\u003c\u002fmfrac>\u003c\u002fmath>";
  const sideConditions: string[] = [];
  return (
    <div role="math" aria-label={"Synthetic vector compiler fixture"} data-bie-element-id={"e0"} data-equation-format={"mathml"} style={{width: "100%", height: "100%", display: "flex", flexDirection: "column", minWidth: 0}}>
      <div style={{flex: 1, minHeight: 0, width: "100%", display: "grid", placeItems: "center"}}>
        {renderMathNode(equationLayout.tree as EquationNode, "equation")}
      </div>
      {sideConditions.length > 0 ? <div aria-label="side conditions">{sideConditions.join(", ")}</div> : null}
    </div>
  );
};
