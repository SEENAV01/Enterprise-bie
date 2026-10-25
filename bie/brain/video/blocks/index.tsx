// BIE's animation block library (Remotion API). A scene is choreography data: layers placed in a 1920x1080
// "world", camera keyframes that zoom into any world box (for example a region of an illustration), and a
// start frame for every layer. Every block animates itself from its start frame, so the AI only decides
// what appears, where and on which spoken word; the look stays consistent across thousands of lessons.
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { getBlock } from "./registry";

export const W = 1920;
export const H = 1080;
export const C = {
  bg0: "#06121c", bg1: "#0b2433", ink: "#f2f6f8", muted: "#9fb3bf", accent: "#38d3c3", warm: "#ffb35c",
  danger: "#ff6b6b", line: "rgba(255,255,255,0.18)", panel: "rgba(8,28,40,0.82)",
};
export const FONT = '"Noto Sans", "Noto Sans Devanagari", Inter, "FreeSans", sans-serif';

export type Box = { x: number; y: number; w: number; h: number };      // 0..1 of the world (or of a parent layer)
export type Pt = { x: number; y: number };
export type Anchor = { layer: string; point: Pt };                       // a point inside another layer's box

export type Layer =
  | { id: string; type: "image"; at: number; until?: number; box: Box; src: string; fit?: "contain" | "cover"; credit?: string }
  | { id: string; type: "title"; at: number; until?: number; box: Box; title: string; subtitle?: string }
  | { id: string; type: "label"; at: number; until?: number; box: Box; text: string; anchor?: Anchor; tone?: "accent" | "warm" }
  | { id: string; type: "highlight"; at: number; until?: number; layer: string; region: Box; shape?: "ring" | "rect"; tone?: "accent" | "warm" | "danger" }
  | { id: string; type: "flow"; at: number; until?: number; layer: string; path: Pt[]; particles?: number; seconds?: number; tone?: "accent" | "warm" }
  | { id: string; type: "steps"; at: number; until?: number; box: Box; title?: string; steps: { label: string; detail?: string; at: number }[] }
  | { id: string; type: "timeline"; at: number; until?: number; box: Box; events: { when: string; label: string; at: number }[] }
  | { id: string; type: "scale"; at: number; until?: number; box: Box; title?: string; items: { label: string; value: number; unit?: string; at: number }[] }
  | { id: string; type: "table"; at: number; until?: number; box: Box; columns: string[]; rows: { label: string; cells: string[] }[]; focus?: { column: number; at: number }[] }
  | { id: string; type: "arrow"; at: number; until?: number; from: Anchor; to: Anchor; label?: string }
  | { id: string; type: "question"; at: number; until?: number; text: string }
  // A toolbox block (Task 046a): "block" names a component registered by the toolbox bundle (three.js, KaTeX, D3,
  // 3Dmol.js, Mol*, matter.js, cannon-es ...); "data" is what a BIE compute adapter made for it.
  | { id: string; type: "block"; at: number; until?: number; box: Box; block: string; data: any };

// A camera key shows a world box, or a region of a layer (for example the nucleus inside an illustration).
export type CameraKey = { at: number; box?: Box; layer?: string; region?: Box; frames?: number };
export type SceneSpec = { id: string; duration: number; layers: Layer[]; camera: CameraKey[]; captions?: { at: number; until: number; text: string }[] };

const px = (b: Box) => ({ left: b.x * W, top: b.y * H, width: b.w * W, height: b.h * H });
const ease = Easing.inOut(Easing.cubic);

function appear(frame: number, at: number, until?: number, fps = 30) {
  if (frame < at) return 0;
  const inn = spring({ frame: frame - at, fps, config: { damping: 18, stiffness: 110 } });
  const out = until === undefined ? 1 : interpolate(frame, [until - 10, until], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return Math.max(0, Math.min(inn, out));
}

export function anchorPoint(layers: Layer[], anchor: Anchor): Pt {
  const parent = layers.find((l) => l.id === anchor.layer) as any;
  const box: Box = parent && parent.box ? parent.box : { x: 0, y: 0, w: 1, h: 1 };
  return { x: box.x + anchor.point.x * box.w, y: box.y + anchor.point.y * box.h };
}

function regionInLayer(layers: Layer[], layerId: string, region: Box): Box {
  const parent = layers.find((l) => l.id === layerId) as any;
  const box: Box = parent && parent.box ? parent.box : { x: 0, y: 0, w: 1, h: 1 };
  return { x: box.x + region.x * box.w, y: box.y + region.y * box.h, w: region.w * box.w, h: region.h * box.h };
}

// Camera: the screen shows one world box; moving between keyframes eases position and zoom together.
const FULL: Box = { x: 0, y: 0, w: 1, h: 1 };

export function keyBox(layers: Layer[], k: CameraKey): Box {
  let box = k.box ?? FULL;
  if (k.layer) box = regionInLayer(layers, k.layer, k.region ?? FULL);
  // Keep the screen's 16:9 shape: grow the shorter side around the centre, with a little breathing room.
  const pad = 1.12;
  let w = box.w * pad, h = box.h * pad;
  if (w / h > 1) h = Math.max(h, w); else w = Math.max(w, h);
  w = Math.min(w, 1); h = Math.min(h, 1);
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  return { x: Math.min(Math.max(cx - w / 2, 0), 1 - w), y: Math.min(Math.max(cy - h / 2, 0), 1 - h), w, h };
}

export function cameraBox(camera: CameraKey[], frame: number, layers: Layer[] = []): Box {
  const keys = camera.length ? camera : [{ at: 0, box: FULL }];
  let current = keys[0].box && !keys[0].layer ? keys[0].box : keyBox(layers, keys[0]);
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    const span = k.frames ?? 36;
    if (frame <= k.at) break;
    const target = k.layer ? keyBox(layers, k) : (k.box ?? FULL);
    const t = interpolate(frame, [k.at, k.at + span], [0, 1], { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const prev = current;
    current = { x: prev.x + (target.x - prev.x) * t, y: prev.y + (target.y - prev.y) * t, w: prev.w + (target.w - prev.w) * t,
      h: prev.h + (target.h - prev.h) * t };
  }
  return current;
}

const Backdrop: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 90) * 30;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at ${50 + drift / 10}% 40%, ${C.bg1} 0%, ${C.bg0} 70%)` }}>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.75)" }} />
    </AbsoluteFill>
  );
};

const ImageLayer: React.FC<{ l: Extract<Layer, { type: "image" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const src = l.src.startsWith("http") || l.src.startsWith("data:") ? l.src : staticFile(l.src);
  return (
    <div style={{ position: "absolute", ...px(l.box), opacity: o, transform: `scale(${0.96 + 0.04 * o})`,
      filter: "drop-shadow(0 18px 40px rgba(0,0,0,0.45))" }}>
      <Img src={src} style={{ width: "100%", height: "100%", objectFit: l.fit ?? "contain" }} />
      {l.credit ? <div style={{ position: "absolute", right: 6, bottom: -26, fontSize: 16, color: C.muted, fontFamily: FONT }}>{l.credit}</div> : null}
    </div>
  );
};

const TitleLayer: React.FC<{ l: Extract<Layer, { type: "title" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  return (
    <div style={{ position: "absolute", ...px(l.box), opacity: o, transform: `translateY(${(1 - o) * 30}px)`, fontFamily: FONT,
      color: C.ink, display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <div style={{ fontSize: 76, fontWeight: 800, letterSpacing: -1, lineHeight: 1.05 }}>{l.title}</div>
      {l.subtitle ? <div style={{ fontSize: 36, color: C.accent, marginTop: 18 }}>{l.subtitle}</div> : null}
    </div>
  );
};

const LabelLayer: React.FC<{ l: Extract<Layer, { type: "label" }>; layers: Layer[] }> = ({ l, layers }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const color = l.tone === "warm" ? C.warm : C.accent;
  const box = px(l.box);
  const draw = interpolate(frame, [l.at, l.at + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  let line = null;
  if (l.anchor) {
    const p = anchorPoint(layers, l.anchor);
    const tx = p.x * W, ty = p.y * H;
    const sx = Math.min(Math.max(tx, box.left), box.left + box.width), sy = box.top + box.height / 2;
    line = (
      <svg style={{ position: "absolute", inset: 0, width: W, height: H, overflow: "visible", opacity: o }}>
        <line x1={sx} y1={sy} x2={sx + (tx - sx) * draw} y2={sy + (ty - sy) * draw} stroke={color} strokeWidth={4} />
        <circle cx={tx} cy={ty} r={10 * draw} fill={color} stroke="#06121c" strokeWidth={3} />
      </svg>
    );
  }
  return (
    <>
      {line}
      <div style={{ position: "absolute", ...box, opacity: o, display: "flex", alignItems: "center" }}>
        <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 700, color: C.ink, background: C.panel, border: `3px solid ${color}`,
          borderRadius: 14, padding: "10px 18px", boxShadow: "0 10px 30px rgba(0,0,0,0.35)" }}>{l.text}</div>
      </div>
    </>
  );
};

const HighlightLayer: React.FC<{ l: Extract<Layer, { type: "highlight" }>; layers: Layer[] }> = ({ l, layers }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const r = regionInLayer(layers, l.layer, l.region);
  const color = l.tone === "warm" ? C.warm : l.tone === "danger" ? C.danger : C.accent;
  const pulse = 1 + 0.06 * Math.sin((frame - l.at) / 5);
  const b = px(r);
  return (
    <div style={{ position: "absolute", ...b, opacity: o, transform: `scale(${pulse})`, border: `6px solid ${color}`,
      borderRadius: l.shape === "rect" ? 18 : "50%", boxShadow: `0 0 40px ${color}` }} />
  );
};

function along(path: Pt[], t: number): Pt {
  if (path.length === 1) return path[0];
  const seg: number[] = [];
  let total = 0;
  for (let i = 1; i < path.length; i++) { const d = Math.hypot(path[i].x - path[i - 1].x, path[i].y - path[i - 1].y); seg.push(d); total += d; }
  let d = ((t % 1) + 1) % 1 * total;
  for (let i = 0; i < seg.length; i++) {
    if (d <= seg[i]) { const k = seg[i] ? d / seg[i] : 0; return { x: path[i].x + (path[i + 1].x - path[i].x) * k, y: path[i].y + (path[i + 1].y - path[i].y) * k }; }
    d -= seg[i];
  }
  return path[path.length - 1];
}

const FlowLayer: React.FC<{ l: Extract<Layer, { type: "flow" }>; layers: Layer[] }> = ({ l, layers }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const o = appear(frame, l.at, l.until);
  const parent = layers.find((x) => x.id === l.layer) as any;
  const box: Box = parent && parent.box ? parent.box : { x: 0, y: 0, w: 1, h: 1 };
  const world = l.path.map((p) => ({ x: (box.x + p.x * box.w) * W, y: (box.y + p.y * box.h) * H }));
  const color = l.tone === "warm" ? C.warm : C.accent;
  const n = l.particles ?? 6;
  const period = (l.seconds ?? 3) * fps;
  const draw = interpolate(frame, [l.at, l.at + 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const d = world.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" ");
  return (
    <svg style={{ position: "absolute", inset: 0, width: W, height: H, opacity: o, overflow: "visible" }}>
      <path d={d} fill="none" stroke={color} strokeOpacity={0.35} strokeWidth={8} strokeLinecap="round" pathLength={1}
        strokeDasharray={1} strokeDashoffset={1 - draw} />
      {Array.from({ length: n }).map((_, i) => {
        const p = along(world, (frame - l.at) / period + i / n);
        return <circle key={i} cx={p.x} cy={p.y} r={11} fill={color} style={{ filter: `drop-shadow(0 0 10px ${color})` }} />;
      })}
    </svg>
  );
};

const Panel: React.FC<{ box: Box; o: number; children: React.ReactNode }> = ({ box, o, children }) => (
  <div style={{ position: "absolute", ...px(box), opacity: o, transform: `translateY(${(1 - o) * 24}px)`, background: C.panel,
    border: `2px solid ${C.line}`, borderRadius: 22, padding: 28, fontFamily: FONT, color: C.ink, boxSizing: "border-box",
    boxShadow: "0 20px 60px rgba(0,0,0,0.4)", overflow: "hidden" }}>{children}</div>
);

const StepsLayer: React.FC<{ l: Extract<Layer, { type: "steps" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const active = l.steps.filter((s) => frame >= s.at).length - 1;
  return (
    <Panel box={l.box} o={o}>
      {l.title ? <div style={{ fontSize: 34, fontWeight: 800, color: C.accent, marginBottom: 16 }}>{l.title}</div> : null}
      {l.steps.map((s, i) => {
        const so = appear(frame, s.at);
        return (
          <div key={i} style={{ display: "flex", gap: 18, alignItems: "flex-start", margin: "10px 0", opacity: 0.25 + 0.75 * so }}>
            <div style={{ minWidth: 48, height: 48, borderRadius: 24, background: i === active ? C.accent : "transparent",
              border: `3px solid ${C.accent}`, color: i === active ? C.bg0 : C.accent, display: "flex", alignItems: "center",
              justifyContent: "center", fontWeight: 800, fontSize: 26 }}>{i + 1}</div>
            <div><div style={{ fontSize: 32, fontWeight: 700 }}>{s.label}</div>
              {s.detail ? <div style={{ fontSize: 24, color: C.muted }}>{s.detail}</div> : null}</div>
          </div>
        );
      })}
    </Panel>
  );
};

const TimelineLayer: React.FC<{ l: Extract<Layer, { type: "timeline" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  return (
    <Panel box={l.box} o={o}>
      <div style={{ position: "relative", height: "100%", display: "flex", alignItems: "stretch" }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: "50%", height: 6, marginTop: -3, background: C.line, borderRadius: 3 }} />
        {l.events.map((e, i) => {
          const eo = appear(frame, e.at);
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "space-between",
              opacity: eo, transform: `translateY(${(1 - eo) * 16}px)`, textAlign: "center", padding: "0 8px" }}>
              <div style={{ fontSize: 30, fontWeight: 800, color: C.warm, flex: 1, display: "flex", alignItems: "flex-end", paddingBottom: 14 }}>{e.when}</div>
              <div style={{ width: 28, height: 28, borderRadius: 14, background: C.accent, boxShadow: `0 0 18px ${C.accent}`, zIndex: 1 }} />
              <div style={{ fontSize: 26, flex: 1, paddingTop: 14 }}>{e.label}</div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
};

const ScaleLayer: React.FC<{ l: Extract<Layer, { type: "scale" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const max = Math.max(...l.items.map((i) => Math.abs(i.value)), 1);
  return (
    <Panel box={l.box} o={o}>
      {l.title ? <div style={{ fontSize: 32, fontWeight: 800, color: C.accent, marginBottom: 18 }}>{l.title}</div> : null}
      {l.items.map((it, i) => {
        const g = interpolate(frame, [it.at, it.at + 40], [0, 1], { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <div key={i} style={{ margin: "14px 0" }}>
            <div style={{ fontSize: 28, display: "flex", justifyContent: "space-between" }}><span>{it.label}</span>
              <span style={{ color: C.warm, fontWeight: 800 }}>{Math.round(it.value * g).toLocaleString("en-IN")}{it.unit ? " " + it.unit : ""}</span></div>
            <div style={{ height: 30, background: "rgba(255,255,255,0.08)", borderRadius: 8, marginTop: 6 }}>
              <div style={{ height: "100%", width: `${(100 * Math.abs(it.value) / max) * g}%`, background: i % 2 ? C.warm : C.accent, borderRadius: 8 }} />
            </div>
          </div>
        );
      })}
    </Panel>
  );
};

const TableLayer: React.FC<{ l: Extract<Layer, { type: "table" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const focus = (l.focus ?? []).filter((f) => frame >= f.at).pop();
  const cell = (c: number) => (focus && focus.column === c ? { background: "rgba(56,211,195,0.22)", color: C.ink } : {});
  return (
    <Panel box={l.box} o={o}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 26 }}>
        <thead><tr><th />{l.columns.map((c, i) => <th key={i} style={{ textAlign: "left", padding: 10, color: C.accent, ...cell(i) }}>{c}</th>)}</tr></thead>
        <tbody>{l.rows.map((r, ri) => (
          <tr key={ri} style={{ borderTop: `2px solid ${C.line}` }}>
            <th style={{ textAlign: "left", padding: 10, color: C.warm }}>{r.label}</th>
            {r.cells.map((c, ci) => <td key={ci} style={{ padding: 10, ...cell(ci) }}>{c}</td>)}
          </tr>))}</tbody>
      </table>
    </Panel>
  );
};

const ArrowLayer: React.FC<{ l: Extract<Layer, { type: "arrow" }>; layers: Layer[] }> = ({ l, layers }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const a = anchorPoint(layers, l.from), b = anchorPoint(layers, l.to);
  const t = interpolate(frame, [l.at, l.at + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const x1 = a.x * W, y1 = a.y * H, x2 = x1 + (b.x * W - x1) * t, y2 = y1 + (b.y * H - y1) * t;
  return (
    <svg style={{ position: "absolute", inset: 0, width: W, height: H, opacity: o, overflow: "visible" }}>
      <defs><marker id={`h-${l.id}`} markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill={C.warm} /></marker></defs>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={C.warm} strokeWidth={7} markerEnd={`url(#h-${l.id})`} />
      {l.label ? <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 18} fill={C.ink} fontSize={30} fontFamily={FONT} textAnchor="middle">{l.label}</text> : null}
    </svg>
  );
};

const QuestionLayer: React.FC<{ l: Extract<Layer, { type: "question" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  return (
    <AbsoluteFill style={{ background: `rgba(6,18,28,${0.65 * o})`, alignItems: "center", justifyContent: "center", opacity: o }}>
      <div style={{ fontFamily: FONT, color: C.ink, background: C.panel, border: `4px solid ${C.warm}`, borderRadius: 28, padding: "40px 56px",
        maxWidth: 1300, fontSize: 48, fontWeight: 800, textAlign: "center", transform: `scale(${0.9 + 0.1 * o})` }}>
        <div style={{ fontSize: 30, color: C.warm, marginBottom: 14 }}>सोचिए!</div>{l.text}
      </div>
    </AbsoluteFill>
  );
};

const ToolLayer: React.FC<{ l: Extract<Layer, { type: "block" }> }> = ({ l }) => {
  const frame = useCurrentFrame();
  const o = appear(frame, l.at, l.until);
  const Block = getBlock(l.block);
  if (!Block) throw new Error(`BIE_BLOCK_MISSING:${l.block} (render with the toolbox bundle, bie/brain/video/preview/build.mjs --toolbox)`);
  const box = px(l.box);
  return (
    <div style={{ position: "absolute", ...box, opacity: o }}>
      <Block data={l.data} at={l.at} until={l.until} width={Math.round(box.width)} height={Math.round(box.height)} id={l.id} />
    </div>
  );
};

const Captions: React.FC<{ captions: { at: number; until: number; text: string }[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const now = captions.find((c) => frame >= c.at && frame < c.until);
  if (!now) return null;
  return (
    <div style={{ position: "absolute", left: 160, right: 160, bottom: 46, textAlign: "center", fontFamily: FONT, fontSize: 34,
      color: C.ink, textShadow: "0 2px 8px rgba(0,0,0,0.9)" }}>{now.text}</div>
  );
};

export const Scene: React.FC<{ spec: SceneSpec; showCaptions?: boolean }> = ({ spec, showCaptions = true }) => {
  const frame = useCurrentFrame();
  const cam = cameraBox(spec.camera, frame, spec.layers);
  const scale = Math.min(1 / cam.w, 1 / cam.h);
  const tx = -(cam.x + cam.w / 2) * W * scale + W / 2;
  const ty = -(cam.y + cam.h / 2) * H * scale + H / 2;
  const world = spec.layers.filter((l) => l.type !== "question");
  const overlays = spec.layers.filter((l) => l.type === "question");
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Backdrop />
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transformOrigin: "0 0",
        transform: `translate(${tx}px, ${ty}px) scale(${scale})` }}>
        {world.map((l) => {
          if (frame < l.at - 1 || (l.until !== undefined && frame > l.until + 1)) return null;
          switch (l.type) {
            case "image": return <ImageLayer key={l.id} l={l} />;
            case "title": return <TitleLayer key={l.id} l={l} />;
            case "label": return <LabelLayer key={l.id} l={l} layers={spec.layers} />;
            case "highlight": return <HighlightLayer key={l.id} l={l} layers={spec.layers} />;
            case "flow": return <FlowLayer key={l.id} l={l} layers={spec.layers} />;
            case "steps": return <StepsLayer key={l.id} l={l} />;
            case "timeline": return <TimelineLayer key={l.id} l={l} />;
            case "scale": return <ScaleLayer key={l.id} l={l} />;
            case "table": return <TableLayer key={l.id} l={l} />;
            case "arrow": return <ArrowLayer key={l.id} l={l} layers={spec.layers} />;
            case "block": return <ToolLayer key={l.id} l={l} />;
            default: return null;
          }
        })}
      </div>
      {overlays.map((l) => (l.type === "question" ? <QuestionLayer key={l.id} l={l} /> : null))}
      {showCaptions && spec.captions ? <Captions captions={spec.captions} /> : null}
    </AbsoluteFill>
  );
};
