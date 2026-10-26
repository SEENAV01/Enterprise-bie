// The 2D grammar blocks (Task 046, Part B): the L3 overlays and panels the visual grammar asks for, drawn with HTML and SVG
// on the dark field, in BIE's one style (one accent per concept, VG-09).
//   kinetic_caption  B-08: the spoken words on top, word by word, the English terms in the accent, the Hindi in white;
//                    the half after "yaani" marked (B-05)
//   board_build      B-07: the "A → B" board that stays and fills, one line per member
//   mnemonic_card    the memory beat: a card with the trick, line by line
//   concept_arrow    B-06: a name and its reason as A → B, with the why under the arrow
//   split_compare    VG-07: two things side by side in the same slots (text panels, or two cell worlds by member)
//   scale_compare    VG-04: a size against a thing the learner knows, as bars that grow
//   flow_arrows      VG-08: arrowheads travelling along a path (magma, water, ions, mucus) over anything
//   graph_plot       VG-06: a graph that draws itself as a lit line, the tangent moving along it
//   timeline         VG-10: a lit timeline with nodes that light up in turn (free "when" labels; timeline_build takes dates)
import React from "react";
import { scaleLinear } from "d3";
import { getBlock, registerBlock, BlockProps } from "../registry";
import { C, FONT, Badge, ramp, useRel } from "./common";
import { ACCENT, Member } from "./benchmark";

const WORD = /[A-Za-z][A-Za-z’'\-]*|[0-9][0-9.,%]*|[ऀ-ॿ][ऀ-ॿ\u200c\u200d]*|[^\s0-9A-Za-zऀ-ॿ]+/g;
const YAANI = /^(यानी|यानि|मतलब|अर्थात|yaani|yani|matlab)$/i;

const KineticCaption: React.FC<BlockProps> = ({ data, at, until, width, height }) => {
  const { rel, fps } = useRel(at);
  const text: string = data.text || "";
  const accent: string = data.accent || C.accent;
  const terms = new Set<string>(((data.terms || []) as string[]).map((t) => t.toLowerCase()));
  const raw = text.match(WORD) || [];
  const tokens: string[] = [];                      // punctuation rides on the word before it ("है:" not "है :")
  for (const t of raw) {
    if (!/[0-9A-Za-zऀ-ॿ]/.test(t) && tokens.length) tokens[tokens.length - 1] += t;
    else tokens.push(t);
  }
  const length = Math.max(1, (until ?? at + (data.seconds ?? 3) * fps) - at);
  const per = (length * (data.reveal ?? 0.7)) / Math.max(1, tokens.length);
  let afterYaani = false;
  const size = data.size || (text.length > 90 ? 38 : text.length > 60 ? 44 : 50);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: data.position === "bottom" ? undefined : 28, bottom: data.position === "bottom" ? 36 : undefined,
      padding: "0 70px", fontFamily: FONT, textAlign: "center", lineHeight: 1.3, textShadow: "0 2px 10px rgba(0,0,0,0.95)" }}>
      <div style={{ display: "inline-block", background: "rgba(6,18,28,0.55)", borderRadius: 16, padding: "10px 26px", maxWidth: width - 140 }}>
        {tokens.map((tok, i) => {
          const o = ramp(rel, i * per, 5);
          const word = tok.replace(/[^A-Za-zऀ-ॿ\u200c\u200d’'\-]+$/, "");
          const low = word.toLowerCase().replace(/[’']s$/, "");
          const isTerm = /^[a-z]/i.test(word) && (terms.size === 0 || terms.has(low) || terms.has(word.toLowerCase()));
          const el = (
            <span key={i} style={{ display: "inline-block", fontSize: afterYaani ? size * 0.9 : size, fontWeight: isTerm ? 800 : 600,
              color: isTerm ? accent : afterYaani ? "#dfe9ee" : C.ink, opacity: o, transform: `translateY(${(1 - o) * 14}px)`,
              marginRight: 12, textDecoration: YAANI.test(word) ? `underline ${accent}` : "none" }}>{tok}</span>
          );
          if (YAANI.test(word)) afterYaani = true;
          return el;
        })}
      </div>
    </div>
  );
};

type Row = { a: string; b: string; at: number; accent?: string };

const BoardBuild: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const rows = (data.rows || []) as Row[];
  const o = ramp(rel, 0, 12);
  const compact = !!data.compact;
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT, color: C.ink, opacity: o, transform: `translateY(${(1 - o) * 20}px)` }}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(8,28,40,0.88)", border: `2px solid ${C.line}`, borderRadius: 22,
        boxShadow: "0 20px 60px rgba(0,0,0,0.45)", padding: compact ? 18 : 28, boxSizing: "border-box", overflow: "hidden" }}>
        {data.title ? <div style={{ fontSize: compact ? 26 : 32, fontWeight: 800, color: C.accent, marginBottom: 10 }}>{data.title}</div> : null}
        {rows.map((r, i) => {
          const ro = ramp(rel, r.at, 12);
          const accent = r.accent || C.warm;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, margin: compact ? "6px 0" : "12px 0", opacity: 0.18 + 0.82 * ro,
              transform: `translateX(${(1 - ro) * 30}px)`, fontSize: compact ? 24 : 30 }}>
              <span style={{ fontWeight: 800, color: accent, minWidth: "38%" }}>{r.a}</span>
              <svg width={54} height={22} style={{ flex: "none" }}><line x1={2} y1={11} x2={2 + 44 * ro} y2={11} stroke={accent} strokeWidth={4} />
                <path d={`M${2 + 44 * ro - 10},4 L${2 + 44 * ro},11 L${2 + 44 * ro - 10},18`} fill="none" stroke={accent} strokeWidth={4} /></svg>
              <span style={{ fontWeight: 600 }}>{r.b}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const MnemonicCard: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const lines = (data.lines || []) as string[];
  const o = ramp(rel, 0, 14);
  const accent = data.accent || C.warm;
  const per = ((data.seconds ?? 3) * fps * 0.7) / Math.max(1, lines.length);
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT }}>
      <div style={{ width: Math.min(width - 80, 1180), background: "linear-gradient(160deg, rgba(40,28,10,0.95), rgba(8,28,40,0.95))",
        border: `4px solid ${accent}`, borderRadius: 30, padding: "34px 48px", boxShadow: `0 0 60px ${accent}66`, opacity: o,
        transform: `scale(${0.92 + 0.08 * o})`, color: C.ink }}>
        <div style={{ fontSize: 26, letterSpacing: 4, color: accent, fontWeight: 800 }}>{data.kicker || "याद रखो"}</div>
        {data.title ? <div style={{ fontSize: 46, fontWeight: 800, margin: "8px 0 14px" }}>{data.title}</div> : null}
        {lines.map((l, i) => {
          const lo = ramp(rel, 10 + i * per, 10);
          return <div key={i} style={{ fontSize: 34, margin: "8px 0", opacity: lo, transform: `translateX(${(1 - lo) * 24}px)`, display: "flex", gap: 16 }}>
            <span style={{ color: accent, fontWeight: 800 }}>{i + 1}.</span><span>{l}</span></div>;
        })}
      </div>
    </div>
  );
};

const ConceptArrow: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const o = ramp(rel, 0, 10), draw = ramp(rel, 6, 18);
  const accent = data.accent || C.warm;
  const bottom = data.position !== "top";
  return (
    <div style={{ position: "absolute", left: 60, right: 60, [bottom ? "bottom" : "top"]: 120, fontFamily: FONT, color: C.ink, opacity: o } as any}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 22 }}>
        <div style={{ fontSize: 40, fontWeight: 800, background: C.panel, border: `3px solid ${accent}`, borderRadius: 16, padding: "12px 26px" }}>{data.from}</div>
        <svg width={170} height={40}><line x1={4} y1={20} x2={4 + 150 * draw} y2={20} stroke={accent} strokeWidth={6} />
          <path d={`M${4 + 150 * draw - 18},8 L${4 + 150 * draw},20 L${4 + 150 * draw - 18},32`} fill="none" stroke={accent} strokeWidth={6} /></svg>
        <div style={{ fontSize: 40, fontWeight: 800, background: C.panel, border: `3px solid ${accent}`, borderRadius: 16, padding: "12px 26px", opacity: draw }}>{data.to}</div>
      </div>
      {data.reason ? <div style={{ textAlign: "center", fontSize: 30, color: "#dfe9ee", marginTop: 14, opacity: ramp(rel, 20, 12) }}>
        <span style={{ color: accent, fontWeight: 800 }}>क्यों? </span>{data.reason}</div> : null}
    </div>
  );
};

type Side = { title: string; lines?: string[]; member?: Member; accent?: string; slots?: string[] };

const SplitCompare: React.FC<BlockProps> = ({ data, at, until, width, height }) => {
  const { rel, fps } = useRel(at);
  const left = data.left as Side, right = data.right as Side;
  const o = ramp(rel, 0, 12);
  const slots = (data.slots || []) as string[];
  const half = Math.floor((width - 36) / 2);
  const panel = (side: Side, i: number) => {
    const accent = side.accent || (side.member ? ACCENT[side.member] : i ? C.warm : C.accent);
    const dx = (1 - o) * (i ? 60 : -60);
    return (
      <div key={i} style={{ position: "absolute", left: i ? half + 36 : 0, top: 0, width: half, height, transform: `translateX(${dx}px)`, opacity: o }}>
        <div style={{ position: "absolute", inset: 0, border: `3px solid ${accent}`, borderRadius: 24, background: "rgba(8,28,40,0.55)", overflow: "hidden" }}>
          {side.member ? <div style={{ position: "absolute", inset: 0 }}>
            <WorldHalf member={side.member} at={at} until={until} width={half} height={height} /></div> : null}
          <div style={{ position: "absolute", left: 24, top: 18, fontFamily: FONT, fontSize: 36, fontWeight: 800, color: accent, textShadow: "0 2px 8px #000" }}>{side.title}</div>
          <div style={{ position: "absolute", left: 24, right: 24, bottom: 22, fontFamily: FONT, color: C.ink }}>
            {(side.lines || []).map((l, k) => {
              const lo = ramp(rel, 10 + k * 14, 10);
              return <div key={k} style={{ fontSize: 28, margin: "6px 0", opacity: lo, display: "flex", gap: 12, background: "rgba(6,18,28,0.6)", borderRadius: 10, padding: "4px 12px" }}>
                {slots[k] ? <span style={{ color: accent, fontWeight: 800, minWidth: 150 }}>{slots[k]}</span> : null}<span>{l}</span></div>;
            })}
          </div>
        </div>
      </div>
    );
  };
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {panel(left, 0)}
      <div style={{ position: "absolute", left: half + 10, top: height * 0.1, width: 16, height: height * 0.8, borderRadius: 8, background: C.line, opacity: o }} />
      {panel(right, 1)}
    </div>
  );
};

// a cell world inside half the frame (split_compare of two members): the same block, its own camera
const WorldHalf: React.FC<{ member: Member; at: number; until?: number; width: number; height: number }> = ({ member, at, until, width, height }) => {
  const Block = getBlock("cell_sheet");
  if (!Block) return null;
  return <Block data={{ member, shots: [{ at: 0, member, camera: { move: "establish" }, focus: "cell" },
    { at: 2, member, camera: { move: "orbit", seconds: 4 }, focus: "cell" }] }} at={at} until={until} width={width} height={height} id={`half-${member}`} />;
};

const ScaleCompare: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const items = (data.items || []) as { label: string; value: number; unit?: string; known?: boolean }[];
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 1e-9);
  const o = ramp(rel, 0, 12);
  const accent = data.accent || C.accent;
  return (
    <div style={{ position: "absolute", left: 60, right: 60, bottom: 90, fontFamily: FONT, color: C.ink, opacity: o }}>
      <div style={{ background: C.panel, border: `2px solid ${C.line}`, borderRadius: 22, padding: "22px 30px" }}>
        {data.title ? <div style={{ fontSize: 32, fontWeight: 800, color: accent, marginBottom: 12 }}>{data.title}</div> : null}
        {items.map((it, i) => {
          const g = ramp(rel, 8 + i * 16, 36);
          const share = Math.abs(it.value) / max;
          return (
            <div key={i} style={{ margin: "10px 0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 28 }}>
                <span style={{ fontWeight: it.known ? 600 : 800 }}>{it.label}{it.known ? " (जाना-पहचाना)" : ""}</span>
                <span style={{ color: C.warm, fontWeight: 800 }}>{(it.value * g).toLocaleString("en-IN", { maximumFractionDigits: 2 })}{it.unit ? " " + it.unit : ""}</span>
              </div>
              <div style={{ height: 26, background: "rgba(255,255,255,0.08)", borderRadius: 8, marginTop: 6 }}>
                <div style={{ height: "100%", width: `${Math.max(1, 100 * share * g)}%`, background: it.known ? C.muted : accent, borderRadius: 8, boxShadow: it.known ? "none" : `0 0 18px ${accent}` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const FlowArrows: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const path = (data.path || [{ x: 0.1, y: 0.5 }, { x: 0.9, y: 0.5 }]) as { x: number; y: number }[];
  const pts = path.map((p) => ({ x: p.x * width, y: p.y * height }));
  const n = data.arrows ?? 7, period = (data.seconds ?? 2.6) * fps;
  const accent = data.accent || C.warm;
  const o = ramp(rel, 0, 10);
  const seg: number[] = [];
  let total = 0;
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y); seg.push(d); total += d; }
  const along = (t: number) => {
    let d = (((t % 1) + 1) % 1) * total;
    for (let i = 0; i < seg.length; i++) {
      if (d <= seg[i]) { const k = seg[i] ? d / seg[i] : 0; const a = pts[i], b = pts[i + 1];
        return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, angle: Math.atan2(b.y - a.y, b.x - a.x) }; }
      d -= seg[i];
    }
    return { x: pts[pts.length - 1].x, y: pts[pts.length - 1].y, angle: 0 };
  };
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" ");
  return (
    <svg style={{ position: "absolute", inset: 0, width, height, opacity: o, overflow: "visible" }}>
      <path d={d} fill="none" stroke={accent} strokeOpacity={0.3} strokeWidth={10} strokeLinecap="round" strokeDasharray="4 18" />
      {Array.from({ length: n }).map((_, i) => {
        const p = along(rel / period + i / n);
        return <g key={i} transform={`translate(${p.x},${p.y}) rotate(${(p.angle * 180) / Math.PI})`}>
          <path d="M-22,-14 L10,0 L-22,14 L-12,0 Z" fill={accent} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} /></g>;
      })}
      {data.label ? <text x={pts[0].x} y={pts[0].y - 28} fill={C.ink} fontSize={30} fontFamily={FONT} fontWeight={700}>{data.label}</text> : null}
    </svg>
  );
};

const GraphPlot: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const xs: number[] = data.x, ys: number[] = data.y;
  const pad = { l: 120, r: 60, t: 90, b: 90 };
  const sx = scaleLinear().domain(data.x_domain || [Math.min(...xs), Math.max(...xs)]).range([pad.l, width - pad.r]);
  const sy = scaleLinear().domain(data.y_domain || [Math.min(...ys), Math.max(...ys)]).nice().range([height - pad.b, pad.t]);
  const accent = data.accent || C.accent;
  const draw = ramp(rel, (data.draw_start ?? 0.3) * fps, (data.draw_seconds ?? 2.5) * fps);
  const reach = (xs.length - 1) * draw, whole = Math.floor(reach), part = reach - whole;
  const pts: [number, number][] = xs.slice(0, whole + 1).map((x, i) => [sx(x), sy(ys[i])]);
  if (part > 0 && whole + 1 < xs.length) pts.push([sx(xs[whole] + (xs[whole + 1] - xs[whole]) * part), sy(ys[whole] + (ys[whole + 1] - ys[whole]) * part)]);
  const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0]},${p[1]}`).join(" ");
  // the tangent (VG-06): slides along the drawn curve after the draw, from tangent_from to tangent_to (fractions of the x range)
  const tangentOn = ramp(rel, (data.draw_start ?? 0.3) * fps + (data.draw_seconds ?? 2.5) * fps, 10);
  const tf = data.tangent_from ?? 0.2, tt = data.tangent_to ?? 0.8;
  const slide = ramp(rel, (data.draw_start ?? 0.3) * fps + (data.draw_seconds ?? 2.5) * fps, (data.tangent_seconds ?? 2.5) * fps);
  const k = Math.min(xs.length - 2, Math.max(0, Math.floor((tf + (tt - tf) * slide) * (xs.length - 1))));
  const slope = (ys[k + 1] - ys[k]) / ((xs[k + 1] - xs[k]) || 1e-9);
  const cx = sx(xs[k]), cy = sy(ys[k]);
  const dx = 160, dy = -slope * dx * ((sy(1) - sy(0)) / (sx(1) - sx(0)) || 1) * -1;
  const o = ramp(rel, 0, 10);
  return (
    <svg style={{ position: "absolute", inset: 0, width, height, opacity: o, fontFamily: FONT }}>
      <defs><filter id={`glow-${at}`}><feGaussianBlur stdDeviation="6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
      <line x1={pad.l} y1={height - pad.b} x2={width - pad.r} y2={height - pad.b} stroke={C.muted} strokeWidth={3} />
      <line x1={pad.l} y1={pad.t} x2={pad.l} y2={height - pad.b} stroke={C.muted} strokeWidth={3} />
      {sx.ticks(6).map((t) => <text key={"x" + t} x={sx(t)} y={height - pad.b + 36} fill={C.muted} fontSize={24} textAnchor="middle">{t}</text>)}
      {sy.ticks(5).map((t) => <text key={"y" + t} x={pad.l - 16} y={sy(t) + 8} fill={C.muted} fontSize={24} textAnchor="end">{t}</text>)}
      {data.x_label ? <text x={(pad.l + width - pad.r) / 2} y={height - 24} fill={C.ink} fontSize={28} textAnchor="middle" fontWeight={700}>{data.x_label}</text> : null}
      {data.y_label ? <text x={30} y={pad.t - 30} fill={C.ink} fontSize={28} fontWeight={700}>{data.y_label}</text> : null}
      {data.title ? <text x={pad.l} y={48} fill={C.ink} fontSize={36} fontWeight={800}>{data.title}</text> : null}
      <path d={line} fill="none" stroke={accent} strokeWidth={7} strokeLinecap="round" filter={`url(#glow-${at})`} />
      {tangentOn > 0 && pts.length > 1 ? <g opacity={tangentOn}>
        <line x1={cx - dx} y1={cy - dy} x2={cx + dx} y2={cy + dy} stroke={C.warm} strokeWidth={5} />
        <circle cx={cx} cy={cy} r={12} fill={C.warm} />
        <text x={cx + 20} y={cy - 20} fill={C.warm} fontSize={28} fontWeight={800}>{data.tangent_label || `slope ${slope.toFixed(2)}`}</text></g> : null}
    </svg>
  );
};

const LitTimeline: React.FC<BlockProps> = ({ data, at, width, height }) => {
  const { rel, fps } = useRel(at);
  const events = (data.events || []) as { when: string; label: string; at?: number }[];
  const accent = data.accent || C.warm;
  const o = ramp(rel, 0, 10);
  const y = height * 0.58, x0 = 110, x1 = width - 110;
  const grow = ramp(rel, 0, 0.8 * fps);
  const per = ((data.seconds ?? 3) * fps * 0.8) / Math.max(1, events.length);
  return (
    <div style={{ position: "absolute", inset: 0, fontFamily: FONT, opacity: o }}>
      {data.title ? <div style={{ position: "absolute", left: 60, top: 34, fontSize: 40, fontWeight: 800, color: C.ink }}>{data.title}</div> : null}
      <svg style={{ position: "absolute", inset: 0, width, height, overflow: "visible" }}>
        <defs><filter id={`tl-${at}`}><feGaussianBlur stdDeviation="8" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
        <line x1={x0} y1={y} x2={x0 + (x1 - x0) * grow} y2={y} stroke={accent} strokeWidth={6} filter={`url(#tl-${at})`} />
        {events.map((e, i) => {
          const px = x0 + ((x1 - x0) * (i + 0.5)) / events.length;
          const on = ramp(rel, e.at ?? 12 + i * per, 10);
          const up = i % 2 === 0;
          return <g key={i} opacity={on}>
            <circle cx={px} cy={y} r={16 + 6 * on} fill={accent} filter={`url(#tl-${at})`} />
            <line x1={px} y1={y} x2={px} y2={y + (up ? -70 : 70)} stroke={C.line} strokeWidth={3} />
            <text x={px} y={y + (up ? -92 : 108)} fill={C.warm} fontSize={30} fontWeight={800} textAnchor="middle" fontFamily={FONT}>{e.when}</text>
            <text x={px} y={y + (up ? -56 : 144)} fill={C.ink} fontSize={26} textAnchor="middle" fontFamily={FONT}>{e.label}</text>
          </g>;
        })}
      </svg>
    </div>
  );
};

registerBlock("kinetic_caption", KineticCaption);
registerBlock("board_build", BoardBuild);
registerBlock("mnemonic_card", MnemonicCard);
registerBlock("concept_arrow", ConceptArrow);
registerBlock("split_compare", SplitCompare);
registerBlock("scale_compare", ScaleCompare);
registerBlock("flow_arrows", FlowArrows);
registerBlock("graph_plot", GraphPlot);
registerBlock("timeline", LitTimeline);
