import React from "react";
import {Interactive} from "remotion";

export const Equation_e0_5c88e7a2: React.FC = () => {
  const expression = "\\frac{1}{2}";
  const sideConditions = [];
  return (
    <Interactive.Div name={"e0"} role="math" aria-label={"Synthetic equation compiler fixture"}>
      <div data-equation-format={"latex"}>{expression}</div>
      {sideConditions.length > 0 ? (
        <div aria-label="side conditions">{sideConditions.join(", ")}</div>
      ) : null}
    </Interactive.Div>
  );
};
