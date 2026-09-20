import React from "react";

type ChartGeometry = {
  kind: string; categories: string[]; values: number[]; units: string; x_label: string; y_label: string;
  width: number; height: number; left: number; right: number; top: number; bottom: number;
  domain: number[] | null; baseline: number | null;
  bars: Array<{index: number; label: string; value: number; x: number; y: number; width: number; height: number}>;
  points: Array<{index: number; label: string; value: number; x: number; y: number}>;
  slices: Array<{index: number; label: string; value: number; fraction: number; path: string}>;
  line_points: string; area_points: string; x_values?: number[]; x_domain?: number[];
};
const chart: ChartGeometry = {"area_points": "", "bars": [{"height": 284.0, "index": 0, "label": "C0", "value": 1.0, "width": 29.907692307692308, "x": 69.81538461538462, "y": 32.0}, {"height": 284.0, "index": 1, "label": "C1", "value": 1.0, "width": 29.907692307692308, "x": 111.35384615384615, "y": 32.0}, {"height": 284.0, "index": 2, "label": "C2", "value": 1.0, "width": 29.907692307692308, "x": 152.89230769230772, "y": 32.0}, {"height": 284.0, "index": 3, "label": "C3", "value": 1.0, "width": 29.907692307692308, "x": 194.43076923076924, "y": 32.0}, {"height": 284.0, "index": 4, "label": "C4", "value": 1.0, "width": 29.907692307692308, "x": 235.9692307692308, "y": 32.0}, {"height": 284.0, "index": 5, "label": "C5", "value": 1.0, "width": 29.907692307692308, "x": 277.5076923076923, "y": 32.0}, {"height": 284.0, "index": 6, "label": "C6", "value": 1.0, "width": 29.907692307692308, "x": 319.04615384615386, "y": 32.0}, {"height": 284.0, "index": 7, "label": "C7", "value": 1.0, "width": 29.907692307692308, "x": 360.5846153846154, "y": 32.0}, {"height": 284.0, "index": 8, "label": "C8", "value": 1.0, "width": 29.907692307692308, "x": 402.12307692307695, "y": 32.0}, {"height": 284.0, "index": 9, "label": "C9", "value": 1.0, "width": 29.907692307692308, "x": 443.6615384615385, "y": 32.0}, {"height": 284.0, "index": 10, "label": "C10", "value": 1.0, "width": 29.907692307692308, "x": 485.20000000000005, "y": 32.0}, {"height": 284.0, "index": 11, "label": "C11", "value": 1.0, "width": 29.907692307692308, "x": 526.7384615384616, "y": 32.0}, {"height": 284.0, "index": 12, "label": "C12", "value": 1.0, "width": 29.907692307692308, "x": 568.2769230769231, "y": 32.0}], "baseline": 316.0, "bottom": 316.0, "categories": ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12"], "domain": [0.0, 1.0], "height": 400, "kind": "bar", "left": 64.0, "line_points": "", "points": [{"index": 0, "label": "C0", "value": 1.0, "x": 84.76923076923077, "y": 32.0}, {"index": 1, "label": "C1", "value": 1.0, "x": 126.3076923076923, "y": 32.0}, {"index": 2, "label": "C2", "value": 1.0, "x": 167.84615384615387, "y": 32.0}, {"index": 3, "label": "C3", "value": 1.0, "x": 209.3846153846154, "y": 32.0}, {"index": 4, "label": "C4", "value": 1.0, "x": 250.92307692307693, "y": 32.0}, {"index": 5, "label": "C5", "value": 1.0, "x": 292.46153846153845, "y": 32.0}, {"index": 6, "label": "C6", "value": 1.0, "x": 334.0, "y": 32.0}, {"index": 7, "label": "C7", "value": 1.0, "x": 375.53846153846155, "y": 32.0}, {"index": 8, "label": "C8", "value": 1.0, "x": 417.0769230769231, "y": 32.0}, {"index": 9, "label": "C9", "value": 1.0, "x": 458.61538461538464, "y": 32.0}, {"index": 10, "label": "C10", "value": 1.0, "x": 500.1538461538462, "y": 32.0}, {"index": 11, "label": "C11", "value": 1.0, "x": 541.6923076923077, "y": 32.0}, {"index": 12, "label": "C12", "value": 1.0, "x": 583.2307692307693, "y": 32.0}], "right": 604.0, "slices": [], "top": 32.0, "units": "", "values": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], "width": 640, "x_label": "", "y_label": ""};
export const Chart_e0_5c88e7a2: React.FC = () => (
  <figure style={{margin: 0, width: "100%", height: "100%", display: "grid", gridTemplateRows: "minmax(0, 1fr) auto"}}>
    <svg viewBox="0 0 640 400" width="100%" height="100%" role="img"
      aria-label={"Synthetic technical fixture h1-chart-dense"} data-chart-kind={"bar"}>
      <title>{chart.categories.map((label, index) => label + ": " + chart.values[index]).join("; ")}</title>
      {chart.kind !== "pie" ? <g data-bie-axis="signed-domain">
        <line x1={chart.left} x2={chart.right} y1={chart.baseline ?? 0} y2={chart.baseline ?? 0} stroke="currentColor" />
        <line x1={chart.left} x2={chart.left} y1={chart.top} y2={chart.bottom} stroke="currentColor" />
        <text x={2} y={chart.top + 12} fontSize={12}>{chart.domain?.[1]}</text>
        <text x={2} y={chart.bottom} fontSize={12}>{chart.domain?.[0]}</text>
        <text x={32} y={chart.baseline ?? 0} fontSize={12}>0</text>
      </g> : null}
      {chart.bars.map((bar) => <rect key={bar.index} data-value={bar.value}
        x={bar.x} y={bar.y} width={bar.width} height={bar.height} fill="currentColor"><title>{bar.label + ": " + bar.value}</title></rect>)}
      {chart.kind === "area" ? <polygon points={chart.area_points} fill="currentColor" fillOpacity={0.18} /> : null}
      {chart.kind === "line" || chart.kind === "area" ? <polyline points={chart.line_points} fill="none" stroke="currentColor" strokeWidth={2} /> : null}
      {chart.kind !== "bar" ? chart.points.map((point) => <circle key={point.index} cx={point.x} cy={point.y} r={4} fill="currentColor"><title>{point.label + ": " + point.value}</title></circle>) : null}
      {chart.slices.map((slice) => <path key={slice.index} d={slice.path} fill="currentColor" fillOpacity={0.25 + 0.65 * (slice.index + 1) / chart.categories.length} stroke="currentColor"><title>{slice.label + ": " + slice.value}</title></path>)}
      {chart.kind !== "pie" ? chart.points.map((point) => <text key={point.index} x={point.x} y={340} textAnchor="middle" fontSize={12}>{point.label}</text>) : null}
      {chart.kind === "scatter" ? <text x={320} y={357} textAnchor="middle" fontSize={11}>{"Numeric x-domain: " + chart.x_domain?.join(" to ")}</text> : null}
      <text x={320} y={375} textAnchor="middle" fontSize={14}>{chart.x_label + (chart.units ? " | units: " + chart.units : "")}</text>
    </svg>
    <figcaption style={{fontSize: 12, overflowWrap: "anywhere"}}>{chart.y_label}{chart.categories.map((label, i) => " | " + label + ": " + chart.values[i]).join("")}</figcaption>
  </figure>
);
