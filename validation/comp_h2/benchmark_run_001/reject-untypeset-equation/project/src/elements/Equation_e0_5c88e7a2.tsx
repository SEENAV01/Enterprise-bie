import React from "react";

type EquationNode = {tag: string; attrs: Record<string, unknown>; children: (EquationNode | string)[]};
const equationLayout = {"accepted": false, "dialect": "matplotlib-mathtext-subset-not-full-latex", "font_hashes": {"DejaVuSans.ttf": "3fdf69cabf06049ea70a00b5919340e2ce1e6d02b0cc3c4b44fb6801bd1e0d22"}, "freetype_version": "2.6.1", "input_sha256": "e7e9536310cdba7ff948771f791cefe32f99b73c608778c9660db79e4926e9f9", "matplotlib_version": "3.10.8", "renderer": "bie.mathtext-svg.v1", "tree": {"attrs": {"height": "100%", "preserveAspectRatio": "xMidYMid meet", "strokeLinecap": "butt", "strokeLinejoin": "round", "version": "1.1", "viewBox": "-1.76 -1.76 22.52 47.52", "width": "100%"}, "children": [{"attrs": {}, "children": [], "tag": "defs"}, {"attrs": {"id": "eq1df0639672b60c2bf40b_figure_1"}, "children": [{"attrs": {"id": "eq1df0639672b60c2bf40b_patch_1"}, "children": [{"attrs": {"d": "M 0 44  L 19 44  L 19 0  L 0 0  L 0 44  z ", "style": {"fill": "none"}}, "children": [], "tag": "path"}], "tag": "g"}, {"attrs": {"id": "eq1df0639672b60c2bf40b_text_1"}, "children": [{"attrs": {"transform": "translate(0 31) scale(0.32 -0.32)"}, "children": [{"attrs": {}, "children": [{"attrs": {"d": "M 794 531  L 1825 531  L 1825 4091  L 703 3866  L 703 4441  L 1819 4666  L 2450 4666  L 2450 531  L 3481 531  L 3481 0  L 794 0  L 794 531  z ", "id": "eq1df0639672b60c2bf40b_DejaVuSans-31", "transform": "scale(0.015625)"}, "children": [], "tag": "path"}, {"attrs": {"d": "M 1228 531  L 3431 531  L 3431 0  L 469 0  L 469 531  Q 828 903 1448 1529  Q 2069 2156 2228 2338  Q 2531 2678 2651 2914  Q 2772 3150 2772 3378  Q 2772 3750 2511 3984  Q 2250 4219 1831 4219  Q 1534 4219 1204 4116  Q 875 4013 500 3803  L 500 4441  Q 881 4594 1212 4672  Q 1544 4750 1819 4750  Q 2544 4750 2975 4387  Q 3406 4025 3406 3419  Q 3406 3131 3298 2873  Q 3191 2616 2906 2266  Q 2828 2175 2409 1742  Q 1991 1309 1228 531  z ", "id": "eq1df0639672b60c2bf40b_DejaVuSans-32", "transform": "scale(0.015625)"}, "children": [], "tag": "path"}], "tag": "defs"}, {"attrs": {"href": "#eq1df0639672b60c2bf40b_DejaVuSans-31", "transform": "translate(0 43.965625) scale(0.7)"}, "children": [], "tag": "use"}, {"attrs": {"href": "#eq1df0639672b60c2bf40b_DejaVuSans-32", "transform": "translate(0 -39.2375) scale(0.7)"}, "children": [], "tag": "use"}, {"attrs": {"d": "M 0 18.965625  L 0 25.215625  L 44.536133 25.215625  L 44.536133 18.965625  L 0 18.965625  z "}, "children": [], "tag": "path"}], "tag": "g"}], "tag": "g"}], "tag": "g"}], "tag": "svg"}, "view_box": [-1.76, -1.76, 22.52, 47.52]};
const renderMathNode = (node: EquationNode | string, key: string): React.ReactNode => {
  if (typeof node === "string") return node;
  return React.createElement(node.tag, {...node.attrs, key}, ...node.children.map((child, i) => renderMathNode(child, key + "-" + i)));
};
export const Equation_e0_5c88e7a2: React.FC = () => {
  const expression = "\\frac{1}{2}";
  const sideConditions: string[] = [];
  return (
    <div role="math" aria-label={"Synthetic equation compiler fixture"} data-bie-element-id={"e0"} data-equation-format={"latex"} style={{width: "100%", height: "100%", display: "flex", flexDirection: "column", minWidth: 0}}>
      <div style={{flex: 1, minHeight: 0, width: "100%", display: "grid", placeItems: "center"}}>
        {renderMathNode(equationLayout.tree as EquationNode, "equation")}
      </div>
      {sideConditions.length > 0 ? <div aria-label="side conditions">{sideConditions.join(", ")}</div> : null}
    </div>
  );
};
