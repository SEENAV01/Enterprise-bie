// canvas: BIE's build-up canvas (canvas_build) and story graph (curve_story) blocks, brought in from the economy kit
// of the asset intake (27 October 2026, Task 046 Part C). Subtitles are not drawn here: the core Captions strip
// (blocks/index.tsx) draws every video's captions once, readable on paper and on the dark world alike.
// canvas_build: a "build-up canvas" block (asset intake, economy batch, 27 Oct 2026).
//
// One composition is built piece by piece while the narrator speaks: icons, text boxes, tags, arrows, numbers that get
// struck out and replaced, crowds that grow, tick/cross marks, highlights and callouts whose phrases light up when
// they are spoken. Every element carries the frame it appears on (``at``, from a cue word through
// bie/brain/video/timing.py) and may leave (``until``). Positions are fractions (0..1) of the block's box and come
// from the layout code (bie/brain/canvas.py), never from the AI, so nothing overlaps.
//
// The block draws its own paper (theme "paper", the light look of the economy references) or stays transparent on
// BIE's dark backdrop (theme "dark"). It registers itself, so the core library and the director need no change: a
// scene uses it as { type: "block", block: "canvas_build", box: {x:0,y:0,w:1,h:1}, data: {...} }, and the scene's
// camera keys can zoom to any region of it.
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { registerBlock, BlockProps } from "../registry";
import { FONT, assetUrl } from "./common";

export const THEMES: Record<string, Record<string, string>> = {
  paper: { bg: "#fbf8f1", ink: "#1f2a36", muted: "#5d6b78", line: "#33414f", accent: "#2b7bd6", warm: "#ef8a1f",
    danger: "#d43f3f", ok: "#2a9a57", tag: "#e2477a", box: "#e2effc", note: "#fff2bf", band: "#ffe58a", shadow: "rgba(30,40,60,0.10)" },
  dark: { bg: "transparent", ink: "#f2f6f8", muted: "#9fb3bf", line: "#cfe3ee", accent: "#38d3c3", warm: "#ffb35c",
    danger: "#ff6b6b", ok: "#5fe08f", tag: "#ff7aa8", box: "rgba(8,28,40,0.82)", note: "rgba(255,179,92,0.18)", band: "rgba(255,213,74,0.35)",
    shadow: "rgba(0,0,0,0.35)" },
};

type Pt = { x: number; y: number };
type Box = { x: number; y: number; w: number; h: number };
type End = { id?: string; side?: "l" | "r" | "t" | "b" | "c"; x?: number; y?: number };
type El = any;

const toneOf = (P: Record<string, string>, tone?: string) => (tone && P[tone]) || tone || P.ink;

/** 0 → 1 as the element enters (a soft spring), 1 → 0 over the last 10 frames before ``until``. */
function presence(frame: number, fps: number, at: number, until?: number) {
  if (frame < at) return 0;
  const inn = spring({ frame: frame - at, fps, config: { damping: 16, stiffness: 120 } });
  const out = until === undefined ? 1 : interpolate(frame, [until - 10, until], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return Math.max(0, Math.min(inn, out));
}

const lin = (frame: number, a: number, b: number) =>
  interpolate(frame, [a, Math.max(a + 1, b)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });

function boxOf(el: El): Box {
  return { x: el.x ?? 0, y: el.y ?? 0, w: el.w ?? 0.1, h: el.h ?? 0.06 };
}

function endPoint(map: Map<string, El>, end: End, toward?: Pt): Pt {
  if (end.id && map.has(end.id)) {
    const b = boxOf(map.get(end.id));
    const c = { x: b.x + b.w / 2, y: b.y + b.h / 2 };
    let side = end.side;
    if (!side && toward) {
      const dx = toward.x - c.x, dy = (toward.y - c.y) * 0.5625;     // screen is 16:9: compare in screen units
      side = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "r" : "l") : (dy > 0 ? "b" : "t");
    }
    const pad = 0.006;
    switch (side) {
      case "r": return { x: b.x + b.w + pad, y: c.y };
      case "l": return { x: b.x - pad, y: c.y };
      case "t": return { x: c.x, y: b.y - pad * 1.6 };
      case "b": return { x: c.x, y: b.y + b.h + pad * 1.6 };
      default: return c;
    }
  }
  return { x: end.x ?? 0.5, y: end.y ?? 0.5 };
}

/** Is the element dimmed by a focus step? (data.focus: [{at, ids}] — elements outside the ids fade to 35 %.) */
function focusLevel(focus: { at: number; until?: number; ids: string[] }[] | undefined, id: string, frame: number) {
  if (!focus) return 1;
  let level = 1;
  for (const f of focus) {
    if (frame < f.at || (f.until !== undefined && frame > f.until)) continue;
    const k = lin(frame, f.at, f.at + 12) * (f.until !== undefined ? 1 - lin(frame, f.until - 12, f.until) : 1);
    level = Math.min(level, f.ids.includes(id) ? 1 : 1 - 0.65 * k);
  }
  return level;
}

/** "L3 touches" (data.touches): depth and life on the same canvas — soft shadows, gentle idle motion, walk-ins,
 *  flowing coins on arrows, flipping price tags, a light sweep and a camera that follows what is being said. */
const phaseOf = (id: string) => Array.from(id).reduce((a, c) => a + c.charCodeAt(0), 0) % 60;

const IconEl: React.FC<{ el: El; P: Record<string, string>; W: number; H: number; o: number; frame?: number; touches?: boolean }> =
  ({ el, P, W, H, o, frame = 0, touches }) => {
  const b = boxOf(el);
  const s = 0.6 + 0.4 * o;
  const bob = touches ? Math.sin((frame + phaseOf(el.id)) / 16) * 4 : 0;
  return (
    <div style={{ position: "absolute", left: b.x * W, top: b.y * H, width: b.w * W, height: b.h * H, opacity: o,
      transform: `scale(${s})`, transformOrigin: "50% 80%" }}>
      {touches ? <div style={{ position: "absolute", left: "18%", width: "64%", top: el.label ? "70%" : "90%", height: "10%", borderRadius: "50%",
        background: "radial-gradient(closest-side, rgba(20,30,45,0.28), rgba(20,30,45,0))", transform: `scaleX(${1 - bob / 40})` }} /> : null}
      <img src={assetUrl(el.src)} style={{ width: "100%", height: el.label ? "78%" : "100%", objectFit: "contain", display: "block",
        transform: `translateY(${bob - (touches ? 4 : 0)}px)`, filter: touches ? "drop-shadow(0 10px 10px rgba(20,30,45,0.22))" : undefined }} />
      {el.label ? <div style={{ fontFamily: FONT, fontSize: el.label_size ?? 22, fontWeight: 700, color: toneOf(P, el.label_tone ?? "muted"),
        textAlign: "center", letterSpacing: 0.5, marginTop: 4, whiteSpace: "nowrap" }}>{el.label}</div> : null}
    </div>
  );
};

/** Text with optional phrase marks: each mark lights up (a highlighter band sweeps under it) at its own frame. */
const MarkedText: React.FC<{ text: string; marks?: { phrase: string; at: number; tone?: string }[]; frame: number; P: Record<string, string> }> =
  ({ text, marks, frame, P }) => {
    if (!marks || !marks.length) return <>{text}</>;
    const parts: React.ReactNode[] = [];
    let rest = text, key = 0;
    const ordered = [...marks].sort((a, b) => text.indexOf(a.phrase) - text.indexOf(b.phrase));
    for (const m of ordered) {
      const i = rest.indexOf(m.phrase);
      if (i < 0) continue;
      parts.push(<span key={key++}>{rest.slice(0, i)}</span>);
      const k = lin(frame, m.at, m.at + 14);
      const col = toneOf(P, m.tone ?? "band");
      parts.push(<span key={key++} style={{ backgroundImage: `linear-gradient(${col}, ${col})`, backgroundRepeat: "no-repeat",
        backgroundSize: `${k * 100}% 100%`, borderRadius: 4, padding: "0 2px" }}>{m.phrase}</span>);
      rest = rest.slice(i + m.phrase.length);
    }
    parts.push(<span key={key++}>{rest}</span>);
    return <>{parts}</>;
  };

const TextEl: React.FC<{ el: El; P: Record<string, string>; W: number; H: number; o: number; frame: number }> = ({ el, P, W, H, o, frame }) => {
  const b = boxOf(el);
  const style = el.style ?? "plain";
  const size = el.size ?? (style === "title" ? 56 : style === "tag" ? 24 : 28);
  const shown = el.write_on ? Math.round(el.text.length * lin(frame, el.at, el.at + Math.max(10, el.text.length * 0.9))) : el.text.length;
  const text = el.text.slice(0, shown);
  const base: React.CSSProperties = { position: "absolute", left: b.x * W, top: b.y * H, width: b.w * W, minHeight: b.h * H,
    fontFamily: FONT, fontSize: size, lineHeight: 1.3, color: toneOf(P, el.tone), opacity: o, boxSizing: "border-box",
    textAlign: el.align ?? (style === "title" || style === "tag" ? "center" : "left"), display: "flex", flexDirection: "column",
    justifyContent: "center", transform: `translateY(${(1 - o) * 12}px)` };
  if (style === "title") Object.assign(base, { fontWeight: 900, letterSpacing: 1 });
  if (style === "box") Object.assign(base, { background: el.fill ? toneOf(P, el.fill) : P.box, borderRadius: 10, padding: "10px 16px",
    border: `2px solid ${el.border ? toneOf(P, el.border) : "transparent"}`, boxShadow: `0 3px 10px ${P.shadow}` });
  if (style === "note") Object.assign(base, { background: P.note, borderRadius: 8, padding: "10px 16px", borderLeft: `6px solid ${P.warm}` });
  if (style === "tag") Object.assign(base, { background: toneOf(P, el.fill ?? "tag"), color: el.tone ? toneOf(P, el.tone) : "#ffffff",
    borderRadius: 999, padding: "4px 18px", fontWeight: 800, letterSpacing: 1, textTransform: "uppercase", whiteSpace: "nowrap" });
  return <div style={base}><div><MarkedText text={text} marks={el.marks} frame={frame} P={P} /></div></div>;
};

const ValueEl: React.FC<{ el: El; P: Record<string, string>; W: number; H: number; frame: number; fps: number; touches?: boolean }> =
  ({ el, P, W, H, frame, fps, touches }) => {
  const steps: { text: string; at: number; dir?: "up" | "down" }[] = el.steps;
  let idx = -1;
  steps.forEach((s, i) => { if (frame >= s.at) idx = i; });
  if (idx < 0) return null;
  const cur = steps[idx], prev = idx > 0 ? steps[idx - 1] : null;
  const size = el.size ?? 52;
  const k = presence(frame, fps, cur.at, undefined);
  const strike = prev ? lin(frame, cur.at, cur.at + 10) : 0;
  const dirCol = cur.dir === "up" ? P.ok : cur.dir === "down" ? P.danger : P.ink;
  const o = presence(frame, fps, steps[0].at, el.until);
  return (
    <div style={{ position: "absolute", left: el.x * W, top: el.y * H, fontFamily: FONT, opacity: o, whiteSpace: "nowrap" }}>
      {prev ? (
        <div style={{ position: "absolute", left: -size * 0.15, top: -size * 0.62, fontSize: size * 0.55, color: P.muted, fontWeight: 700 }}>
          {prev.text}
          <div style={{ position: "absolute", left: -4, top: "52%", height: 4, width: `calc(${strike * 100}% + 8px)`, background: P.danger,
            transform: "rotate(-8deg)" }} />
        </div>
      ) : null}
      {touches && prev ? <span style={{ position: "absolute", left: -size * 0.3, top: -size * 0.25, width: size * 3.2, height: size * 1.6, borderRadius: size,
        background: `radial-gradient(closest-side, ${P.warm}66, ${P.warm}00)`, opacity: Math.max(0, 1 - lin(frame, cur.at + 6, cur.at + 40)) }} /> : null}
      <span style={{ fontSize: size, fontWeight: 900, color: toneOf(P, el.tone), display: "inline-block",
        transform: touches && prev ? `perspective(600px) rotateX(${(1 - lin(frame, cur.at, cur.at + 12)) * 90}deg)` : `scale(${0.7 + 0.3 * k})`,
        transformOrigin: touches && prev ? "50% 50%" : "0 70%", textShadow: touches ? "0 6px 14px rgba(20,30,45,0.22)" : undefined,
        position: "relative" }}>{cur.text}</span>
      {cur.dir ? <span style={{ fontSize: size * 0.8, fontWeight: 900, color: dirCol, marginLeft: 8, display: "inline-block",
        transform: `translateY(${(1 - k) * (cur.dir === "up" ? 20 : -20)}px)`, opacity: k }}>{cur.dir === "up" ? "▲" : "▼"}</span> : null}
    </div>
  );
};

const CrowdEl: React.FC<{ el: El; W: number; H: number; frame: number; fps: number; touches?: boolean }> = ({ el, W, H, frame, fps, touches }) => {
  const b = boxOf(el);
  const steps: { n: number; at: number }[] = el.steps;
  const max = Math.max(...steps.map((s) => s.n));
  const cols = el.cols ?? Math.min(max, Math.max(1, Math.round(Math.sqrt(max * (b.w * 16) / (b.h * 9)))));
  const rows = Math.ceil(max / cols);
  const cw0 = (b.w * W) / cols, ch0 = (b.h * H) / rows, s = Math.min(cw0, ch0) * 0.92;
  const cw = Math.min(cw0, s * 1.15), ch = Math.min(ch0, s * 1.1);           // keep the crowd together, centred in its box
  const offX = (b.w * W - cw * cols) / 2, offY = (b.h * H - ch * rows) / 2;
  const appearAt: number[] = [];
  let prevN = 0;
  for (const st of steps) {
    for (let i = prevN; i < st.n; i++) appearAt[i] = st.at + (i - prevN) * (el.stagger ?? 2);
    prevN = Math.max(prevN, st.n);
  }
  const removeAt: number[] = [];
  for (const st of steps) if (st.n < max) for (let i = st.n; i < max; i++) if (appearAt[i] < st.at && removeAt[i] === undefined) removeAt[i] = st.at;
  return (
    <div style={{ position: "absolute", left: b.x * W, top: b.y * H, width: b.w * W, height: b.h * H }}>
      {Array.from({ length: max }, (_, i) => {
        const o = presence(frame, fps, appearAt[i], removeAt[i]);
        if (o <= 0 && !(touches && frame >= appearAt[i] && (removeAt[i] === undefined || frame < removeAt[i] + 15))) return null;
        const r = Math.floor(i / cols), c = i % cols;
        if (touches) {
          // walk in from the right (a little bounce per step), walk out to the right when they leave
          const inK = lin(frame, appearAt[i], appearAt[i] + 22);
          const outK = removeAt[i] !== undefined ? lin(frame, removeAt[i] - 10, removeAt[i] + 14) : 0;
          const walking = (inK > 0 && inK < 1) || (outK > 0 && outK < 1);
          const dx = (1 - inK) * 140 + outK * 160;
          const step = walking ? Math.abs(Math.sin((frame + i * 7) / 3)) * -7 : Math.sin((frame + i * 11) / 20) * 1.5;
          return (
            <div key={i} style={{ position: "absolute", left: offX + c * cw + (cw - s) / 2 + dx, top: offY + r * ch + (ch - s) / 2, width: s, height: s,
              opacity: Math.min(1, inK * 1.6) * (1 - outK) }}>
              <div style={{ position: "absolute", left: "25%", width: "50%", top: "88%", height: "10%", borderRadius: "50%",
                background: "radial-gradient(closest-side, rgba(20,30,45,0.3), rgba(20,30,45,0))" }} />
              <img src={assetUrl(el.src)} style={{ width: "100%", height: "100%", objectFit: "contain", transform: `translateY(${step}px) scaleX(${outK > 0 ? -1 : 1})`,
                filter: "drop-shadow(0 6px 6px rgba(20,30,45,0.2))" }} />
            </div>
          );
        }
        return <img key={i} src={assetUrl(el.src)} style={{ position: "absolute", left: offX + c * cw + (cw - s) / 2, top: offY + r * ch + (ch - s) / 2 + (1 - o) * 14,
          width: s, height: s, opacity: o, objectFit: "contain" }} />;
      })}
    </div>
  );
};

/** A table whose rows appear on their cue words and whose cells/columns light up when they are discussed. */
const TableEl: React.FC<{ el: El; P: Record<string, string>; W: number; H: number; frame: number; fps: number }> = ({ el, P, W, H, frame, fps }) => {
  const b = boxOf(el);
  const cols: string[] = el.columns;
  const rows: { cells: string[]; at: number }[] = el.rows;
  const nRows = rows.length + 1;
  const rh = (b.h * H) / nRows;
  const size = el.size ?? Math.min(30, Math.round(rh * 0.42));
  const lit = (r: number, c: number) => {
    let best = 0, tone = "band";
    for (const h of el.highlights ?? []) {
      const hit = (h.row === undefined || h.row === r) && (h.col === undefined || h.col === c);
      if (!hit || frame < h.at || (h.until !== undefined && frame > h.until)) continue;
      const k = lin(frame, h.at, h.at + 10) * (h.until !== undefined ? 1 - lin(frame, h.until - 10, h.until) : 1);
      if (k > best) { best = k; tone = h.tone ?? "band"; }
    }
    return { k: best, col: toneOf(P, tone) };
  };
  const o = presence(frame, fps, el.at ?? 0, el.until);
  return (
    <div style={{ position: "absolute", left: b.x * W, top: b.y * H, width: b.w * W, height: b.h * H, opacity: o, fontFamily: FONT }}>
      {[cols, ...rows.map((r) => r.cells)].map((cells, r) => {
        const ro = r === 0 ? 1 : presence(frame, fps, rows[r - 1].at, undefined);
        if (ro <= 0) return null;
        return (
          <div key={r} style={{ position: "absolute", left: 0, top: r * rh, width: "100%", height: rh - 4, display: "flex", opacity: ro,
            transform: `translateX(${(1 - ro) * 20}px)` }}>
            {cells.map((t, c) => {
              const h = r === 0 ? { k: 0, col: "" } : lit(r - 1, c);
              return (
                <div key={c} style={{ flex: 1, marginRight: 4, display: "flex", alignItems: "center", justifyContent: c === 0 ? "flex-start" : "center",
                  padding: "0 14px", fontSize: size, fontWeight: r === 0 ? 800 : 600, color: r === 0 ? "#ffffff" : P.ink, borderRadius: 6,
                  background: r === 0 ? P.accent : h.k > 0 ? h.col : P.box, boxShadow: h.k > 0 ? `0 0 0 ${3 * h.k}px ${P.warm}` : undefined,
                  letterSpacing: r === 0 ? 0.5 : 0, whiteSpace: "nowrap" }}>{t}</div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

const ArrowsAndMarks: React.FC<{ els: El[]; map: Map<string, El>; P: Record<string, string>; W: number; H: number; frame: number; fps: number;
  focus: any }> = ({ els, map, P, W, H, frame, fps, focus }) => (
  <svg style={{ position: "absolute", left: 0, top: 0, width: W, height: H, overflow: "visible", pointerEvents: "none" }}>
    <defs>
      {["ink", "line", "accent", "warm", "danger", "ok", "muted", "tag"].map((t) => (
        <marker key={t} id={`cb-head-${t}`} markerWidth="9" markerHeight="9" refX="6.5" refY="4.5" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L9,4.5 L0,9 z" fill={toneOf(P, t)} />
        </marker>
      ))}
    </defs>
    {els.map((el) => {
      const o = presence(frame, fps, el.at, el.until) * focusLevel(focus, el.id, frame);
      if (o <= 0) return null;
      if (el.kind === "arrow") {
        const fromGuess = el.from.id && map.has(el.from.id) ? (() => { const b = boxOf(map.get(el.from.id)); return { x: b.x + b.w / 2, y: b.y + b.h / 2 }; })() : endPoint(map, el.from);
        const toGuess = el.to.id && map.has(el.to.id) ? (() => { const b = boxOf(map.get(el.to.id)); return { x: b.x + b.w / 2, y: b.y + b.h / 2 }; })() : endPoint(map, el.to);
        const a = endPoint(map, el.from, toGuess), b = endPoint(map, el.to, fromGuess);
        const x1 = a.x * W, y1 = a.y * H, x2 = b.x * W, y2 = b.y * H;
        const bend = el.curve ?? 0;
        const mx = (x1 + x2) / 2 - (y2 - y1) * bend, my = (y1 + y2) / 2 + (x2 - x1) * bend;
        const elbow = el.elbow;   // "hv" (horizontal then vertical) or "vh"
        const ym = (y1 + y2) / 2;
        const d = elbow === "vhv" ? `M${x1},${y1} L${x1},${ym} L${x2},${ym} L${x2},${y2}`
          : elbow === "hv" ? `M${x1},${y1} L${x2},${y1} L${x2},${y2}` : elbow === "vh" ? `M${x1},${y1} L${x1},${y2} L${x2},${y2}`
          : bend ? `M${x1},${y1} Q${mx},${my} ${x2},${y2}` : `M${x1},${y1} L${x2},${y2}`;
        const len = elbow ? Math.abs(x2 - x1) + Math.abs(y2 - y1) : Math.hypot(x2 - x1, y2 - y1) * (bend ? 1.15 : 1);
        const draw = lin(frame, el.at, el.at + (el.draw_frames ?? 14));
        const tone = el.tone ?? "line";
        const pointAt = (t: number) => {
          if (elbow === "vhv") {
            const L = [Math.abs(ym - y1), Math.abs(x2 - x1), Math.abs(y2 - ym)], T = L[0] + L[1] + L[2], d0 = t * T;
            if (d0 < L[0]) return [x1, y1 + Math.sign(ym - y1) * d0];
            if (d0 < L[0] + L[1]) return [x1 + Math.sign(x2 - x1) * (d0 - L[0]), ym];
            return [x2, ym + Math.sign(y2 - ym) * (d0 - L[0] - L[1])];
          }
          if (bend) { const u = 1 - t; return [u * u * x1 + 2 * u * t * mx + t * t * x2, u * u * y1 + 2 * u * t * my + t * t * y2]; }
          return [x1 + (x2 - x1) * t, y1 + (y2 - y1) * t];
        };
        const flow = el.flow && frame >= (el.flow.at ?? el.at + 14) && (el.flow.until === undefined || frame < el.flow.until) ? el.flow : null;
        return (
          <g key={el.id} opacity={o}>
            {flow ? Array.from({ length: flow.count ?? 4 }, (_, i) => {
              const period = flow.period ?? 40;
              let t = (((frame - (flow.at ?? el.at + 14)) / period) + i / (flow.count ?? 4)) % 1;
              if (flow.reverse) t = 1 - t;
              const [px, py] = pointAt(t);
              const sz = flow.size ?? 34;
              const fade = Math.min(1, t * 6, (1 - t) * 6);
              return <image key={i} href={assetUrl(flow.src)} x={px - sz / 2} y={py - sz / 2 - 14} width={sz} height={sz} opacity={fade} />;
            }) : null}
            <path d={d} fill="none" stroke={toneOf(P, tone)} strokeWidth={el.width ?? 4} strokeLinecap="round"
              strokeDasharray={el.dashed ? "10 9" : `${len} ${len}`} strokeDashoffset={el.dashed ? 0 : len * (1 - draw)}
              markerEnd={draw > 0.95 && el.head !== false ? `url(#cb-head-${tone})` : undefined} />
            {el.label ? <text x={elbow === "hv" ? (x1 + x2) / 2 : bend ? mx : (x1 + x2) / 2} y={(elbow === "hv" ? y1 : bend ? my : (y1 + y2) / 2) - 12}
              fill={toneOf(P, el.label_tone ?? "muted")} fontSize={el.label_size ?? 22} fontWeight={700} fontFamily={FONT} textAnchor="middle"
              opacity={draw}>{el.label}</text> : null}
          </g>
        );
      }
      if (el.kind === "mark" && map.has(el.target)) {
        const b = boxOf(map.get(el.target));
        const pos = el.pos ?? "c";
        const r = (el.size ?? 0.022) * W;
        const cx = (pos === "tr" ? b.x + b.w : b.x + b.w / 2) * W + (pos === "tr" ? r * 1.2 : 0), cy = (pos === "tr" ? b.y : b.y + b.h / 2) * H;
        const k = lin(frame, el.at, el.at + 10);
        if (el.mark === "tick") {
          return <path key={el.id} d={`M${cx - r},${cy} L${cx - r * 0.25},${cy + r * 0.7} L${cx + r},${cy - r * 0.8}`} fill="none" stroke={P.ok}
            strokeWidth={r * 0.32} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={`${r * 4} ${r * 4}`} strokeDashoffset={r * 4 * (1 - k)} opacity={o} />;
        }
        return (
          <g key={el.id} opacity={o} stroke={P.danger} strokeWidth={r * 0.3} strokeLinecap="round">
            <line x1={cx - r * 0.7} y1={cy - r * 0.7} x2={cx - r * 0.7 + r * 1.4 * Math.min(1, k * 2)} y2={cy - r * 0.7 + r * 1.4 * Math.min(1, k * 2)} />
            {k > 0.5 ? <line x1={cx + r * 0.7} y1={cy - r * 0.7} x2={cx + r * 0.7 - r * 1.4 * (k * 2 - 1)} y2={cy - r * 0.7 + r * 1.4 * (k * 2 - 1)} /> : null}
          </g>
        );
      }
      if (el.kind === "highlight") {
        const b = el.target && map.has(el.target) ? boxOf(map.get(el.target)) : boxOf(el);
        const pad = el.pad ?? 0.008;
        const x = (b.x - pad) * W, y = (b.y - pad * 1.6) * H, w = (b.w + 2 * pad) * W, h = (b.h + pad * 3.2) * H;
        const tone = toneOf(P, el.tone ?? "accent");
        const k = lin(frame, el.at, el.at + 12);
        if (el.style === "band") return <rect key={el.id} x={x} y={y} width={w * k} height={h} rx={8} fill={tone} opacity={0.22 * o} />;
        const per = 2 * (w + h);
        return <rect key={el.id} x={x} y={y} width={w} height={h} rx={10} fill="none" stroke={tone} strokeWidth={4}
          strokeDasharray={el.style === "dashed" ? "12 8" : `${per} ${per}`} strokeDashoffset={el.style === "dashed" ? 0 : per * (1 - k)} opacity={o} />;
      }
      return null;
    })}
  </svg>
);


/** The block's own camera: keyframes [{at, box}] eased over 24 frames (``frames`` to change); full view by default. */
function camBox(keys: { at: number; box: Box; frames?: number }[] | undefined, frame: number): Box {
  const FULL = { x: 0, y: 0, w: 1, h: 1 };
  if (!keys || !keys.length) return FULL;
  let cur: Box = FULL;
  for (const k of keys) {
    if (frame < k.at) break;
    const t = lin(frame, k.at, k.at + (k.frames ?? 24));
    cur = { x: cur.x + (k.box.x - cur.x) * t, y: cur.y + (k.box.y - cur.y) * t, w: cur.w + (k.box.w - cur.w) * t, h: cur.h + (k.box.h - cur.h) * t };
  }
  return cur;
}

const CanvasBuild: React.FC<BlockProps> = ({ data, width, height }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const P = THEMES[data.theme ?? "paper"] ?? THEMES.paper;
  const els: El[] = data.elements ?? [];
  const map = new Map<string, El>(els.map((e) => [e.id, e]));
  const svgKinds = new Set(["arrow", "mark", "highlight"]);
  const touches = !!data.touches;
  const cam = camBox(data.cam, frame);
  const drift = touches ? 1 + 0.015 * Math.sin(frame / 140) : 1;
  const sc = Math.min(1 / cam.w, 1 / cam.h) * drift;
  const tx = -(cam.x + cam.w / 2) * width * sc + width / 2, ty = -(cam.y + cam.h / 2) * height * sc + height / 2;
  return (
    <div style={{ position: "absolute", inset: 0, background: touches ? `radial-gradient(ellipse at 50% 35%, #fffdf8 0%, ${P.bg} 55%, #efe8da 100%)` : P.bg,
      overflow: "hidden" }}>
      {touches ? <div style={{ position: "absolute", inset: -40, backgroundImage: `radial-gradient(rgba(60,70,90,0.07) 1.6px, transparent 1.6px)`,
        backgroundSize: "44px 44px", transform: `translate(${(tx * 0.15) % 44}px, ${(ty * 0.15) % 44}px)` }} /> : null}
      {data.grid ? <div style={{ position: "absolute", inset: 0, backgroundImage: `radial-gradient(${P.shadow} 1.5px, transparent 1.5px)`,
        backgroundSize: "36px 36px", opacity: 0.8 }} /> : null}
      <div style={{ position: "absolute", left: 0, top: 0, width, height, transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${sc})` }}>
      <ArrowsAndMarks els={els.filter((e) => e.kind === "arrow" || e.kind === "highlight")} map={map} P={P} W={width} H={height}
        frame={frame} fps={fps} focus={data.focus} />
      {els.filter((e) => !svgKinds.has(e.kind)).map((el) => {
        const f = focusLevel(data.focus, el.id, frame);
        const o = presence(frame, fps, el.at ?? (el.steps ? el.steps[0].at : 0), el.until) * f;
        if (o <= 0 && el.kind !== "value" && el.kind !== "crowd" && el.kind !== "table") return null;
        switch (el.kind) {
          case "icon": return <IconEl key={el.id} el={el} P={P} W={width} H={height} o={o} frame={frame} touches={touches} />;
          case "text": case "callout": return <TextEl key={el.id} el={{ ...el, style: el.kind === "callout" ? el.style ?? "note" : el.style }} P={P}
            W={width} H={height} o={o} frame={frame} />;
          case "value": return <div key={el.id} style={{ opacity: f }}><ValueEl el={el} P={P} W={width} H={height} frame={frame} fps={fps} touches={touches} /></div>;
          case "crowd": return <div key={el.id} style={{ opacity: f }}><CrowdEl el={el} W={width} H={height} frame={frame} fps={fps} touches={touches} /></div>;
          case "table": return <div key={el.id} style={{ opacity: f }}><TableEl el={el} P={P} W={width} H={height} frame={frame} fps={fps} /></div>;
          default: return null;
        }
      })}
      <ArrowsAndMarks els={els.filter((e) => e.kind === "mark")} map={map} P={P} W={width} H={height} frame={frame} fps={fps} focus={data.focus} />
      </div>
      {touches ? <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 220px rgba(80,60,30,0.16)", pointerEvents: "none" }} /> : null}
    </div>
  );
};

registerBlock("canvas_build", CanvasBuild);

// curve_story: a schematic graph that tells a story step by step (asset intake, economy batch, 27 Oct 2026).
//
// Axes with names (no clutter), curves that draw themselves, a dot that walks along a curve to the x values the
// narration names (with dashed drop lines to both axes and the values shown), vertical/horizontal guide lines
// (a natural rate, a target), shaded bands (short run, a gap), a curve that shifts (draw the new one, fade the old
// one with ``until``) and short notes. Economics needs exactly this: Phillips curve and NAIRU, demand and supply,
// AD-AS, the business cycle, Laffer, Lorenz. Curves arrive as points from Python (an adapter or the director's
// numbers), so the block never invents a shape. Coordinates of notes are fractions of the block.


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
