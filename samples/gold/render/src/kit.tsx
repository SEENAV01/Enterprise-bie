// House style and building blocks for gold-sample lessons (seed of the Task 041 block library).
import React, { createContext, useContext } from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "./lite";

export const C = {
  bg0: "#071624", bg1: "#0d2438", ink: "#F4F7FB", soft: "#A9BCD0", dim: "#5F7891",
  leaf: "#4ADE80", leafDeep: "#16A34A", amber: "#FBBF24", coral: "#FB7185", sky: "#38BDF8",
  violet: "#A78BFA", teal: "#2DD4BF", wall: "#65A30D", cyto: "#FDE68A", nucleus: "#7C3AED",
  card: "rgba(255,255,255,0.06)", cardLine: "rgba(255,255,255,0.14)", red: "#F43F5E", green: "#22C55E",
};
export const FONT = "Inter, 'DejaVu Sans', sans-serif";

export type SceneInfo = { id: string; zone?: string | null; duration: number; marks: Record<string, number>;
  beats: { id: string; start: number; end: number }[] };
export const SceneCtx = createContext<SceneInfo>({ id: "", duration: 1, marks: {}, beats: [] });
export const useScene = () => useContext(SceneCtx);

export function useMark(name: string): number {
  const { marks } = useScene();
  return name in marks ? marks[name] : 1e9;
}

/** Spring 0 -> 1 starting at a mark (or a frame number). */
export function useIn(at: string | number, delay = 0, stiff = 140): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { marks } = useScene();
  const start = typeof at === "number" ? at : (at in marks ? marks[at] : 1e9);
  return Math.max(0, spring({ frame, fps, delay: start + delay, config: { damping: 15, stiffness: stiff } }));
}

/** Eased 0 -> 1 over `dur` frames starting at a mark. */
export function useRamp(at: string | number, dur = 20, delay = 0, easing = Easing.inOut): number {
  const frame = useCurrentFrame();
  const { marks } = useScene();
  const start = (typeof at === "number" ? at : (at in marks ? marks[at] : 1e9)) + delay;
  return interpolate(frame, [start, start + dur], [0, 1], { easing });
}

export const pulse = (frame: number, period = 45, low = 0.55) => low + (1 - low) * (0.5 + 0.5 * Math.sin((frame / period) * Math.PI * 2));

export function seeded(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
}

/** Background used by every scene: deep gradient, slow floating particles, vignette. */
export const Stage: React.FC<{ children: React.ReactNode; tint?: string }> = ({ children, tint = C.sky }) => {
  const frame = useCurrentFrame();
  const rnd = seeded(7);
  const dots = Array.from({ length: 34 }, () => ({ x: rnd() * 1920, y: rnd() * 1080, r: 1 + rnd() * 2.6, s: 0.2 + rnd() * 0.6, p: rnd() * 6 }));
  return (
    <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, fontFamily: FONT }}>
      <defs>
        <radialGradient id="bgGrad" cx="50%" cy="38%" r="75%">
          <stop offset="0%" stopColor={C.bg1} />
          <stop offset="100%" stopColor={C.bg0} />
        </radialGradient>
        <radialGradient id="vig" cx="50%" cy="50%" r="70%">
          <stop offset="70%" stopColor="#000" stopOpacity={0} />
          <stop offset="100%" stopColor="#000" stopOpacity={0.45} />
        </radialGradient>
        <radialGradient id="sheen" cx="35%" cy="28%" r="75%">
          <stop offset="0%" stopColor="#fff" stopOpacity={0.55} />
          <stop offset="45%" stopColor="#fff" stopOpacity={0.08} />
          <stop offset="100%" stopColor="#000" stopOpacity={0.18} />
        </radialGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="10" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="10" stdDeviation="14" floodColor="#000" floodOpacity="0.35" />
        </filter>
        <marker id="arrowHead" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="context-stroke" />
        </marker>
      </defs>
      <rect width={1920} height={1080} fill="url(#bgGrad)" />
      {dots.map((d, i) => (
        <circle key={i} cx={(d.x + frame * d.s) % 1960 - 20} cy={d.y + Math.sin(frame / 60 + d.p) * 12} r={d.r}
          fill={tint} opacity={0.12 + 0.08 * Math.sin(frame / 40 + d.p)} />
      ))}
      {children}
      <rect width={1920} height={1080} fill="url(#vig)" pointerEvents="none" />
    </svg>
  );
};

/** Persistent header: chapter tag on the left, section chip on the right, progress line on top. */
export const Header: React.FC<{ section: string; color?: string; progress: number }> = ({ section, color = C.sky, progress }) => (
  <g>
    <rect x={0} y={0} width={1920 * progress} height={6} fill={color} opacity={0.9} />
    <text x={70} y={74} fill={C.soft} fontSize={28} fontWeight={600} letterSpacing={1}>TISSUES · PART 1</text>
    <g transform="translate(1850,50)">
      <rect x={-section.length * 15 - 56} y={0} width={section.length * 15 + 56} height={44} rx={22} fill={color} opacity={0.16} />
      <circle cx={-section.length * 15 - 32} cy={22} r={7} fill={color} />
      <text x={-section.length * 15 - 16} y={31} fill={color} fontSize={24} fontWeight={700}>{section}</text>
    </g>
  </g>
);

/** Text that rises and fades in. */
export const Rise: React.FC<{ p: number; x: number; y: number; size?: number; color?: string; weight?: number;
  anchor?: "start" | "middle" | "end"; children: React.ReactNode; italic?: boolean }> = ({ p, x, y, size = 44, color = C.ink, weight = 700, anchor = "start", children, italic }) => (
  <text x={x} y={y + (1 - Math.min(1, p)) * 24} fill={color} fontSize={size} fontWeight={weight} textAnchor={anchor}
    opacity={Math.min(1, Math.max(0, p))} fontStyle={italic ? "italic" : undefined}>{children}</text>
);

/** Label with a leader line that draws from the target to the text. */
export const Leader: React.FC<{ p: number; from: [number, number]; to: [number, number]; text: string; color?: string; size?: number;
  anchor?: "start" | "end" | "middle"; sub?: string }> = ({ p, from, to, text, color = C.ink, size = 36, anchor = "start", sub }) => {
  const len = Math.hypot(to[0] - from[0], to[1] - from[1]);
  const draw = Math.min(1, p * 1.6);
  const tp = Math.max(0, Math.min(1, (p - 0.35) / 0.65));
  const dx = anchor === "end" ? -14 : anchor === "middle" ? 0 : 14;
  return (
    <g opacity={p > 0 ? 1 : 0}>
      <circle cx={from[0]} cy={from[1]} r={8 * draw} fill={color} />
      <line x1={from[0]} y1={from[1]} x2={to[0]} y2={to[1]} stroke={color} strokeWidth={3} strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
      <text x={to[0] + dx} y={to[1] + size * 0.35} fill={color} fontSize={size} fontWeight={700} textAnchor={anchor} opacity={tp}>{text}</text>
      {sub && <text x={to[0] + dx} y={to[1] + size * 0.35 + size * 0.95} fill={C.soft} fontSize={size * 0.68} fontWeight={500} textAnchor={anchor} opacity={tp}>{sub}</text>}
    </g>
  );
};

/** Rounded pill. */
export const Chip: React.FC<{ x: number; y: number; text: string; color: string; p?: number; size?: number; solid?: boolean }> = ({ x, y, text, color, p = 1, size = 30, solid }) => {
  const w = text.length * size * 0.56 + size * 1.4;
  const h = size * 1.6;
  const s = Math.min(1, p);
  return (
    <g transform={`translate(${x},${y}) scale(${0.6 + 0.4 * s})`} opacity={s}>
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={h / 2} fill={solid ? color : "rgba(0,0,0,0)"} stroke={color} strokeWidth={3}
        fillOpacity={solid ? 1 : 0} />
      {!solid && <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={h / 2} fill={color} opacity={0.14} />}
      <text x={0} y={size * 0.36} textAnchor="middle" fill={solid ? C.bg0 : color} fontSize={size} fontWeight={800}>{text}</text>
    </g>
  );
};

/** Card panel with optional title; children are positioned inside the card's own coordinates. */
export const Card: React.FC<{ x: number; y: number; w: number; h: number; p?: number; title?: string; color?: string; children?: React.ReactNode }> = ({ x, y, w, h, p = 1, title, color = C.sky, children }) => {
  const s = Math.min(1, Math.max(0, p));
  return (
    <g transform={`translate(${x},${y + (1 - s) * 30})`} opacity={s}>
      <rect width={w} height={h} rx={28} fill="rgba(255,255,255,0.055)" stroke={C.cardLine} strokeWidth={2} filter="url(#soft)" />
      {title && <>
        <rect width={w} height={70} rx={28} fill={color} opacity={0.16} />
        <rect y={42} width={w} height={28} fill={color} opacity={0.0} />
        <text x={32} y={47} fill={color} fontSize={32} fontWeight={800}>{title}</text>
      </>}
      {children}
    </g>
  );
};

/** Big rotated stamp (correct / wrong). */
export const Stamp: React.FC<{ x: number; y: number; text: string; color: string; p: number; rotate?: number; size?: number }> = ({ x, y, text, color, p, rotate = -8, size = 64 }) => {
  if (p <= 0) return null;
  const s = 1.8 - 0.8 * Math.min(1, p);
  const w = text.length * size * 0.62 + size;
  return (
    <g transform={`translate(${x},${y}) rotate(${rotate}) scale(${s})`} opacity={Math.min(1, p * 1.5)}>
      <rect x={-w / 2} y={-size * 0.85} width={w} height={size * 1.5} rx={14} fill="none" stroke={color} strokeWidth={7} />
      <text x={0} y={size * 0.32} fill={color} fontSize={size} fontWeight={900} textAnchor="middle" letterSpacing={3}>{text}</text>
    </g>
  );
};

/** Arrow that draws itself along a path. */
export const DrawPath: React.FC<{ d: string; p: number; color: string; width?: number; length?: number; head?: boolean; dash?: string }> = ({ d, p, color, width = 6, length = 1200, head = true }) => (
  <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeDasharray={length}
    strokeDashoffset={length * (1 - Math.min(1, Math.max(0, p)))} markerEnd={head && p > 0.98 ? "url(#arrowHead)" : undefined} />
);

/** Generic biological cell. */
export const Cell: React.FC<{ x: number; y: number; r: number; shape?: "round" | "rect" | "hex" | "oval"; fill?: string; edge?: string;
  wall?: number; wallColor?: string; nucleus?: number; vacuole?: number; vacuoleX?: number; granules?: number; seed?: number; opacity?: number;
  rot?: number; nucleusX?: number; nucleusY?: number; stretch?: number }> = ({ x, y, r, shape = "round", fill = C.cyto, edge = "#F59E0B", wall = 0,
  wallColor = C.wall, nucleus = 0.32, vacuole = 0, vacuoleX = 0.1, granules = 0, seed = 1, opacity = 1, rot = 0, nucleusX, nucleusY, stretch = 1 }) => {
  const rnd = seeded(seed * 97 + 13);
  const w = r * 2 * (shape === "oval" ? 1.35 : 1) * stretch, h = r * 2 * (shape === "oval" ? 0.85 : 1);
  const body = (inset: number, props: React.SVGProps<SVGElement>) => {
    if (shape === "rect") return <rect x={-w / 2 + inset} y={-h / 2 + inset} width={w - 2 * inset} height={h - 2 * inset} rx={r * 0.22} {...(props as any)} />;
    if (shape === "hex") {
      const pts = Array.from({ length: 6 }, (_, i) => { const a = Math.PI / 3 * i + Math.PI / 6; return `${(r - inset) * Math.cos(a)},${(r - inset) * Math.sin(a)}`; }).join(" ");
      return <polygon points={pts} {...(props as any)} />;
    }
    return <ellipse rx={w / 2 - inset} ry={h / 2 - inset} {...(props as any)} />;
  };
  const nx = nucleusX ?? 0, ny = nucleusY ?? 0;
  return (
    <g transform={`translate(${x},${y}) rotate(${rot})`} opacity={opacity}>
      {wall > 0 && body(-wall, { fill: wallColor, stroke: "#3F6212", strokeWidth: 2 })}
      {body(0, { fill, stroke: edge, strokeWidth: Math.max(2, r * 0.05) })}
      {body(0, { fill: "url(#sheen)", stroke: "none" })}
      {Array.from({ length: granules }, (_, i) => {
        const a = rnd() * Math.PI * 2, d = rnd() * r * 0.75;
        return <circle key={i} cx={Math.cos(a) * d * (w / (2 * r))} cy={Math.sin(a) * d * (h / (2 * r))} r={Math.max(1.5, r * 0.035)} fill="#D97706" opacity={0.55} />;
      })}
      {vacuole > 0 && <ellipse cx={r * vacuoleX} cy={0} rx={r * vacuole * (shape === "rect" ? 1.05 * stretch : 1)} ry={r * vacuole * 0.82} fill="#BAE6FD" stroke="#38BDF8" strokeWidth={2} opacity={0.92} />}
      {nucleus > 0 && <>
        <circle cx={nx} cy={ny} r={r * nucleus} fill={C.nucleus} opacity={0.92} />
        <circle cx={nx - r * nucleus * 0.25} cy={ny - r * nucleus * 0.2} r={r * nucleus * 0.32} fill="#C4B5FD" opacity={0.85} />
        <circle cx={nx} cy={ny} r={r * nucleus} fill="url(#sheen)" />
      </>}
    </g>
  );
};

/** Row of a checklist with a tick that pops in. */
export const CheckRow: React.FC<{ x: number; y: number; p: number; k: string; v: string; color?: string; good?: boolean }> = ({ x, y, p, k, v, color = C.leaf, good = true }) => {
  const s = Math.min(1, Math.max(0, p));
  return (
    <g transform={`translate(${x + (1 - s) * 40},${y})`} opacity={s}>
      <circle cx={22} cy={-12} r={22} fill={good ? color : C.red} opacity={0.2} />
      <text x={22} y={-1} textAnchor="middle" fill={good ? color : C.red} fontSize={30} fontWeight={900}>{good ? "✓" : "✗"}</text>
      <text x={62} y={0} fill={C.soft} fontSize={30} fontWeight={600}>{k}</text>
      <text x={62} y={44} fill={C.ink} fontSize={36} fontWeight={800}>{v}</text>
    </g>
  );
};

/** Wraps text into lines of at most `max` characters. */
export function wrap(text: string, max: number): string[] {
  const out: string[] = [];
  let line = "";
  for (const word of text.split(" ")) {
    if ((line + " " + word).trim().length > max) { out.push(line.trim()); line = word; } else line += " " + word;
  }
  if (line.trim()) out.push(line.trim());
  return out;
}

export const Lines: React.FC<{ x: number; y: number; lines: string[]; size?: number; color?: string; weight?: number; gap?: number; anchor?: "start" | "middle" | "end"; p?: number }> = ({ x, y, lines, size = 36, color = C.ink, weight = 600, gap = 1.3, anchor = "start", p = 1 }) => (
  <g opacity={Math.min(1, Math.max(0, p))}>
    {lines.map((l, i) => <text key={i} x={x} y={y + i * size * gap} fill={color} fontSize={size} fontWeight={weight} textAnchor={anchor}>{l}</text>)}
  </g>
);
