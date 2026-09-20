import React from "react";

const labels = ["A", "B"];
const values = [-2.0, 3.0];
const maxValue = Math.max(1, ...values.map((value) => Math.abs(value)));

export const Chart_e0_5c88e7a2: React.FC = () => {
  return (
    <div role="img" aria-label={"Synthetic chart compiler fixture"} data-chart-kind={"bar"}
      style={{display: "flex", alignItems: "end", gap: 12, height: 240}}>
      {values.map((value, index) => (
        <div key={labels[index]} style={{display: "grid", gap: 4, justifyItems: "center"}}>
          <div style={{width: 28, height: `${Math.abs(value) / maxValue * 180}px`, background: "currentColor"}} />
          <span>{labels[index]}</span>
        </div>
      ))}
    </div>
  );
};
