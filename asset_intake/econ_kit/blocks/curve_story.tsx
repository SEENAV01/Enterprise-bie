// curve_story: a schematic graph that tells a story step by step (asset intake, economy batch, 27 Oct 2026).
//
// Axes with names (no clutter), curves that draw themselves, a dot that walks along a curve to the x values the
// narration names (with dashed drop lines to both axes and the values shown), vertical/horizontal guide lines
// (a natural rate, a target), shaded bands (short run, a gap), a curve that shifts (draw the new one, fade the old
// one with ``until``) and short notes. Economics needs exactly this: Phillips curve and NAIRU, demand and supply,
// AD-AS, the business cycle, Laffer, Lorenz. Curves arrive as points from Python (an adapter or the director's
// numbers), so the block never invents a shape. Coordinates of notes are fractions of the block.
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { registerBlock, BlockProps } from "../../../bie/brain/video/blocks/registry";
import { FONT } from "../../../bie/brain/video/blocks/toolbox/common";
import { THEMES } from "./canvas_build";

const lin = (f: number, a: number, b: number) =>
  interpolate(f, [a, Math.max(a + 1, b)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
const presence = (frame: number, fps: number, at: number, until?: number) => {
  if (frame < at) return 0;
  const inn = spring({ frame: frame - at, fps, config: { damping: 18, stiffness: 120 } });
  const out = until === undefined ? 1 : interpolate(frame, [until - 10, until], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return Math.max(0, Math.min(inn, out));
};

function yAt(points: number[][], x: number) {
  for (let i = 0; i < points.length - 1; i++) {
    const [x0, y0] = points[i], [x1, y1] = points[i + 1];
    if ((x >= x0 && x <= x1) || (x <= x0 && x >= x1)) return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0 || 1);
  }
  return points[x < points[0][0] ? 0 : points.length - 1][1];
}

const CurveStory: React.FC<BlockProps> = ({ data, width: W, height: H }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const P = THEMES[data.theme ?? "paper"] ?? THEMES.paper;
  const tone = (t?: string) => (t && P[t]) || t || P.ink;
  const plot = data.plot ?? { x: 0.1, y: 0.1, w: 0.8, h: 0.72 };
  const [xa, xb] = data.x_domain ?? [0, 10], [ya, yb] = data.y_domain ?? [0, 10];
  const px = (x: number) => (plot.x + ((x - xa) / (xb - xa)) * plot.w) * W;
  const py = (y: number) => (plot.y + plot.h - ((y - ya) / (yb - ya)) * plot.h) * H;
  const axisAt = data.axes_at ?? 0;
  const axesK = lin(frame, axisAt, axisAt + 18);
  const x0 = px(xa), y0 = py(ya), x1 = px(xb), y1 = py(yb);
  const head = (id: string, col: string) => (
    <marker id={id} markerWidth="9" markerHeight="9" refX="6.5" refY="4.5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L9,4.5 L0,9 z" fill={col} /></marker>
  );
  return (
    <div style={{ position: "absolute", inset: 0, background: data.transparent ? "transparent" : P.bg, fontFamily: FONT }}>
      <svg style={{ position: "absolute", inset: 0, width: W, height: H, overflow: "visible" }}>
        <defs>{head("cs-axis", P.line)}</defs>
        {(data.shades ?? []).map((s: any) => {
          const o = presence(frame, fps, s.at, s.until);
          if (!o) return null;
          const k = lin(frame, s.at, s.at + 16);
          const xs = px(s.x0), xe = px(s.x0 + (s.x1 - s.x0) * k);
          if (s.under) {
            const c = (data.curves ?? []).find((c: any) => c.id === s.under);
            if (!c) return null;
            const pts = c.points.filter((p: number[]) => p[0] >= s.x0 && p[0] <= s.x0 + (s.x1 - s.x0) * k);
            const d = `M${xs},${y0} ` + pts.map((p: number[]) => `L${px(p[0])},${py(p[1])}`).join(" ") + ` L${xe},${y0} Z`;
            return <path key={s.id} d={d} fill={tone(s.tone ?? "accent")} opacity={0.18 * o} />;
          }
          return (
            <g key={s.id} opacity={o}>
              <rect x={Math.min(xs, xe)} y={y1} width={Math.abs(xe - xs)} height={y0 - y1} fill={tone(s.tone ?? "accent")} opacity={0.14} />
              {s.hatch ? Array.from({ length: Math.ceil(Math.abs(xe - xs) / 14) }, (_, i) => (
                <line key={i} x1={Math.min(xs, xe) + i * 14} y1={y1} x2={Math.min(xs, xe) + i * 14} y2={y0} stroke={tone(s.tone ?? "accent")} strokeWidth={2} opacity={0.35} />
              )) : null}
              {s.label ? <text x={(xs + xe) / 2} y={y1 + 30} textAnchor="middle" fontSize={24} fontWeight={800} fill={tone(s.tone ?? "accent")}>{s.label}</text> : null}
            </g>
          );
        })}
        <g opacity={axesK}>
          <line x1={x0} y1={y0} x2={x0} y2={y0 + (y1 - 30 - y0) * axesK} stroke={P.line} strokeWidth={4} markerEnd="url(#cs-axis)" />
          <line x1={x0} y1={y0} x2={x0 + (x1 + 30 - x0) * axesK} y2={y0} stroke={P.line} strokeWidth={4} markerEnd="url(#cs-axis)" />
          <text x={x1 + 10} y={y0 + 46} textAnchor="end" fontSize={28} fontWeight={700} fill={P.muted}>{data.x_label} →</text>
          <text transform={`translate(${x0 - 26},${y1 + 10}) rotate(-90)`} textAnchor="end" fontSize={28} fontWeight={700} fill={P.muted}>{data.y_label} →</text>
          {(data.x_ticks ?? []).map((t: any, i: number) => <text key={i} x={px(t.x)} y={y0 + 34} textAnchor="middle" fontSize={22} fill={P.muted}>{t.label}</text>)}
          {(data.y_ticks ?? []).map((t: any, i: number) => <text key={i} x={x0 - 14} y={py(t.y) + 8} textAnchor="end" fontSize={22} fill={P.muted}>{t.label}</text>)}
        </g>
        {(data.guides ?? []).map((g: any) => {
          const o = presence(frame, fps, g.at, g.until);
          if (!o) return null;
          const k = lin(frame, g.at, g.at + 16);
          const col = tone(g.tone ?? "warm");
          return g.x !== undefined ? (
            <g key={g.id} opacity={o}>
              <line x1={px(g.x)} y1={y0} x2={px(g.x)} y2={y0 + (y1 - y0) * k} stroke={col} strokeWidth={g.width ?? 5} strokeDasharray={g.dashed ? "12 9" : undefined} />
              {g.label ? <text x={px(g.x)} y={y0 + 60} textAnchor="middle" fontSize={24} fontWeight={800} fill={col}>{g.label}</text> : null}
            </g>
          ) : (
            <g key={g.id} opacity={o}>
              <line x1={x0} y1={py(g.y)} x2={x0 + (x1 - x0) * k} y2={py(g.y)} stroke={col} strokeWidth={g.width ?? 5} strokeDasharray={g.dashed ? "12 9" : undefined} />
              {g.label ? <text x={x1} y={py(g.y) - 12} textAnchor="end" fontSize={24} fontWeight={800} fill={col}>{g.label}</text> : null}
            </g>
          );
        })}
        {(data.curves ?? []).map((c: any) => {
          const o = presence(frame, fps, c.at, c.until);
          if (!o) return null;
          const d = c.points.map((p: number[], i: number) => `${i ? "L" : "M"}${px(p[0])},${py(p[1])}`).join(" ");
          let len = 0;
          for (let i = 1; i < c.points.length; i++) len += Math.hypot(px(c.points[i][0]) - px(c.points[i - 1][0]), py(c.points[i][1]) - py(c.points[i - 1][1]));
          const k = lin(frame, c.at, c.at + (c.draw_frames ?? 30));
          const end = c.points[c.points.length - 1];
          return (
            <g key={c.id} opacity={o * (c.faded ? 0.35 : 1)}>
              <path d={d} fill="none" stroke={tone(c.tone ?? "accent")} strokeWidth={c.width ?? 6} strokeLinecap="round" strokeLinejoin="round"
                strokeDasharray={c.dashed ? "14 10" : `${len} ${len}`} strokeDashoffset={c.dashed ? 0 : len * (1 - k)} />
              {c.label ? <text x={px(end[0]) + (c.label_dx ?? 12)} y={py(end[1]) + (c.label_dy ?? 8)} fontSize={26} fontWeight={800}
                fill={tone(c.tone ?? "accent")} opacity={k}>{c.label}</text> : null}
            </g>
          );
        })}
        {(data.dots ?? []).map((dt: any) => {
          const c = (data.curves ?? []).find((c: any) => c.id === dt.curve);
          if (!c || frame < dt.steps[0].at) return null;
          const o = presence(frame, fps, dt.steps[0].at, dt.until);
          let x = dt.steps[0].x;
          for (let i = 1; i < dt.steps.length; i++) {
            const s = dt.steps[i];
            if (frame >= s.at) x = dt.steps[i - 1].x + (s.x - dt.steps[i - 1].x) * lin(frame, s.at, s.at + (dt.move_frames ?? 22));
          }
          const y = yAt(c.points, x);
          const col = tone(dt.tone ?? "danger");
          const cx = px(x), cy = py(y);
          return (
            <g key={dt.id} opacity={o}>
              {dt.drops ? <>
                {dt.drops.includes("x") ? <line x1={cx} y1={cy} x2={cx} y2={y0} stroke={col} strokeWidth={3} strokeDasharray="8 7" /> : null}
                {dt.drops.includes("y") ? <line x1={cx} y1={cy} x2={x0} y2={cy} stroke={col} strokeWidth={3} strokeDasharray="8 7" /> : null}
              </> : null}
              <circle cx={cx} cy={cy} r={16} fill={col} opacity={0.25} />
              <circle cx={cx} cy={cy} r={10} fill={col} stroke="#ffffff" strokeWidth={3} />
              {dt.label ? <text x={cx + 20} y={cy - 18} fontSize={24} fontWeight={800} fill={col}>{dt.label}</text> : null}
            </g>
          );
        })}
      </svg>
      {(data.notes ?? []).map((n: any) => {
        const o = presence(frame, fps, n.at, n.until);
        if (!o) return null;
        return (
          <div key={n.id} style={{ position: "absolute", left: n.fx * W, top: n.fy * H, width: (n.fw ?? 0.24) * W, opacity: o,
            transform: `translateY(${(1 - o) * 10}px)`, background: n.box === false ? "transparent" : P.note, borderLeft: n.box === false ? undefined : `6px solid ${tone(n.tone ?? "warm")}`,
            borderRadius: 8, padding: n.box === false ? 0 : "8px 14px", fontSize: n.size ?? 26, lineHeight: 1.3, color: P.ink, fontWeight: n.bold ? 800 : 500,
            boxSizing: "border-box" }}>{n.text}</div>
        );
      })}
      {data.title ? <div style={{ position: "absolute", left: plot.x * W, top: 22, fontSize: 40, fontWeight: 900, color: P.ink }}>{data.title}</div> : null}
    </div>
  );
};

registerBlock("curve_story", CurveStory);
