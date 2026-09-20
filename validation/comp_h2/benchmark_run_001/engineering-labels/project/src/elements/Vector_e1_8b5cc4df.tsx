import React from "react";
const vector = {"components": [2.0, 1.0], "dimensions": 2, "endpoint": [300.0, 95.0], "is_zero": false, "label": "", "origin": [200, 145], "projected": [2.0, 1.0], "projection_label": "2D Cartesian (x right, y up)", "projection_matrix": null, "scale_px_per_unit": 50.0, "units": ""};
export const Vector_e1_8b5cc4df: React.FC = () => (
  <svg viewBox="0 0 400 320" width="100%" height="100%" role="img" aria-label={"Synthetic vector compiler fixture"}>
    <title>{"components: " + vector.components.join(", ") + " " + vector.units + "; " + vector.projection_label}</title>
    <defs><marker id="arrow-Vector_e1_8b5cc4df" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="currentColor" /></marker></defs>
    <line x1={70} y1={145} x2={330} y2={145} stroke="currentColor" strokeOpacity={0.3} />
    <line x1={200} y1={35} x2={200} y2={255} stroke="currentColor" strokeOpacity={0.3} />
    {vector.is_zero ? <circle cx={200} cy={145} r={4} fill="currentColor" /> : <line x1={200} y1={145} x2={vector.endpoint[0]} y2={vector.endpoint[1]} stroke="currentColor" strokeWidth={3} markerEnd="url(#arrow-Vector_e1_8b5cc4df)" />}
    <text x={8} y={274} fontSize={12}>{vector.label + " (" + vector.components.join(", ") + ") " + vector.units}</text>
    <text x={8} y={291} fontSize={11}>{vector.projection_label}</text>
    <text x={8} y={309} fontSize={10}>{"View scale: " + vector.scale_px_per_unit + " px/unit (individual vector)"}</text>
  </svg>
);
