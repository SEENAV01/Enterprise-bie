import React from "react";

const routes = [[[0.1, 0.2], [0.5, 0.6], [0.9, 0.8]]] as const;

export const Map_e0_5c88e7a2: React.FC = () => {
  return (
    <svg viewBox="0 0 1000 600" role="img" aria-label={"Synthetic map compiler fixture"} data-crs={"BIE:NORMALIZED"}>
      <rect x={0} y={0} width={1000} height={600} fill="transparent" />
      {routes.map((points,index) => {
        const d = points.map(([x,y],i) => `${i === 0 ? "M" : "L"} ${x * 1000} ${(1-y) * 600}`).join(" ");
        return <path key={index} d={d} fill="none" stroke="currentColor" strokeWidth={4} />;
      })}
    </svg>
  );
};
