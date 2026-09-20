import React from "react";

const vertices = [[0.2, 0.2], [0.8, 0.2], [0.5, 0.8]] as const;
const edges = [[0, 1], [1, 2], [2, 0]] as const;

export const Model2D_e0_5c88e7a2: React.FC = () => {
  return (
    <svg viewBox="0 0 400 300" role="img" aria-label={"Synthetic model2d compiler fixture"}>
      {edges.map(([a,b],index) => (
        <line key={index}
          x1={vertices[a][0] * 400} y1={vertices[a][1] * 300}
          x2={vertices[b][0] * 400} y2={vertices[b][1] * 300}
          stroke="currentColor" strokeWidth={2} />
      ))}
    </svg>
  );
};
