import React from "react";

const series = [[[0.0, 0.1], [0.5, 0.3], [1.0, 0.8]]] as const;

export const Graph_e0_5c88e7a2: React.FC = () => {
  return (
    <svg viewBox="0 0 400 240" role="img" aria-label={"Synthetic graph compiler fixture"}>
      <line x1={40} y1={200} x2={380} y2={200} stroke="currentColor" />
      <line x1={40} y1={20} x2={40} y2={200} stroke="currentColor" />
      {series.map((points, index) => {
        const d = points.map(([x,y],i) => `${i === 0 ? "M" : "L"} ${40 + x * 300} ${200 - y * 150}`).join(" ");
        return <path key={index} d={d} fill="none" stroke="currentColor" strokeWidth={2} />;
      })}
    </svg>
  );
};
