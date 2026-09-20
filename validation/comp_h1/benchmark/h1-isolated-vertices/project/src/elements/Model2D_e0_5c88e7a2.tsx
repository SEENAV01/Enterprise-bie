import React from "react";
const vertices: ReadonlyArray<readonly [number, number]> = [[0.0, 0.0], [1.0, 1.0]];
const edges: ReadonlyArray<readonly [number, number]> = [];
export const Model2D_e0_5c88e7a2: React.FC = () => (
  <svg viewBox="0 0 400 300" width="100%" height="100%" role="img" aria-label={"Synthetic technical fixture h1-isolated-vertices"}>
    {edges.map(([a,b], index) => <line key={index} x1={8 + vertices[a][0] * 384} y1={8 + vertices[a][1] * 284} x2={8 + vertices[b][0] * 384} y2={8 + vertices[b][1] * 284} stroke="currentColor" strokeWidth={2} />)}
    {vertices.map(([x,y], index) => <circle key={index} cx={8 + x * 384} cy={8 + y * 284} r={3} fill="currentColor"><title>{"vertex " + index}</title></circle>)}
  </svg>
);
