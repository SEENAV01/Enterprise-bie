// The parametric character rig of BIE's showing engine (Phase 1, agreement of 3 November 2026 §2.3; rebuilt from the
// v2 demo's builder.py semantics — dist/people.js itself was never committed). One rig, parametric looks (skin, top,
// bottom, head-wear, hair, gender, size), poses with hand positions, held items, walk, nod, shake, expressions.
// No real persons. Every function is pure and returns an SVG string; the engine positions it (feet at the origin).

// Pose = [a1, a2, b1, b2]: front-arm shoulder and elbow angles, back-arm shoulder and elbow angles, in degrees,
// measured from straight down, rotating toward the facing side. Identical numbers to the v2 demo's builder.py.
import { svgBounds } from "./boxes.mjs";

export const POSES = {
  stand: [8, 5, 8, 5], give: [80, 0, 10, 5], receive: [62, 18, 10, 5], hold: [20, 85, 10, 5], holdBoth: [22, 80, 22, 80],
  think: [28, 145, 10, 5], point: [120, 5, 10, 5], shrug: [40, 110, 40, 110], wave: [150, 25, 10, 5], carry: [160, 40, 10, 5],
  write: [35, 75, 10, 5], walk: [10, 5, 10, 5], refuse: [55, 105, 10, 5],
  pull: [84, 6, 78, 10], raise: [172, 4, 10, 5],          // Sloman book (5 Nov 2026): a tug of war; a hand raised (confess, vote, ask)
};

// Looks: named parameter sets. Every field can also be given directly (a look object instead of a name).
export const LOOKS = {
  ramu:     { skin: "#c98850", top: "#e8863a", bottom: "#f3ead6", headwear: "turban", hw: "#fff3dd", hair: "#2b2017" },
  mohan:    { skin: "#b97745", top: "#3a7bd5", bottom: "#2e3440", headwear: "cap", hw: "#24466e", hair: "#241b12" },
  sita:     { skin: "#c98850", top: "#c2447a", bottom: "#8f2f5c", female: true, hair: "#241b12" },
  kamla:    { skin: "#a8663a", top: "#2fa08c", bottom: "#1d6e60", female: true, hair: "#2b2017" },
  raju:     { skin: "#b97745", top: "#7b61ff", bottom: "#2e3440", hair: "#241b12" },
  villager: { skin: "#c98850", top: "#8a9b56", bottom: "#efe6cf", headwear: "turban", hw: "#e7d9b8", hair: "#2b2017" },
  oil:      { skin: "#a8663a", top: "#c9a400", bottom: "#4a3b2a", headwear: "cap", hw: "#8a6d1f", hair: "#241b12" },
  salt:     { skin: "#b97745", top: "#2fb463", bottom: "#f3ead6", headwear: "turban", hw: "#dff0e3", hair: "#2b2017" },
  herder:   { skin: "#9c5c32", top: "#a9713c", bottom: "#6b4a26", headwear: "turban", hw: "#d8c49a", hair: "#241b12" },
  shop:     { skin: "#b97745", top: "#d96a2b", bottom: "#4a3b2a", headwear: "cap", hw: "#a34e1c", hair: "#241b12", apron: "#f3ead6" },
  // Roles for the Sloman economics book (5 November 2026): generic people known by their clothes and kit, never a real
  // person. Extra fields (drawn only when present, so the looks above stay as they were): coat (long coat or robe, its
  // sleeves too), collar (white bands), vest (sleeveless jacket; stripe: reflective band), tie, badge (ID card on a
  // lanyard), stetho, tape (tailor's tape), belt, shawl, sash (over a woman's shoulder), bag (box | school | basket on
  // the back, bagColor), cane, shorts, glasses, shades, beard, moustache, bandage; head-wear helmet, hardhat, police,
  // dupatta, bun.
  officer:      { skin: "#b97745", top: "#f1efe6", bottom: "#4a4f5a", vest: "#5b6b7f", glasses: true, hair: "#241b12" },
  doctor:       { skin: "#c98850", top: "#2a9d8f", bottom: "#2e3440", coat: "#fbfbf8", stetho: true, hair: "#241b12" },
  patient:      { skin: "#b97745", top: "#9cc3e0", bottom: "#7fa9c9", bandage: true, hair: "#241b12" },
  police:       { skin: "#a8663a", top: "#b59a6a", bottom: "#9c8256", headwear: "police", hw: "#7d6840", belt: "#4a3b2a", moustache: "#241b12", hair: "#241b12" },
  student:      { skin: "#c98850", top: "#e5484d", bottom: "#2e3440", bag: "school", bagColor: "#3a7bd5", hair: "#241b12" },
  teacher:      { skin: "#b97745", top: "#7b5cd6", bottom: "#5b3fae", female: true, sash: "#f2c14e", glasses: true, headwear: "bun", hair: "#241b12" },
  rider:        { skin: "#a8663a", top: "#f29f05", bottom: "#2e3440", headwear: "helmet", hw: "#e5484d", bag: "box", bagColor: "#e5484d", hair: "#241b12" },
  clerk:        { skin: "#c98850", top: "#dfe8f3", bottom: "#4a4f5a", badge: "#3a7bd5", glasses: true, hair: "#241b12" },
  banker:       { skin: "#b97745", top: "#f4f7fa", bottom: "#2e3440", tie: "#2459a6", badge: "#2459a6", hair: "#241b12" },
  trader:       { skin: "#c98850", top: "#dfe8f3", bottom: "#2e3440", coat: "#2d3748", tie: "#e5484d", hair: "#241b12" },
  economist:    { skin: "#b97745", top: "#f1efe6", bottom: "#6b4a26", vest: "#a0703d", glasses: true, hair: "#3a2b1c" },
  landlord:     { skin: "#c98850", top: "#f3ead6", bottom: "#f3ead6", shawl: "#8e2b3a", moustache: "#241b12", hair: "#241b12" },
  tout:         { skin: "#a8663a", top: "#e2558f", bottom: "#4a3b2a", headwear: "cap", hw: "#2e3440", shades: true, moustache: "#241b12", hair: "#241b12" },
  mason:        { skin: "#9c5c32", top: "#8a9b56", bottom: "#6b5a44", headwear: "hardhat", hw: "#f2c14e", vest: "#f08a3c", stripe: true, hair: "#241b12" },
  contractor:   { skin: "#b97745", top: "#f3ead6", bottom: "#f3ead6", vest: "#6b4a26", moustache: "#241b12", shades: true, hair: "#241b12" },
  tailor:       { skin: "#c98850", top: "#f3ead6", bottom: "#4a3b2a", tape: "#f2c14e", glasses: true, hair: "#241b12" },
  teaPicker:    { skin: "#9c5c32", top: "#2fa35b", bottom: "#1d6e60", female: true, headwear: "dupatta", hw: "#f29f05", bag: "basket", bagColor: "#a0703d", hair: "#241b12" },
  weaver:       { skin: "#a8663a", top: "#f3ead6", bottom: "#f3ead6", shawl: "#c2447a", headwear: "turban", hw: "#3a7bd5", hair: "#241b12" },
  oldMan:       { skin: "#b97745", top: "#f3ead6", bottom: "#f3ead6", hair: "#dcdcdc", beard: "#ececec", glasses: true, shawl: "#8a6d3b", cane: true },
  oldWoman:     { skin: "#c98850", top: "#efe6cf", bottom: "#d8cbb0", female: true, hair: "#dcdcdc", headwear: "bun", sash: "#8a9b56", glasses: true, cane: true },
  child:        { skin: "#c98850", top: "#f2c14e", bottom: "#3a7bd5", shorts: true, bag: "school", bagColor: "#e5484d", hair: "#241b12" },
  girl:         { skin: "#b97745", top: "#e2558f", bottom: "#c2447a", female: true, bag: "school", bagColor: "#2a9d8f", hair: "#241b12" },
  farmWoman:    { skin: "#a8663a", top: "#e0533d", bottom: "#a3273a", female: true, headwear: "dupatta", hw: "#f2c14e", hair: "#241b12" },
  worker:       { skin: "#9c5c32", top: "#4a7fb5", bottom: "#3d6a99", headwear: "cap", hw: "#2e4a6e", hair: "#241b12" },
  executive:    { skin: "#c98850", top: "#f4f7fa", bottom: "#2e3440", coat: "#3a4250", tie: "#7b5cd6", hair: "#241b12" },
  judge:        { skin: "#b97745", top: "#ffffff", bottom: "#1f2328", coat: "#1f2328", collar: true, glasses: true, hair: "#3a2b1c" },
  engineer:     { skin: "#a8663a", top: "#3a7bd5", bottom: "#2e3440", headwear: "hardhat", hw: "#ffffff", badge: "#2fa35b", hair: "#241b12" },
  unionLeader:  { skin: "#a8663a", top: "#f3ead6", bottom: "#f3ead6", shawl: "#d6454f", glasses: true, moustache: "#241b12", hair: "#241b12" },
  halwai:       { skin: "#c98850", top: "#ffffff", bottom: "#f3ead6", apron: "#f2c14e", moustache: "#241b12", hair: "#241b12" },
  foreignMan:   { skin: "#f1c9a5", top: "#5b7fb8", bottom: "#c8b48a", hair: "#b8893a" },
  foreignWoman: { skin: "#f1c9a5", top: "#2a9d8f", bottom: "#1d6e60", female: true, hair: "#8a5a2b" },
};

const rad = (d) => (d * Math.PI) / 180;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** Front-hand position for a pose, relative to the feet. The same forward kinematics as the v2 demo's builder.hand():
 *  shoulder at (0.12H·s, −0.76H), upper arm 0.17H at a1, forearm 0.16H at a1+a2. */
export function handAt(H, s, pose) {
  const [a1, a2] = (Array.isArray(pose) ? pose : POSES[pose] || POSES.stand);
  return handAtAngles(H, s, a1, a2);
}

export function handAtAngles(H, s, a1, a2) {
  const sx = 0.12 * H * s, sy = -0.76 * H;
  const ex = sx + Math.sin(rad(a1)) * 0.17 * H * s, ey = sy + Math.cos(rad(a1)) * 0.17 * H;
  return [ex + Math.sin(rad(a1 + a2)) * 0.16 * H * s, ey + Math.cos(rad(a1 + a2)) * 0.16 * H];
}

function arm(H, s, sx, sy, a1, a2, color, width) {
  const ex = sx + Math.sin(rad(a1)) * 0.17 * H * s, ey = sy + Math.cos(rad(a1)) * 0.17 * H;
  const hx = ex + Math.sin(rad(a1 + a2)) * 0.16 * H * s, hy = ey + Math.cos(rad(a1 + a2)) * 0.16 * H;
  return { svg: `<path d="M${sx.toFixed(1)} ${sy.toFixed(1)} L${ex.toFixed(1)} ${ey.toFixed(1)} L${hx.toFixed(1)} ${hy.toFixed(1)}" stroke="${color}" stroke-width="${width.toFixed(1)}" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`, hand: [hx, hy] };
}

function face(H, expr, skin) {
  const r = 0.105 * H, cx = 0.015 * H, cy = -0.885 * H;
  const ex = 0.038 * H, ey = cy - 0.012 * H;
  const eyes = `<circle cx="${cx + ex}" cy="${ey}" r="${0.011 * H}" fill="#241b12"/><circle cx="${cx + ex * 0.15}" cy="${ey}" r="${0.011 * H}" fill="#241b12"/>`;
  const mw = 0.045 * H, mx = cx + 0.028 * H, my = cy + 0.052 * H;
  let mouth, brow = "";
  if (expr === "happy") mouth = `<path d="M${mx - mw} ${my - 0.006 * H} Q${mx} ${my + 0.035 * H} ${mx + mw * 0.7} ${my - 0.006 * H} Z" fill="#7a3327"/>`;
  else if (expr === "frown" || expr === "refusing") { mouth = `<path d="M${mx - mw} ${my + 0.014 * H} Q${mx} ${my - 0.02 * H} ${mx + mw * 0.7} ${my + 0.014 * H}" stroke="#7a3327" stroke-width="${0.013 * H}" fill="none" stroke-linecap="round"/>`; brow = `<path d="M${cx + ex - 0.025 * H} ${ey - 0.035 * H} L${cx + ex + 0.02 * H} ${ey - 0.022 * H}" stroke="#241b12" stroke-width="${0.01 * H}" stroke-linecap="round"/>`; }
  else if (expr === "sad") { mouth = `<path d="M${mx - mw} ${my + 0.012 * H} Q${mx} ${my - 0.018 * H} ${mx + mw * 0.7} ${my + 0.012 * H}" stroke="#7a3327" stroke-width="${0.013 * H}" fill="none" stroke-linecap="round"/>`; brow = `<path d="M${cx + ex - 0.022 * H} ${ey - 0.024 * H} L${cx + ex + 0.02 * H} ${ey - 0.036 * H}" stroke="#241b12" stroke-width="${0.01 * H}" stroke-linecap="round"/>`; }
  else if (expr === "surprised") mouth = `<circle cx="${mx}" cy="${my}" r="${0.018 * H}" fill="#7a3327"/>`;
  else mouth = `<path d="M${mx - mw} ${my - 0.004 * H} Q${mx} ${my + 0.022 * H} ${mx + mw * 0.7} ${my - 0.004 * H}" stroke="#7a3327" stroke-width="${0.013 * H}" fill="none" stroke-linecap="round"/>`;
  return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${skin}"/>` + eyes + brow + mouth;
}

function headwear(H, kind, color, hair, female) {
  const cx = 0.015 * H, cy = -0.885 * H, r = 0.105 * H;
  if (kind === "turban")
    return `<path d="M${cx - r * 1.08} ${cy - r * 0.02} A${r * 1.08} ${r * 1.18} 0 0 1 ${cx + r * 1.08} ${cy - r * 0.02} Q${cx} ${cy - r * 0.34} ${cx - r * 1.08} ${cy - r * 0.02} Z" fill="${color}" stroke="${shade(color, 0.8)}" stroke-width="${0.014 * H}" stroke-linejoin="round"/>` +
           `<path d="M${cx - r * 0.98} ${cy - r * 0.42} Q${cx} ${cy - r * 0.78} ${cx + r * 0.98} ${cy - r * 0.42}" stroke="${shade(color, 0.82)}" stroke-width="${0.016 * H}" fill="none"/>` +
           `<path d="M${cx - r * 0.82} ${cy - r * 0.74} Q${cx + r * 0.1} ${cy - r * 1.04} ${cx + r * 0.86} ${cy - r * 0.6}" stroke="${shade(color, 0.82)}" stroke-width="${0.014 * H}" fill="none"/>` +
           `<circle cx="${cx + r * 0.62}" cy="${cy - r * 1.0}" r="${r * 0.26}" fill="${color}" stroke="${shade(color, 0.8)}" stroke-width="${0.012 * H}"/>`;
  if (kind === "cap")
    return `<path d="M${cx - r * 0.95} ${cy - r * 0.35} A${r * 0.97} ${r * 0.9} 0 0 1 ${cx + r * 0.95} ${cy - r * 0.35} L${cx + r * 0.8} ${cy - r * 0.12} L${cx - r * 0.8} ${cy - r * 0.12} Z" fill="${color}"/>`;
  if (kind === "helmet" || kind === "hardhat" || kind === "police" || kind === "dupatta" || kind === "bun")
    return moreHeadwear(H, kind, color, hair, female, cx, cy, r);
  if (female)
    return `<path d="M${cx - r * 1.02} ${cy + r * 0.25} Q${cx - r * 1.15} ${cy - r * 1.05} ${cx} ${cy - r * 1.02} Q${cx + r * 1.15} ${cy - r * 1.05} ${cx + r * 1.02} ${cy + r * 0.25} L${cx + r * 0.72} ${cy + r * 0.2} A${r * 0.9} ${r} 0 0 0 ${cx - r * 0.72} ${cy + r * 0.2} Z" fill="${hair}"/>`;
  return `<path d="M${cx - r * 0.98} ${cy - r * 0.18} A${r} ${r} 0 0 1 ${cx + r * 0.98} ${cy - r * 0.18} L${cx + r * 0.85} ${cy - r * 0.5} A${r} ${r * 0.7} 0 0 0 ${cx - r * 0.85} ${cy - r * 0.5} Z" fill="${hair}"/>`;
}

function shade(hex) {
  const n = parseInt(hex.slice(1), 16);
  const f = (v) => Math.max(0, Math.round(v * 0.72));
  return `#${((f(n >> 16) << 16) | (f((n >> 8) & 255) << 8) | f(n & 255)).toString(16).padStart(6, "0")}`;
}

const f1 = (v) => (Math.round(v * 10) / 10).toString();

// ---------------------------------------------------------------- the role looks' kit (Sloman book, 5 Nov 2026)
function femaleHair(cx, cy, r, hair) {
  return `<path d="M${cx - r * 1.02} ${cy + r * 0.25} Q${cx - r * 1.15} ${cy - r * 1.05} ${cx} ${cy - r * 1.02} Q${cx + r * 1.15} ${cy - r * 1.05} ${cx + r * 1.02} ${cy + r * 0.25} L${cx + r * 0.72} ${cy + r * 0.2} A${r * 0.9} ${r} 0 0 0 ${cx - r * 0.72} ${cy + r * 0.2} Z" fill="${hair}"/>`;
}

function moreHeadwear(H, kind, color, hair, female, cx, cy, r) {
  const d = shade(color);
  if (kind === "helmet")          // an open-face riding helmet: the shell over the head and the back, a visor band
    return `<path d="M${f1(cx - r * 1.12)} ${f1(cy + r * 0.38)} A${f1(r * 1.13)} ${f1(r * 1.16)} 0 0 1 ${f1(cx + r * 1.08)} ${f1(cy - r * 0.22)} L${f1(cx + r * 0.32)} ${f1(cy - r * 0.42)} Q${f1(cx - r * 0.52)} ${f1(cy - r * 0.34)} ${f1(cx - r * 0.66)} ${f1(cy + r * 0.38)} Z" fill="${color}" stroke="${d}" stroke-width="${f1(0.012 * H)}" stroke-linejoin="round"/>` +
      `<path d="M${f1(cx - r * 0.4)} ${f1(cy - r * 0.5)} Q${f1(cx + r * 0.4)} ${f1(cy - r * 0.62)} ${f1(cx + r * 1.12)} ${f1(cy - r * 0.3)}" stroke="#2b2b33" stroke-width="${f1(0.028 * H)}" fill="none" stroke-linecap="round" opacity="0.75"/>` +
      `<path d="M${f1(cx - r * 0.9)} ${f1(cy - r * 0.6)} Q${f1(cx - r * 0.3)} ${f1(cy - r * 1.05)} ${f1(cx + r * 0.4)} ${f1(cy - r * 0.95)}" stroke="#ffffff" stroke-width="${f1(0.014 * H)}" fill="none" stroke-linecap="round" opacity="0.45"/>`;
  if (kind === "hardhat")         // a construction hard hat with a brim and a ridge
    return `<path d="M${f1(cx - r * 0.95)} ${f1(cy - r * 0.32)} A${f1(r * 0.97)} ${f1(r * 0.98)} 0 0 1 ${f1(cx + r * 0.95)} ${f1(cy - r * 0.32)} Z" fill="${color}" stroke="${d}" stroke-width="${f1(0.01 * H)}"/>` +
      `<rect x="${f1(cx - r * 1.18)}" y="${f1(cy - r * 0.42)}" width="${f1(r * 2.45)}" height="${f1(r * 0.17)}" rx="${f1(r * 0.08)}" fill="${color}" stroke="${d}" stroke-width="${f1(0.008 * H)}"/>` +
      `<path d="M${f1(cx)} ${f1(cy - r * 1.28)} L${f1(cx)} ${f1(cy - r * 0.45)}" stroke="${d}" stroke-width="${f1(0.016 * H)}"/>`;
  if (kind === "police")          // a peaked cap: a crown wider at the top, a band with a round badge, the peak forward
    return `<path d="M${f1(cx - r * 0.92)} ${f1(cy - r * 0.42)} L${f1(cx - r * 1.12)} ${f1(cy - r * 0.98)} Q${f1(cx)} ${f1(cy - r * 1.22)} ${f1(cx + r * 1.12)} ${f1(cy - r * 0.98)} L${f1(cx + r * 0.92)} ${f1(cy - r * 0.42)} Z" fill="${color}" stroke="${d}" stroke-width="${f1(0.01 * H)}"/>` +
      `<rect x="${f1(cx - r * 0.94)}" y="${f1(cy - r * 0.62)}" width="${f1(r * 1.88)}" height="${f1(r * 0.24)}" fill="${d}"/>` +
      `<circle cx="${f1(cx + r * 0.2)}" cy="${f1(cy - r * 0.78)}" r="${f1(r * 0.17)}" fill="#e6c25a" stroke="#a8862a" stroke-width="${f1(0.006 * H)}"/>` +
      `<path d="M${f1(cx + r * 0.1)} ${f1(cy - r * 0.42)} L${f1(cx + r * 1.32)} ${f1(cy - r * 0.3)} L${f1(cx + r * 0.1)} ${f1(cy - r * 0.26)} Z" fill="#2b2b33"/>`;
  if (kind === "dupatta")         // the hair, and a cloth over the head falling behind the shoulder
    return femaleHair(cx, cy, r, hair) +
      `<path d="M${f1(cx - r * 1.12)} ${f1(cy + r * 1.6)} Q${f1(cx - r * 1.35)} ${f1(cy - r * 0.6)} ${f1(cx - r * 0.2)} ${f1(cy - r * 1.12)} Q${f1(cx + r * 0.9)} ${f1(cy - r * 1.25)} ${f1(cx + r * 1.08)} ${f1(cy - r * 0.2)} L${f1(cx + r * 0.78)} ${f1(cy - r * 0.42)} Q${f1(cx + r * 0.3)} ${f1(cy - r * 0.95)} ${f1(cx - r * 0.55)} ${f1(cy - r * 0.62)} Q${f1(cx - r * 0.95)} ${f1(cy + r * 0.2)} ${f1(cx - r * 0.7)} ${f1(cy + r * 1.6)} Z" fill="${color}" stroke="${d}" stroke-width="${f1(0.008 * H)}" stroke-linejoin="round"/>`;
  // bun: the hair drawn close and a bun at the back of the head
  return (female ? femaleHair(cx, cy, r, hair)
    : `<path d="M${cx - r * 0.98} ${cy - r * 0.18} A${r} ${r} 0 0 1 ${cx + r * 0.98} ${cy - r * 0.18} L${cx + r * 0.85} ${cy - r * 0.5} A${r} ${r * 0.7} 0 0 0 ${cx - r * 0.85} ${cy - r * 0.5} Z" fill="${hair}"/>`) +
    `<circle cx="${f1(cx - r * 0.98)}" cy="${f1(cy - r * 0.45)}" r="${f1(r * 0.36)}" fill="${hair}" stroke="${shade(hair)}" stroke-width="${f1(0.006 * H)}"/>`;
}

/** Things worn on the face: glasses or shades, a beard, a moustache, a head bandage (inside the head group). */
function faceKit(H, L) {
  const cx = 0.015 * H, cy = -0.885 * H, r = 0.105 * H, ex = 0.038 * H, ey = cy - 0.012 * H;
  let out = "";
  if (L.beard)
    out += `<path d="M${f1(cx - r * 0.86)} ${f1(cy + r * 0.05)} Q${f1(cx - r * 0.55)} ${f1(cy + r * 1.22)} ${f1(cx + r * 0.3)} ${f1(cy + r * 1.12)} Q${f1(cx + r * 0.95)} ${f1(cy + r * 0.95)} ${f1(cx + r * 0.98)} ${f1(cy + r * 0.2)} L${f1(cx + r * 0.78)} ${f1(cy + r * 0.62)} Q${f1(cx + r * 0.3)} ${f1(cy + r * 0.86)} ${f1(cx - r * 0.3)} ${f1(cy + r * 0.62)} Q${f1(cx - r * 0.6)} ${f1(cy + r * 0.4)} ${f1(cx - r * 0.66)} ${f1(cy + r * 0.05)} Z" fill="${L.beard}"/>`;
  const must = L.moustache || L.beard;
  if (must) {
    const mx = cx + 0.028 * H, my = cy + 0.034 * H;
    out += `<path d="M${f1(mx - 0.05 * H)} ${f1(my + 0.006 * H)} Q${f1(mx - 0.012 * H)} ${f1(my - 0.016 * H)} ${f1(mx)} ${f1(my - 0.004 * H)} Q${f1(mx + 0.012 * H)} ${f1(my - 0.016 * H)} ${f1(mx + 0.04 * H)} ${f1(my + 0.006 * H)} Q${f1(mx)} ${f1(my + 0.002 * H)} ${f1(mx - 0.05 * H)} ${f1(my + 0.006 * H)} Z" fill="${must}"/>`;
  }
  if (L.bandage)
    out += `<path d="M${f1(cx - r * 0.98)} ${f1(cy - r * 0.42)} Q${f1(cx)} ${f1(cy - r * 0.72)} ${f1(cx + r * 0.98)} ${f1(cy - r * 0.38)} L${f1(cx + r * 0.96)} ${f1(cy - r * 0.16)} Q${f1(cx)} ${f1(cy - r * 0.48)} ${f1(cx - r * 0.98)} ${f1(cy - r * 0.2)} Z" fill="#fbfbf8" stroke="#c9c6bd" stroke-width="${f1(0.005 * H)}"/>` +
      `<rect x="${f1(cx + r * 0.32)}" y="${f1(cy - r * 0.62)}" width="${f1(r * 0.3)}" height="${f1(r * 0.3)}" fill="#f2d7c9" stroke="#c9a08a" stroke-width="${f1(0.004 * H)}"/>`;
  if (L.glasses || L.shades) {
    const gr = 0.026 * H, a = [cx + ex, cx + ex * 0.15], fill = L.shades ? "#2b2b33" : "none";
    out += a.map((x) => `<circle cx="${f1(x)}" cy="${f1(ey)}" r="${f1(gr)}" fill="${fill}" stroke="#2b2b33" stroke-width="${f1(0.007 * H)}"/>`).join("") +
      `<path d="M${f1(a[1] + gr)} ${f1(ey)} L${f1(a[0] - gr)} ${f1(ey)} M${f1(a[1] - gr)} ${f1(ey)} L${f1(cx - r * 0.75)} ${f1(ey - 0.008 * H)}" stroke="#2b2b33" stroke-width="${f1(0.007 * H)}" fill="none"/>`;
  }
  return out;
}

/** Things carried on the back (drawn behind the body): a delivery box, a school bag, a picker's basket. */
function backKit(H, L) {
  const c = L.bagColor || "#e5484d", d = shade(c);
  if (L.bag === "box")
    return `<rect x="${f1(-0.34 * H)}" y="${f1(-0.82 * H)}" width="${f1(0.24 * H)}" height="${f1(0.26 * H)}" rx="${f1(0.015 * H)}" fill="${c}" stroke="${d}" stroke-width="${f1(0.01 * H)}"/>` +
      `<path d="M${f1(-0.34 * H)} ${f1(-0.74 * H)} L${f1(-0.1 * H)} ${f1(-0.74 * H)}" stroke="${d}" stroke-width="${f1(0.008 * H)}"/>` +
      `<rect x="${f1(-0.27 * H)}" y="${f1(-0.7 * H)}" width="${f1(0.1 * H)}" height="${f1(0.06 * H)}" rx="${f1(0.01 * H)}" fill="#ffffff" opacity="0.85"/>`;
  if (L.bag === "school")
    return `<rect x="${f1(-0.25 * H)}" y="${f1(-0.74 * H)}" width="${f1(0.15 * H)}" height="${f1(0.22 * H)}" rx="${f1(0.04 * H)}" fill="${c}" stroke="${d}" stroke-width="${f1(0.008 * H)}"/>` +
      `<rect x="${f1(-0.235 * H)}" y="${f1(-0.62 * H)}" width="${f1(0.12 * H)}" height="${f1(0.08 * H)}" rx="${f1(0.02 * H)}" fill="${d}"/>`;
  if (L.bag === "basket") {          // a conical basket on the back, hung from a strap over the head
    let weave = "";
    for (let i = 1; i < 4; i++) weave += `<path d="M${f1(-0.36 * H + i * 0.008 * H)} ${f1(-0.84 * H + i * 0.09 * H)} L${f1(-0.08 * H - i * 0.012 * H)} ${f1(-0.84 * H + i * 0.09 * H)}" stroke="${d}" stroke-width="${f1(0.006 * H)}"/>`;
    return `<path d="M${f1(-0.38 * H)} ${f1(-0.86 * H)} L${f1(-0.06 * H)} ${f1(-0.86 * H)} L${f1(-0.14 * H)} ${f1(-0.46 * H)} L${f1(-0.28 * H)} ${f1(-0.46 * H)} Z" fill="${c}" stroke="${d}" stroke-width="${f1(0.009 * H)}" stroke-linejoin="round"/>` + weave +
      `<path d="M${f1(-0.36 * H)} ${f1(-0.87 * H)} Q${f1(-0.3 * H)} ${f1(-0.93 * H)} ${f1(-0.2 * H)} ${f1(-0.92 * H)} Q${f1(-0.1 * H)} ${f1(-0.92 * H)} ${f1(-0.07 * H)} ${f1(-0.87 * H)}" fill="#3f6b1f"/>`;
  }
  return "";
}

/** Things worn on the body, over the top: coat or robe, vest, belt (drawn before the neck). */
function bodyKit(H, L, top) {
  let out = "";
  if (L.coat && !L.female) {
    const c = L.coat;
    out += `<path d="M${f1(-0.15 * H)} ${f1(-0.765 * H)} Q0 ${f1(-0.8 * H)} ${f1(0.15 * H)} ${f1(-0.765 * H)} L${f1(0.19 * H)} ${f1(-0.2 * H)} L${f1(-0.19 * H)} ${f1(-0.2 * H)} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${f1(0.008 * H)}"/>` +
      `<path d="M${f1(-0.04 * H)} ${f1(-0.785 * H)} L${f1(0.04 * H)} ${f1(-0.785 * H)} L${f1(0.012 * H)} ${f1(-0.5 * H)} L${f1(-0.012 * H)} ${f1(-0.5 * H)} Z" fill="${top}"/>` +
      `<path d="M${f1(-0.045 * H)} ${f1(-0.78 * H)} L${f1(-0.012 * H)} ${f1(-0.5 * H)} L${f1(-0.012 * H)} ${f1(-0.2 * H)} M${f1(0.045 * H)} ${f1(-0.78 * H)} L${f1(0.012 * H)} ${f1(-0.5 * H)}" stroke="${shade(c)}" stroke-width="${f1(0.008 * H)}" fill="none"/>`;
    if (L.collar) out += `<path d="M${f1(-0.012 * H)} ${f1(-0.77 * H)} L${f1(-0.02 * H)} ${f1(-0.7 * H)} L${f1(-0.002 * H)} ${f1(-0.7 * H)} Z M${f1(0.012 * H)} ${f1(-0.77 * H)} L${f1(0.02 * H)} ${f1(-0.7 * H)} L${f1(0.002 * H)} ${f1(-0.7 * H)} Z" fill="#ffffff" stroke="#c9c6bd" stroke-width="${f1(0.003 * H)}"/>`;
  }
  if (L.vest) {
    const c = L.vest;
    out += `<path d="M${f1(-0.13 * H)} ${f1(-0.765 * H)} L${f1(-0.045 * H)} ${f1(-0.785 * H)} L0 ${f1(-0.64 * H)} L${f1(0.045 * H)} ${f1(-0.785 * H)} L${f1(0.13 * H)} ${f1(-0.765 * H)} L${f1(0.166 * H)} ${f1(-0.43 * H)} Q0 ${f1(-0.395 * H)} ${f1(-0.166 * H)} ${f1(-0.43 * H)} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${f1(0.007 * H)}" stroke-linejoin="round"/>` +
      (L.stripe ? `<path d="M${f1(-0.155 * H)} ${f1(-0.55 * H)} L${f1(0.155 * H)} ${f1(-0.55 * H)}" stroke="#f4f7fa" stroke-width="${f1(0.028 * H)}" opacity="0.9"/>`
        : [0.6, 0.53, 0.46].map((y) => `<circle cx="0" cy="${f1(-y * H)}" r="${f1(0.008 * H)}" fill="${shade(c)}"/>`).join(""));
  }
  if (L.belt && !L.female)
    out += `<rect x="${f1(-0.172 * H)}" y="${f1(-0.455 * H)}" width="${f1(0.344 * H)}" height="${f1(0.032 * H)}" fill="${L.belt}"/>` +
      `<rect x="${f1(-0.022 * H)}" y="${f1(-0.46 * H)}" width="${f1(0.044 * H)}" height="${f1(0.042 * H)}" rx="${f1(0.006 * H)}" fill="#e6c25a" stroke="#a8862a" stroke-width="${f1(0.004 * H)}"/>`;
  if (L.sash && L.female)
    out += `<path d="M${f1(0.1 * H)} ${f1(-0.78 * H)} Q${f1(0.02 * H)} ${f1(-0.6 * H)} ${f1(-0.16 * H)} ${f1(-0.44 * H)}" stroke="${L.sash}" stroke-width="${f1(0.05 * H)}" fill="none" stroke-linecap="round"/>`;
  return out;
}

/** Things worn at the neck, over everything on the body: shawl, tie, ID badge, stethoscope, tailor's tape. */
function neckKit(H, L) {
  let out = "";
  if (L.shawl) {
    const c = L.shawl;
    out += `<path d="M${f1(-0.168 * H)} ${f1(-0.69 * H)} Q${f1(-0.16 * H)} ${f1(-0.81 * H)} 0 ${f1(-0.815 * H)} Q${f1(0.16 * H)} ${f1(-0.81 * H)} ${f1(0.168 * H)} ${f1(-0.69 * H)} L${f1(0.12 * H)} ${f1(-0.5 * H)} L${f1(0.075 * H)} ${f1(-0.52 * H)} Q${f1(0.04 * H)} ${f1(-0.7 * H)} 0 ${f1(-0.72 * H)} Q${f1(-0.04 * H)} ${f1(-0.7 * H)} ${f1(-0.075 * H)} ${f1(-0.52 * H)} L${f1(-0.12 * H)} ${f1(-0.5 * H)} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${f1(0.007 * H)}" stroke-linejoin="round"/>`;
  }
  if (L.tie)
    out += `<path d="M${f1(-0.014 * H)} ${f1(-0.79 * H)} L${f1(0.014 * H)} ${f1(-0.79 * H)} L${f1(0.01 * H)} ${f1(-0.762 * H)} L${f1(0.024 * H)} ${f1(-0.56 * H)} L0 ${f1(-0.53 * H)} L${f1(-0.024 * H)} ${f1(-0.56 * H)} L${f1(-0.01 * H)} ${f1(-0.762 * H)} Z" fill="${L.tie}" stroke="${shade(L.tie)}" stroke-width="${f1(0.004 * H)}"/>`;
  if (L.badge)
    out += `<path d="M${f1(-0.035 * H)} ${f1(-0.79 * H)} L${f1(0.045 * H)} ${f1(-0.64 * H)} M${f1(0.075 * H)} ${f1(-0.78 * H)} L${f1(0.045 * H)} ${f1(-0.64 * H)}" stroke="${L.badge}" stroke-width="${f1(0.008 * H)}" fill="none"/>` +
      `<rect x="${f1(0.018 * H)}" y="${f1(-0.645 * H)}" width="${f1(0.055 * H)}" height="${f1(0.07 * H)}" rx="${f1(0.006 * H)}" fill="#ffffff" stroke="${L.badge}" stroke-width="${f1(0.005 * H)}"/>` +
      `<rect x="${f1(0.026 * H)}" y="${f1(-0.635 * H)}" width="${f1(0.039 * H)}" height="${f1(0.016 * H)}" fill="${L.badge}"/>`;
  if (L.stetho)
    out += `<path d="M${f1(-0.05 * H)} ${f1(-0.79 * H)} Q${f1(-0.07 * H)} ${f1(-0.64 * H)} ${f1(0.0)} ${f1(-0.6 * H)} Q${f1(0.07 * H)} ${f1(-0.64 * H)} ${f1(0.05 * H)} ${f1(-0.79 * H)} M${f1(0.0)} ${f1(-0.6 * H)} L${f1(0.03 * H)} ${f1(-0.53 * H)}" stroke="#4a5568" stroke-width="${f1(0.011 * H)}" fill="none" stroke-linecap="round"/>` +
      `<circle cx="${f1(0.03 * H)}" cy="${f1(-0.52 * H)}" r="${f1(0.016 * H)}" fill="#c9ced6" stroke="#4a5568" stroke-width="${f1(0.006 * H)}"/>`;
  if (L.tape)
    out += `<path d="M${f1(-0.05 * H)} ${f1(-0.8 * H)} L${f1(-0.07 * H)} ${f1(-0.52 * H)} M${f1(0.05 * H)} ${f1(-0.8 * H)} L${f1(0.07 * H)} ${f1(-0.56 * H)}" stroke="${L.tape}" stroke-width="${f1(0.02 * H)}" fill="none"/>` +
      `<path d="M${f1(-0.05 * H)} ${f1(-0.78 * H)} L${f1(-0.068 * H)} ${f1(-0.54 * H)}" stroke="#2b2b33" stroke-width="${f1(0.006 * H)}" stroke-dasharray="${f1(0.004 * H)} ${f1(0.012 * H)}" fill="none"/>`;
  return out;
}

/** The whole person as SVG, feet at the origin.
 *  opts: look (name or params), h, facing (1|-1), arms ([a1,a2,b1,b2] or pose name), expr, walkPhase (null or 0..),
 *  headDx/headDy (shake/nod offsets, stage px), label (name tag text drawn by the engine, not here). */
export function drawPerson(opts) {
  const L = typeof opts.look === "string" ? (LOOKS[opts.look] || LOOKS.villager) : (opts.look || LOOKS.villager);
  const H = opts.h || 440, s = opts.facing || 1;
  const arms = Array.isArray(opts.arms) ? opts.arms : (POSES[opts.arms || "stand"] || POSES.stand);
  const [a1, a2, b1, b2] = arms;
  const skin = L.skin || "#c98850", top = L.top || "#3a7bd5", bottom = L.bottom || "#2e3440";
  const armW = 0.055 * H, legW = 0.065 * H;
  const wp = opts.walkPhase;
  const swing = wp == null ? 0 : Math.sin(wp * Math.PI * 2) * 16;
  const bob = wp == null ? 0 : -Math.abs(Math.sin(wp * Math.PI * 2)) * 0.018 * H;
  const hipY = -0.40 * H, hipX = 0.05 * H;
  const leg = (x0, a) => {
    const fx = x0 + Math.sin(rad(a)) * 0.38 * H, fy = hipY + Math.cos(rad(a)) * 0.40 * H;
    if (L.shorts) {                    // shorts: the cloth to the knee, the skin below
      const kx = x0 + (fx - x0) * 0.45, ky = hipY + (Math.min(0, fy) - hipY) * 0.45;
      return `<path d="M${x0} ${hipY} L${fx.toFixed(1)} ${Math.min(0, fy).toFixed(1)}" stroke="${skin}" stroke-width="${(legW * 0.8).toFixed(1)}" stroke-linecap="round"/>` +
        `<path d="M${x0} ${hipY} L${kx.toFixed(1)} ${ky.toFixed(1)}" stroke="${bottom}" stroke-width="${(legW * 1.15).toFixed(1)}" stroke-linecap="round"/>`;
    }
    return `<path d="M${x0} ${hipY} L${fx.toFixed(1)} ${Math.min(0, fy).toFixed(1)}" stroke="${bottom}" stroke-width="${legW}" stroke-linecap="round"/>`;
  };
  const legs = L.female
    ? `<path d="M${-0.17 * H} 0 L${-0.13 * H} ${hipY} L${0.13 * H} ${hipY} L${0.17 * H} 0 Z" fill="${bottom}"/>` +
      `<ellipse cx="${-0.07 * H}" cy="0" rx="${0.055 * H}" ry="${0.018 * H}" fill="#5a4632"/><ellipse cx="${0.07 * H}" cy="0" rx="${0.055 * H}" ry="${0.018 * H}" fill="#5a4632"/>`
    : leg(-hipX, -swing) + leg(hipX, swing) +
      `<ellipse cx="${-hipX - Math.sin(rad(swing)) * 0.38 * H}" cy="${-0.012 * H}" rx="${0.06 * H}" ry="${0.02 * H}" fill="#5a4632"/>` +
      `<ellipse cx="${hipX + Math.sin(rad(swing)) * 0.38 * H}" cy="${-0.012 * H}" rx="${0.06 * H}" ry="${0.02 * H}" fill="#5a4632"/>`;
  const bodyW = 0.17 * H;
  const body = L.female
    ? `<path d="M${-bodyW * 0.72} ${-0.76 * H} Q${-bodyW * 1.25} ${-0.45 * H} ${-bodyW * 0.95} ${hipY} L${bodyW * 0.95} ${hipY} Q${bodyW * 1.25} ${-0.45 * H} ${bodyW * 0.72} ${-0.76 * H} Q0 ${-0.80 * H} ${-bodyW * 0.72} ${-0.76 * H} Z" fill="${top}"/>` +
      `<path d="M${-bodyW * 0.5} ${-0.76 * H} Q${bodyW * 0.3} ${-0.6 * H} ${bodyW * 0.55} ${hipY - 0.02 * H}" stroke="${shade(top)}" stroke-width="${0.035 * H}" fill="none"/>`
    : `<path d="M${-bodyW * 0.85} ${-0.76 * H} Q0 ${-0.80 * H} ${bodyW * 0.85} ${-0.76 * H} L${bodyW} ${hipY - 0.02 * H} Q0 ${hipY + 0.035 * H} ${-bodyW} ${hipY - 0.02 * H} Z" fill="${top}"/>` +
      (L.apron ? `<path d="M${-bodyW * 0.6} ${-0.66 * H} L${bodyW * 0.6} ${-0.66 * H} L${bodyW * 0.72} ${hipY} Q0 ${hipY + 0.03 * H} ${-bodyW * 0.72} ${hipY} Z" fill="${L.apron}" opacity="0.92"/>` : "");
  const sleeve = L.coat && !L.female ? L.coat : top;   // a coat's sleeves cover the arms
  const back = arm(H, s, -0.09 * H * s, -0.75 * H, b1, b2, shade(sleeve), armW);
  const front = arm(H, s, 0.12 * H * s, -0.76 * H, a1, a2, sleeve, armW);
  const hx = opts.headDx || 0, hy = opts.headDy || 0;
  const head = `<g transform="translate(${hx.toFixed(1)},${hy.toFixed(1)})">` + face(H, opts.expr || "smile", skin) +
    headwear(H, L.headwear, L.hw || "#e7d9b8", L.hair || "#241b12", !!L.female) + faceKit(H, L) + `</g>`;
  const neck = `<rect x="${-0.025 * H}" y="${-0.80 * H}" width="${0.05 * H}" height="${0.05 * H}" fill="${skin}"/>`;
  const cx0 = back.hand[0], cy0 = back.hand[1] - 0.02 * H, cfoot = cx0 - (L.female ? 0.21 : 0.13) * H;   // a cane leaning back from the back hand
  const cane = L.cane ? `<path d="M${cx0.toFixed(1)} ${cy0.toFixed(1)} L${cfoot.toFixed(1)} 0" stroke="#7a4e22" stroke-width="${(0.018 * H).toFixed(1)}" stroke-linecap="round"/>` +
    `<path d="M${cx0.toFixed(1)} ${cy0.toFixed(1)} q${(0.03 * H).toFixed(1)} ${(-0.035 * H).toFixed(1)} ${(0.06 * H).toFixed(1)} ${(-0.005 * H).toFixed(1)}" stroke="#7a4e22" stroke-width="${(0.018 * H).toFixed(1)}" fill="none" stroke-linecap="round"/>` : "";
  // facing mirrors the whole body; the head offsets are inside the mirror so a shake reads the same either way
  return `<g transform="translate(0,${bob.toFixed(1)}) scale(${s},1)">` + backKit(H, L) + back.svg + cane + legs + body + bodyKit(H, L, top) + neck +
    neckKit(H, L) + head + front.svg + `</g>`;
}

/** Where the front hand is on screen for a drawn person (facing applied), relative to the feet. */
export function frontHand(opts) {
  const H = opts.h || 440, s = opts.facing || 1;
  const arms = Array.isArray(opts.arms) ? opts.arms : (POSES[opts.arms || "stand"] || POSES.stand);
  const [x, y] = handAtAngles(H, 1, arms[0], arms[1]);
  const wp = opts.walkPhase;
  const bob = wp == null ? 0 : -Math.abs(Math.sin(wp * Math.PI * 2)) * 0.018 * H;
  return [x * s, y + bob];
}

/** The box rule (Navin, 5 November 2026): a person's whole box and face box, feet at the origin, facing right, at
 *  height H — measured from the very drawing (the arms in their resting pose). The compiler keeps things and texts
 *  off a face; facing left mirrors both boxes. */
export function personBoxes(opts = {}) {
  const L = typeof opts.look === "string" ? (LOOKS[opts.look] || LOOKS.villager) : (opts.look || LOOKS.villager);
  const H = opts.h || 440;
  const whole = svgBounds(drawPerson({ ...opts, facing: 1, arms: opts.arms || "stand" })).box;
  const head = svgBounds(face(H, "smile", L.skin || "#c98850") + headwear(H, L.headwear, L.hw || "#e7d9b8", L.hair || "#241b12", !!L.female)).box;
  return { box: whole, face: head };
}

export const _test = { shade, esc };
