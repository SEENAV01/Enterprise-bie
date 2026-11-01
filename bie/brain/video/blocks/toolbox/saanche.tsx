// saanche: kriya ke saanche drawn from general motion parts (Task 046 Part D2 and its addendum of 2 November 2026: "jis cheej ka
// jikar hai wohi cheej dikhe"). One stage (1000 x 620 units, feet on y = 600) plays an action's parts in time: hold, give/take,
// move along a path, transform A -> B, a screen or sign shows text, a counter or meter changes, appear one by one,
// refuse/accept, compare. bie/brain/video/saanche.py composes them from the rulebook's recipes (or the maker's own composition)
// and times them; a world places the stage on its street (world.tsx), the canvas fits it into a node's cells (canvas.tsx).
//
// The block draws people (BIE's own procedural figures with hands that hold, moods, a head shake and a nod) and generic marks
// (a cross, a tick, a thought bubble, a text card, a meter, a number panel, a plain chip with text). It draws no object of its
// own: every thing on the stage is the image the plan named for the beat's thing (icon index, asset library, BIE's coder), or a
// plain chip with the part's text when the plan named none.
import React from "react";
import { Easing, interpolate, spring } from "remotion";
import { FONT, assetUrl } from "./common";

export const STAGE_W = 1000, STAGE_H = 620, FEET = 600;
const ease = Easing.inOut(Easing.cubic);
const lin = (f: number, a: number, b: number) =>
  interpolate(f, [a, Math.max(a + 1, b)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const pop = (frame: number, fps: number, at: number) => (frame < at ? 0 : spring({ frame: frame - at, fps, config: { damping: 12, stiffness: 140 } }));
const SKIN = ["#f1c7a3", "#d9a37c", "#b9805a", "#8d5a3b", "#e8b896"];
const SHIRT = ["#e4572e", "#2e86de", "#17a589", "#f4b400", "#8e44ad", "#e67e22", "#16a085", "#c0392b", "#2c3e50", "#d35400"];
const PANTS = ["#34495e", "#2c3e50", "#5d4037", "#37474f", "#4a4a6a"];
const HAIR = ["#2b1d14", "#1b1b1b", "#4a2f1d", "#3b2a20"];

function pick<T>(xs: T[], seed: number, k: number): T {
  const v = Math.abs(Math.sin(seed * 12.9898 + k * 78.233) * 43758.5453) % 1;
  return xs[Math.floor(v * xs.length)];
}

type Pose = { reach?: number; raise?: number; shake?: number; nod?: number; mood?: string; hold?: React.ReactNode; holdBack?: React.ReactNode };

/** A big person: s = 1 is 300 units tall. ``reach`` (0..1) swings the front arm forward to give or take; ``raise`` lifts it up
 *  (a phone to a QR stand); ``shake`` and ``nod`` move the head; ``hold`` is drawn in the front hand, ``holdBack`` in the other. */
export const Actor: React.FC<{ x: number; y: number; s?: number; facing: number; look: number; pose?: Pose; main?: boolean; label?: string }> =
  ({ x, y, s = 1, facing, look, pose = {}, main, label }) => {
    const skin = pick(SKIN, look, 1), shirt = pick(SHIRT, look, 2), pants = pick(PANTS, look, 3), hair = pick(HAIR, look, 4);
    const reach = pose.reach ?? 0, raise = pose.raise ?? 0;
    const armAngle = -20 - reach * 55 - raise * 95;         // degrees from hanging down, forward is negative
    const head = (pose.shake ?? 0) * 14;
    const nod = (pose.nod ?? 0) * 10;
    const mood = pose.mood ?? "neutral";
    const mouth = mood === "pleased" ? "M4,-243 Q14,-232 26,-243" : mood === "refusing" ? "M4,-235 Q14,-245 26,-235"
      : mood === "unsure" ? "M4,-239 Q9,-243 15,-239 Q20,-235 26,-239" : "M6,-239 L24,-239";
    const brow = mood === "unsure" ? "M10,-276 L28,-284" : mood === "refusing" ? "M10,-283 L28,-275" : "M10,-279 L28,-279";
    return (
      <g transform={`translate(${x},${y}) scale(${s * facing},${s})`}>
        <ellipse cx={0} cy={2} rx={46} ry={10} fill="rgba(30,25,20,0.22)" />
        {/* legs */}
        <rect x={-22} y={-110} width={20} height={110} rx={10} fill={pants} />
        <rect x={2} y={-110} width={20} height={110} rx={10} fill={pants} />
        <ellipse cx={-10} cy={0} rx={18} ry={8} fill="#2a2a2a" /><ellipse cx={16} cy={0} rx={18} ry={8} fill="#1e1e1e" />
        {/* back arm */}
        <g transform={`translate(-18,-205) rotate(${12})`}>
          <rect x={-9} y={0} width={18} height={84} rx={9} fill={shirt} opacity={0.85} /><circle cx={0} cy={88} r={10} fill={skin} />
          {pose.holdBack ? <g transform="translate(0,98)">{pose.holdBack}</g> : null}
        </g>
        {/* torso */}
        <rect x={-34} y={-222} width={68} height={120} rx={28} fill={shirt} />
        {main ? <path d="M-34,-170 L34,-150 L34,-136 L-34,-156 Z" fill="#ffffff" opacity={0.85} /> : null}
        <rect x={-34} y={-122} width={68} height={22} rx={9} fill={pants} />
        {/* head */}
        <g transform={`translate(0,${nod}) rotate(${head} 0 -215)`}>
          <rect x={-9} y={-236} width={18} height={20} rx={6} fill={skin} />
          <circle cx={4} cy={-262} r={34} fill={skin} />
          <path d={main ? "M-30,-268 C-30,-312 40,-312 38,-268 L38,-282 C20,-300 -12,-300 -30,-280 Z" : "M-30,-266 C-30,-306 38,-308 36,-270 C22,-288 -8,-292 -30,-266 Z"} fill={hair} />
          {main ? <path d="M-34,-286 Q4,-322 42,-286 L42,-278 Q4,-300 -34,-278 Z" fill="#f39c12" /> : null}
          <circle cx={18} cy={-262} r={4} fill="#2b2b2b" />
          <path d={brow} stroke="#3b2a20" strokeWidth={3.5} strokeLinecap="round" />
          <path d={mouth} stroke="#7a3f2a" strokeWidth={3.5} fill="none" strokeLinecap="round" />
        </g>
        {/* front arm (gives, takes, raises a phone) */}
        <g transform={`translate(14,-205) rotate(${armAngle})`}>
          <rect x={-9} y={0} width={18} height={86} rx={9} fill={shirt} /><circle cx={0} cy={90} r={11} fill={skin} />
          {pose.hold ? <g transform={`translate(0,100) rotate(${-armAngle})`}>{pose.hold}</g> : null}
        </g>
        {/* the name tag above the head, never at the feet (the subtitle strip is below them in a close-up) */}
        {label ? <g transform={`scale(${facing},1)`}>
          <rect x={-70} y={-352} width={140} height={34} rx={17} fill="rgba(30,40,55,0.82)" />
          <text x={0} y={-328} textAnchor="middle" fontSize={22} fontWeight={800} fill="#fff" fontFamily={FONT}>{label}</text>
        </g> : null}
      </g>
    );
  };

/** Where a person's front hand is (stage units), for an object travelling between hands. */
function handAt(x: number, y: number, s: number, facing: number, reach: number, raise = 0) {
  const ang = ((-20 - reach * 55 - raise * 95) * Math.PI) / 180;
  const sx = 14, sy = -205, L = 100;
  const hx = sx - Math.sin(ang) * L, hy = sy + Math.cos(ang) * L;
  return { x: x + hx * s * facing, y: y + hy * s };
}


/** A thing the beat names (an icon or library picture), or a plain chip with the part's text when the plan named no picture. */
const Thing: React.FC<{ obj?: { src?: string; label?: string; chip?: string }; size?: number; label?: boolean }> = ({ obj, size = 120, label = true }) => {
  if (!obj) return null;
  if (!obj.src) return <Chip text={obj.chip ?? ""} size={size} />;
  return (
    <g>
      <image href={assetUrl(obj.src)} x={-size / 2} y={-size / 2} width={size} height={size} preserveAspectRatio="xMidYMid meet" />
      {label && obj.label ? <g>
        <rect x={-obj.label.length * 7.5 - 14} y={size / 2 + 4} width={obj.label.length * 15 + 28} height={32} rx={16} fill="rgba(255,255,255,0.92)" stroke="#2b3a4a" strokeWidth={2} />
        <text x={0} y={size / 2 + 27} textAnchor="middle" fontSize={22} fontWeight={800} fill="#2b3a4a" fontFamily={FONT}>{obj.label}</text>
      </g> : null}
    </g>
  );
};

/** A plain chip: a rounded token with a short text (an amount, a word); never a drawing of any particular object. */
const Chip: React.FC<{ text: string; size?: number }> = ({ text, size = 110 }) => {
  const w = Math.max(size * 0.9, text.length * size * 0.17 + 30), h = size * 0.56;
  return (
    <g>
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={h * 0.32} fill="#fdf3d7" stroke="#6b5a2e" strokeWidth={4} />
      {text ? <text x={0} y={h * 0.16} textAnchor="middle" fontSize={h * 0.46} fontWeight={900} fill="#3b2f12" fontFamily={FONT}>{text}</text> : null}
    </g>
  );
};

const Cross: React.FC<{ k: number; size?: number }> = ({ k, size = 90 }) => (
  <g transform={`scale(${k})`} opacity={Math.min(1, k)}>
    <path d={`M${-size},${-size} L${size},${size} M${size},${-size} L${-size},${size}`} stroke="#d63031" strokeWidth={size * 0.22} strokeLinecap="round" />
  </g>
);
const Tick: React.FC<{ k: number; size?: number }> = ({ k, size = 90 }) => (
  <g transform={`scale(${k})`} opacity={Math.min(1, k)}>
    <path d={`M${-size},0 L${-size * 0.3},${size * 0.7} L${size},${-size * 0.8}`} stroke="#27ae60" strokeWidth={size * 0.22} fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </g>
);
const Bubble: React.FC<{ k: number; children: React.ReactNode }> = ({ k, children }) => (
  <g transform={`scale(${k})`} opacity={Math.min(1, k)}>
    <circle cx={-40} cy={70} r={10} fill="#fff" stroke="#2c3e50" strokeWidth={3} /><circle cx={-20} cy={48} r={14} fill="#fff" stroke="#2c3e50" strokeWidth={3} />
    <ellipse cx={20} cy={-10} rx={86} ry={62} fill="#fff" stroke="#2c3e50" strokeWidth={4} />
    <g transform="translate(20,-10)">{children}</g>
  </g>
);
/** A card that shows a short text: a tag on a thing, a sign, a screen, an "ok" screen with a tick, or text written stroke by stroke. */
const TextCard: React.FC<{ text: string; style: string; reveal?: number }> = ({ text, style, reveal = 1 }) => {
  const big = style === "screen" || style === "ok";
  const fs = big ? 46 : style === "write" ? 32 : 26;
  const w = Math.max(big ? 200 : 90, text.length * fs * 0.6 + (style === "ok" ? 110 : 44)), h = big ? 120 : fs + 26;
  const fill = style === "ok" ? "#27ae60" : style === "screen" ? "#eaf2f8" : style === "tag" ? "#fff8e1" : "#ffffff";
  const ink = style === "ok" ? "#ffffff" : "#1f2a36";
  const id = `rv-${Math.round(w)}-${text.length}`;
  return (
    <g>
      {big ? <rect x={-w / 2 - 12} y={-h / 2 - 12} width={w + 24} height={h + 24} rx={26} fill="#1f2a36" /> : null}
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={big ? 18 : 12} fill={fill} stroke={big ? "none" : "#2b3a4a"} strokeWidth={3} />
      {style === "ok" ? <path d={`M${-w / 2 + 22},2 L${-w / 2 + 40},20 L${-w / 2 + 72},-18`} stroke="#fff" strokeWidth={10} fill="none" strokeLinecap="round" strokeLinejoin="round" /> : null}
      <clipPath id={id}><rect x={-w / 2} y={-h / 2} width={w * reveal} height={h} /></clipPath>
      <g clipPath={`url(#${id})`}>
        <text x={style === "ok" ? 30 : 0} y={fs * 0.36} textAnchor="middle" fontSize={fs} fontWeight={900} fill={ink} fontFamily={FONT}>{text}</text>
      </g>
    </g>
  );
};
/** A counter that changes: the old value struck out, the new value with an up or down arrow, under a short title. */
const NumberPanel: React.FC<{ title: string; before?: string; after: string; dir?: string; flip: number }> = ({ title, before, after, dir, flip }) => {
  const up = dir !== "down";
  return (
    <g>
      <rect x={-150} y={-110} width={300} height={220} rx={12} fill="#ffffff" stroke="#2c3e50" strokeWidth={4} />
      {title ? <><rect x={-150} y={-110} width={300} height={44} rx={12} fill="#1f3a5f" />
        <text x={0} y={-80} textAnchor="middle" fontSize={24} fontWeight={800} fill="#fff" fontFamily={FONT}>{title}</text></> : null}
      {before ? <g opacity={flip > 0.5 ? 0.6 : 1}>
        <text x={0} y={-22} textAnchor="middle" fontSize={34} fontWeight={800} fill="#7f8c8d" fontFamily={FONT}>{before}</text>
        {flip > 0.5 ? <line x1={-80} y1={-32} x2={80} y2={-36} stroke="#d63031" strokeWidth={5} /> : null}
      </g> : null}
      {flip > 0.5 ? <g>
        <text x={-10} y={58} textAnchor="middle" fontSize={50} fontWeight={900} fill={up ? "#1e8449" : "#c0392b"} fontFamily={FONT}>{after}</text>
        {dir ? <path d={up ? "M110,58 l18,-30 l18,30 z" : "M110,28 l18,30 l18,-30 z"} fill={up ? "#27ae60" : "#d63031"} /> : null}
      </g> : null}
    </g>
  );
};
/** A plain table on an empty stage, where a thing rests at the counter spot (beside a place the place's own counter is used). */
const Table: React.FC<{ x: number; w: number }> = ({ x, w }) => (
  <g>
    <rect x={x - w / 2} y={FEET - 190} width={w} height={190} fill="#b07a4f" />
    <rect x={x - w / 2 - 10} y={FEET - 204} width={w + 20} height={20} rx={6} fill="#8e5c36" />
  </g>
);

/** Travel along a gentle arc from a to b while t goes 0 -> 1. */
function arc(a: { x: number; y: number }, b: { x: number; y: number }, t: number, lift = 60) {
  return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t) - Math.sin(t * Math.PI) * lift };
}

// the stage's named spots (stage units), the same as rulebook/saanche.json
const SPOTS: Record<string, [number, number]> = { center: [500, 300], counter: [570, 340], far: [840, 250], left: [330, 330], right: [670, 330], pile: [300, 560], meter: [650, 600] };
type XY = { x: number; y: number };
type Obj = { visible: boolean; holder: number | null; at: XY | null; pos?: XY; scale: number; opacity: number; tag?: string; size?: number; popAt?: number };

export const ActionStage: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  const actors: any[] = el.actors ?? [];
  const objs: Record<string, any> = el.objects ?? {};
  const parts: any[] = [...(el.parts ?? [])].sort((a, b) => a.at - b.at);
  const k = pop(frame, fps, el.at ?? 0) * (el.until !== undefined ? 1 - lin(frame, el.until, el.until + 15) : 1);
  if (k <= 0.001) return null;
  const slots: XY[] = actors.length >= 2 ? [{ x: 260, y: FEET }, { x: 740, y: FEET }] : actors.length === 1 ? [{ x: 260, y: FEET }] : [];
  const facing = (i: number) => (i === 0 ? 1 : -1);
  const spot = (name?: string): XY => { const s = SPOTS[name ?? "center"] ?? SPOTS.center; return { x: s[0], y: s[1] }; };
  const pose = actors.map((a) => ({ reach: 0, raise: 0, shake: 0, nod: 0, mood: (a.mood ?? "neutral") as string }));
  const st: Record<string, Obj> = {};
  const get = (name: string) => st[name] ?? (st[name] = { visible: false, holder: null, at: null, scale: 1, opacity: 1 });
  const hand = (i: number) => { const a = slots[i] ?? spot("center"); const p = pose[i] ?? { reach: 0, raise: 0 }; return handAt(a.x, a.y, 1, facing(i), p.reach, p.raise); };
  const where = (name: string): XY => { const o = get(name); if (o.pos) return o.pos; if (o.holder !== null && slots[o.holder]) return hand(o.holder); return o.at ?? spot("center"); };
  const head = (i: number): XY => ({ x: (slots[i] ?? spot("center")).x, y: FEET - 330 });
  const targetOf = (to: any): XY => (to?.actor !== undefined ? hand(to.actor) : to?.object ? { ...where(to.object), y: where(to.object).y - 40 } : spot(to?.spot));
  const signs: any[] = [], meters: any[] = [], copies: any[] = [], marks: any[] = [], compares: any[] = [];

  for (const p of parts) {
    if (frame < p.at) continue;
    const t = (d: number) => lin(frame, p.at, p.at + d);
    if (p.part === "hold" && slots[p.actor]) {
      const o = get(p.object); o.visible = true; o.holder = p.actor; o.at = null; o.pos = undefined; o.size = 100;
      if (p.text && objs[p.object]?.src) o.tag = p.text;
      pose[p.actor].reach = lerp(pose[p.actor].reach, p.reach ?? 0.25, t(18));
    } else if (p.part === "give" && slots[p.from] && slots[p.to]) {
      const o = get(p.object); const tt = t(24);
      o.visible = true; if (p.text && objs[p.object]?.src) o.tag = p.text;
      const half = tt < 0.5;
      pose[p.from].reach = half ? lerp(pose[p.from].reach, 1, tt * 2) : lerp(1, 0.2, (tt - 0.5) * 2);
      pose[p.to].reach = half ? lerp(pose[p.to].reach, 1, tt * 2) : lerp(1, 0.6, (tt - 0.5) * 2);
      if (tt < 1) { o.pos = arc(hand(p.from), hand(p.to), tt); } else { o.pos = undefined; o.holder = p.to; o.at = null; }
      if (frame >= p.at + 44) pose[p.to].mood = "pleased";
    } else if (p.part === "move") {
      const o = get(p.object); const from = where(p.object); const to = targetOf(p.to);
      const tt = t(p.back ? 40 : 30); o.visible = true;
      if (p.back) {
        const q = tt < 0.5 ? tt * 2 : (1 - tt) * 2;
        o.pos = q > 0 && tt < 1 ? arc(from, to, q, 30) : undefined;
        if (o.holder !== null && pose[o.holder]) pose[o.holder].raise = q * 0.8;
      } else if (tt < 1) {
        o.pos = arc(from, to, tt);
        if (p.into_target) { o.scale = 1 - 0.7 * tt; o.opacity = 1 - Math.max(0, (tt - 0.6) / 0.4); }
      } else {
        o.pos = undefined;
        if (p.into_target) { o.visible = false; }
        else if (p.to?.actor !== undefined) { o.holder = p.to.actor; o.at = null; }
        else { o.holder = null; o.at = to; }
      }
    } else if (p.part === "transform") {
      const a = get(p.object), b = get(p.into); const tt = t(24);
      b.visible = true; b.holder = a.holder; b.at = a.at ?? where(p.object); b.pos = a.pos; b.size = a.size;
      a.opacity = 1 - tt; b.opacity = tt; if (tt >= 1) a.visible = false;
    } else if (p.part === "show_text") {
      if (p.until === undefined || frame < p.until) signs.push(p);
    } else if (p.part === "meter") {
      meters.push(p);
    } else if (p.part === "appear") {
      const multi = (p.items ?? []).length > 1 || p.layout === "pile";
      if (multi) copies.push(p);
      else { const o = get(p.object); o.visible = true; o.holder = null; o.at = spot(p.spot); o.popAt = p.at; o.size = p.spot === "right" || p.spot === "center" ? 200 : 130; }
    } else if (p.part === "refuse" || p.part === "accept") {
      const moving = frame < p.at + 36;
      if (p.actor !== undefined && pose[p.actor]) {
        if (p.part === "refuse") { pose[p.actor].shake = moving ? Math.sin((frame - p.at) / 2.2) : 0; pose[p.actor].mood = "refusing"; }
        else { pose[p.actor].nod = moving ? Math.abs(Math.sin((frame - p.at) / 4)) : 0; pose[p.actor].mood = "pleased"; pose[p.actor].reach = 0.4; }
      }
      marks.push(p);
    } else if (p.part === "compare") {
      compares.push(p);
    }
  }

  const atCounter = Object.values(st).some((o) => o.visible && o.at && Math.abs(o.at.x - SPOTS.counter[0]) < 2);
  const objectNodes = Object.entries(st).filter(([, o]) => o.visible).map(([name, o]) => {
    const pos = where(name);
    const s = (o.popAt !== undefined ? pop(frame, fps, o.popAt) : 1) * o.scale;
    return <g key={name} transform={`translate(${pos.x},${pos.y}) scale(${s})`} opacity={o.opacity}>
      <Thing obj={objs[name]} size={o.size ?? 110} />
      {o.tag ? <g transform={`translate(0,${-(o.size ?? 110) / 2 - 26})`}><TextCard text={o.tag} style="tag" /></g> : null}
    </g>;
  });
  const copyNodes = copies.flatMap((p, j) => {
    const items: number[] = p.items ?? [];
    if (p.layout === "pile") {
      const start = items[0] ?? p.at, stop = p.end ?? start + items.length * 6;
      const n = Math.max(0, Math.min(items.length, Math.floor((Math.min(frame, stop) - start) / 6)));
      const nodes = Array.from({ length: n }, (_, i) => <g key={`${j}-${i}`} transform={`translate(${SPOTS.pile[0] + (i % 3) * 40 - 40},${FEET - 40 - Math.floor(i / 3) * 26})`}><Thing obj={objs[p.object]} size={64} label={false} /></g>);
      if (frame >= start && frame < stop) nodes.push(<g key={`${j}-drop`} transform={`translate(${SPOTS.pile[0]},${lerp(120, FEET - 60 - Math.floor(n / 3) * 26, ((frame - start) % 6) / 6)})`}><Thing obj={objs[p.object]} size={64} label={false} /></g>);
      return nodes;
    }
    const n = items.length, cols = n <= 4 ? n : n <= 8 ? 4 : 6, size = n <= 4 ? 170 : n <= 8 ? 140 : 110, rows = Math.ceil(n / Math.max(1, cols));
    const c0 = spot(p.spot ?? "center");
    return items.map((at, i) => {
      const c = i % cols, r = Math.floor(i / cols);
      const x = c0.x + (c - (cols - 1) / 2) * (size + 24);
      const y = FEET - 80 - (rows - 1 - r) * (size + 30) - size / 2;
      const kk = pop(frame, fps, at);
      return kk > 0 ? <g key={`${j}-${i}`} transform={`translate(${x},${y}) scale(${kk})`}><Thing obj={objs[p.object]} size={size} label={i === n - 1} />
        <g transform={`translate(${size / 2 - 6},${-size / 2 + 6})`}><circle r={20} fill="#2e86de" /><text y={8} textAnchor="middle" fontSize={22} fontWeight={900} fill="#fff" fontFamily={FONT}>{i + 1}</text></g></g> : null;
    });
  });
  const markNodes = marks.map((p, i) => {
    const pile = copies.find((c) => c.object === p.object && c.layout === "pile");
    const kk = pop(frame, fps, p.at + 6);
    if (pile) {                       // one more than the limit: it bounces off the pile with a cross
      const b = lin(frame, p.at + 6, p.at + 30);
      return <g key={`m${i}`} transform={`translate(${560 + b * 120},${FEET - 520 - Math.sin(b * Math.PI) * 60})`} opacity={1 - b * 0.3}>
        <Thing obj={objs[p.object]} size={64} label={false} /><Cross k={kk} size={40} /></g>;
    }
    const pos = where(p.object);
    return <g key={`m${i}`} transform={`translate(${pos.x},${pos.y})`}>{p.part === "refuse" ? <Cross k={kk} size={Math.min(120, (get(p.object).size ?? 110) * 0.55)} />
      : <g transform={`translate(${(get(p.object).size ?? 110) * 0.55},${-(get(p.object).size ?? 110) * 0.5})`}><Tick k={kk} size={60} /></g>}</g>;
  });
  const signNodes = signs.map((p, i) => {
    const kk = pop(frame, fps, p.at);
    const style = p.style ?? "sign";
    if (style === "bubble" && p.on?.actor !== undefined) {
      const h = head(p.on.actor);
      return <g key={`s${i}`} transform={`translate(${h.x + 40},${FEET - 430})`}><Bubble k={kk}>
        {p.inside ? <g><Thing obj={objs[p.inside]} size={60} label={false} /><text x={46} y={14} fontSize={48} fontWeight={900} fill="#e67e22" fontFamily={FONT}>{p.text}</text></g>
          : <text x={0} y={14} textAnchor="middle" fontSize={40} fontWeight={900} fill="#2c3e50" fontFamily={FONT}>{p.text}</text>}
      </Bubble></g>;
    }
    let pos: XY;
    if (p.on?.object) { const o = where(p.on.object); pos = style === "tag" || style === "write" ? { x: o.x, y: o.y - 90 } : { x: o.x < 500 ? o.x - 120 : o.x + 140, y: FEET - 430 }; }
    else if (p.on?.actor !== undefined) { const h = head(p.on.actor); pos = style === "tag" ? { x: h.x, y: h.y } : { x: h.x < 500 ? h.x - 110 : h.x + 150, y: FEET - 430 }; }
    else pos = spot("center");
    const reveal = style === "write" ? lin(frame, p.at, p.at + 40) : 1;
    return <g key={`s${i}`} transform={`translate(${pos.x},${pos.y}) scale(${kk * (style === "ok" || style === "screen" ? 0.85 : 1)})`}><TextCard text={p.text ?? ""} style={style} reveal={reveal} /></g>;
  });
  const meterNodes = meters.map((p, i) => {
    if (p.style === "number") {
      const x = p.on?.actor !== undefined ? (slots[p.on.actor]?.x ?? 500) : 500;
      const flip = lin(frame, p.at + 10, p.at + 30);
      return <g key={`n${i}`} transform={`translate(${Math.min(840, Math.max(160, x))},300) scale(${0.92 * pop(frame, fps, p.at + i * 8)})`}>
        <NumberPanel title={p.title ?? ""} before={p.value_from} after={p.value_to ?? ""} dir={p.dir} flip={flip} /></g>;
    }
    const stop = p.end ?? p.at + 60;
    const level = Math.min(1, Math.max(0, (frame - p.at) / Math.max(1, stop - p.at))) * 0.92 + (frame >= stop ? 0.08 : 0);
    return <g key={`b${i}`} transform={`translate(${SPOTS.meter[0]},0)`}>
      <rect x={-50} y={FEET - 470} width={100} height={460} rx={20} fill="#ecf0f1" stroke="#2c3e50" strokeWidth={5} />
      <rect x={-38} y={FEET - 20 - 432 * level} width={76} height={432 * level} rx={12} fill={frame >= stop ? "#e74c3c" : "#f1c40f"} />
      {p.limit ? <><line x1={-70} y1={FEET - 452} x2={70} y2={FEET - 452} stroke="#d63031" strokeWidth={8} />
        <text x={90} y={FEET - 444} fontSize={38} fontWeight={900} fill="#d63031" fontFamily={FONT}>{p.limit}</text></> : null}
      {!p.limit && p.value_to ? <text x={0} y={FEET - 490} textAnchor="middle" fontSize={34} fontWeight={900} fill="#2c3e50" fontFamily={FONT}>{p.value_to}</text> : null}
    </g>;
  });
  const compareNodes = compares.map((p, i) => {
    const kk = pop(frame, fps, p.at);
    const l = spot("left"), r = spot("right");
    return <g key={`c${i}`} transform={`scale(1)`} opacity={Math.min(1, kk)}>
      <g transform={`translate(${l.x},${l.y}) scale(${kk})`}><Thing obj={objs[p.left]} size={170} label={false} />
        {p.left_text ? <g transform="translate(0,120)"><TextCard text={p.left_text} style="tag" /></g> : null}</g>
      <g transform={`translate(${r.x},${r.y}) scale(${kk})`}><Thing obj={objs[p.right]} size={170} label={false} />
        {p.right_text ? <g transform="translate(0,120)"><TextCard text={p.right_text} style="tag" /></g> : null}</g>
      <text x={500} y={l.y + 24} textAnchor="middle" fontSize={84} fontWeight={900} fill="#2c3e50" fontFamily={FONT}>{p.sign ?? "?"}</text>
    </g>;
  });

  return (
    <g opacity={Math.min(1, k)}>
      {atCounter && !el.on_place ? <Table x={SPOTS.counter[0] + 60} w={300} /> : null}
      {actors.map((a, i) => slots[i] ? <Actor key={`a${i}`} x={slots[i].x} y={slots[i].y} s={1} facing={facing(i)} look={a.look} main={a.main} label={a.label}
        pose={{ reach: pose[i].reach, raise: pose[i].raise, shake: pose[i].shake, nod: pose[i].nod, mood: pose[i].mood }} /> : null)}
      {copyNodes}{compareNodes}{objectNodes}{markNodes}{meterNodes}{signNodes}
    </g>
  );
};
