// xy_lines (Task 046a, batch 2): several series on one pair of axes, each drawn over its own time window, with labelled
// points and an optional LaTeX note. The Chart component is shared by other blocks (a circuit's trace, a T–s chart).
import React from "react";
import katex from "katex";
import { line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, ticks, useRel } from "./common";

export type Series = { x: number[]; y: (number | null)[]; label?: string; colour?: string; dash?: string; width?: number;
  start?: number; seconds?: number; fill?: boolean };
export type Point = { x: number; y: number; label?: string; at?: number; colour?: string };

const PALETTE = [C.accent, C.warm, "#c79bff", "#7CFFB2", C.danger, "#6fb7ff"];

/** The part of a series drawn after ``reach`` of it (0..1), cut at a fractional sample so short series grow smoothly. */
export function grown(xs: number[], ys: (number | null)[], reach: number): [number, number | null][] {
  const f = (xs.length - 1) * Math.max(0, Math.min(1, reach));
  const whole = Math.floor(f), part = f - whole;
  const out: [number, number | null][] = xs.slice(0, whole + 1).map((x, i) => [x, ys[i]]);
  if (part > 0 && whole + 1 < xs.length && ys[whole] !== null && ys[whole + 1] !== null)
    out.push([xs[whole] + (xs[whole + 1] - xs[whole]) * part, (ys[whole] as number) + ((ys[whole + 1] as number) - (ys[whole] as number)) * part]);
  return out;
}

export const Chart: React.FC<{ series: Series[]; points?: Point[]; rel: number; fps: number; left: number; top: number; width: number;
  height: number; xLabel?: string; yLabel?: string; xDomain?: [number, number]; yDomain?: [number, number]; legend?: boolean;
  fontSize?: number }> = ({ series, points = [], rel, fps, left, top, width, height, xLabel, yLabel, xDomain, yDomain, legend = true, fontSize = 24 }) => {
  const pad = { l: 92, r: 24, t: 16, b: 70 };
  const xsAll = series.flatMap((s) => s.x);
  const ysAll = series.flatMap((s) => s.y.filter((v) => v !== null) as number[]).concat(points.map((p) => p.y));
  const xd = xDomain || [Math.min(...xsAll), Math.max(...xsAll)];
  const yd = yDomain || [Math.min(...ysAll), Math.max(...ysAll)];
  const sx = scaleLinear().domain(xd).range([left + pad.l, left + width - pad.r]);
  const sy = scaleLinear().domain(yd).nice().range([top + height - pad.b, top + pad.t]);
  const [y0, y1] = sy.domain();
  const mk = line<[number, number | null]>().defined((p) => p[1] !== null).x((p) => sx(p[0])).y((p) => sy(p[1] as number));
  const placed: [number, number][] = [];                       // end labels already placed: a label that would sit on one moves down
  const labelY = (x: number, y: number) => {
    let out = y;
    while (placed.some(([px, py]) => Math.abs(px - x) < 140 && Math.abs(py - out) < fontSize + 4)) out += fontSize + 6;
    placed.push([x, out]);
    return out;
  };
  return (
    <g fontFamily={FONT}>
      {ticks(xd[0], xd[1], 6).map((v) => <g key={"x" + v}>
        <line x1={sx(v)} x2={sx(v)} y1={top + pad.t} y2={top + height - pad.b} stroke={C.line} />
        <text x={sx(v)} y={top + height - pad.b + 32} fill={C.muted} fontSize={fontSize} textAnchor="middle">{+v.toFixed(3)}</text></g>)}
      {ticks(y0, y1, 5).map((v) => <g key={"y" + v}>
        <line x1={left + pad.l} x2={left + width - pad.r} y1={sy(v)} y2={sy(v)} stroke={C.line} />
        <text x={left + pad.l - 12} y={sy(v) + 8} fill={C.muted} fontSize={fontSize} textAnchor="end">{+v.toFixed(3)}</text></g>)}
      {xLabel ? <text x={left + width - pad.r} y={top + height - 10} fill={C.ink} fontSize={fontSize} textAnchor="end">{xLabel}</text> : null}
      {yLabel ? <text x={left + pad.l} y={top + pad.t - 2} fill={C.ink} fontSize={fontSize} dy={-8}>{yLabel}</text> : null}
      {series.map((s, i) => {
        const colour = s.colour || PALETTE[i % PALETTE.length];
        const reach = ramp(rel, (s.start ?? 0.2) * fps, (s.seconds ?? 2.5) * fps, (t: number) => t);
        if (reach <= 0) return null;                            // a series not started yet draws nothing, not even a dot
        const pts = grown(s.x, s.y, reach);
        const tip = pts[pts.length - 1];
        return (
          <g key={i}>
            {s.fill && pts.length > 1 ? <path d={(mk(pts) || "") + `L${sx(tip[0])},${sy(Math.max(y0, 0))}L${sx(pts[0][0])},${sy(Math.max(y0, 0))}Z`}
              fill={colour} opacity={0.16} /> : null}
            <path d={mk(pts) || ""} fill="none" stroke={colour} strokeWidth={s.width ?? 5} strokeDasharray={s.dash} strokeLinejoin="round" strokeLinecap="round" />
            {reach > 0 && reach < 1 && tip[1] !== null ? <circle cx={sx(tip[0])} cy={sy(tip[1] as number)} r={9} fill={C.ink} stroke={colour} strokeWidth={4} /> : null}
            {legend && s.label && reach >= 1 && tip[1] !== null ?
              <text x={Math.min(sx(tip[0]) + 12, left + width - 8)} y={labelY(sx(tip[0]), sy(tip[1] as number) - 10)} fill={colour} fontSize={fontSize}
                fontWeight={700} textAnchor={sx(tip[0]) + 160 > left + width ? "end" : "start"}>{s.label}</text> : null}
          </g>
        );
      })}
      {points.map((p, i) => {
        const o = ramp(rel, (p.at ?? 0) * fps, 10);
        return <g key={"p" + i} opacity={o}>
          <circle cx={sx(p.x)} cy={sy(p.y)} r={11} fill={p.colour || C.warm} stroke={C.bg0} strokeWidth={3} />
          {p.label ? <text x={sx(p.x) + 16} y={sy(p.y) - 14} fill={C.ink} fontSize={fontSize + 4} fontWeight={800}>{p.label}</text> : null}
        </g>;
      })}
    </g>
  );
};

export const tex = (latex: string) => katex.renderToString(latex, { displayMode: false, throwOnError: true, output: "html" });

const XYLines: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const end = Math.max(...(data.series as Series[]).map((s) => (s.start ?? 0.2) + (s.seconds ?? 2.5)));
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <Chart series={data.series} points={data.points} rel={rel} fps={fps} left={20} top={130} width={width - 40} height={height - 150}
          xLabel={data.x_label} yLabel={data.y_label} xDomain={data.x_domain} yDomain={data.y_domain} legend={!data.legend_box} />
      </svg>
      {data.legend_box ? <div style={{ position: "absolute", right: 60, bottom: 110, background: C.panel, borderRadius: 12, padding: "8px 18px",
        display: "flex", flexDirection: "column", gap: 6 }}>
        {(data.series as Series[]).filter((s) => s.label).map((s, i) => <div key={i} style={{ display: "flex", alignItems: "center", gap: 10,
          fontSize: 26, color: C.ink, opacity: ramp(rel, (s.start ?? 0.2) * fps, 10) }}>
          <span style={{ width: 30, height: 6, borderRadius: 3, background: s.colour || PALETTE[(data.series as Series[]).indexOf(s) % PALETTE.length] }} />
          {s.label}</div>)}
      </div> : null}
      <Title text={data.title} sub={data.subtitle} />
      {data.latex ? <div style={{ position: "absolute", right: 50, top: 28, fontSize: 40, color: C.ink, background: C.panel, padding: "6px 18px",
        borderRadius: 14, opacity: ramp(rel, 0, 15) }} dangerouslySetInnerHTML={{ __html: tex(data.latex) }} /> : null}
      {data.note ? <Badge text={data.note} style={{ position: "absolute", right: 50, top: data.latex ? 150 : 36, opacity: ramp(rel, end * fps, 12) }} /> : null}
    </div>
  );
};

registerBlock("xy_lines", XYLines);
