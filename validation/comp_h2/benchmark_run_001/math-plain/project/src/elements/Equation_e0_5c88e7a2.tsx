import React from "react";

type EquationNode = {tag: string; attrs: Record<string, unknown>; children: (EquationNode | string)[]};
const equationLayout = null;
const renderMathNode = (node: EquationNode | string, key: string): React.ReactNode => {
  if (typeof node === "string") return node;
  return React.createElement(node.tag, {...node.attrs, key}, ...node.children.map((child, i) => renderMathNode(child, key + "-" + i)));
};
export const Equation_e0_5c88e7a2: React.FC = () => {
  const expression = "x + 1 = 2";
  const sideConditions: string[] = [];
  return (
    <div role="math" aria-label={"Synthetic equation compiler fixture"} data-bie-element-id={"e0"} data-equation-format={"plain"} style={{width: "100%", height: "100%", display: "flex", flexDirection: "column", minWidth: 0}}>
      <div style={{flex: 1, minHeight: 0, width: "100%", display: "grid", placeItems: "center"}}>
        {expression}
      </div>
      {sideConditions.length > 0 ? <div aria-label="side conditions">{sideConditions.join(", ")}</div> : null}
    </div>
  );
};
