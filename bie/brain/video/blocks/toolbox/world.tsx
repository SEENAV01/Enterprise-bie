// world: the L3 world_scene block, brought in from the economy kit of the asset intake (27 October 2026, Task 046 Part C).
// Captions come from the core Captions strip, not from here.
//
// Instead of a canvas, the lesson happens inside a small 2.5D world that BIE builds from data: a street with parallax
// layers (sky, far city, mid buildings, street, foreground), a shop with a shelf of goods and a hanging price tag, or a bank
// with a teller behind its counter and a board whose value changes (the bank kit, Task 046 Part C PR 3), BIE's own walking
// people (procedural characters, no third-party art), coin rain, a balance of supply against demand, a big "pull" arrow,
// glass labels and a title — all timed to cue words, with a camera that glides, pushes in and pulls back
// through the layers (near things move faster than far things, far things are softer). Everything is drawn by code, so
// every lesson can rebuild it for ₹0. Coordinates are world pixels: the world is ``data.world_width`` wide and 1080 tall;
// the street's walking line is y = 860.
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { registerBlock, BlockProps } from "../registry";
import { FONT } from "./common";

const ease = Easing.inOut(Easing.cubic);
const lin = (f: number, a: number, b: number) =>
  interpolate(f, [a, Math.max(a + 1, b)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const pop = (frame: number, fps: number, at: number) => (frame < at ? 0 : spring({ frame: frame - at, fps, config: { damping: 13, stiffness: 130 } }));

/** Deterministic pseudo-random numbers, so the same data always draws the same world. */
function rng(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
}

const GROUND = 860;
const SKIN = ["#f1c7a3", "#d9a37c", "#b9805a", "#8d5a3b", "#e8b896"];
const SHIRT = ["#e4572e", "#2e86de", "#17a589", "#f4b400", "#8e44ad", "#e67e22", "#16a085", "#c0392b", "#2c3e50", "#d35400", "#27ae60", "#2980b9"];
const PANTS = ["#34495e", "#2c3e50", "#5d4037", "#37474f", "#4a4a6a"];
const HAIR = ["#2b1d14", "#1b1b1b", "#4a2f1d", "#3b2a20"];

type Cam = { at: number; x: number; y: number; zoom: number; frames?: number };

function camAt(keys: Cam[], frame: number) {
  let c = { x: keys[0].x, y: keys[0].y, zoom: keys[0].zoom };
  for (const k of keys) {
    if (frame < k.at) break;
    const t = lin(frame, k.at, k.at + (k.frames ?? 36));
    c = { x: lerp(c.x, k.x, t), y: lerp(c.y, k.y, t), zoom: lerp(c.zoom, k.zoom, t) };
  }
  return c;
}

/** One of BIE's own people: legs and arms swing when walking, the body bobs, the face turns with the direction. */
const Person: React.FC<{ x: number; y: number; s: number; facing: number; phase: number; walking: boolean; look: number; haze?: number;
  hand?: React.ReactNode }> = ({ x, y, s, facing, phase, walking, look, haze = 0, hand }) => {
  const r = rng(look * 7919 + 13);
  const skin = SKIN[Math.floor(r() * SKIN.length)], shirt = SHIRT[Math.floor(r() * SHIRT.length)];
  const pants = PANTS[Math.floor(r() * PANTS.length)], hair = HAIR[Math.floor(r() * HAIR.length)];
  const tall = 0.92 + r() * 0.16, wide = 0.9 + r() * 0.25, longHair = r() > 0.6;
  const swing = walking ? Math.sin(phase) * 28 : Math.sin(phase * 0.15) * 3;
  const bob = walking ? Math.abs(Math.sin(phase)) * -6 : 0;
  return (
    <g transform={`translate(${x},${y}) scale(${s * facing},${s})`} opacity={1 - haze * 0.35}>
      <ellipse cx={0} cy={2} rx={34 * wide} ry={9} fill="rgba(30,25,20,0.22)" />
      <g transform={`translate(0,${bob}) scale(${wide * 0.95},${tall})`}>
        {/* back leg and arm */}
        <g transform={`translate(-6,-78) rotate(${-swing})`}><rect x={-9} y={0} width={18} height={80} rx={9} fill={pants} /><ellipse cx={4} cy={80} rx={14} ry={7} fill="#2a2a2a" /></g>
        <g transform={`translate(-10,-148) rotate(${swing * 0.8})`}><rect x={-7} y={0} width={14} height={62} rx={7} fill={shirt} opacity={0.85} /><circle cx={0} cy={64} r={8} fill={skin} /></g>
        {/* torso */}
        <rect x={-26} y={-160} width={52} height={90} rx={22} fill={shirt} />
        <rect x={-26} y={-96} width={52} height={20} rx={8} fill={pants} />
        {/* front leg */}
        <g transform={`translate(6,-78) rotate(${swing})`}><rect x={-9} y={0} width={18} height={80} rx={9} fill={pants} /><ellipse cx={4} cy={80} rx={14} ry={7} fill="#1e1e1e" /></g>
        {/* head */}
        <rect x={-7} y={-172} width={14} height={16} rx={5} fill={skin} />
        <circle cx={2} cy={-196} r={26} fill={skin} />
        <path d={longHair ? "M-26,-196 C-28,-232 30,-236 28,-200 L28,-170 L20,-196 C10,-214 -12,-214 -22,-190 L-24,-160 Z" : "M-26,-198 C-26,-230 30,-232 28,-202 C18,-214 -8,-218 -26,-198 Z"} fill={hair} />
        <circle cx={14} cy={-198} r={3.2} fill="#2b2b2b" />
        <path d="M10,-184 Q16,-180 21,-185" stroke="#7a3f2a" strokeWidth={2.5} fill="none" strokeLinecap="round" />
        {/* front arm (may hold something) */}
        <g transform={`translate(10,-148) rotate(${-swing * 0.8 - (hand ? 55 : 0)})`}>
          <rect x={-7} y={0} width={14} height={62} rx={7} fill={shirt} /><circle cx={0} cy={64} r={8} fill={skin} />
          {hand ? <g transform="translate(0,70) rotate(55)">{hand}</g> : null}
        </g>
      </g>
    </g>
  );
};

const SugarBag: React.FC<{ x: number; y: number; s?: number }> = ({ x, y, s = 1 }) => (
  <g transform={`translate(${x},${y}) scale(${s})`}>
    <path d="M-26,0 L-30,-70 Q0,-80 30,-70 L26,0 Z" fill="#f7f7f2" stroke="#d8d4c8" strokeWidth={2} />
    <path d="M-30,-70 Q0,-84 30,-70 L26,-78 Q0,-90 -26,-78 Z" fill="#e9e5da" />
    <rect x={-20} y={-50} width={40} height={24} rx={4} fill="#2e86de" />
    <text x={0} y={-33} textAnchor="middle" fontSize={14} fontWeight={800} fill="#fff" fontFamily={FONT}>चीनी</text>
  </g>
);

/** Far city and mid buildings, drawn once from a seed. */
const Skyline: React.FC<{ width: number; seed: number; far: boolean }> = ({ width, seed, far }) => {
  const r = rng(seed);
  const items: React.ReactNode[] = [];
  let x = -400;
  let i = 0;
  while (x < width + 400) {
    const w = far ? 90 + r() * 140 : 220 + r() * 160;
    const h = far ? 160 + r() * 260 : 300 + r() * 220;
    const base = far ? 700 : GROUND - 40;
    if (far) {
      items.push(<rect key={i} x={x} y={base - h} width={w} height={h} fill="#9fb6c9" />);
    } else {
      const col = ["#f2c37b", "#e8a87c", "#c9d6a3", "#f0d9b5", "#d9a5a0", "#a7c4d9"][Math.floor(r() * 6)];
      items.push(
        <g key={i}>
          <rect x={x} y={base - h} width={w - 14} height={h} fill={col} />
          <rect x={x} y={base - h} width={w - 14} height={18} fill="rgba(0,0,0,0.08)" />
          {Array.from({ length: Math.floor((h - 60) / 70) }, (_, row) => Array.from({ length: Math.floor((w - 40) / 60) }, (_, c) => (
            <rect key={`${row}-${c}`} x={x + 18 + c * 60} y={base - h + 40 + row * 70} width={34} height={42} rx={4}
              fill={r() > 0.8 ? "#ffe9a8" : "#6f8aa3"} opacity={0.85} />
          )))}
        </g>,
      );
    }
    x += w + (far ? 10 : 0);
    i++;
  }
  return <>{items}</>;
};

const Shop: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  const x = el.x, w = 760, top = GROUND - 560;
  const packets = (() => { let n = el.packets?.[0]?.n ?? 0; for (const p of el.packets ?? []) if (frame >= p.at) n = p.n; return n; })();
  const sway = Math.sin(frame / 18) * 4;
  return (
    <g>
      {/* building */}
      <rect x={x - w / 2 - 40} y={top - 220} width={w + 80} height={780} fill="#f5e6c8" />
      <rect x={x - w / 2 - 40} y={top - 220} width={w + 80} height={26} fill="#d9c49b" />
      {[0, 1, 2].map((i) => <rect key={i} x={x - w / 2 + 40 + i * 250} y={top - 170} width={150} height={110} rx={8} fill="#7d9bb5" stroke="#fff" strokeWidth={8} />)}
      {/* sign */}
      <rect x={x - 260} y={top - 40} width={520} height={86} rx={14} fill="#c0392b" />
      <text x={x} y={top + 20} textAnchor="middle" fontSize={52} fontWeight={900} fill="#fff7e0" fontFamily={FONT}>{el.sign ?? "किराना स्टोर"}</text>
      {/* opening and interior */}
      <rect x={x - w / 2} y={top + 70} width={w} height={490} fill="#6b4f3a" />
      <rect x={x - w / 2 + 20} y={top + 90} width={w - 40} height={300} fill="#8a6a4f" />
      {[0, 1].map((i) => <rect key={i} x={x - w / 2 + 40} y={top + 270 + i * 110} width={w - 80} height={14} fill="#4e3626" />)}
      {Array.from({ length: packets }, (_, i) => {
        const k = pop(frame, fps, (el.packets?.[0]?.at ?? 0) + i * 4);
        return <SugarBag key={i} x={x - 160 + i * 160} y={top + 270} s={1.45 * k} />;
      })}
      {/* awning */}
      {Array.from({ length: 10 }, (_, i) => (
        <path key={i} d={`M${x - w / 2 - 30 + i * ((w + 60) / 10)},${top + 60} l${(w + 60) / 10},0 l0,70 q${-(w + 60) / 20},26 ${-(w + 60) / 10},0 z`}
          fill={i % 2 ? "#ffffff" : "#e74c3c"} />
      ))}
      <rect x={x - w / 2 - 34} y={top + 50} width={w + 68} height={16} rx={6} fill="#a93226" />
      {/* counter */}
      <rect x={x - w / 2 + 10} y={GROUND - 170} width={w - 20} height={170} fill="#b07a4f" />
      <rect x={x - w / 2} y={GROUND - 185} width={w} height={22} rx={6} fill="#8e5c36" />
    </g>
  );
};

/** The bank kit's place: a stone front with a pediment and pillars, a sign band, a teller window and a counter on the street
 *  (Task 046 Part C, PR 3: the Money chapter's v1 saves ₹500 in an account and pays an EMI). The teller stands behind the
 *  counter, so the counter is drawn after the person. */
const Bank: React.FC<{ el: any; teller?: any; frame: number }> = ({ el, teller, frame }) => {
  const x = el.x, w = 900, top = GROUND - 540;          // the whole front fits a 1080-tall frame at zoom 1 (camera y 540)
  return (
    <g>
      {/* facade */}
      <rect x={x - w / 2 - 50} y={top - 150} width={w + 100} height={750} fill="#e9e2d3" />
      <path d={`M${x - w / 2 - 80},${top - 176} L${x},${top - 280} L${x + w / 2 + 80},${top - 176} Z`} fill="#d8ccb2" stroke="#c4b79a" strokeWidth={6} />
      <rect x={x - w / 2 - 80} y={top - 182} width={w + 160} height={40} fill="#cfc4ad" />
      {/* sign band */}
      <rect x={x - 320} y={top - 112} width={640} height={92} rx={14} fill="#1f3a5f" />
      <text x={x} y={top - 46} textAnchor="middle" fontSize={56} fontWeight={900} fill="#fff7e0" fontFamily={FONT}>{el.sign ?? "बैंक"}</text>
      {/* hall */}
      <rect x={x - w / 2 + 70} y={top + 4} width={w - 140} height={556} fill="#2b3f55" />
      <rect x={x - w / 2 + 90} y={top + 24} width={w - 180} height={300} fill="#3b556f" />
      {/* teller window */}
      <rect x={x - 230} y={top + 70} width={460} height={230} rx={18} fill="#9fd3ff" opacity={0.5} stroke="#fff" strokeWidth={6} />
      <rect x={x - 230} y={top + 300} width={460} height={28} fill="#cfd8dc" />
      {/* pillars */}
      {[-1, 1].map((s) => (
        <g key={s}>
          <rect x={x + s * (w / 2 - 20) - 34} y={top - 16} width={68} height={576} fill="#f4efe4" stroke="#cfc4ad" strokeWidth={4} />
          <rect x={x + s * (w / 2 - 20) - 46} y={top - 36} width={92} height={28} fill="#d8ccb2" />
        </g>
      ))}
      {teller ? <Person x={teller.x ?? x} y={GROUND - 190} s={0.9} facing={-1} phase={frame / 3} walking={false} look={teller.look ?? 5} /> : null}
      {/* counter */}
      <rect x={x - w / 2 + 70} y={GROUND - 200} width={w - 140} height={200} fill="#6d4c41" />
      <rect x={x - w / 2 + 50} y={GROUND - 216} width={w - 100} height={26} rx={6} fill="#4e342e" />
      <rect x={x - 60} y={GROUND - 176} width={120} height={14} rx={4} fill="#ffe9a8" opacity={0.8} />
      {/* step */}
      <rect x={x - w / 2 - 90} y={GROUND - 26} width={w + 180} height={26} fill="#cfc4ad" />
    </g>
  );
};

/** A standing display whose value changes on its cue word: a passbook balance, an EMI due, the few words that change. The
 *  value is up to three lines (code wraps a long line at spaces, world.py); the font and the box fit the longest line, so
 *  nothing runs out of the card. The old value is struck out above the new one when it was short (as the price tag does),
 *  and `dir` adds a green up or a red down arrow. */
const Board: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  const steps: { text: string; lines?: string[]; at: number; dir?: string }[] = el.steps ?? [];
  if (!steps.length || frame < steps[0].at || (el.until !== undefined && frame > el.until + 15)) return null;
  let idx = 0;
  steps.forEach((s, i) => { if (frame >= s.at) idx = i; });
  const cur = steps[idx], prev = idx > 0 ? steps[idx - 1] : null;
  const linesOf = (s: { text: string; lines?: string[] }) => (s.lines && s.lines.length ? s.lines : String(s.text ?? "").split("\n"));
  const flip = prev ? lin(frame, cur.at, cur.at + 16) : 1;
  const shown = flip < 0.5 && prev ? prev : cur;
  const lines = linesOf(shown);
  const longest = Math.max(1, ...lines.map((l) => l.length));
  const fs = lines.length === 1 && longest <= 8 ? 96 : lines.length === 1 && longest <= 14 ? 72 : 46;
  const w = Math.max(440, Math.min(960, Math.round(longest * fs * 0.6 + 90)));
  const body = lines.length * fs * 1.22;
  const h = Math.max(310, Math.round(140 + body + 40));
  const k = pop(frame, fps, steps[0].at) * (el.until !== undefined ? 1 - lin(frame, el.until, el.until + 15) : 1);
  const glow = prev ? Math.max(0, 1 - lin(frame, cur.at + 8, cur.at + 60)) : 0;
  const header = el.fill ?? "#1f3a5f";
  const stand = Math.max(0, GROUND - el.y - h / 2);
  const ghost = prev && flip > 0.5 && linesOf(prev).length === 1 && linesOf(prev)[0].length <= 14 ? linesOf(prev)[0] : null;
  const top = -h / 2 + 70 + (ghost ? 44 : 0);
  const free = h - 70 - (ghost ? 44 : 0) - 30;
  const y0 = top + Math.max(0, (free - body) / 2) + fs * 0.95;
  return (
    <g transform={`translate(${el.x},${el.y}) scale(${k})`}>
      <rect x={-14} y={h / 2 - 4} width={28} height={stand + 4} fill="#45535e" />
      <rect x={-90} y={h / 2 + stand - 16} width={180} height={16} rx={6} fill="#45535e" />
      {glow ? <circle cx={0} cy={50} r={250} fill={cur.dir === "down" ? "#ff9f7a" : "#ffcf5a"} opacity={0.32 * glow} /> : null}
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={24} fill="#fffdf6" stroke="#2c3e50" strokeWidth={6} />
      <path d={`M${-w / 2},${-h / 2 + 24} a24,24 0 0 1 24,-24 h${w - 48} a24,24 0 0 1 24,24 v46 h${-w} z`} fill={header} />
      <text x={0} y={-h / 2 + 48} textAnchor="middle" fontSize={34} fontWeight={800} fill="#fff" fontFamily={FONT}>{el.text ?? ""}</text>
      {ghost ? <g opacity={Math.min(1, (flip - 0.5) * 3)}>
        <text x={0} y={-h / 2 + 104} textAnchor="middle" fontSize={34} fontWeight={800} fill="#8a8a8a" fontFamily={FONT}>{ghost}</text>
        <line x1={-ghost.length * 11} y1={-h / 2 + 94} x2={ghost.length * 11} y2={-h / 2 + 90} stroke="#d63031" strokeWidth={6} />
      </g> : null}
      <g transform={`translate(0,0) scale(1,${Math.abs(Math.cos((1 - flip) * Math.PI / 2))})`}>
        {lines.map((line, i) => (
          <text key={i} x={0} y={y0 + i * fs * 1.22} textAnchor="middle" fontSize={fs} fontWeight={900} fill="#2b2b2b" fontFamily={FONT}>{line}</text>
        ))}
      </g>
      {cur.dir === "up" && flip > 0.9 ? <path d="M0,0 l30,-48 l30,48 l-18,0 l0,46 l-24,0 l0,-46 z" fill="#27ae60"
        transform={`translate(${w / 2 - 90},${h / 2 - 110 + (1 - pop(frame, fps, cur.at + 10)) * 30})`} /> : null}
      {cur.dir === "down" && flip > 0.9 ? <path d="M0,0 l30,48 l30,-48 l-18,0 l0,-46 l-24,0 l0,46 z" fill="#d63031"
        transform={`translate(${w / 2 - 90},${h / 2 - 110 + (1 - pop(frame, fps, cur.at + 10)) * -30})`} /> : null}
    </g>
  );
};

const PriceTag: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  const steps: { text: string; at: number; dir?: string }[] = el.steps;
  let idx = 0;
  steps.forEach((s, i) => { if (frame >= s.at) idx = i; });
  if (frame < steps[0].at) return null;
  const cur = steps[idx], prev = idx > 0 ? steps[idx - 1] : null;
  const flip = prev ? lin(frame, cur.at, cur.at + 14) : 1;
  const lift = el.lift && frame >= el.lift.at ? lin(frame, el.lift.at, el.lift.at + 40) * el.lift.dy : 0;
  const sway = Math.sin(frame / 14) * (3 + (prev ? 9 * Math.max(0, 1 - lin(frame, cur.at, cur.at + 60)) : 0));
  const k = pop(frame, fps, steps[0].at);
  const glow = prev ? Math.max(0, 1 - lin(frame, cur.at + 8, cur.at + 60)) : 0;
  return (
    <g transform={`translate(${el.x},${el.y - lift}) rotate(${sway}) scale(${k})`}>
      <line x1={0} y1={-90 - (el.string ?? 60)} x2={0} y2={-40} stroke="#5a4636" strokeWidth={4} />
      {glow ? <circle cx={0} cy={20} r={150} fill="#ffcf5a" opacity={0.35 * glow} /> : null}
      <g transform={`scale(1,${Math.abs(Math.cos((1 - flip) * Math.PI / 2))})`}>
        <path d="M-110,-40 L90,-40 L130,20 L90,80 L-110,80 Z" fill="#fff8e1" stroke="#e0a100" strokeWidth={6} />
        <circle cx={92} cy={20} r={10} fill="#e0a100" />
        <text x={-10} y={46} textAnchor="middle" fontSize={Math.min(78, Math.floor(200 / (Math.max(1, String(flip < 0.5 && prev ? prev.text : cur.text).length) * 0.6)))}
          fontWeight={900} fill="#2b2b2b" fontFamily={FONT}>{flip < 0.5 && prev ? prev.text : cur.text}</text>
      </g>
      {cur.dir === "up" && flip > 0.9 ? <path d="M150,40 l30,-48 l30,48 l-18,0 l0,46 l-24,0 l0,-46 z" fill="#27ae60" transform={`translate(0,${(1 - pop(frame, fps, cur.at + 10)) * 30})`} /> : null}
      {prev && flip > 0.5 ? <g opacity={Math.min(1, (flip - 0.5) * 3)}>
        <text x={-20} y={-60} textAnchor="middle" fontSize={36} fontWeight={800} fill="#8a8a8a" fontFamily={FONT}>{prev.text}</text>
        <line x1={-80} y1={-70} x2={40} y2={-78} stroke="#d63031" strokeWidth={6} />
      </g> : null}
    </g>
  );
};

/** People of a crowd: arrive walking to their spots, wait (small idle sway), and leave walking when the count drops. */
const Crowd: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame }) => {
  const steps: { n: number; at: number }[] = el.steps;
  const max = Math.max(...steps.map((s) => s.n));
  const cols = Math.max(1, Math.ceil(max / 3));
  const slots = Array.from({ length: max }, (_, i) => {
    const row = Math.floor(i / cols), col = i % cols;
    return { x: el.x0 + col * el.spacing + (row % 2) * el.spacing * 0.5, depth: row };
  });
  const arrive: number[] = [], leave: (number | undefined)[] = [];
  let have = 0;
  for (const st of steps) {
    if (st.n > have) { for (let i = have; i < st.n; i++) arrive[i] = st.at + (i - have) * 5; have = st.n; }
    else if (st.n < have) { for (let i = st.n; i < have; i++) leave[i] = st.at + (i - st.n) * 4; have = st.n; }
  }
  const order = slots.map((s, i) => i).sort((a, b) => slots[a].depth - slots[b].depth);
  return (
    <g>
      {order.map((i) => {
        if (arrive[i] === undefined || frame < arrive[i]) return null;
        const sl = slots[i];
        const walkIn = 70;
        const fromX = el.enter_x + (i % 2 ? -60 : 0) * (sl.depth + 1);
        const t = lin(frame, arrive[i], arrive[i] + walkIn);
        let x = lerp(fromX, sl.x, t), facing = sl.x > fromX ? 1 : -1, walking = t > 0 && t < 1;
        if (!walking && t >= 1) facing = el.face ?? 1;
        const lv = leave[i];
        let alpha = 1;
        if (lv !== undefined && frame >= lv) {
          const u = lin(frame, lv, lv + 80);
          x = lerp(sl.x, el.exit_x, u);
          facing = el.exit_x > sl.x ? 1 : -1;
          walking = u < 1;
          alpha = 1 - Math.max(0, (u - 0.75) * 4);
          if (u >= 1) return null;
        }
        const y = GROUND - 26 + sl.depth * -34, s = 0.92 - sl.depth * 0.09;
        return (
          <g key={i} opacity={alpha}>
            <Person x={x} y={y} s={s} facing={facing} phase={frame / 3.2 + i * 1.7} walking={walking} look={(el.seed ?? 1) * 100 + i} haze={sl.depth * 0.5}
              hand={el.carry && el.carry.at <= frame && i < el.carry.n ? <SugarBag x={0} y={10} s={0.55} /> : undefined} />
          </g>
        );
      })}
    </g>
  );
};

const CoinRain: React.FC<{ el: any; frame: number }> = ({ el, frame }) => {
  if (frame < el.at || frame > (el.until ?? el.at + 120) + 40) return null;
  const r = rng(el.seed ?? 7);
  return (
    <g>
      {Array.from({ length: el.count ?? 40 }, (_, i) => {
        const x = el.x0 + r() * (el.x1 - el.x0), delay = r() * 70, spin = r() * 6;
        const t = (frame - el.at - delay) / 45;
        if (t < 0 || t > 1.3) return null;
        const y = lerp(80, GROUND - 230 - r() * 60, Math.min(1, t));
        const sq = Math.abs(Math.cos(frame / 5 + spin));
        return (
          <g key={i} transform={`translate(${x},${y})`} opacity={t > 1 ? Math.max(0, 1 - (t - 1) * 3.3) : 1}>
            <ellipse cx={0} cy={0} rx={22 * Math.max(0.15, sq)} ry={22} fill="#f5b041" stroke="#b9770e" strokeWidth={4} />
            {sq > 0.5 ? <text x={0} y={9} textAnchor="middle" fontSize={24} fontWeight={900} fill="#9a6408" fontFamily={FONT}>₹</text> : null}
          </g>
        );
      })}
    </g>
  );
};

/** A balance: goods on one pan, people on the other; it tips towards the heavier side as the story says so. */
const Balance: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  if (frame < el.at || (el.until !== undefined && frame > el.until + 15)) return null;
  const k = pop(frame, fps, el.at) * (el.until !== undefined ? 1 - lin(frame, el.until, el.until + 15) : 1);
  const tilt = lin(frame, el.tilt_at ?? el.at + 20, (el.tilt_at ?? el.at + 20) + 30) * (el.tilt ?? 14);
  const arm = 260;
  const a = (tilt * Math.PI) / 180;
  const lx = -arm * Math.cos(a), ly = -arm * Math.sin(a), rx = arm * Math.cos(a), ry = arm * Math.sin(a);
  const pan = (x: number, y: number, content: React.ReactNode, label: string, col: string) => (
    <g transform={`translate(${x},${y})`}>
      <line x1={-70} y1={110} x2={0} y2={0} stroke="#7f8c8d" strokeWidth={3} /><line x1={70} y1={110} x2={0} y2={0} stroke="#7f8c8d" strokeWidth={3} />
      <path d="M-100,110 Q0,150 100,110 Z" fill="#bdc3c7" stroke="#95a5a6" strokeWidth={3} />
      <g transform="translate(0,104)">{content}</g>
      <rect x={-80} y={150} width={160} height={42} rx={21} fill={col} />
      <text x={0} y={180} textAnchor="middle" fontSize={26} fontWeight={900} fill="#fff" fontFamily={FONT}>{label}</text>
    </g>
  );
  return (
    <g transform={`translate(${el.x},${el.y}) scale(${k * (el.scale ?? 1.25)})`}>
      <rect x={-300} y={-60} width={600} height={360} rx={30} fill="rgba(255,255,255,0.72)" stroke="rgba(255,255,255,0.9)" strokeWidth={3} />
      <rect x={-10} y={-10} width={20} height={250} fill="#7f8c8d" /><rect x={-80} y={230} width={160} height={22} rx={8} fill="#7f8c8d" />
      <line x1={lx} y1={ly} x2={rx} y2={ry} stroke="#566573" strokeWidth={12} strokeLinecap="round" />
      <circle cx={0} cy={0} r={16} fill="#566573" />
      {pan(lx, ly, <>{[-34, 0, 34].map((dx) => <SugarBag key={dx} x={dx} y={0} s={0.45} />)}</>, "SUPPLY", "#2e86de")}
      {pan(rx, ry, <>{Array.from({ length: 12 }, (_, i) => <circle key={i} cx={-60 + (i % 6) * 24} cy={-12 - Math.floor(i / 6) * 22} r={10} fill={SHIRT[i % SHIRT.length]} />)}</>, "DEMAND", "#e67e22")}
    </g>
  );
};

const GlassLabel: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  if (frame < el.at || (el.until !== undefined && frame > el.until + 12)) return null;
  const k = pop(frame, fps, el.at) * (el.until !== undefined ? 1 - lin(frame, el.until, el.until + 12) : 1);
  const w = el.text.length * (el.size ?? 34) * 0.62 + 56;
  return (
    <g transform={`translate(${el.x},${el.y - (1 - k) * 30})`} opacity={k}>
      {el.pointer ? <line x1={0} y1={34} x2={0} y2={el.pointer} stroke="rgba(255,255,255,0.9)" strokeWidth={4} strokeDasharray="8 8" /> : null}
      <rect x={-w / 2} y={-34} width={w} height={68} rx={34} fill={el.fill ?? "rgba(30,40,55,0.82)"} stroke="rgba(255,255,255,0.6)" strokeWidth={2} />
      <text x={0} y={12} textAnchor="middle" fontSize={el.size ?? 34} fontWeight={800} fill="#fff" fontFamily={FONT}>{el.text}</text>
    </g>
  );
};

const PullArrow: React.FC<{ el: any; frame: number }> = ({ el, frame }) => {
  if (frame < el.at) return null;
  const t = lin(frame, el.at, el.at + 30);
  const y = lerp(el.y0, el.y1, t);
  return (
    <g opacity={Math.min(1, t * 3)}>
      <path d={`M${el.x - 40},${el.y0} L${el.x - 40},${y + 60} L${el.x - 90},${y + 60} L${el.x},${y - 30} L${el.x + 90},${y + 60} L${el.x + 40},${y + 60} L${el.x + 40},${el.y0} Z`}
        fill="#e67e22" stroke="#fff" strokeWidth={6} opacity={0.92} />
      <text x={el.x} y={(el.y0 + y) / 2 + 60} textAnchor="middle" fontSize={36} fontWeight={900} fill="#fff" fontFamily={FONT}
        transform={`rotate(-90 ${el.x} ${(el.y0 + y) / 2 + 60})`}>{el.text ?? "DEMAND"}</text>
    </g>
  );
};

const Title: React.FC<{ el: any; frame: number; fps: number; W: number }> = ({ el, frame, fps, W }) => {
  if (frame < el.at) return null;
  const k = pop(frame, fps, el.at);
  const sweep = lin(frame, el.at + 10, el.at + 50);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: 70, display: "flex", justifyContent: "center", transform: `translateY(${(1 - k) * -40}px)`, opacity: k }}>
      <div style={{ position: "relative", overflow: "hidden", padding: "16px 48px", borderRadius: 22, background: "rgba(20,28,40,0.86)", color: "#fff",
        fontFamily: FONT, fontWeight: 900, fontSize: 64, letterSpacing: 2, boxShadow: "0 16px 40px rgba(0,0,0,0.3)" }}>
        {el.text}
        <div style={{ position: "absolute", top: 0, bottom: 0, width: 160, left: `${-20 + sweep * 120}%`,
          background: "linear-gradient(100deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%)" }} />
      </div>
    </div>
  );
};


/** A parallax layer: a div the compositor caches (will-change), moved by a CSS transform each frame; its SVG draws in world
 *  pixels and overflows the frame. Static layers (sun, skylines, road, foreground) are memoised, so React never redraws them
 *  and Chromium re-uses their raster: the camera only moves cached pictures (Task 046 Part C, PR 4: render speed). Depth
 *  is shown by colour and opacity instead of per-frame blur filters, which cost most of a frame on a software renderer. */
const Layer: React.FC<{ W: number; H: number; transform: string; opacity?: number; children: React.ReactNode }> = ({ W, H, transform, opacity, children }) => (
  <div style={{ position: "absolute", left: 0, top: 0, width: W, height: H, transformOrigin: "0 0", transform, willChange: "transform", opacity }}>
    <svg width={W} height={H} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>{children}</svg>
  </div>
);

const SunLayer = React.memo(({ WW }: { WW: number }) => (
  <>
    <defs>
      <radialGradient id="ws-sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stopColor="#fff6c8" /><stop offset="0.4" stopColor="#ffe08a" stopOpacity="0.8" /><stop offset="1" stopColor="#ffe08a" stopOpacity="0" /></radialGradient>
    </defs>
    <circle cx={WW * 0.45} cy={200} r={260} fill="url(#ws-sun)" />
  </>
));

const FarSkyline = React.memo(({ WW }: { WW: number }) => <Skyline width={WW} seed={11} far />);
const NearSkyline = React.memo(({ WW }: { WW: number }) => <Skyline width={WW} seed={23} far={false} />);

const Road = React.memo(({ WW }: { WW: number }) => (
  <>
    <defs>
      <linearGradient id="ws-road" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#b8b2a7" /><stop offset="1" stopColor="#8c867c" /></linearGradient>
    </defs>
    <rect x={-2000} y={GROUND - 40} width={WW + 4000} height={60} fill="#d8cfbf" />
    <rect x={-2000} y={GROUND + 20} width={WW + 4000} height={400} fill="url(#ws-road)" />
    {Array.from({ length: Math.ceil((WW + 4000) / 260) }, (_, i) => <rect key={i} x={-2000 + i * 260} y={GROUND + 140} width={130} height={14} rx={7} fill="#f3f0e8" opacity={0.8} />)}
  </>
));

const Foreground = React.memo(({ els }: { els: any[] }) => (
  <>
    <defs>
      <radialGradient id="ws-bush" cx="0.5" cy="0.5" r="0.5"><stop offset="0.55" stopColor="#3f7d4e" /><stop offset="1" stopColor="#3f7d4e" stopOpacity="0" /></radialGradient>
      <radialGradient id="ws-bush2" cx="0.5" cy="0.5" r="0.5"><stop offset="0.55" stopColor="#4f9a5f" /><stop offset="1" stopColor="#4f9a5f" stopOpacity="0" /></radialGradient>
    </defs>
    {els.map((e) => <g key={e.id}>
      <ellipse cx={e.x} cy={GROUND + 190} rx={230} ry={120} fill="url(#ws-bush)" /><ellipse cx={e.x - 100} cy={GROUND + 160} rx={150} ry={95} fill="url(#ws-bush2)" />
      <ellipse cx={e.x + 110} cy={GROUND + 170} rx={140} ry={90} fill="url(#ws-bush)" />
    </g>)}
  </>
));

const WorldScene: React.FC<BlockProps> = ({ data, width: W, height: H }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cam = camAt(data.camera, frame);
  const WW = data.world_width ?? 5200;
  // a layer at depth d (1 = street) follows the camera by d; far layers also zoom less
  const layer = (d: number) => {
    const z = 1 + (cam.zoom - 1) * d;
    return `translate(${W / 2}px, ${H / 2}px) scale(${z}) translate(${-cam.x * d - (1 - d) * WW * 0.35}px, ${-(cam.y * d + (1 - d) * 540)}px)`;
  };
  const els: any[] = data.elements ?? [];
  const byKind = (k: string) => els.filter((e) => e.kind === k);
  const clouds = rng(5);
  const foreground = byKind("foreground");
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "linear-gradient(#8ec5ff 0%, #cfe6ff 45%, #ffe7c4 75%)" }}>
      <Layer W={W} H={H} transform={layer(0.05)}><SunLayer WW={WW} /></Layer>
      <Layer W={W} H={H} transform={layer(0.05)}>
        {Array.from({ length: 9 }, (_, i) => {
          const cx = (clouds() * WW * 1.2 + frame * (0.4 + clouds() * 0.5)) % (WW * 1.2) - WW * 0.1, cy = 90 + clouds() * 220, s = 0.6 + clouds();
          return <g key={i} transform={`translate(${cx},${cy}) scale(${s})`} opacity={0.9}>
            <ellipse cx={0} cy={0} rx={110} ry={38} fill="#fff" /><ellipse cx={-50} cy={-20} rx={60} ry={40} fill="#fff" /><ellipse cx={40} cy={-26} rx={70} ry={46} fill="#fff" />
          </g>;
        })}
      </Layer>
      <Layer W={W} H={H} transform={layer(0.3)} opacity={0.7}><FarSkyline WW={WW} /></Layer>
      <Layer W={W} H={H} transform={layer(0.65)} opacity={0.92}><NearSkyline WW={WW} /></Layer>
      <Layer W={W} H={H} transform={layer(1)}><Road WW={WW} /></Layer>
      <Layer W={W} H={H} transform={layer(1)}>
        {byKind("shop").map((e) => <Shop key={e.id} el={e} frame={frame} fps={fps} />)}
        {byKind("bank").map((e) => <Bank key={e.id} el={e} frame={frame} teller={byKind("teller").find((t) => Math.abs((t.x ?? e.x) - e.x) < 600)} />)}
          {byKind("lamp").map((e) => <g key={e.id}><rect x={e.x - 7} y={GROUND - 420} width={14} height={420} fill="#45535e" /><rect x={e.x - 40} y={GROUND - 440} width={80} height={24} rx={10} fill="#45535e" /><ellipse cx={e.x} cy={GROUND - 412} rx={30} ry={10} fill="#ffe9a8" /></g>)}
        {byKind("shopkeeper").map((e) => <Person key={e.id} x={e.x} y={GROUND - 150} s={0.9} facing={-1} phase={frame / 3} walking={false} look={e.look ?? 3} />)}
        {byKind("crowd").map((e) => <Crowd key={e.id} el={e} frame={frame} fps={fps} />)}
        {byKind("price_tag").map((e) => <PriceTag key={e.id} el={e} frame={frame} fps={fps} />)}
        {byKind("coin_rain").map((e) => <CoinRain key={e.id} el={e} frame={frame} />)}
        {byKind("pull_arrow").map((e) => <PullArrow key={e.id} el={e} frame={frame} />)}
        {byKind("balance").map((e) => <Balance key={e.id} el={e} frame={frame} fps={fps} />)}
        {byKind("board").map((e) => <Board key={e.id} el={e} frame={frame} fps={fps} />)}
        {byKind("label").map((e) => <GlassLabel key={e.id} el={e} frame={frame} fps={fps} />)}
      </Layer>
      {foreground.length ? <Layer W={W} H={H} transform={layer(1.6)}><Foreground els={foreground} /></Layer> : null}
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none",
        background: "linear-gradient(180deg, rgba(255,220,170,0.10), rgba(255,200,140,0.0) 40%, rgba(60,40,20,0.12))" }} />
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none",
        background: "radial-gradient(ellipse at 50% 50%, rgba(40,25,10,0) 58%, rgba(40,25,10,0.35) 100%)" }} />
      {byKind("title").map((e) => <Title key={e.id} el={e} frame={frame} fps={fps} W={W} />)}
    </div>
  );
};

registerBlock("world_scene", WorldScene);
