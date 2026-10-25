// Maths blocks (Task 046a): equation_steps (KaTeX; every step proved by SymPy before it may be shown) and
// function_graph (D3 scales; the curve is drawn over time, with optional data points and a fitted line).
import React from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { line, scaleLinear } from "d3";
import { registerBlock, BlockProps } from "../registry";
import { C, FONT, Title, Badge, ramp, ticks, useRel } from "./common";

const tex = (latex: string, display = true) => katex.renderToString(latex, { displayMode: display, throwOnError: true, output: "html" });

const EquationSteps: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const steps = data.steps as { latex: string; checked: boolean; why: string }[];
  const bad = steps.find((s) => !s.checked);
  if (bad) throw new Error("BIE_UNCHECKED_STEP: " + bad.latex + " (" + bad.why + ")");          // never show a wrong step
  const every = (data.step_seconds ?? 1.2) * fps;
  const shown = Math.min(steps.length, Math.floor(rel / every) + 1);
  const rowH = Math.min(150, (height - 140) / steps.length);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT, color: C.ink }}>
      <Title text={data.title} sub={data.subtitle} />
      {steps.map((s, i) => {
        const o = ramp(rel, i * every, 12);
        const current = i === shown - 1;
        return (
          <div key={i} style={{ position: "absolute", left: 60, right: 60, top: 110 + i * rowH, height: rowH, display: "flex", alignItems: "center",
            gap: 28, opacity: i < shown ? (current ? o : 0.45) : 0, transform: `translateX(${(1 - o) * 40}px)` }}>
            <div style={{ fontSize: Math.min(64, rowH * 0.5), color: current ? C.ink : C.muted, minWidth: 0 }}
              dangerouslySetInnerHTML={{ __html: tex(s.latex) }} />
            {current && i > 0 ? <Badge text={data.check_label || "✓ SymPy: same solutions"} style={{ opacity: ramp(rel, i * every + 10, 10) }} /> : null}
          </div>
        );
      })}
    </div>
  );
};

const FunctionGraph: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const pad = { l: 110, r: 50, t: 110, b: 80 };
  const xs: number[] = data.x, ys: (number | null)[] = data.y;
  const xd = data.x_domain || [Math.min(...xs), Math.max(...xs)];
  const finite = ys.filter((v) => v !== null) as number[];
  const pts = (data.points?.y || []) as number[];
  const yd = data.y_domain || [Math.min(...finite, ...pts), Math.max(...finite, ...pts)];
  const sx = scaleLinear().domain(xd).range([pad.l, width - pad.r]);
  const sy = scaleLinear().domain(yd).nice().range([height - pad.b, pad.t]);
  const start = (data.draw_start ?? 0.3) * fps, drawn = start + (data.draw_seconds ?? 3) * fps;
  // Drawn up to a fractional sample, so a fitted line given by its two end points still grows smoothly.
  const reach = (xs.length - 1) * ramp(rel, start, drawn - start);
  const whole = Math.floor(reach), part = reach - whole;
  const shown: [number, number | null][] = xs.slice(0, whole + 1).map((x, i) => [x, ys[i]]);
  if (part > 0 && ys[whole] !== null && ys[whole + 1] !== null)
    shown.push([xs[whole] + (xs[whole + 1] - xs[whole]) * part, (ys[whole] as number) + ((ys[whole + 1] as number) - (ys[whole] as number)) * part]);
  const path = line<[number, number | null]>().defined((p) => p[1] !== null).x((p) => sx(p[0])).y((p) => sy(p[1] as number))(shown) || "";
  const [tx, ty] = shown[shown.length - 1];
  const [y0, y1] = sy.domain();
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {ticks(xd[0], xd[1], 8).map((v) => <g key={"x" + v}>
          <line x1={sx(v)} x2={sx(v)} y1={pad.t} y2={height - pad.b} stroke={C.line} />
          <text x={sx(v)} y={height - pad.b + 34} fill={C.muted} fontSize={24} textAnchor="middle">{v}</text></g>)}
        {ticks(y0, y1, 6).map((v) => <g key={"y" + v}>
          <line x1={pad.l} x2={width - pad.r} y1={sy(v)} y2={sy(v)} stroke={C.line} />
          <text x={pad.l - 16} y={sy(v) + 8} fill={C.muted} fontSize={24} textAnchor="end">{v}</text></g>)}
        {y0 < 0 && y1 > 0 ? <line x1={pad.l} x2={width - pad.r} y1={sy(0)} y2={sy(0)} stroke={C.ink} strokeOpacity={0.6} strokeWidth={2} /> : null}
        {xd[0] < 0 && xd[1] > 0 ? <line x1={sx(0)} x2={sx(0)} y1={pad.t} y2={height - pad.b} stroke={C.ink} strokeOpacity={0.6} strokeWidth={2} /> : null}
        {pts.map((v, i) => <circle key={"p" + i} cx={sx(data.points.x[i])} cy={sy(v)} r={9} fill={C.warm} opacity={ramp(rel, i * 3, 8)} />)}
        <path d={path} fill="none" stroke={C.accent} strokeWidth={6} strokeLinecap="round" />
        {ty !== null ? <circle cx={sx(tx)} cy={sy(ty)} r={12} fill={C.ink} stroke={C.accent} strokeWidth={4} /> : null}
      </svg>
      <Title text={data.title} sub={data.subtitle} />
      {data.latex ? <div style={{ position: "absolute", right: 60, top: 120, fontSize: 44, color: C.ink, background: C.panel, padding: "6px 20px", borderRadius: 14,
        opacity: ramp(rel, 0, 15) }} dangerouslySetInnerHTML={{ __html: tex(data.latex, false) }} /> : null}
      {data.note ? <Badge text={data.note} style={{ position: "absolute", right: 60, top: 200, opacity: ramp(rel, drawn, 12) }} /> : null}
      {data.note_latex ? <div style={{ position: "absolute", right: 60, top: 200, fontSize: 34, color: C.accent, background: C.panel, padding: "4px 18px",
        borderRadius: 12, border: `2px solid ${C.accent}`, opacity: ramp(rel, drawn, 12) }} dangerouslySetInnerHTML={{ __html: tex(data.note_latex, false) }} /> : null}
    </div>
  );
};

registerBlock("equation_steps", EquationSteps);
registerBlock("function_graph", FunctionGraph);
