// saanche: kriya ke saanche, the process templates (Task 046 Part D2, Navin's verdict of 1 November 2026: "process show nahi ho
// rahi hai ... jaise scanner phone scan, tab maja hai"). One stage (1000 x 620 units, feet on y = 600) that draws a template's
// actors, objects and amounts, timed by the step frames bie/brain/video/saanche.py computed. A world places the stage on its
// street (world.tsx), the canvas fits it into a node's cells (canvas.tsx): the same action in both modes.
//
// Everything is BIE's own drawing: big people (about half the stage tall) with hands that hold things, a phone in hand, simple
// moods (pleased, unsure, refusing), a head shake and a nod; BIE's own note and coin (the amount written on them, clearly not
// a replica of a real note: no portrait, no emblem, no bank name), a QR stand, a POS machine, a cheque, a passbook, a limit
// meter. The things the story names (salt, wheat, cloth) come in as image sources resolved from the icon index.
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
        {label ? <g transform={`scale(${facing},1)`}>
          <rect x={-70} y={14} width={140} height={34} rx={17} fill="rgba(30,40,55,0.82)" />
          <text x={0} y={38} textAnchor="middle" fontSize={22} fontWeight={800} fill="#fff" fontFamily={FONT}>{label}</text>
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

/** BIE's own banknote, by the rules of docs/bie/BIE_MONEY_OBJECTS.md (the same as the bie:note-* drawings): 1.6 : 1 with round
 *  corners (real notes are 1.95-2.5 : 1), BIE's own colour per amount, the amount written large, a white band with "BIE" and
 *  "नमूना · not money"; no portrait, emblem, issuer, promise, signature, number or security feature. */
export const Note: React.FC<{ text: string; w?: number }> = ({ text, w = 150 }) => {
  const n = Number(String(text).replace(/[^0-9]/g, "")) || 0;
  const col = n >= 2000 ? "#c2185b" : n >= 500 ? "#6d8b3a" : n >= 200 ? "#e6a23c" : n >= 100 ? "#7e57c2" : n >= 50 ? "#26a69a" : n >= 20 ? "#f57c00" : "#2a9d8f";
  const h = w / 1.6;
  return (
    <g>
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={14} fill={col} stroke="#2b2b2b" strokeWidth={4} />
      <text x={0} y={h * 0.08} textAnchor="middle" fontSize={h * 0.42} fontWeight={900} fill="#fff" fontFamily={FONT}>{text}</text>
      <rect x={-w / 2 + 6} y={h / 2 - h * 0.3} width={w - 12} height={h * 0.24} rx={6} fill="#ffffff" />
      <text x={-w / 2 + 14} y={h / 2 - h * 0.12} fontSize={h * 0.14} fontWeight={900} fill={col} fontFamily={FONT}>BIE</text>
      <text x={w / 2 - 10} y={h / 2 - h * 0.12} textAnchor="end" fontSize={h * 0.12} fontWeight={700} fill="#2b2b2b" fontFamily={FONT}>नमूना · not money</text>
    </g>
  );
};

/** BIE's own coin: a size and colour by amount, the amount written on it. */
export const Coin: React.FC<{ text: string; r?: number }> = ({ text, r = 34 }) => {
  const paise = /पैसे|paise|p$/i.test(text);
  const col = paise ? "#c9a227" : "#b0b7bf";
  return (
    <g>
      <circle cx={0} cy={0} r={r} fill={col} stroke="#6b5a1e" strokeWidth={3} />
      <circle cx={0} cy={0} r={r * 0.78} fill="none" stroke="#ffffff" strokeOpacity={0.5} strokeWidth={2} />
      <text x={0} y={r * 0.22} textAnchor="middle" fontSize={r * (text.length > 4 ? 0.48 : 0.62)} fontWeight={900} fill="#3b3b3b" fontFamily={FONT}>{text}</text>
      <text x={0} y={r * 0.66} textAnchor="middle" fontSize={r * 0.24} fontWeight={800} fill="#3b3b3b" opacity={0.75} fontFamily={FONT}>BIE</text>
    </g>
  );
};

/** A thing the story names (an icon or library picture), with an optional short label under it. */
const Thing: React.FC<{ obj?: { src?: string; label?: string }; size?: number; label?: boolean }> = ({ obj, size = 120, label = true }) => {
  if (!obj || !obj.src) return null;
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

const Phone: React.FC<{ screen?: string; ok?: boolean; glow?: number }> = ({ screen = "", ok = false, glow = 0 }) => (
  <g>
    {glow ? <circle cx={0} cy={0} r={90} fill="#2ecc71" opacity={0.25 * glow} /> : null}
    <rect x={-34} y={-62} width={68} height={124} rx={12} fill="#1f2a36" />
    <rect x={-28} y={-52} width={56} height={100} rx={6} fill={ok ? "#27ae60" : "#eaf2f8"} />
    {ok ? <path d="M-14,-14 L-3,-2 L16,-24" stroke="#fff" strokeWidth={6} fill="none" strokeLinecap="round" /> : null}
    {screen ? <text x={0} y={22} textAnchor="middle" fontSize={screen.length > 9 ? 9 : 11} fontWeight={900} fill={ok ? "#fff" : "#2b3a4a"} fontFamily={FONT}>{screen}</text> : null}
  </g>
);

/** The screen of a phone, big, beside the actor: what the close-up reads ("₹300 paid"). */
const PhoneCard: React.FC<{ title: string; amount: string; ok: boolean }> = ({ title, amount, ok }) => (
  <g>
    <rect x={-120} y={-170} width={240} height={340} rx={30} fill="#1f2a36" />
    <rect x={-104} y={-148} width={208} height={296} rx={18} fill={ok ? "#27ae60" : "#eaf2f8"} />
    {ok ? <path d="M-36,-60 L-8,-30 L44,-92" stroke="#fff" strokeWidth={14} fill="none" strokeLinecap="round" strokeLinejoin="round" /> : null}
    <text x={0} y={30} textAnchor="middle" fontSize={48} fontWeight={900} fill={ok ? "#fff" : "#2b3a4a"} fontFamily={FONT}>{amount}</text>
    <text x={0} y={82} textAnchor="middle" fontSize={30} fontWeight={800} fill={ok ? "#eafaf1" : "#2b3a4a"} fontFamily={FONT}>{title}</text>
  </g>
);

const QRStand: React.FC<{ scan?: number }> = ({ scan = 0 }) => {
  const cells: React.ReactNode[] = [];
  for (let r = 0; r < 9; r++) for (let c = 0; c < 9; c++) {
    const corner = (r < 3 && c < 3) || (r < 3 && c > 5) || (r > 5 && c < 3);
    const on = corner ? !(r % 3 === 1 && c % 3 === 1) : Math.abs(Math.sin(r * 7.1 + c * 3.7)) > 0.45;
    if (on) cells.push(<rect key={`${r}-${c}`} x={-45 + c * 10} y={-95 + r * 10} width={10} height={10} fill="#1b1b1b" />);
  }
  return (
    <g>
      <rect x={-8} y={0} width={16} height={60} fill="#7f8c8d" /><rect x={-40} y={56} width={80} height={10} rx={4} fill="#7f8c8d" />
      <rect x={-60} y={-110} width={120} height={120} rx={10} fill="#ffffff" stroke="#2c3e50" strokeWidth={4} />
      {cells}
      <rect x={-60} y={-142} width={120} height={30} rx={8} fill="#5f27cd" />
      <text x={0} y={-120} textAnchor="middle" fontSize={20} fontWeight={900} fill="#fff" fontFamily={FONT}>SCAN · PAY</text>
      {scan > 0 && scan < 1 ? <rect x={-56} y={-104 + scan * 104} width={112} height={6} fill="#e74c3c" opacity={0.85} /> : null}
    </g>
  );
};

const POS: React.FC<{ text?: string; ok?: boolean }> = ({ text = "", ok = false }) => (
  <g>
    <rect x={-60} y={-90} width={120} height={180} rx={18} fill="#34495e" />
    <rect x={-46} y={-76} width={92} height={60} rx={8} fill={ok ? "#27ae60" : "#bdc3c7"} />
    <text x={0} y={-38} textAnchor="middle" fontSize={text.length > 6 ? 16 : 20} fontWeight={900} fill="#fff" fontFamily={FONT}>{ok ? `✓ ${text}` : text}</text>
    {[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={-40 + c * 30} y={0 + r * 26} width={20} height={16} rx={4} fill="#95a5a6" />))}
  </g>
);

const Card: React.FC = () => (
  <g>
    <rect x={-50} y={-32} width={100} height={64} rx={8} fill="#2e86de" stroke="#1b4f72" strokeWidth={3} />
    <rect x={-38} y={-14} width={22} height={16} rx={3} fill="#f1c40f" />
    <rect x={-38} y={12} width={60} height={6} rx={3} fill="#ffffff" opacity={0.7} />
  </g>
);

const Cheque: React.FC<{ amount: string; write: number }> = ({ amount, write }) => (
  <g>
    <rect x={-210} y={-95} width={420} height={190} rx={10} fill="#fdf6e3" stroke="#8e7c55" strokeWidth={4} />
    <rect x={-210} y={-95} width={420} height={34} rx={10} fill="#d4c39a" />
    <text x={-190} y={-71} fontSize={20} fontWeight={800} fill="#5a4a2a" fontFamily={FONT}>CHEQUE · चेक</text>
    <line x1={-190} y1={-20} x2={190} y2={-20} stroke="#b9a77a" strokeWidth={2} />
    <line x1={-190} y1={20} x2={60} y2={20} stroke="#b9a77a" strokeWidth={2} />
    <rect x={80} y={-2} width={110} height={44} rx={6} fill="#ffffff" stroke="#b9a77a" strokeWidth={2} />
    <clipPath id="cheque-write"><rect x={-190} y={-60} width={380 * write} height={120} /></clipPath>
    <g clipPath="url(#cheque-write)">
      <text x={135} y={30} textAnchor="middle" fontSize={26} fontWeight={900} fill="#1a3c8a" fontFamily={FONT}>{amount}</text>
      <path d="M40,62 q20,-24 40,0 t40,0 t40,-6" stroke="#1a3c8a" strokeWidth={3} fill="none" />
    </g>
  </g>
);

const Passbook: React.FC<{ title: string; before?: string; after: string; dir: "up" | "down"; flip: number }> = ({ title, before, after, dir, flip }) => (
  <g>
    <rect x={-150} y={-110} width={300} height={220} rx={12} fill="#ffffff" stroke="#2c3e50" strokeWidth={4} />
    <rect x={-150} y={-110} width={300} height={44} rx={12} fill="#1f3a5f" />
    <text x={0} y={-80} textAnchor="middle" fontSize={24} fontWeight={800} fill="#fff" fontFamily={FONT}>{title}</text>
    {before ? <g opacity={flip > 0.5 ? 0.6 : 1}>
      <text x={0} y={-22} textAnchor="middle" fontSize={34} fontWeight={800} fill="#7f8c8d" fontFamily={FONT}>{before}</text>
      {flip > 0.5 ? <line x1={-80} y1={-32} x2={80} y2={-36} stroke="#d63031" strokeWidth={5} /> : null}
    </g> : null}
    {flip > 0.5 ? <g>
      <text x={-10} y={58} textAnchor="middle" fontSize={50} fontWeight={900} fill={dir === "up" ? "#1e8449" : "#c0392b"} fontFamily={FONT}>{after}</text>
      <path d={dir === "up" ? "M110,58 l18,-30 l18,30 z" : "M110,28 l18,30 l18,-30 z"} fill={dir === "up" ? "#27ae60" : "#d63031"} />
    </g> : null}
  </g>
);

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
const Counter: React.FC<{ x: number; w: number }> = ({ x, w }) => (
  <g>
    <rect x={x - w / 2} y={FEET - 190} width={w} height={190} fill="#b07a4f" />
    <rect x={x - w / 2 - 10} y={FEET - 204} width={w + 20} height={20} rx={6} fill="#8e5c36" />
  </g>
);

/** Travel along a gentle arc from a to b while t goes 0 → 1. */
function arc(a: { x: number; y: number }, b: { x: number; y: number }, t: number, lift = 60) {
  return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t) - Math.sin(t * Math.PI) * lift };
}

export const ActionStage: React.FC<{ el: any; frame: number; fps: number }> = ({ el, frame, fps }) => {
  const st: Record<string, number> = el.step_at ?? {};
  const actors: any[] = el.actors ?? [];
  const obj: Record<string, any> = el.objects ?? {};
  const amt: Record<string, string> = el.amounts ?? {};
  const k = pop(frame, fps, el.at ?? 0) * (el.until !== undefined ? 1 - lin(frame, el.until, el.until + 15) : 1);
  if (k <= 0.001) return null;
  const S = 1.0;
  const L = { x: 260, y: FEET }, R = { x: 740, y: FEET };
  const actor = (i: number) => actors[i] ?? { look: 7 + i, mood: "neutral" };
  const t = el.template as string;
  const after = (name: string, d = 0) => frame >= (st[name] ?? 1e9) + d;
  const prog = (name: string, d = 24) => lin(frame, st[name] ?? 1e9, (st[name] ?? 1e9) + d);
  let body: React.ReactNode = null;

  if (t === "hand_over") {
    const g = prog("give"), tk = prog("take");
    const a = handAt(L.x, L.y, S, 1, g * (1 - tk * 0.6)), b = handAt(R.x, R.y, S, -1, tk);
    const p = tk > 0 ? arc(a, b, tk) : a;
    body = <>
      <Actor x={L.x} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label} pose={{ reach: g * (1 - tk * 0.6), mood: actor(0).mood }} />
      <Actor x={R.x} y={R.y} s={S} facing={-1} look={actor(1).look} main={actor(1).main} label={actor(1).label} pose={{ reach: tk, mood: after("take", 20) ? "pleased" : actor(1).mood }} />
      <g transform={`translate(${p.x},${p.y})`}><Thing obj={obj.thing} size={110} /></g>
    </>;
  } else if (t === "pay_change") {
    const pay = prog("pay"), goods = prog("goods"), ch = prog("change");
    const buyerHand = handAt(L.x, L.y, S, 1, Math.max(pay * (1 - goods), ch * 0.9 + goods * 0.6));
    const sellerHand = handAt(R.x, R.y, S, -1, Math.max(pay, ch));
    const note = pay < 1 ? arc(handAt(L.x, L.y, S, 1, pay), handAt(R.x, R.y, S, -1, pay), pay) : sellerHand;
    const counterTop = { x: R.x - 160, y: FEET - 260 };
    const gp = goods > 0 ? arc(counterTop, handAt(L.x, L.y, S, 1, 0.6), goods, 40) : counterTop;
    const cp = ch > 0 ? arc(handAt(R.x, R.y, S, -1, 1), handAt(L.x, L.y, S, 1, 0.9), ch) : null;
    const changeIsCoin = (Number(String(amt.change ?? "").replace(/[^0-9]/g, "")) || 0) < 10;
    body = <>
      {el.on_place ? null : <Counter x={R.x - 120} w={300} />}
      {amt.price ? <g transform={`translate(${R.x - 70},${FEET - 330})`}><rect x={-46} y={-22} width={92} height={40} rx={8} fill="#fff8e1" stroke="#e0a100" strokeWidth={4} />
        <text x={0} y={8} textAnchor="middle" fontSize={24} fontWeight={900} fill="#2b2b2b" fontFamily={FONT}>{amt.price}</text></g> : null}
      <Actor x={R.x} y={R.y} s={S} facing={-1} look={actor(1).look} main={actor(1).main} label={actor(1).label} pose={{ reach: Math.max(pay, ch), mood: actor(1).mood }} />
      <Actor x={L.x} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label}
        pose={{ reach: Math.max(pay * (1 - goods), ch * 0.9), mood: after("change", 20) ? "pleased" : actor(0).mood }} />
      <g transform={`translate(${gp.x},${gp.y})`}><Thing obj={obj.goods} size={goods > 0.5 ? 100 : 120} /></g>
      {after("pay", -18) ? <g transform={`translate(${note.x},${note.y})`} opacity={after("change") ? Math.max(0.35, 1 - ch) : 1}><Note text={amt.paid ?? ""} w={140} /></g> : null}
      {cp ? <g transform={`translate(${cp.x},${cp.y - 30})`}>{changeIsCoin ? <Coin text={amt.change ?? ""} r={34} /> : <Note text={amt.change ?? ""} w={120} />}</g> : null}
    </>;
  } else if (t === "barter_swap") {
    const off = prog("offer"), ask = prog("ask", 18), sw = prog("swap", 30);
    const aHand = handAt(L.x, L.y, S, 1, Math.max(off, sw)), bHand = handAt(R.x, R.y, S, -1, Math.max(off * 0.5, sw));
    const aPos = sw > 0 ? arc(aHand, bHand, sw, 80) : aHand, bPos = sw > 0 ? arc(bHand, aHand, sw, -40) : bHand;
    const yes = after("ask", 36);
    body = <>
      <Actor x={L.x} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label} pose={{ reach: Math.max(off, sw), mood: sw >= 1 ? "pleased" : ask > 0 && !yes ? "unsure" : actor(0).mood }} />
      <Actor x={R.x} y={R.y} s={S} facing={-1} look={actor(1).look} main={actor(1).main} label={actor(1).label} pose={{ reach: Math.max(off * 0.5, sw), mood: sw >= 1 ? "pleased" : ask > 0 && !yes ? "unsure" : actor(1).mood }} />
      <g transform={`translate(${aPos.x},${aPos.y})`}><Thing obj={obj.a_thing} size={100} /></g>
      <g transform={`translate(${bPos.x},${bPos.y})`}><Thing obj={obj.b_thing} size={100} /></g>
      {ask > 0 && sw < 0.3 ? <>
        <g transform={`translate(${L.x + 40},${FEET - 430})`}><Bubble k={ask}>{yes ? <Tick k={1} size={34} /> : <g><Thing obj={obj.b_thing} size={60} label={false} /><text x={46} y={14} fontSize={48} fontWeight={900} fill="#e67e22" fontFamily={FONT}>?</text></g>}</Bubble></g>
        <g transform={`translate(${R.x + 40},${FEET - 430})`}><Bubble k={ask}>{yes ? <Tick k={1} size={34} /> : <g><Thing obj={obj.a_thing} size={60} label={false} /><text x={46} y={14} fontSize={48} fontWeight={900} fill="#e67e22" fontFamily={FONT}>?</text></g>}</Bubble></g>
      </> : null}
    </>;
  } else if (t === "upi") {
    const sc = prog("scan", 20), scanLine = lin(frame, (st.scan ?? 1e9) + 10, (st.scan ?? 1e9) + 50);
    const paid = after("paid"), recv = after("received");
    const raise = Math.max(sc, 0) * (paid ? 0.8 : 1);
    const qr = { x: R.x - 170, y: FEET - 260 };
    body = <>
      {el.on_place ? null : <Counter x={R.x - 100} w={320} />}
      <g transform={`translate(${qr.x},${qr.y})`}><QRStand scan={scanLine} /></g>
      <Actor x={R.x + 20} y={R.y} s={S} facing={-1} look={actor(1).look} main={actor(1).main} label={actor(1).label}
        pose={{ raise: recv ? 0.55 : 0, mood: recv ? "pleased" : actor(1).mood, hold: <Phone screen={recv ? "received" : ""} ok={recv} /> }} />
      <Actor x={L.x} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label}
        pose={{ raise, mood: paid ? "pleased" : actor(0).mood, hold: <Phone screen={paid ? "paid" : ""} ok={paid} glow={paid ? 1 - lin(frame, st.paid, st.paid + 40) : 0} /> }} />
      {paid ? <g transform={`translate(${L.x - 40},${FEET - 470}) scale(${pop(frame, fps, st.paid) * 0.62})`}><PhoneCard title="paid" amount={amt.amount ?? ""} ok /></g> : null}
      {recv ? <g transform={`translate(${R.x + 150},${FEET - 470}) scale(${pop(frame, fps, st.received) * 0.62})`}><PhoneCard title="received" amount={amt.amount ?? ""} ok /></g> : null}
    </>;
  } else if (t === "card_tap") {
    const tap = prog("tap", 22), ok = after("approved");
    const pos = { x: R.x - 160, y: FEET - 300 };
    const cardFrom = handAt(L.x, L.y, S, 1, tap);
    const cp = arc(cardFrom, { x: pos.x - 10, y: pos.y - 120 }, tap, 30);
    body = <>
      {el.on_place ? null : <Counter x={R.x - 100} w={320} />}
      <g transform={`translate(${pos.x},${pos.y})`}><POS text={amt.amount ?? ""} ok={ok} /></g>
      {tap > 0.7 && !ok ? [1, 2, 3].map((i) => <path key={i} d={`M${pos.x - 70 - i * 14},${pos.y - 150} a${20 + i * 14},${20 + i * 14} 0 0 1 0,${40 + i * 28}`}
        stroke="#3498db" strokeWidth={5} fill="none" opacity={0.8 - i * 0.2} />) : null}
      <Actor x={R.x + 20} y={R.y} s={S} facing={-1} look={actor(1).look} main={actor(1).main} label={actor(1).label} pose={{ mood: ok ? "pleased" : actor(1).mood }} />
      <Actor x={L.x} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label} pose={{ reach: tap, mood: ok ? "pleased" : actor(0).mood }} />
      <g transform={`translate(${cp.x},${cp.y})`}><Card /></g>
    </>;
  } else if (t === "cheque") {
    // the payer writes the cheque (its amount written on, stroke by stroke), it travels to the bank and shrinks into it, then
    // the bank gives way to the two passbooks: the payer's balance goes down (red arrow), the payee's goes up (green arrow)
    const w = prog("write", 40), hand = prog("hand", 30), bal = after("balances");
    const flip = lin(frame, (st.balances ?? 1e9) + 10, (st.balances ?? 1e9) + 30);
    const bank = { x: 840, y: 250 };
    const cq = hand > 0 ? arc({ x: 520, y: 300 }, { x: bank.x, y: bank.y + 20 }, hand, 50) : { x: 520, y: 300 };
    const scale = 1 - hand * 0.62;
    const a = amt.amount ?? "";
    const bankFade = bal ? 1 - lin(frame, st.balances, st.balances + 12) : 1;
    body = <>
      {bankFade > 0 ? <g transform={`translate(${bank.x},${bank.y})`} opacity={bankFade}>
        <rect x={-110} y={-90} width={220} height={150} rx={14} fill="#1f3a5f" />
        <text x={0} y={-50} textAnchor="middle" fontSize={30} fontWeight={900} fill="#fff7e0" fontFamily={FONT}>बैंक</text>
        <rect x={-80} y={-30} width={160} height={70} rx={8} fill="#9fd3ff" opacity={0.6} />
      </g> : null}
      <Actor x={170} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label} pose={{ reach: Math.max(w * 0.4, hand), mood: actor(0).mood }} />
      {!bal ? <g transform={`translate(${cq.x},${cq.y}) scale(${scale * pop(frame, fps, (st.write ?? 1e9) - 6)})`}><Cheque amount={a} write={w} /></g> : null}
      {bal ? <>
        <g transform={`translate(500,300) scale(${0.92 * pop(frame, fps, st.balances)})`}>
          <Passbook title={actor(0).label || "payer"} before={amt.payer_before} after={amt.payer_after ?? `− ${a}`} dir="down" flip={flip} />
        </g>
        <g transform={`translate(820,300) scale(${0.92 * pop(frame, fps, st.balances + 8)})`}>
          <Passbook title={actor(1).label || "payee"} before={amt.payee_before} after={amt.payee_after ?? `+ ${a}`} dir="up" flip={flip} />
        </g>
      </> : null}
    </>;
  } else if (t === "coin_count") {
    const start = st.count ?? 1e9, stop = st.limit ?? 1e9;
    const n = Math.max(0, Math.min(18, Math.floor((Math.min(frame, stop) - start) / 6)));
    const level = Math.min(1, Math.max(0, (frame - start) / Math.max(1, stop - start))) * 0.92 + (frame >= stop ? 0.08 : 0);
    const bounce = frame >= stop ? lin(frame, stop + 6, stop + 30) : 0;
    const coin = obj.coin;
    const coinNode = (key: number, x: number, y: number) => <g key={key} transform={`translate(${x},${y})`}>
      {coin && coin.src ? <image href={assetUrl(coin.src)} x={-34} y={-34} width={68} height={68} /> : <Coin text={amt.each ?? ""} r={34} />}
    </g>;
    body = <>
      {Array.from({ length: n }, (_, i) => coinNode(i, 300 + (i % 3) * 40 - 40, FEET - 40 - Math.floor(i / 3) * 26))}
      {frame >= start && frame < stop ? coinNode(99, 300, lerp(120, FEET - 60 - Math.floor(n / 3) * 26, ((frame - start) % 6) / 6)) : null}
      <g transform="translate(650,0)">
        <rect x={-50} y={FEET - 470} width={100} height={460} rx={20} fill="#ecf0f1" stroke="#2c3e50" strokeWidth={5} />
        <rect x={-38} y={FEET - 20 - 432 * level} width={76} height={432 * level} rx={12} fill={frame >= stop ? "#e74c3c" : "#f1c40f"} />
        <line x1={-70} y1={FEET - 452} x2={70} y2={FEET - 452} stroke="#d63031" strokeWidth={8} />
        <text x={90} y={FEET - 444} fontSize={38} fontWeight={900} fill="#d63031" fontFamily={FONT}>{amt.limit ?? ""}</text>
      </g>
      {frame >= stop ? <g transform={`translate(${560 + bounce * 120},${FEET - 520 - Math.sin(bounce * Math.PI) * 60})`} opacity={1 - bounce * 0.3}>
        {coinNode(100, 0, 0)}<g transform="translate(0,0)"><Cross k={pop(frame, fps, stop + 8)} size={40} /></g>
      </g> : null}
    </>;
  } else if (t === "refuse" || t === "accept") {
    const shown = pop(frame, fps, (st.show ?? 1e9));
    const at = st[t] ?? 1e9;
    const moving = frame >= at && frame < at + 36;
    const shake = t === "refuse" && moving ? Math.sin((frame - at) / 2.2) : 0;
    const nod = t === "accept" && moving ? Math.abs(Math.sin((frame - at) / 4)) : 0;
    const mark = pop(frame, fps, at + 6);
    body = <>
      <Actor x={L.x} y={L.y} s={S} facing={1} look={actor(0).look} main={actor(0).main} label={actor(0).label}
        pose={{ shake, nod, mood: frame >= at ? (t === "refuse" ? "refusing" : "pleased") : "unsure", reach: t === "accept" && frame >= at ? 0.4 : 0 }} />
      <g transform={`translate(680,${FEET - 300}) scale(${shown})`}>
        <Thing obj={obj.thing} size={220} />
        {frame >= at ? (t === "refuse" ? <Cross k={mark} size={120} /> : <g transform="translate(120,-110)"><Tick k={mark} size={70} /></g>) : null}
      </g>
    </>;
  } else if (t === "count_stack") {
    const items: number[] = el.items ?? [];
    const n = items.length;
    const cols = n <= 4 ? n : n <= 8 ? 4 : 6;
    const size = n <= 4 ? 170 : n <= 8 ? 140 : 110;
    const rows = Math.ceil(n / Math.max(1, cols));
    body = <>{items.map((at, i) => {
      const c = i % cols, r = Math.floor(i / cols);
      const x = STAGE_W / 2 + (c - (cols - 1) / 2) * (size + 24);
      const y = FEET - 80 - (rows - 1 - r) * (size + 30) - size / 2;
      const kk = pop(frame, fps, at);
      return kk > 0 ? <g key={i} transform={`translate(${x},${y}) scale(${kk})`}><Thing obj={obj.thing} size={size} label={i === n - 1} />
        <g transform={`translate(${size / 2 - 6},${-size / 2 + 6})`}><circle r={20} fill="#2e86de" /><text y={8} textAnchor="middle" fontSize={22} fontWeight={900} fill="#fff" fontFamily={FONT}>{i + 1}</text></g></g> : null;
    })}</>;
  }
  return <g opacity={Math.min(1, k)}>{body}</g>;
};
