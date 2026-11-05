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
  if (female)
    return `<path d="M${cx - r * 1.02} ${cy + r * 0.25} Q${cx - r * 1.15} ${cy - r * 1.05} ${cx} ${cy - r * 1.02} Q${cx + r * 1.15} ${cy - r * 1.05} ${cx + r * 1.02} ${cy + r * 0.25} L${cx + r * 0.72} ${cy + r * 0.2} A${r * 0.9} ${r} 0 0 0 ${cx - r * 0.72} ${cy + r * 0.2} Z" fill="${hair}"/>`;
  return `<path d="M${cx - r * 0.98} ${cy - r * 0.18} A${r} ${r} 0 0 1 ${cx + r * 0.98} ${cy - r * 0.18} L${cx + r * 0.85} ${cy - r * 0.5} A${r} ${r * 0.7} 0 0 0 ${cx - r * 0.85} ${cy - r * 0.5} Z" fill="${hair}"/>`;
}

function shade(hex) {
  const n = parseInt(hex.slice(1), 16);
  const f = (v) => Math.max(0, Math.round(v * 0.72));
  return `#${((f(n >> 16) << 16) | (f((n >> 8) & 255) << 8) | f(n & 255)).toString(16).padStart(6, "0")}`;
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
  const back = arm(H, s, -0.09 * H * s, -0.75 * H, b1, b2, shade(top), armW);
  const front = arm(H, s, 0.12 * H * s, -0.76 * H, a1, a2, top, armW);
  const hx = opts.headDx || 0, hy = opts.headDy || 0;
  const head = `<g transform="translate(${hx.toFixed(1)},${hy.toFixed(1)})">` + face(H, opts.expr || "smile", skin) +
    headwear(H, L.headwear, L.hw || "#e7d9b8", L.hair || "#241b12", !!L.female) + `</g>`;
  const neck = `<rect x="${-0.025 * H}" y="${-0.80 * H}" width="${0.05 * H}" height="${0.05 * H}" fill="${skin}"/>`;
  // facing mirrors the whole body; the head offsets are inside the mirror so a shake reads the same either way
  return `<g transform="translate(0,${bob.toFixed(1)}) scale(${s},1)">` + back.svg + legs + body + neck + head + front.svg + `</g>`;
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
