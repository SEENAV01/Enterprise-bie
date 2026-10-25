// Signal blocks (Task 046a): signal_trace (an ECG on its paper, drawn by a moving pen, with P, QRS and T labels from
// NeuroKit2) and wave (two travelling waves and their sum, a standing wave with its nodes, computed with NumPy).
import React from "react";
import { line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, useRel } from "./common";

const SignalTrace: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const mv: number[] = data.mv, rate: number = data.sampling_rate;
  const pad = { l: 40, r: 40, t: 110, b: 50 };
  const sx = scaleLinear().domain([0, mv.length - 1]).range([pad.l, width - pad.r]);
  const lo = data.mv_min - 0.2, hi = data.mv_max + 0.3;
  const sy = scaleLinear().domain([lo, hi]).range([height - pad.b, pad.t]);
  const seconds = data.draw_seconds ?? mv.length / rate;
  const n = Math.max(2, Math.min(mv.length, Math.round((rel / (seconds * fps)) * mv.length)));
  const path = line<number>().x((_, i) => sx(i)).y((v) => sy(v))(mv.slice(0, n)) || "";
  const small = (width - pad.l - pad.r) / ((mv.length / rate) / 0.04);         // 1 mm = 0.04 s at 25 mm/s
  const grid = [];
  for (let x = pad.l, k = 0; x <= width - pad.r + 0.1; x += small, k++)
    grid.push(<line key={"gx" + k} x1={x} x2={x} y1={pad.t} y2={height - pad.b} stroke="#ff6b8a" strokeOpacity={k % 5 ? 0.12 : 0.32} />);
  for (let y = height - pad.b, k = 0; y >= pad.t - 0.1; y -= small, k++)
    grid.push(<line key={"gy" + k} x1={pad.l} x2={width - pad.r} y1={y} y2={y} stroke="#ff6b8a" strokeOpacity={k % 5 ? 0.12 : 0.32} />);
  const labels = data.labels || {};
  const marks: { i: number; t: string }[] = [];
  for (const [key, text] of [["P", "P"], ["R", "QRS"], ["T", "T"]] as [string, string][])
    for (const i of (labels[key] || []).slice(0, data.label_beats ?? 1)) marks.push({ i, t: text });
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <rect x={pad.l} y={pad.t} width={width - pad.l - pad.r} height={height - pad.t - pad.b} fill="#1a0d14" opacity={0.55} />
        {grid}
        <path d={path} fill="none" stroke="#7CFFB2" strokeWidth={4} strokeLinejoin="round" style={{ filter: "drop-shadow(0 0 6px #7CFFB2)" }} />
        <circle cx={sx(n - 1)} cy={sy(mv[n - 1])} r={9} fill="#eaffef" />
        {marks.filter((m) => m.i < n).map((m, k) => (
          <g key={k} opacity={ramp(n, m.i, 20)}>
            <text x={sx(m.i)} y={sy(mv[m.i]) - 26} fill={C.warm} fontSize={34} fontWeight={800} textAnchor="middle">{m.t}</text>
          </g>))}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.badge ? <Badge text={data.badge} style={{ position: "absolute", right: 50, top: 30 }} /> : null}
    </div>
  );
};

const Wave: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel } = useRel(at);
  const xs: number[] = data.x;
  const frames = data.sum.length;
  const f = rel % frames;
  const pad = { l: 60, r: 60, t: 120, b: 60 };
  const sx = scaleLinear().domain([xs[0], xs[xs.length - 1]]).range([pad.l, width - pad.r]);
  const A = data.amplitude * 2.2;
  const sy = scaleLinear().domain([-A, A]).range([height - pad.b, pad.t]);
  const make = (ys: number[]) => line<number>().x((_, i) => sx(xs[i])).y((v) => sy(v))(ys) || "";
  const parts = ramp(rel, 0, 20), total = ramp(rel, 40, 25);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <line x1={pad.l} x2={width - pad.r} y1={sy(0)} y2={sy(0)} stroke={C.line} strokeWidth={2} />
        <path d={make(data.right[f])} fill="none" stroke={C.accent} strokeWidth={3} strokeDasharray="10 8" opacity={0.85 * parts} />
        <path d={make(data.left[f])} fill="none" stroke={C.warm} strokeWidth={3} strokeDasharray="10 8" opacity={0.85 * parts} />
        <path d={make(data.sum[f])} fill="none" stroke={C.ink} strokeWidth={7} opacity={total} />
        {data.nodes.map((x: number, i: number) => <g key={i} opacity={total}>
          <circle cx={sx(x)} cy={sy(0)} r={11} fill={C.danger} />
          <text x={sx(x)} y={sy(0) + 46} fill={C.danger} fontSize={26} fontWeight={800} textAnchor="middle">N</text></g>)}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      <div style={{ position: "absolute", right: 50, top: 24, display: "flex", gap: 14, opacity: parts }}>
        <Badge text={data.right_label || "wave →"} /><Badge text={data.left_label || "← wave"} tone="warm" />
        <Badge text={data.sum_label || "sum = standing wave"} style={{ color: C.ink, borderColor: C.ink, opacity: total }} />
      </div>
    </div>
  );
};

registerBlock("signal_trace", SignalTrace);
registerBlock("wave", Wave);
