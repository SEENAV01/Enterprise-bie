// The first saanche of BIE's showing engine: parametric drawing functions (Phase 1, agreement §2.2; rebuilt from the
// v2 demo's builder.py vocabulary — dist/draw.js itself was never committed). Every saancha is a pure function of its
// parameters returning an SVG string; "bottom"-anchored ones stand on their origin (the floor), "center" ones are
// centred on it. No real currency designs (notes carry ₹ and a value in BIE's own colours), no real persons.

import { world } from "./worlds.mjs";
import { FAMILY_DRAWS } from "./families/index.mjs";
import { svgBounds } from "./boxes.mjs";

export const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
export const FONT = "'Noto Sans', 'Noto Sans Devanagari', sans-serif";
export const INK = "#2b2b33";

export function shade(hex, f = 0.72) {
  const n = parseInt(hex.slice(1), 16);
  const c = (v) => Math.max(0, Math.min(255, Math.round(v * f)));
  return `#${((c(n >> 16) << 16) | (c((n >> 8) & 255) << 8) | c(n & 255)).toString(16).padStart(6, "0")}`;
}

export function rnd(seed) {
  let x = seed >>> 0 || 1;
  return () => ((x = (x * 1103515245 + 12345) >>> 0), x / 4294967296);
}

export const label = (text, y, size, fill = INK, weight = 700) =>
  text ? `<text x="0" y="${y}" font-family=${JSON.stringify(FONT)} font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="middle">${esc(text)}</text>` : "";

// ---------------------------------------------------------------- things
function sack(p) {
  const w = p.w || 220, h = w * 1.0, c = p.content === "salt" ? "#e9e2d2" : "#d9a44a";
  const body = p.content === "salt" ? "#cbb98f" : "#c08a3e";
  return `<path d="M${-w * 0.46} ${-h * 0.08} Q${-w * 0.55} ${-h * 0.62} ${-w * 0.2} ${-h * 0.78} L${-w * 0.14} ${-h * 0.9} L${w * 0.14} ${-h * 0.9} L${w * 0.2} ${-h * 0.78} Q${w * 0.55} ${-h * 0.62} ${w * 0.46} ${-h * 0.08} Q0 ${h * 0.06} ${-w * 0.46} ${-h * 0.08} Z" fill="${body}" stroke="${shade(body)}" stroke-width="${w * 0.03}"/>` +
    `<path d="M${-w * 0.16} ${-h * 0.82} L${w * 0.16} ${-h * 0.82}" stroke="${shade(body, 0.6)}" stroke-width="${w * 0.05}" stroke-linecap="round"/>` +
    `<ellipse cx="0" cy="${-h * 0.9}" rx="${w * 0.14}" ry="${w * 0.05}" fill="${c}" stroke="${shade(body)}" stroke-width="${w * 0.02}"/>` +
    (p.label ? `<rect x="${-w * 0.3}" y="${-h * 0.56}" width="${w * 0.6}" height="${h * 0.26}" rx="${w * 0.04}" fill="#f7f1e5" stroke="${shade(body)}" stroke-width="${w * 0.02}"/>` + label(p.label, -h * 0.37, Math.min(w * 0.17, (w * 0.56) / Math.max(1, String(p.label).length) * 1.7)) : "");
}

function clothRoll(p) {
  const w = p.w || 170, h = w * 0.46, col = p.color || "#e0533d";
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${h * 0.24}" fill="${col}" stroke="${shade(col)}" stroke-width="${w * 0.025}"/>` +
    `<ellipse cx="${w * 0.5 - h * 0.24}" cy="0" rx="${h * 0.24}" ry="${h * 0.5}" fill="${shade(col, 0.85)}" stroke="${shade(col)}" stroke-width="${w * 0.02}"/>` +
    `<circle cx="${w * 0.5 - h * 0.24}" cy="0" r="${h * 0.18}" fill="#f7f1e5"/>` +
    `<path d="M${-w * 0.42} ${-h * 0.5} L${-w * 0.3} ${h * 0.5} M${-w * 0.18} ${-h * 0.5} L${-w * 0.06} ${h * 0.5} M${w * 0.06} ${-h * 0.5} L${w * 0.18} ${h * 0.5}" stroke="${shade(col, 0.86)}" stroke-width="${w * 0.02}"/>`;
}

function clothStack(p) {
  const w = p.w || 230, cols = ["#e0533d", "#3a7bd5", "#2fb463", "#c2447a"];
  return cols.map((c, i) => `<g transform="translate(0,${-i * w * 0.14})">` +
    `<rect x="${-w * 0.5}" y="${-w * 0.14}" width="${w}" height="${w * 0.14}" rx="${w * 0.045}" fill="${c}" stroke="${shade(c)}" stroke-width="${w * 0.016}"/>` +
    `<path d="M${-w * 0.5 + w * 0.08} ${-w * 0.14} L${-w * 0.5 + w * 0.08} 0" stroke="${shade(c, 0.85)}" stroke-width="${w * 0.014}"/></g>`).join("");
}

function saltPacket(p) {
  const w = p.w || 90, h = w * 1.3;
  return `<path d="M${-w * 0.5} ${-h} L${w * 0.5} ${-h} L${w * 0.5} 0 L${-w * 0.5} 0 Z" fill="#f2f7fb" stroke="#9db3c7" stroke-width="${w * 0.04}"/>` +
    `<path d="M${-w * 0.5} ${-h} L${-w * 0.36} ${-h * 1.08} L${w * 0.36} ${-h * 1.08} L${w * 0.5} ${-h} Z" fill="#dde9f2" stroke="#9db3c7" stroke-width="${w * 0.035}"/>` +
    `<rect x="${-w * 0.36}" y="${-h * 0.74}" width="${w * 0.72}" height="${h * 0.34}" rx="${w * 0.06}" fill="#3a7bd5"/>` +
    `<g transform="translate(0,${-h * 0.5})">` + label("नमक", 0, w * 0.26, "#ffffff", 800) + `</g>` +
    `<circle cx="0" cy="${-h * 0.2}" r="${w * 0.1}" fill="#dde9f2"/>`;
}

const NOTE_COLORS = { 2000: "#6b4ab0", 500: "#1f8a70", 200: "#d97b29", 100: "#c2447a", 50: "#4a7fb5", 20: "#7a8c3f", 10: "#8a5a44" };
function note(p) {
  const w = p.w || 170, v = p.value == null ? 500 : p.value, h = w * 0.46;
  const col = NOTE_COLORS[v] || "#1f8a70";
  const vs = typeof v === "number" ? String(v) : esc(v);
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${w * 0.03}" fill="${col}" stroke="${shade(col)}" stroke-width="${w * 0.02}"/>` +
    `<rect x="${-w * 0.46}" y="${-h * 0.42}" width="${w * 0.92}" height="${h * 0.84}" rx="${w * 0.02}" fill="none" stroke="#f7f1e5" stroke-width="${w * 0.012}" opacity="0.85"/>` +
    `<circle cx="${-w * 0.28}" cy="0" r="${h * 0.3}" fill="#f7f1e5" opacity="0.9"/>` +
    (p.bare ? "" : `<text x="${-w * 0.28}" y="${h * 0.12}" font-family=${JSON.stringify(FONT)} font-size="${h * 0.42}" font-weight="800" fill="${col}" text-anchor="middle">₹</text>` +
    `<text x="${w * 0.14}" y="${h * 0.18}" font-family=${JSON.stringify(FONT)} font-size="${h * 0.52}" font-weight="800" fill="#f7f1e5" text-anchor="middle">${vs}</text>`) +
    `<rect x="${w * 0.38}" y="${-h * 0.42}" width="${w * 0.05}" height="${h * 0.84}" fill="#f7f1e5" opacity="0.5"/>`;
}

function noteBundle(p) {
  const w = p.w || 190, v = p.value == null ? 500 : p.value, h = w * 0.46;
  const col = NOTE_COLORS[v] || "#1f8a70";
  const blank = (dy) => `<rect x="${-w * 0.5}" y="${-h * 0.5 + dy}" width="${w}" height="${h}" rx="${w * 0.03}" fill="${shade(col, 0.88)}" stroke="${shade(col, 0.7)}" stroke-width="${w * 0.015}"/>`;
  return blank(w * 0.1) + blank(w * 0.05) + note({ w, value: v, bare: p.bare }) +
    `<rect x="${-w * 0.09}" y="${-w * 0.26}" width="${w * 0.18}" height="${w * 0.42}" fill="#e8d9b0" stroke="#c9b683" stroke-width="${w * 0.015}"/>`;
}

const METALS = { gold: ["#f2c14e", "#b8860b"], silver: ["#d7dde4", "#8d99a6"], copper: ["#c77b4a", "#8a4f2d"] };
function coin(p) {
  const r = p.r || 40, [c, dark] = METALS[p.metal || "gold"] || METALS.gold;
  return `<circle r="${r}" fill="${c}" stroke="${dark}" stroke-width="${r * 0.09}"/>` +
    `<circle r="${r * 0.72}" fill="none" stroke="${dark}" stroke-width="${r * 0.05}" stroke-dasharray="${r * 0.12} ${r * 0.09}"/>` +
    `<circle cx="${-r * 0.3}" cy="${-r * 0.3}" r="${r * 0.14}" fill="#ffffff" opacity="0.55"/>`;
}

function coinStack(p) {
  const r = p.r || 45, n = p.n || 5, [c, dark] = METALS[p.metal || "gold"] || METALS.gold;
  let out = "";
  for (let i = 0; i < n; i++)
    out += `<g transform="translate(${(i % 2 ? 3 : -2)},${-i * r * 0.42})"><ellipse rx="${r}" ry="${r * 0.34}" fill="${c}" stroke="${dark}" stroke-width="${r * 0.07}"/></g>`;
  return out + `<ellipse cy="${-(n - 1) * r * 0.42 - r * 0.06}" rx="${r * 0.7}" ry="${r * 0.2}" fill="#ffffff" opacity="0.35"/>`;
}

function goldBar(p) {
  const w = p.w || 170, h = w * 0.42;
  return `<path d="M${-w * 0.38} ${-h} L${w * 0.38} ${-h} L${w * 0.5} 0 L${-w * 0.5} 0 Z" fill="#f2c14e" stroke="#b8860b" stroke-width="${w * 0.03}"/>` +
    `<path d="M${-w * 0.3} ${-h * 0.78} L${w * 0.3} ${-h * 0.78}" stroke="#ffffff" stroke-width="${w * 0.035}" opacity="0.5" stroke-linecap="round"/>` +
    `<g transform="translate(0,${-h * 0.28})">` + label("24K", 0, h * 0.4, "#8a6508", 800) + `</g>`;
}

function oilTin(p) {
  const w = p.w || 110, h = w * 1.2;
  return `<rect x="${-w * 0.5}" y="${-h}" width="${w}" height="${h}" rx="${w * 0.08}" fill="#c9a400" stroke="${shade("#c9a400")}" stroke-width="${w * 0.035}"/>` +
    `<rect x="${-w * 0.34}" y="${-h * 0.72}" width="${w * 0.68}" height="${h * 0.4}" rx="${w * 0.05}" fill="#f7f1e5"/>` +
    `<g transform="translate(0,${-h * 0.46})">` + label("तेल", 0, w * 0.26, "#8a6508", 800) + `</g>` +
    `<rect x="${w * 0.16}" y="${-h * 1.12}" width="${w * 0.16}" height="${h * 0.14}" fill="#8a6d1f"/>` +
    `<rect x="${-w * 0.2}" y="${-h * 1.06}" width="${w * 0.4}" height="${h * 0.07}" rx="${w * 0.03}" fill="#8a6d1f"/>`;
}

function matka(p) {
  const w = p.w || 130;
  return `<path d="M${-w * 0.18} ${-w * 0.92} Q${-w * 0.62} ${-w * 0.78} ${-w * 0.5} ${-w * 0.34} Q${-w * 0.4} 0 0 0 Q${w * 0.4} 0 ${w * 0.5} ${-w * 0.34} Q${w * 0.62} ${-w * 0.78} ${w * 0.18} ${-w * 0.92}" fill="#b5651d" stroke="${shade("#b5651d")}" stroke-width="${w * 0.03}"/>` +
    `<ellipse cx="0" cy="${-w * 0.92}" rx="${w * 0.19}" ry="${w * 0.07}" fill="#7a3f12" stroke="${shade("#b5651d")}" stroke-width="${w * 0.02}"/>` +
    `<path d="M${-w * 0.4} ${-w * 0.52} Q0 ${-w * 0.62} ${w * 0.4} ${-w * 0.52}" stroke="#e0a05f" stroke-width="${w * 0.035}" fill="none"/>`;
}

function bowl(p) {
  const w = p.w || 60;
  return `<path d="M${-w * 0.5} ${-w * 0.4} Q${-w * 0.45} 0 0 0 Q${w * 0.45} 0 ${w * 0.5} ${-w * 0.4} Z" fill="#c77b4a" stroke="${shade("#c77b4a")}" stroke-width="${w * 0.04}"/>` +
    `<ellipse cx="0" cy="${-w * 0.4}" rx="${w * 0.5}" ry="${w * 0.12}" fill="#e8c9a8" stroke="${shade("#c77b4a")}" stroke-width="${w * 0.03}"/>`;
}

function veg(p) {
  const w = p.w || 60;
  return `<ellipse cx="${-w * 0.22}" cy="${-w * 0.18}" rx="${w * 0.22}" ry="${w * 0.3}" transform="rotate(-18)" fill="#6b3fa0" stroke="${shade("#6b3fa0")}" stroke-width="${w * 0.03}"/>` +
    `<circle cx="${w * 0.22}" cy="${-w * 0.16}" r="${w * 0.22}" fill="#e0533d" stroke="${shade("#e0533d")}" stroke-width="${w * 0.03}"/>` +
    `<path d="M${w * 0.22} ${-w * 0.38} l${-w * 0.06} ${-w * 0.1} M${-w * 0.28} ${-w * 0.5} l${w * 0.05} ${-w * 0.08}" stroke="#2fb463" stroke-width="${w * 0.05}" stroke-linecap="round"/>`;
}

function wheat(p) {
  const w = p.w || 100, h = w * 1.15;
  let out = `<path d="M0 0 L0 ${-h * 0.62}" stroke="#b8860b" stroke-width="${w * 0.05}"/>` +
    `<path d="M${-w * 0.2} 0 L${-w * 0.06} ${-h * 0.5}" stroke="#b8860b" stroke-width="${w * 0.045}"/>` +
    `<path d="M${w * 0.2} 0 L${w * 0.06} ${-h * 0.5}" stroke="#b8860b" stroke-width="${w * 0.045}"/>`;
  for (const [bx, by, rot] of [[0, -h * 0.62, 0], [-w * 0.08, -h * 0.5, -14], [w * 0.08, -h * 0.5, 14]])
    for (let i = 0; i < 5; i++)
      out += `<g transform="translate(${bx},${by}) rotate(${rot})"><ellipse cx="0" cy="${-i * h * 0.072}" rx="${w * 0.085}" ry="${h * 0.05}" fill="#e8b84a" stroke="#b8860b" stroke-width="${w * 0.015}"/></g>`;
  return `<g transform="translate(0,${h * 0.5})">${out}</g>`;
}

function charpai(p) {
  const w = p.w || 430, h = w * 0.42, legH = h * 0.52, top = -legH - h * 0.16;
  let weave = "";
  for (let i = 1; i < 8; i++) weave += `<path d="M${-w * 0.5 + (i * w) / 8} ${top} L${-w * 0.5 + (i * w) / 8 - w * 0.06} ${top + h * 0.16}" stroke="#d8c49a" stroke-width="${w * 0.012}"/>`;
  for (let i = 1; i < 4; i++) weave += `<path d="M${-w * 0.48} ${top + (i * h * 0.16) / 4} L${w * 0.46} ${top + (i * h * 0.16) / 4}" stroke="#d8c49a" stroke-width="${w * 0.01}"/>`;
  return `<rect x="${-w * 0.47}" y="${-legH}" width="${w * 0.05}" height="${legH}" fill="#8a5a2b"/><rect x="${w * 0.42}" y="${-legH}" width="${w * 0.05}" height="${legH}" fill="#8a5a2b"/>` +
    `<rect x="${-w * 0.36}" y="${-legH * 0.92}" width="${w * 0.05}" height="${legH * 0.92}" fill="#6e4722"/><rect x="${w * 0.31}" y="${-legH * 0.92}" width="${w * 0.05}" height="${legH * 0.92}" fill="#6e4722"/>` +
    `<rect x="${-w * 0.52}" y="${top}" width="${w * 1.04}" height="${h * 0.16}" rx="${h * 0.07}" fill="#a9713c" stroke="${shade("#a9713c")}" stroke-width="${w * 0.015}"/>` + weave;
}

function saw(p) {
  const w = p.w || 170, h = w * 0.34;
  let teeth = "";
  for (let i = 0; i < 9; i++) teeth += `L${-w * 0.42 + ((i + 0.5) * w * 0.72) / 9} ${h * 0.34} L${-w * 0.42 + ((i + 1) * w * 0.72) / 9} ${h * 0.12}`;
  return `<path d="M${-w * 0.42} ${h * 0.12} ${teeth} L${w * 0.3} ${h * 0.12} L${w * 0.3} ${-h * 0.3} L${-w * 0.42} ${-h * 0.14} Z" fill="#c8cdd4" stroke="#7f8691" stroke-width="${w * 0.02}"/>` +
    `<path d="M${w * 0.28} ${-h * 0.32} Q${w * 0.52} ${-h * 0.5} ${w * 0.5} ${-h * 0.05} Q${w * 0.48} ${h * 0.3} ${w * 0.3} ${h * 0.14}" fill="#8a5a2b" stroke="${shade("#8a5a2b")}" stroke-width="${w * 0.02}"/>`;
}

function calendar(p) {
  const w = p.w || 200, h = w * 0.92;
  let grid = "";
  for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++)
    grid += `<rect x="${-w * 0.36 + c * w * 0.19}" y="${-h * 0.34 + r * h * 0.16}" width="${w * 0.14}" height="${h * 0.11}" rx="${w * 0.015}" fill="#e9eef4"/>`;
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${w * 0.05}" fill="#ffffff" stroke="#9db3c7" stroke-width="${w * 0.025}"/>` +
    `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h * 0.26}" rx="${w * 0.05}" fill="#e5484d"/>` +
    `<rect x="${-w * 0.3}" y="${-h * 0.6}" width="${w * 0.06}" height="${h * 0.16}" rx="${w * 0.03}" fill="${INK}"/><rect x="${w * 0.24}" y="${-h * 0.6}" width="${w * 0.06}" height="${h * 0.16}" rx="${w * 0.03}" fill="${INK}"/>` +
    `<g transform="translate(0,${-h * 0.305})">` + label(p.text || "", 0, h * 0.15, "#ffffff", 800) + `</g>` + grid;
}

function bugs(p) {
  const w = p.w || 160, n = p.n || 7, r = rnd(42 + n);
  let out = "";
  for (let i = 0; i < n; i++) {
    const x = (r() - 0.5) * w, y = (r() - 0.5) * w * 0.4, a = r() * 360, s = w * (0.035 + r() * 0.02);
    out += `<g class="bug" transform="translate(${x.toFixed(1)},${y.toFixed(1)}) rotate(${a.toFixed(0)})">` +
      `<ellipse rx="${s}" ry="${s * 0.62}" fill="#4a3b2a"/><circle cx="${s * 0.9}" r="${s * 0.42}" fill="#2b2017"/>` +
      `<path d="M${-s * 0.5} ${-s * 0.6} l${-s * 0.4} ${-s * 0.4} M0 ${-s * 0.65} l0 ${-s * 0.5} M${s * 0.5} ${-s * 0.6} l${s * 0.4} ${-s * 0.4} M${-s * 0.5} ${s * 0.6} l${-s * 0.4} ${s * 0.4} M0 ${s * 0.65} l0 ${s * 0.5} M${s * 0.5} ${s * 0.6} l${s * 0.4} ${s * 0.4}" stroke="#2b2017" stroke-width="${s * 0.14}"/></g>`;
  }
  return out;
}

function sweat(p) {
  const w = p.w || 36;
  return [[0, 0], [w * 0.9, w * 0.5], [-w * 0.7, w * 0.7]].map(([x, y], i) =>
    `<path transform="translate(${x},${y}) scale(${1 - i * 0.22})" d="M0 ${-w * 0.6} Q${w * 0.42} 0 0 ${w * 0.34} Q${-w * 0.42} 0 0 ${-w * 0.6} Z" fill="#6fb7e8" stroke="#3a7bd5" stroke-width="${w * 0.07}"/>`).join("");
}

function heap(p) {
  const w = p.w || 160, salt = (p.kind || "salt") === "salt";
  const col = salt ? (p.wet ? "#cfc7b4" : "#f2efe6") : "#e0b55a", dark = salt ? "#a89f8a" : "#a5793a";
  let grains = "";
  const r = rnd(7);
  for (let i = 0; i < 14; i++) grains += `<circle cx="${((r() - 0.5) * w * 0.7).toFixed(1)}" cy="${(-r() * w * 0.3 - w * 0.05).toFixed(1)}" r="${w * 0.016}" fill="${dark}"/>`;
  const drips = p.wet ? `<path d="M${-w * 0.3} 0 q${-w * 0.02} ${w * 0.08} ${-w * 0.06} ${w * 0.1} M${w * 0.26} 0 q${w * 0.02} ${w * 0.09} ${w * 0.05} ${w * 0.12}" stroke="#7fa8c9" stroke-width="${w * 0.03}" fill="none" stroke-linecap="round"/>` : "";
  return `<path d="M${-w * 0.5} 0 Q${-w * 0.2} ${-w * 0.52} 0 ${-w * 0.5} Q${w * 0.2} ${-w * 0.52} ${w * 0.5} 0 Z" fill="${col}" stroke="${dark}" stroke-width="${w * 0.025}"/>` + grains + drips;
}

function teaBrick(p) {
  const w = p.w || 120, h = w * 0.62;
  const crack = p.crack ? `<path d="M${-w * 0.08} ${-h} L${w * 0.03} ${-h * 0.55} L${-w * 0.05} ${-h * 0.2} L${w * 0.04} 0" stroke="#2b1d12" stroke-width="${w * 0.03}" fill="none"/>` +
    `<g transform="translate(${w * 0.62},${-h * 0.14}) rotate(9)"><rect x="${-w * 0.14}" y="${-h * 0.3}" width="${w * 0.28}" height="${h * 0.3}" rx="${w * 0.03}" fill="#4a3421" stroke="#2b1d12" stroke-width="${w * 0.02}"/></g>` : "";
  let stamps = "";
  for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++)
    stamps += `<rect x="${-w * 0.36 + c * w * 0.26}" y="${-h * 0.78 + r * h * 0.36}" width="${w * 0.18}" height="${h * 0.24}" rx="${w * 0.02}" fill="none" stroke="#6e4e31" stroke-width="${w * 0.018}"/>`;
  return `<rect x="${-w * 0.5}" y="${-h}" width="${w}" height="${h}" rx="${w * 0.03}" fill="#4a3421" stroke="#2b1d12" stroke-width="${w * 0.025}"/>` + stamps + crack;
}

function tobacco(p) {
  const w = p.w || 120;
  const leaf = (rot, s) => `<g transform="rotate(${rot}) scale(${s})"><path d="M0 0 Q${-w * 0.2} ${-w * 0.3} 0 ${-w * 0.74} Q${w * 0.2} ${-w * 0.3} 0 0 Z" fill="#8a6d3b" stroke="#5e4a26" stroke-width="${w * 0.02}"/><path d="M0 ${-w * 0.06} L0 ${-w * 0.66}" stroke="#5e4a26" stroke-width="${w * 0.018}"/></g>`;
  return `<g transform="translate(0,${w * 0.37})">` + leaf(-26, 0.96) + leaf(24, 0.96) + leaf(0, 1.06) +
    `<rect x="${-w * 0.1}" y="${-w * 0.14}" width="${w * 0.2}" height="${w * 0.1}" rx="${w * 0.03}" fill="#c9a16b"/></g>`;
}

function cowries(p) {
  const w = p.w || 32;
  const shell = (x, y, rot) => `<g transform="translate(${x},${y}) rotate(${rot})"><ellipse rx="${w * 0.52}" ry="${w * 0.4}" fill="#f3ead6" stroke="#b8a37e" stroke-width="${w * 0.06}"/>` +
    `<path d="M${-w * 0.34} 0 L${w * 0.34} 0" stroke="#8a775a" stroke-width="${w * 0.08}" stroke-dasharray="${w * 0.08} ${w * 0.07}"/></g>`;
  return shell(0, -w * 0.3, -8) + shell(-w * 0.65, w * 0.25, 12) + shell(w * 0.65, w * 0.25, -14);
}

function cheque(p) {
  const w = p.w || 240, h = w * 0.46;
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${w * 0.02}" fill="#fbf7ec" stroke="#b9c7d4" stroke-width="${w * 0.015}"/>` +
    `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h * 0.16}" fill="#dfe9f2"/>` +
    `<path d="M${-w * 0.42} ${-h * 0.1} L${w * 0.05} ${-h * 0.1} M${-w * 0.42} ${h * 0.08} L${w * 0.1} ${h * 0.08}" stroke="#9db3c7" stroke-width="${w * 0.012}"/>` +
    `<rect x="${w * 0.14}" y="${-h * 0.2}" width="${w * 0.3}" height="${h * 0.26}" rx="${w * 0.015}" fill="#ffffff" stroke="#9db3c7" stroke-width="${w * 0.012}"/>` +
    (p.amount ? `<g transform="translate(${w * 0.29},${-h * 0.015})">` + label(p.amount, 0, h * 0.17, INK, 800) + `</g>` : "") +
    `<path d="M${w * 0.12} ${h * 0.3} q${w * 0.05} ${-h * 0.14} ${w * 0.1} 0 q${w * 0.05} ${h * 0.12} ${w * 0.12} ${-h * 0.05}" stroke="${INK}" stroke-width="${w * 0.014}" fill="none"/>` +
    `<g transform="translate(${-w * 0.3},${-h * 0.33})">` + label("चेक", 0, h * 0.14, "#5a748c", 800) + `</g>`;
}

function accountCard(p) {
  const w = p.w || 380, h = w * 0.5, col = p.color || "#3a7bd5";
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${w * 0.04}" fill="#ffffff" stroke="${col}" stroke-width="${w * 0.012}"/>` +
    `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h * 0.32}" rx="${w * 0.04}" fill="${col}"/>` +
    `<rect x="${-w * 0.5}" y="${-h * 0.5 + h * 0.2}" width="${w}" height="${h * 0.12}" fill="${col}"/>` +
    `<g transform="translate(0,${-h * 0.24})">` + label(p.title || "", 0, h * 0.17, "#ffffff", 800) + `</g>` +
    (p.amount ? `<g transform="translate(0,${h * 0.18})">` + label(p.amount, 0, h * 0.3, INK, 800) + `</g>` : "");
}

function bank(p) {
  const w = p.w || 210, h = w * 0.82;
  let cols = "";
  for (let i = 0; i < 4; i++) cols += `<rect x="${-w * 0.33 + i * w * 0.22 - w * 0.045}" y="${-h * 0.62}" width="${w * 0.09}" height="${h * 0.44}" fill="#e8e0cc" stroke="#b9ad90" stroke-width="${w * 0.012}"/>`;
  return `<rect x="${-w * 0.44}" y="${-h * 0.18}" width="${w * 0.88}" height="${h * 0.18}" fill="#cfc4a6" stroke="#b9ad90" stroke-width="${w * 0.014}"/>` + cols +
    `<rect x="${-w * 0.48}" y="${-h * 0.7}" width="${w * 0.96}" height="${h * 0.09}" fill="#d9cfb2" stroke="#b9ad90" stroke-width="${w * 0.014}"/>` +
    `<path d="M${-w * 0.5} ${-h * 0.7} L0 ${-h} L${w * 0.5} ${-h * 0.7} Z" fill="#e8e0cc" stroke="#b9ad90" stroke-width="${w * 0.016}"/>` +
    `<circle cx="0" cy="${-h * 0.82}" r="${w * 0.055}" fill="#c9a400"/>` +
    (p.label ? `<g transform="translate(0,${h * 0.12})"><rect x="${-w * 0.36}" y="${-h * 0.1}" width="${w * 0.72}" height="${h * 0.14}" rx="${h * 0.04}" fill="${INK}"/>` + label(p.label, h * 0.015, Math.min(h * 0.11, (w * 0.68) / Math.max(1, String(p.label).length * 0.6)), "#ffffff", 700) + `</g>` : "");   // was font-size 0: the label never showed (found by the box rule)
}

function qrModules(w, seed = 11) {
  const n = 9, cell = w / n, r = rnd(seed);
  let out = "";
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const corner = (x < 3 && y < 3) || (x > 5 && y < 3) || (x < 3 && y > 5);
    if (!corner && r() > 0.52) out += `<rect x="${x * cell}" y="${y * cell}" width="${cell * 0.9}" height="${cell * 0.9}" fill="${INK}"/>`;
  }
  const finder = (x, y) => `<rect x="${x * cell}" y="${y * cell}" width="${cell * 2.6}" height="${cell * 2.6}" fill="none" stroke="${INK}" stroke-width="${cell * 0.5}"/><rect x="${(x + 0.9) * cell}" y="${(y + 0.9) * cell}" width="${cell * 0.9}" height="${cell * 0.9}" fill="${INK}"/>`;
  return out + finder(0.1, 0.1) + finder(6.2, 0.1) + finder(0.1, 6.2);
}

function qrStand(p) {
  const w = p.w || 170, q = w * 0.72;
  return `<rect x="${-w * 0.09}" y="${-w * 0.5}" width="${w * 0.18}" height="${w * 0.5}" fill="#8a8f98"/>` +
    `<rect x="${-w * 0.3}" y="${-w * 0.06}" width="${w * 0.6}" height="${w * 0.06}" rx="${w * 0.03}" fill="#6e737c"/>` +
    `<g transform="translate(0,${-w * 1.18})"><rect x="${-w * 0.5}" y="0" width="${w}" height="${w * 0.78}" rx="${w * 0.05}" fill="#ffffff" stroke="#6e737c" stroke-width="${w * 0.03}"/>` +
    `<g transform="translate(${-q / 2},${w * 0.06})">${qrModules(q * 0.72 / 0.72 * 0.66)}</g>` +
    `<g transform="translate(0,${w * 0.72})">` + label("यहाँ scan करें", 0, w * 0.1, INK, 700) + `</g></g>`;
}

function phone(p) {
  const w = p.w || 90, h = w * 2.05, s = p.screen || "home";
  let screen = "";
  const sw = w * 0.84, sx = -sw / 2, sy = -h * 0.42;
  if (s === "scan") screen = `<g transform="translate(${sx + sw * 0.14},${sy + h * 0.1})">${qrModules(sw * 0.72, 11)}</g>` +
    `<rect x="${sx + sw * 0.08}" y="${sy + h * 0.06}" width="${sw * 0.84}" height="${sw * 0.84}" fill="none" stroke="#2fb463" stroke-width="${w * 0.045}" rx="${w * 0.04}"/>` +
    `<g transform="translate(0,${sy + h * 0.62})">` + label("scan…", 0, w * 0.17, INK, 700) + `</g>`;
  else if (s === "paid") screen = `<circle cx="0" cy="${sy + h * 0.2}" r="${w * 0.2}" fill="#2fb463"/><path d="M${-w * 0.09} ${sy + h * 0.2} l${w * 0.07} ${w * 0.07} l${w * 0.12} ${-w * 0.14}" stroke="#ffffff" stroke-width="${w * 0.05}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>` +
    `<g transform="translate(0,${sy + h * 0.42})">` + label(p.amount || "", 0, w * 0.2, INK, 800) + `</g>` +
    `<g transform="translate(0,${sy + h * 0.56})">` + label("भेजे", 0, w * 0.15, "#2fb463", 700) + `</g>`;
  else if (s === "received") screen = `<g transform="translate(0,${sy + h * 0.26})">` + label(p.amount || "", 0, w * 0.2, INK, 800) + `</g>` +
    `<g transform="translate(0,${sy + h * 0.42})">` + label("मिले ✓", 0, w * 0.15, "#2fb463", 700) + `</g>`;
  else { for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) screen += `<rect x="${sx + sw * 0.12 + c * sw * 0.28}" y="${sy + h * 0.08 + r * sw * 0.28}" width="${sw * 0.2}" height="${sw * 0.2}" rx="${w * 0.03}" fill="${["#3a7bd5", "#2fb463", "#f29f05", "#e0533d", "#7b61ff", "#2fa08c", "#c2447a", "#c9a400", "#8a9b56"][r * 3 + c]}"/>`; }
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${w * 0.14}" fill="${INK}"/>` +
    `<rect x="${sx}" y="${sy}" width="${sw}" height="${h * 0.8}" rx="${w * 0.07}" fill="#f4f7fa"/>` + screen;
}

// ---------------------------------------------------------------- economy kit, batch 3 (4 Nov 2026)
// Learned from 37 Indian-economy reference videos (asset_intake/econ_kit, rules/show_lexicon.json): the things those
// videos draw most that the Money v2 set lacked. BIE's own drawings: no logos, emblems, seals or real persons — an
// institution is shown by institutionBadge (the references showed real logos in 25 of 37 videos).
export const tx = (text, x, cy, size, fill = INK, weight = 700) =>
  text === "" || text == null ? "" : `<g transform="translate(${x},0)">` + label(String(text), cy + size * 0.35, size, fill, weight) + `</g>`;
export const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0));

const BADGE_KINDS = {
  central_bank: ["#138a8a", "coin"], bank: ["#3a7bd5", "columns"], government: ["#e07b24", "dome"],
  regulator: ["#7b5cd6", "scale"], international: ["#2a9d8f", "globe"], cooperative: ["#2fa35b", "hands"],
  committee: ["#a0703d", "table"], market: ["#d6454f", "chart"], company: ["#4a5568", "factory"],
};

function badgeGlyph(kind, s) {
  const w = "#ffffff";
  switch (kind) {
    case "coin": return `<circle r="${s * 0.42}" fill="none" stroke="${w}" stroke-width="${s * 0.09}"/>` + tx("₹", 0, 0, s * 0.55, w, 800);
    case "columns": return `<path d="M${-s * 0.5} ${-s * 0.18} L0 ${-s * 0.5} L${s * 0.5} ${-s * 0.18} Z" fill="${w}"/>` +
      [-0.34, -0.11, 0.11, 0.34].map((x) => `<rect x="${x * s - s * 0.06}" y="${-s * 0.12}" width="${s * 0.12}" height="${s * 0.46}" fill="${w}"/>`).join("") +
      `<rect x="${-s * 0.52}" y="${s * 0.36}" width="${s * 1.04}" height="${s * 0.1}" fill="${w}"/>`;
    case "dome": return `<path d="M${-s * 0.32} ${-s * 0.08} A${s * 0.32} ${s * 0.32} 0 0 1 ${s * 0.32} ${-s * 0.08} Z" fill="${w}"/><rect x="${-s * 0.03}" y="${-s * 0.55}" width="${s * 0.06}" height="${s * 0.18}" fill="${w}"/>` +
      [-0.36, -0.12, 0.12, 0.36].map((x) => `<rect x="${x * s - s * 0.05}" y="${-s * 0.02}" width="${s * 0.1}" height="${s * 0.36}" fill="${w}"/>`).join("") +
      `<rect x="${-s * 0.5}" y="${s * 0.36}" width="${s}" height="${s * 0.1}" fill="${w}"/>`;
    case "scale": return `<rect x="${-s * 0.04}" y="${-s * 0.45}" width="${s * 0.08}" height="${s * 0.8}" fill="${w}"/><rect x="${-s * 0.46}" y="${-s * 0.36}" width="${s * 0.92}" height="${s * 0.07}" fill="${w}"/>` +
      `<path d="M${-s * 0.54} ${s * 0.02} A${s * 0.14} ${s * 0.1} 0 0 0 ${-s * 0.26} ${s * 0.02} Z M${s * 0.26} ${s * 0.02} A${s * 0.14} ${s * 0.1} 0 0 0 ${s * 0.54} ${s * 0.02} Z" fill="${w}"/>` +
      `<path d="M${-s * 0.4} ${-s * 0.3} L${-s * 0.52} ${s * 0.02} M${-s * 0.4} ${-s * 0.3} L${-s * 0.28} ${s * 0.02} M${s * 0.4} ${-s * 0.3} L${s * 0.28} ${s * 0.02} M${s * 0.4} ${-s * 0.3} L${s * 0.52} ${s * 0.02}" stroke="${w}" stroke-width="${s * 0.04}"/>` +
      `<rect x="${-s * 0.22}" y="${s * 0.34}" width="${s * 0.44}" height="${s * 0.08}" fill="${w}"/>`;
    case "globe": return `<circle r="${s * 0.42}" fill="none" stroke="${w}" stroke-width="${s * 0.07}"/><ellipse rx="${s * 0.18}" ry="${s * 0.42}" fill="none" stroke="${w}" stroke-width="${s * 0.05}"/>` +
      `<path d="M${-s * 0.42} 0 L${s * 0.42} 0 M${-s * 0.36} ${-s * 0.2} Q0 ${-s * 0.1} ${s * 0.36} ${-s * 0.2} M${-s * 0.36} ${s * 0.2} Q0 ${s * 0.1} ${s * 0.36} ${s * 0.2}" fill="none" stroke="${w}" stroke-width="${s * 0.045}"/>`;
    case "hands": return [-0.3, 0, 0.3].map((x, i) => `<circle cx="${x * s}" cy="${-s * 0.22 - (i === 1 ? s * 0.06 : 0)}" r="${s * 0.12}" fill="${w}"/>` +
      `<path d="M${x * s - s * 0.17} ${s * 0.3} Q${x * s - s * 0.17} ${-s * 0.04} ${x * s} ${-s * 0.04} Q${x * s + s * 0.17} ${-s * 0.04} ${x * s + s * 0.17} ${s * 0.3} Z" fill="${w}"/>`).join("") +
      `<path d="M${-s * 0.48} ${s * 0.1} Q0 ${s * 0.32} ${s * 0.48} ${s * 0.1}" fill="none" stroke="${w}" stroke-width="${s * 0.06}"/>`;
    case "table": return [-0.32, 0, 0.32].map((x) => `<circle cx="${x * s}" cy="${-s * 0.24}" r="${s * 0.11}" fill="${w}"/><rect x="${x * s - s * 0.13}" y="${-s * 0.11}" width="${s * 0.26}" height="${s * 0.22}" rx="${s * 0.08}" fill="${w}"/>`).join("") +
      `<rect x="${-s * 0.52}" y="${s * 0.1}" width="${s * 1.04}" height="${s * 0.1}" rx="${s * 0.03}" fill="${w}"/><rect x="${-s * 0.42}" y="${s * 0.2}" width="${s * 0.07}" height="${s * 0.22}" fill="${w}"/><rect x="${s * 0.35}" y="${s * 0.2}" width="${s * 0.07}" height="${s * 0.22}" fill="${w}"/>`;
    case "chart": return `<path d="M${-s * 0.45} ${s * 0.3} L${-s * 0.15} ${-s * 0.05} L${s * 0.08} ${s * 0.12} L${s * 0.42} ${-s * 0.35}" fill="none" stroke="${w}" stroke-width="${s * 0.09}" stroke-linecap="round" stroke-linejoin="round"/>` +
      `<path d="M${s * 0.22} ${-s * 0.4} L${s * 0.46} ${-s * 0.4} L${s * 0.46} ${-s * 0.16}" fill="none" stroke="${w}" stroke-width="${s * 0.08}" stroke-linecap="round"/>`;
    case "factory": return `<path d="M${-s * 0.5} ${s * 0.4} L${-s * 0.5} ${-s * 0.05} L${-s * 0.2} ${s * 0.12} L${-s * 0.2} ${-s * 0.05} L${s * 0.1} ${s * 0.12} L${s * 0.1} ${-s * 0.45} L${s * 0.3} ${-s * 0.45} L${s * 0.3} ${s * 0.12} L${s * 0.5} ${s * 0.12} L${s * 0.5} ${s * 0.4} Z" fill="${w}"/>`;
    default: return "";
  }
}

function institutionBadge(p) {
  const w = p.w || 160, r = w / 2, [col, g] = BADGE_KINDS[p.kind] || BADGE_KINDS.central_bank, c = p.color || col, name = String(p.name ?? "RBI");
  const fs = name.length > 5 ? r * 0.3 : name.length > 3 ? r * 0.36 : r * 0.44;
  return `<circle r="${r}" fill="#ffffff" stroke="${shade(c)}" stroke-width="${w * 0.015}"/><circle r="${r * 0.88}" fill="${c}"/>` +
    `<circle r="${r * 0.78}" fill="none" stroke="#ffffff" stroke-width="${r * 0.025}" stroke-dasharray="${r * 0.05} ${r * 0.05}" opacity="0.55"/>` +
    `<g transform="translate(0,${-r * 0.3})">${badgeGlyph(g, r * 0.62)}</g>` + tx(name, 0, r * 0.36, fs, "#ffffff", 800) +
    (p.sub ? `<rect x="${-r * 1.1}" y="${r * 0.78}" width="${r * 2.2}" height="${r * 0.42}" rx="${r * 0.12}" fill="#ffffff" stroke="${shade(c)}" stroke-width="${r * 0.04}"/>` + tx(p.sub, 0, r * 0.99, r * 0.24, shade(c), 700) : "");
}

const PAPER_KINDS = {
  law: ["#8e2b3a", "#fbf3e6", "scale"], bond: ["#1f8a5b", "#eef8f1", "coin"], licence: ["#2459a6", "#eef3fb", "columns"],
  contract: ["#4a5568", "#f4f5f7", "hands"], bill: ["#d9822b", "#fdf3e7", "factory"], report: ["#7b5cd6", "#f3f0fc", "chart"],
  share: ["#c0563f", "#fbefe9", "factory"], unit: ["#2a9d8f", "#ecf7f5", "chart"],
  receipt: ["#3a7bd5", "#eef3fb", "globe"], invoice: ["#d6454f", "#fdeeee", "factory"],
};

function paper(p) {
  const w = p.w || 170, h = w * 1.3, fold = w * 0.16, x0 = -w / 2, y0 = -h / 2, [band, tint, icon] = PAPER_KINDS[p.kind] || PAPER_KINDS.law;
  const title = String(p.title ?? "Act"), year = String(p.year ?? ""), value = String(p.value ?? ""), note = String(p.note ?? "");
  const lines = Math.max(0, Math.min(8, p.lines == null ? 4 : Math.round(p.lines)));
  let body = p.kind === "bond" ? `<rect x="${x0 + w * 0.07}" y="${y0 + h * 0.2}" width="${w * 0.86}" height="${h * 0.72}" rx="${w * 0.03}" fill="none" stroke="${band}" stroke-width="${w * 0.012}" stroke-dasharray="${w * 0.03} ${w * 0.015}"/>` : "";
  const top = y0 + h * 0.27;
  if (year) body += tx(year, 0, top + h * 0.06, w * 0.17, band, 800);
  if (value) body += tx(value, 0, top + (year ? h * 0.2 : h * 0.08), w * 0.15, INK, 800);
  const ly = top + (year || value ? h * (year && value ? 0.31 : 0.19) : h * 0.03);
  for (let i = 0; i < lines; i++)
    body += `<rect x="${-w * 0.36}" y="${ly + i * h * 0.075}" width="${w * (i === lines - 1 ? 0.45 : 0.72 - (i % 2) * 0.08)}" height="${h * 0.026}" rx="${h * 0.013}" fill="#c9c6bd"/>`;
  const sigY = note ? 0.7 : 0.86;
  if (p.kind === "contract") body += [-1, 1].map((s) => `<path d="M${s * w * 0.22 - w * 0.14} ${y0 + h * sigY} q${w * 0.05} ${-h * 0.05} ${w * 0.09} 0 t${w * 0.1} 0" fill="none" stroke="#2d3748" stroke-width="${w * 0.012}"/>` +
    `<path d="M${s * w * 0.22 - w * 0.17} ${y0 + h * (sigY + 0.03)} L${s * w * 0.22 + w * 0.17} ${y0 + h * (sigY + 0.03)}" stroke="#8a8f98" stroke-width="${w * 0.008}"/>`).join("");
  if (note) body += `<rect x="${-w * 0.42}" y="${y0 + h * 0.8}" width="${w * 0.84}" height="${h * 0.12}" rx="${h * 0.04}" fill="${band}"/>` + tx(note, 0, y0 + h * 0.86, Math.min(w * 0.1, (w * 0.8) / Math.max(1, note.length) * 1.8), "#ffffff", 700);
  const stamp = p.stamp ? `<g transform="translate(${w * 0.12},${h * 0.22}) rotate(-14)" opacity="0.92"><rect x="${-w * 0.36}" y="${-h * 0.07}" width="${w * 0.72}" height="${h * 0.14}" rx="${w * 0.03}" fill="none" stroke="${p.stampColor || "#d6454f"}" stroke-width="${w * 0.025}"/>` +
    tx(p.stamp, 0, 0, Math.min(w * 0.12, (w * 0.66) / Math.max(1, String(p.stamp).length) * 1.6), p.stampColor || "#d6454f", 800) + `</g>` : "";
  return `<path d="M${x0} ${y0} L${-x0 - fold} ${y0} L${-x0} ${y0 + fold} L${-x0} ${-y0} L${x0} ${-y0} Z" fill="${tint}" stroke="${shade(tint, 0.8)}" stroke-width="${w * 0.012}"/>` +
    `<path d="M${-x0 - fold} ${y0} L${-x0 - fold} ${y0 + fold} L${-x0} ${y0 + fold} Z" fill="#d9d3c6"/>` +
    `<path d="M${x0} ${y0} L${-x0 - fold} ${y0} L${-x0 - fold * 0.35} ${y0 + h * 0.17} L${x0} ${y0 + h * 0.17} Z" fill="${band}"/>` +
    `<g transform="translate(${x0 + w * 0.13},${y0 + h * 0.085})">${badgeGlyph(icon, w * 0.13)}</g>` +
    tx(title, w * 0.06, y0 + h * 0.085, Math.min(title.length > 9 ? w * 0.09 : w * 0.11, (w * 0.62) / Math.max(1, title.length) * 1.7), "#ffffff", 800) + body + stamp;
}

function disc(p) {
  const w = p.w || 130, r = w / 2, c = p.color || "#d6454f", t = String(p.text ?? "RISK");
  return `<circle r="${r}" fill="${c}" stroke="${shade(c)}" stroke-width="${w * 0.02}"/><circle r="${r * 0.84}" fill="none" stroke="#ffffff" stroke-width="${r * 0.05}" opacity="0.8"/>` +
    tx(t, 0, 0, Math.min(t.length > 4 ? r * 0.4 : r * 0.5, (r * 1.5) / Math.max(1, t.length) * 1.7), "#ffffff", 800);
}

function vault(p) {
  const w = p.w || 180, h = w * 0.95, x0 = -w / 2, y0 = -h - w * 0.06, inset = w * 0.09;
  const [c0, c1, c2] = p.metal === "steel" ? ["#c7ccd3", "#8e96a1", "#5a626d"] : ["#f3cf6a", "#c99a2e", "#8a6a1c"];
  const ix = x0 + inset, iy = y0 + inset, iw = w - inset * 2, ih = h - inset * 2, n = Math.round(clamp01(p.fill == null ? 0.5 : p.fill) * 9);
  let stack = "";
  for (let i = 0; i < n; i++) {
    const row = Math.floor(i / 3), col = i % 3, bw = (iw / 3) * 0.8;
    stack += `<g transform="translate(${ix + (col + 0.5) * (iw / 3)},${iy + ih - (row + 0.5) * (ih / 3)})">${noteBundle({ w: bw, value: 500, bare: true })}</g>`;   // miniature notes carry no words (the box rule's floor)
  }
  const shelves = [1, 2].map((k) => `<rect x="${ix}" y="${iy + (k * ih) / 3 - w * 0.01}" width="${iw}" height="${w * 0.02}" fill="${c2}" opacity="0.5"/>`).join("");
  const d = clamp01(p.door), dw = w - inset * 0.6, cx = dw * 0.5, cy = y0 + h * 0.5;
  const spokes = [0, 60, 120].map((a) => { const c = Math.cos((a * Math.PI) / 180) * w * 0.15, s = Math.sin((a * Math.PI) / 180) * w * 0.15;
    return `<path d="M${cx - c} ${cy - s} L${cx + c} ${cy + s}" stroke="${c2}" stroke-width="${w * 0.025}" stroke-linecap="round"/>`; }).join("");
  const closed = `<g transform="translate(${x0 + inset * 0.3},0) scale(${1 - d * 1.76},1)"><rect x="0" y="${y0 + inset * 0.3}" width="${dw}" height="${h - inset * 0.6}" rx="${w * 0.04}" fill="${c0}" stroke="${c1}" stroke-width="${w * 0.015}"/>` +
    `<circle cx="${cx}" cy="${cy}" r="${w * 0.16}" fill="none" stroke="${c2}" stroke-width="${w * 0.03}"/>${spokes}<circle cx="${cx}" cy="${cy}" r="${w * 0.045}" fill="${c2}"/></g>`;
  const hx = x0 + inset * 0.3;
  const open = `<path d="M${hx} ${y0 + inset * 0.3} L${hx - w * 0.3 * d} ${y0 - h * 0.04 * d} L${hx - w * 0.3 * d} ${y0 + h + h * 0.04 * d - inset * 0.3} L${hx} ${y0 + h - inset * 0.3} Z" fill="${c0}" stroke="${c2}" stroke-width="${w * 0.01}"/>` +
    `<ellipse cx="${hx - w * 0.15 * d}" cy="${cy}" rx="${w * 0.05 * d}" ry="${w * 0.15}" fill="none" stroke="${c2}" stroke-width="${w * 0.025}"/>`;
  const locked = p.locked !== false, sh = locked ? 0 : w * 0.05;
  const lock = `<g transform="translate(${-x0 - w * 0.02},${y0 + w * 0.02})"><path d="M${-w * 0.07} 0 L${-w * 0.07} ${-w * 0.07 - sh} A${w * 0.07} ${w * 0.07} 0 0 1 ${w * 0.07} ${-w * 0.07 - sh} L${w * 0.07} ${locked ? 0 : -sh}" fill="none" stroke="#4a5568" stroke-width="${w * 0.03}"/>` +
    `<rect x="${-w * 0.11}" y="0" width="${w * 0.22}" height="${w * 0.17}" rx="${w * 0.03}" fill="${locked ? "#2d3748" : "#2fa35b"}"/><circle cy="${w * 0.08}" r="${w * 0.025}" fill="#ffffff"/></g>`;
  const tc = p.tagColor || "#d6454f";
  const tag = p.tag ? `<g transform="translate(${-x0 + w * 0.02},${y0 + h * 0.55})"><path d="M0 0 L${w * 0.12} ${w * 0.08}" stroke="#8a8f98" stroke-width="${w * 0.012}"/><rect x="${w * 0.1}" y="${w * 0.03}" width="${w * 0.52}" height="${w * 0.17}" rx="${w * 0.05}" fill="${tc}"/>` +
    tx(p.tag, w * 0.36, w * 0.115, Math.min(w * 0.085, (w * 0.48) / Math.max(1, String(p.tag).length) * 1.8), "#ffffff", 800) + `</g>` : "";
  return `<rect x="${x0 + w * 0.08}" y="${-w * 0.08}" width="${w * 0.12}" height="${w * 0.08}" fill="${c2}"/><rect x="${-x0 - w * 0.2}" y="${-w * 0.08}" width="${w * 0.12}" height="${w * 0.08}" fill="${c2}"/>` +
    `<rect x="${x0}" y="${y0}" width="${w}" height="${h}" rx="${w * 0.06}" fill="${c1}" stroke="${c2}" stroke-width="${w * 0.015}"/>` +
    `<rect x="${ix}" y="${iy}" width="${iw}" height="${ih}" rx="${w * 0.03}" fill="#3b3326"/>${shelves}${stack}` +
    (d < 0.5 ? closed : open) +
    (p.label ? `<rect x="${-w * 0.3}" y="${y0 - w * 0.2}" width="${w * 0.6}" height="${w * 0.17}" rx="${w * 0.05}" fill="#2d3748"/>` + tx(p.label, 0, y0 - w * 0.115, Math.min(w * 0.11, (w * 0.56) / Math.max(1, String(p.label).length) * 1.8), "#ffffff", 800) : "") +
    lock + tag;
}

const SKINS = ["#c68a5c", "#d39a6a", "#b97c50", "#a8714a", "#d8a274", "#c98c5e"];
const SHIRTS = ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f", "#2a9d8f", "#9b6b43"];
function miniPerson(x, y, s, i, dim) {
  const sk = SKINS[(i * 7) % SKINS.length], sh = SHIRTS[(i * 5 + 3) % SHIRTS.length];
  return `<g transform="translate(${x},${y})" opacity="${dim ? 0.3 : 1}"><path d="M${-s * 0.3} 0 L${-s * 0.3} ${-s * 0.55} Q${-s * 0.3} ${-s * 0.82} 0 ${-s * 0.82} Q${s * 0.3} ${-s * 0.82} ${s * 0.3} ${-s * 0.55} L${s * 0.3} 0 Z" fill="${sh}" stroke="${shade(sh)}" stroke-width="${s * 0.03}"/>` +
    `<circle cy="${-s}" r="${s * 0.2}" fill="${sk}" stroke="${shade(sk)}" stroke-width="${s * 0.02}"/><path d="M${-s * 0.2} ${-s * 1.03} Q0 ${-s * 1.3} ${s * 0.2} ${-s * 1.03} Q${s * 0.1} ${-s * 1.12} 0 ${-s * 1.12} Q${-s * 0.1} ${-s * 1.12} ${-s * 0.2} ${-s * 1.03} Z" fill="#1f1a17"/>` +
    ((i * 11) % 3 === 0 ? `<circle cx="${s * 0.17}" cy="${-s * 1.12}" r="${s * 0.08}" fill="#1f1a17"/>` : "") + `</g>`;
}

function crowd(p) {
  const w = p.w || 420, n = Math.max(1, Math.min(200, Math.round(p.n || 24))), cols = Math.max(1, Math.min(n, Math.round(p.cols || 8)));
  const rows = Math.ceil(n / cols), s = (w / cols) * 0.95, rowH = s * 1.25, H = rows * rowH + s * 0.4, fs = Math.max(26, s * 0.5);
  const cut = Math.round(clamp01(p.share) * cols);
  let out = "";
  if (cut > 0) out += `<rect x="${-w / 2 - s * 0.12}" y="${-H}" width="${(cut * w) / cols + s * 0.24}" height="${H + s * 0.15}" rx="${s * 0.3}" fill="${p.shareColor || "#f2c94c"}" opacity="0.55"/>`;
  if (p.restColor && cut < cols) out += `<rect x="${-w / 2 + (cut * w) / cols - s * 0.05}" y="${-H}" width="${w - (cut * w) / cols + s * 0.17}" height="${H + s * 0.15}" rx="${s * 0.3}" fill="${p.restColor}" opacity="0.35"/>`;
  for (let i = 0; i < n; i++) {
    const r = Math.floor(i / cols), c = i % cols;
    out += miniPerson(-w / 2 + (c + 0.5) * (w / cols), -(rows - 1 - r) * rowH - s * 0.08, s * 0.78, i, p.dimRest && c >= cut);
  }
  if (p.shareLabel && cut > 0) out += tx(p.shareLabel, -w / 2 + (cut * w) / cols / 2, -H - fs * 0.7, fs, "#6b4a00", 700);
  if (p.restLabel && cut < cols) out += tx(p.restLabel, -w / 2 + (cut * w) / cols + (w - (cut * w) / cols) / 2, -H - fs * 0.7, fs, "#8a1c24", 700);
  if (p.label) out += tx(p.label, 0, s * 0.3 + fs * 0.8, fs * 1.1, INK, 700);
  return out;
}

function centralBank(p) {
  const w = p.w || 260, h = w * 0.82;
  let cols = "";
  for (let i = 0; i < 6; i++) cols += `<rect x="${-w * 0.4 + i * w * 0.15}" y="${-h * 0.6}" width="${w * 0.07}" height="${h * 0.44}" fill="#efe9dc" stroke="#bdb5a4" stroke-width="${w * 0.008}"/>`;
  return `<rect x="${-w * 0.54}" y="${-h * 0.08}" width="${w * 1.08}" height="${h * 0.08}" fill="#bdb5a4"/><rect x="${-w * 0.5}" y="${-h * 0.16}" width="${w}" height="${h * 0.08}" fill="#cfc8b8"/>` + cols +
    `<rect x="${-w * 0.47}" y="${-h * 0.67}" width="${w * 0.94}" height="${h * 0.07}" fill="#0f6e6e"/>` +
    `<path d="M${-w * 0.52} ${-h * 0.67} L0 ${-h * 0.98} L${w * 0.52} ${-h * 0.67} Z" fill="#ece6da" stroke="#bdb5a4" stroke-width="${w * 0.01}"/>` +
    `<circle cy="${-h * 0.79}" r="${h * 0.09}" fill="#f3cf6a" stroke="#c99a2e" stroke-width="${h * 0.015}"/>` + tx("₹", 0, -h * 0.79, h * 0.11, "#8a6a1c", 800) +
    `<g transform="translate(0,${-h * 0.31})"><rect x="${-w * 0.1}" y="${-h * 0.14}" width="${w * 0.2}" height="${h * 0.3}" rx="${w * 0.02}" fill="#8e96a1"/><circle r="${w * 0.05}" fill="none" stroke="#4a5568" stroke-width="${w * 0.012}"/><circle r="${w * 0.012}" fill="#4a5568"/></g>` +
    (p.label ? `<rect x="${-w * 0.2}" y="${-h * 1.13}" width="${w * 0.4}" height="${h * 0.13}" rx="${h * 0.03}" fill="#0f6e6e"/>` + tx(p.label, 0, -h * 1.065, Math.min(h * 0.09, (w * 0.36) / Math.max(1, String(p.label).length) * 1.8), "#ffffff", 700) : "");
}

function committee(p) {
  const w = p.w || 420, n = Math.max(1, Math.min(12, Math.round(p.n || 6))), s = Math.min((w / n) * 0.8, w * 0.17), top = -s * 0.85;
  const fs = Math.max(26, s * 0.3), ph = fs * 1.5, name = String(p.name ?? "समिति"), col = p.color || "#0f6e6e";
  let ppl = "";
  for (let i = 0; i < n; i++) ppl += miniPerson(-w / 2 + (i + 0.5) * (w / n), top + s * 0.3, s * 1.05, i + 3, false);
  const plateW = Math.max(w * 0.4, name.length * fs * 0.62 + fs);
  return ppl + `<rect x="${-w * 0.54}" y="${top}" width="${w * 1.08}" height="${s * 0.18}" rx="${s * 0.06}" fill="#8a5d2e"/>` +
    `<rect x="${-w * 0.5}" y="${top + s * 0.16}" width="${w}" height="${-top - s * 0.16}" fill="#a8763f" stroke="#7d5427" stroke-width="${w * 0.006}"/>` +
    `<rect x="${-plateW / 2}" y="${top + s * 0.16 + (-top - s * 0.16 - ph) / 2}" width="${plateW}" height="${ph}" rx="${ph * 0.25}" fill="${col}"/>` +
    tx(name, 0, top + s * 0.16 + (-top - s * 0.16) / 2, fs, "#ffffff", 800) + (p.sub ? tx(p.sub, 0, fs * 0.9, fs * 0.9, INK, 700) : "");
}

function moneyBag(p) {
  const w = p.w || 160, h = w * 1.1, c = p.color || "#c9965a", sign = p.sign == null ? "₹" : String(p.sign);
  return `<path d="M${-w * 0.16} ${-h * 0.78} Q${-w * 0.52} ${-h * 0.55} ${-w * 0.48} ${-h * 0.22} Q${-w * 0.44} 0 0 0 Q${w * 0.44} 0 ${w * 0.48} ${-h * 0.22} Q${w * 0.52} ${-h * 0.55} ${w * 0.16} ${-h * 0.78} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${w * 0.02}"/>` +
    `<path d="M${-w * 0.16} ${-h * 0.78} L${-w * 0.26} ${-h * 0.95} Q0 ${-h * 0.86} ${w * 0.26} ${-h * 0.95} L${w * 0.16} ${-h * 0.78} Z" fill="${shade(c, 0.9)}" stroke="${shade(c)}" stroke-width="${w * 0.015}"/>` +
    `<rect x="${-w * 0.2}" y="${-h * 0.81}" width="${w * 0.4}" height="${h * 0.06}" rx="${h * 0.03}" fill="#7d5427"/>` +
    (sign ? tx(sign, 0, -h * 0.36, w * 0.42, "#6b4a22", 800) : "") +
    (p.label ? `<rect x="${-w * 0.42}" y="${-h * 0.16}" width="${w * 0.84}" height="${h * 0.14}" rx="${h * 0.05}" fill="#f7efe0"/>` + tx(p.label, 0, -h * 0.09, Math.min(w * 0.13, (w * 0.8) / Math.max(1, String(p.label).length) * 1.8), "#6b4a22", 700) : "");
}

// ---------------------------------------------------------------- economy kit, batch 4 (4 Nov 2026)
// The recurring things of the 37-video needs list still missing after batch 3: one parametric building (office,
// government, exchange, house, tower, shop, warehouse, village branch), a price tag that is struck and replaced, a
// gauge, a generic foreign note and a barrier wall. Generic shapes only: no real landmark, no real currency design.
const BUILDING_KINDS = {
  office: ["#5b7fb8", "#e9eef6"], government: ["#e07b24", "#f6efe6"], exchange: ["#2a9d8f", "#eef6f4"],
  house: ["#c0563f", "#f4ead9"], tower: ["#6c7a8c", "#e7ecf1"], shop: ["#e5484d", "#f7efe2"],
  warehouse: ["#8a6d3b", "#efe6d6"], hut: ["#a0703d", "#efe2c8"], court: ["#7a4e22", "#f3ead9"], factory: ["#9b4a3a", "#e4ded2"],
};

function windows(x0, y0, cols, rows, cw, ch, gx, gy, fill) {
  let out = "";
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++)
    out += `<rect x="${x0 + c * (cw + gx)}" y="${y0 + r * (ch + gy)}" width="${cw}" height="${ch}" rx="${cw * 0.12}" fill="${fill}"/>`;
  return out;
}

function building(p) {
  const kind = BUILDING_KINDS[p.kind] ? p.kind : "office", [roof, wall] = BUILDING_KINDS[kind], w = p.w || 220;
  let body = "", top = 0;
  if (kind === "office" || kind === "tower") {
    const h = kind === "tower" ? w * 1.45 : w * 1.05; top = -h;
    body = `<rect x="${-w * 0.42}" y="${-h}" width="${w * 0.84}" height="${h}" rx="${w * 0.02}" fill="${wall}" stroke="${shade(wall, 0.7)}" stroke-width="${w * 0.012}"/>` +
      `<rect x="${-w * 0.46}" y="${-h - w * 0.04}" width="${w * 0.92}" height="${w * 0.06}" fill="${roof}"/>` +
      windows(-w * 0.34, -h + w * 0.1, 4, Math.max(2, Math.floor((h - w * 0.36) / (w * 0.17))), w * 0.12, w * 0.1, w * 0.06, w * 0.07, shade(roof, 1.25)) +
      `<rect x="${-w * 0.09}" y="${-w * 0.2}" width="${w * 0.18}" height="${w * 0.2}" fill="${shade(roof, 0.8)}"/>`;
  } else if (kind === "government") {
    const h = w * 0.78; top = -h - w * 0.42;
    let cols = "";
    for (let i = 0; i < 5; i++) cols += `<rect x="${-w * 0.36 + i * w * 0.18 - w * 0.04}" y="${-h * 0.72}" width="${w * 0.08}" height="${h * 0.56}" fill="${wall}" stroke="${shade(wall, 0.75)}" stroke-width="${w * 0.008}"/>`;
    body = `<rect x="${-w * 0.48}" y="${-h * 0.16}" width="${w * 0.96}" height="${h * 0.16}" fill="${shade(wall, 0.85)}"/>` + cols +
      `<rect x="${-w * 0.46}" y="${-h * 0.8}" width="${w * 0.92}" height="${h * 0.1}" fill="${shade(wall, 0.9)}" stroke="${shade(wall, 0.75)}" stroke-width="${w * 0.008}"/>` +
      `<path d="M${-w * 0.22} ${-h * 0.8} A${w * 0.22} ${w * 0.22} 0 0 1 ${w * 0.22} ${-h * 0.8} Z" fill="${roof}"/>` +
      `<rect x="${-w * 0.015}" y="${-h * 0.8 - w * 0.36}" width="${w * 0.03}" height="${w * 0.16}" fill="${shade(roof, 0.7)}"/>`;
  } else if (kind === "exchange") {
    const h = w * 0.9; top = -h - w * 0.1;
    body = `<rect x="${-w * 0.46}" y="${-h}" width="${w * 0.92}" height="${h}" rx="${w * 0.02}" fill="${wall}" stroke="${shade(wall, 0.7)}" stroke-width="${w * 0.012}"/>` +
      `<rect x="${-w * 0.46}" y="${-h * 0.82}" width="${w * 0.92}" height="${h * 0.16}" fill="#1f2a33"/>` +
      `<path d="M${-w * 0.4} ${-h * 0.7} L${-w * 0.2} ${-h * 0.76} L${-w * 0.02} ${-h * 0.71} L${w * 0.18} ${-h * 0.79} L${w * 0.38} ${-h * 0.74}" fill="none" stroke="#2fb463" stroke-width="${w * 0.018}"/>` +
      windows(-w * 0.36, -h * 0.55, 4, 2, w * 0.14, w * 0.11, w * 0.06, w * 0.07, shade(roof, 1.3)) +
      `<rect x="${-w * 0.1}" y="${-w * 0.2}" width="${w * 0.2}" height="${w * 0.2}" fill="${shade(roof, 0.8)}"/>` +
      `<rect x="${-w * 0.5}" y="${-h - w * 0.06}" width="${w}" height="${w * 0.07}" fill="${roof}"/>`;
  } else if (kind === "house") {
    const h = w * 0.6; top = -h - w * 0.4;
    body = `<rect x="${-w * 0.36}" y="${-h}" width="${w * 0.72}" height="${h}" fill="${wall}" stroke="${shade(wall, 0.75)}" stroke-width="${w * 0.012}"/>` +
      `<path d="M${-w * 0.46} ${-h} L0 ${-h - w * 0.38} L${w * 0.46} ${-h} Z" fill="${roof}" stroke="${shade(roof)}" stroke-width="${w * 0.012}"/>` +
      `<rect x="${-w * 0.08}" y="${-h * 0.5}" width="${w * 0.16}" height="${h * 0.5}" fill="${shade(roof, 0.8)}"/>` + windows(-w * 0.29, -h * 0.72, 1, 1, w * 0.14, w * 0.12, 0, 0, "#9fc7e8") + windows(w * 0.15, -h * 0.72, 1, 1, w * 0.14, w * 0.12, 0, 0, "#9fc7e8");
  } else if (kind === "shop") {
    const h = w * 0.62; top = -h - w * 0.06;
    let awning = "";
    for (let i = 0; i < 6; i++) awning += `<path d="M${-w * 0.45 + i * w * 0.15} ${-h * 0.82} L${-w * 0.3 + i * w * 0.15} ${-h * 0.82} L${-w * 0.3 + i * w * 0.15} ${-h * 0.66} Q${-w * 0.375 + i * w * 0.15} ${-h * 0.58} ${-w * 0.45 + i * w * 0.15} ${-h * 0.66} Z" fill="${i % 2 ? "#ffffff" : roof}"/>`;
    body = `<rect x="${-w * 0.45}" y="${-h}" width="${w * 0.9}" height="${h}" fill="${wall}" stroke="${shade(wall, 0.75)}" stroke-width="${w * 0.012}"/>` + awning +
      `<rect x="${-w * 0.36}" y="${-h * 0.48}" width="${w * 0.72}" height="${h * 0.3}" fill="#c8a06a" stroke="#8a6d3b" stroke-width="${w * 0.01}"/>`;
  } else if (kind === "warehouse") {
    const h = w * 0.6; top = -h - w * 0.2;
    body = `<path d="M${-w * 0.48} 0 L${-w * 0.48} ${-h} L0 ${-h - w * 0.2} L${w * 0.48} ${-h} L${w * 0.48} 0 Z" fill="${wall}" stroke="${shade(roof)}" stroke-width="${w * 0.012}"/>` +
      `<rect x="${-w * 0.24}" y="${-h * 0.62}" width="${w * 0.48}" height="${h * 0.62}" fill="${shade(roof, 1.1)}"/>` +
      [0.1, 0.22, 0.34, 0.46].map((f) => `<path d="M${-w * 0.24} ${-h * 0.62 + h * f * 1.2} L${w * 0.24} ${-h * 0.62 + h * f * 1.2}" stroke="${shade(roof, 0.8)}" stroke-width="${w * 0.01}"/>`).join("");
  } else if (kind === "factory") {
    const h = w * 0.5, sick = p.sick === true; top = -h - w * 0.17;
    let saw = "";
    for (let i = 0; i < 3; i++) saw += `<path d="M${-w * 0.46 + i * w * 0.2} ${-h} L${-w * 0.34 + i * w * 0.2} ${-h - w * 0.13} L${-w * 0.26 + i * w * 0.2} ${-h} Z" fill="${shade(wall, 0.8)}" stroke="${shade(wall, 0.65)}" stroke-width="${w * 0.008}"/>`;
    const smoke = sick ? "" : [0, 1, 2].map((k) => `<circle cx="${w * 0.33 + k * w * 0.05}" cy="${-h - w * 0.5 - k * w * 0.07}" r="${w * (0.05 + k * 0.02)}" fill="#c7ccd3" opacity="${0.85 - k * 0.2}"/>`).join("");
    body = `<rect x="${-w * 0.46}" y="${-h}" width="${w * 0.66}" height="${h}" fill="${sick ? "#e8d6d6" : wall}" stroke="${shade(wall, 0.65)}" stroke-width="${w * 0.01}"/>` + saw +
      `<rect x="${w * 0.27}" y="${-h - w * 0.42}" width="${w * 0.1}" height="${h + w * 0.42}" fill="${sick ? "#9a8f8f" : roof}"/>` + smoke +
      windows(-w * 0.4, -h * 0.75, 3, 1, w * 0.13, w * 0.1, w * 0.06, 0, sick ? "#8a8f98" : "#9fc7e8") +
      `<rect x="${-w * 0.2}" y="${-h * 0.42}" width="${w * 0.18}" height="${h * 0.42}" fill="${shade(roof, 0.8)}"/>` +
      (sick ? `<path d="M${-w * 0.4} ${-h * 0.72} L${-w * 0.3} ${-h * 0.58} M${-w * 0.3} ${-h * 0.72} L${-w * 0.4} ${-h * 0.58}" stroke="#5a4636" stroke-width="${w * 0.012}"/>` : "");
  } else if (kind === "court") {
    const h = w * 0.72; top = -h - w * 0.3;
    let cols = "";
    for (let i = 0; i < 4; i++) cols += `<rect x="${-w * 0.33 + i * w * 0.22 - w * 0.035}" y="${-h * 0.8}" width="${w * 0.07}" height="${h * 0.66}" fill="${wall}" stroke="${shade(wall, 0.75)}" stroke-width="${w * 0.008}"/>`;
    const sx = w * 0.09, sy = -h - w * 0.13;
    body = `<rect x="${-w * 0.48}" y="${-h * 0.14}" width="${w * 0.96}" height="${h * 0.14}" fill="${shade(wall, 0.85)}"/>` + cols +
      `<rect x="${-w * 0.46}" y="${-h * 0.88}" width="${w * 0.92}" height="${h * 0.09}" fill="${shade(wall, 0.9)}" stroke="${shade(wall, 0.75)}" stroke-width="${w * 0.008}"/>` +
      `<path d="M${-w * 0.5} ${-h * 0.88} L0 ${-h - w * 0.28} L${w * 0.5} ${-h * 0.88} Z" fill="${roof}" stroke="${shade(roof)}" stroke-width="${w * 0.01}"/>` +
      `<g stroke="#e6c25a" stroke-width="${w * 0.012}" fill="none" stroke-linecap="round"><path d="M0 ${sy - w * 0.05} L0 ${sy + w * 0.06} M${-sx} ${sy - w * 0.03} L${sx} ${sy - w * 0.03}"/>` +
      `<path d="M${-sx * 1.35} ${sy + w * 0.03} Q${-sx} ${sy + w * 0.07} ${-sx * 0.65} ${sy + w * 0.03} M${sx * 0.65} ${sy + w * 0.03} Q${sx} ${sy + w * 0.07} ${sx * 1.35} ${sy + w * 0.03}"/></g>`;
  } else {
    const h = w * 0.5; top = -h - w * 0.32;
    body = `<rect x="${-w * 0.38}" y="${-h}" width="${w * 0.76}" height="${h}" fill="${wall}" stroke="${shade(wall, 0.7)}" stroke-width="${w * 0.012}"/>` +
      `<path d="M${-w * 0.48} ${-h} Q0 ${-h - w * 0.42} ${w * 0.48} ${-h} Z" fill="#c9a24b" stroke="#8a6d3b" stroke-width="${w * 0.012}"/>` +
      `<rect x="${-w * 0.08}" y="${-h * 0.62}" width="${w * 0.16}" height="${h * 0.62}" fill="${shade(roof, 0.8)}"/>`;
  }
  const lab = p.label ? `<g transform="translate(0,${top - w * 0.06})"><rect x="${-w * 0.32}" y="${-w * 0.12}" width="${w * 0.64}" height="${w * 0.13}" rx="${w * 0.03}" fill="${INK}"/>` +
    tx(p.label, 0, -w * 0.055, Math.min(w * 0.09, (w * 0.6) / Math.max(1, String(p.label).length) * 1.8), "#ffffff", 700) + `</g>` : "";
  return body + lab;
}

function priceTag(p) {
  const w = p.w || 170, h = w * 0.56, col = p.color || "#f2c14e", now = String(p.value ?? "₹50"), old = p.old ? String(p.old) : "";
  const arrow = p.trend === "up" ? `<path d="M${w * 0.36} ${h * 0.14} L${w * 0.46} ${-h * 0.06} L${w * 0.56} ${h * 0.14} Z" fill="#2fa35b"/>`
    : p.trend === "down" ? `<path d="M${w * 0.36} ${-h * 0.06} L${w * 0.46} ${h * 0.14} L${w * 0.56} ${-h * 0.06} Z" fill="#e5484d"/>` : "";
  return `<path d="M${-w * 0.5} ${-h * 0.5} L${w * 0.32} ${-h * 0.5} L${w * 0.5} 0 L${w * 0.32} ${h * 0.5} L${-w * 0.5} ${h * 0.5} Z" fill="${col}" stroke="${shade(col)}" stroke-width="${w * 0.02}"/>` +
    `<circle cx="${w * 0.3}" cy="0" r="${h * 0.08}" fill="#ffffff" stroke="${shade(col)}" stroke-width="${w * 0.01}"/>` +
    (old ? tx(old, -w * 0.1, -h * 0.2, h * 0.28, "#7a5a00", 700) + `<path d="M${-w * 0.36} ${-h * 0.2} L${w * 0.16} ${-h * 0.2}" stroke="#e5484d" stroke-width="${h * 0.06}"/>` : "") +
    tx(now, -w * 0.1, old ? h * 0.2 : 0, old ? h * 0.36 : h * 0.44, INK, 800) + arrow;
}

function gauge(p) {
  const w = p.w || 220, r = w * 0.42, v = clamp01(p.value == null ? 0.6 : p.value), a = Math.PI * (1 - v), cy = -w * 0.24;
  const seg = (f0, f1, c) => { const a0 = Math.PI * (1 - f0), a1 = Math.PI * (1 - f1);
    return `<path d="M${Math.cos(a0) * r} ${cy - Math.sin(a0) * r} A${r} ${r} 0 0 1 ${Math.cos(a1) * r} ${cy - Math.sin(a1) * r}" fill="none" stroke="${c}" stroke-width="${w * 0.09}"/>`; };
  const t = p.text ? String(p.text) : "";
  return `<path d="M${-r - w * 0.07} ${cy} A${r + w * 0.07} ${r + w * 0.07} 0 0 1 ${r + w * 0.07} ${cy} Z" fill="#ffffff" stroke="#cfd6de" stroke-width="${w * 0.01}"/>` +
    seg(0, 0.34, p.reverse ? "#2fa35b" : "#e5484d") + seg(0.34, 0.67, "#f2c14e") + seg(0.67, 1, p.reverse ? "#e5484d" : "#2fa35b") +
    `<path d="M0 ${cy} L${Math.cos(a) * r * 0.8} ${cy - Math.sin(a) * r * 0.8}" stroke="${INK}" stroke-width="${w * 0.03}" stroke-linecap="round"/><circle cy="${cy}" r="${w * 0.04}" fill="${INK}"/>` +
    `<rect x="${-r - w * 0.07}" y="${cy + w * 0.02}" width="${2 * r + w * 0.14}" height="${-cy - w * 0.02}" rx="${w * 0.03}" fill="#2d3748"/>` +
    tx(t || (p.label ? String(p.label) : ""), 0, cy / 2 + w * 0.01, Math.min(w * 0.12, (w * 0.9) / Math.max(1, (t || String(p.label || "")).length) * 1.8), "#ffffff", 800) +
    (t && p.label ? tx(p.label, 0, cy - r - w * 0.15, Math.min(w * 0.09, (w * 0.9) / Math.max(1, String(p.label).length) * 1.8), INK, 700) : "");
}

const FX = { "$": "#3d8b5a", "€": "#3a6fb5", "£": "#8e4fa8", "¥": "#c0563f", "¤": "#6b7280" };
function foreignNote(p) {
  const w = p.w || 170, h = w * 0.46, sign = FX[p.sign] ? p.sign : "$", col = p.color || FX[sign], v = String(p.value ?? "100");
  return `<rect x="${-w * 0.5}" y="${-h * 0.5}" width="${w}" height="${h}" rx="${w * 0.03}" fill="${shade(col, 1.6)}" stroke="${col}" stroke-width="${w * 0.02}"/>` +
    `<rect x="${-w * 0.44}" y="${-h * 0.38}" width="${w * 0.88}" height="${h * 0.76}" rx="${w * 0.02}" fill="none" stroke="${col}" stroke-width="${w * 0.01}" stroke-dasharray="${w * 0.02} ${w * 0.012}"/>` +
    `<ellipse cx="0" cy="0" rx="${h * 0.32}" ry="${h * 0.3}" fill="${col}" opacity="0.85"/>` + tx(sign, 0, 0, h * 0.42, "#ffffff", 800) +
    tx(v, -w * 0.32, -h * 0.2, h * 0.24, col, 800) + tx(v, w * 0.32, h * 0.2, h * 0.24, col, 800);
}

function barrier(p) {
  const w = p.w || 240, h = w * 0.5, rows = 4, bh = h / rows;
  let bricks = "";
  for (let r = 0; r < rows; r++) {
    const off = r % 2 ? w * 0.08 : 0;
    for (let x = -w / 2 - off; x < w / 2; x += w * 0.16) {
      const x0 = Math.max(-w / 2, x), x1 = Math.min(w / 2, x + w * 0.15);
      if (x1 > x0) bricks += `<rect x="${x0}" y="${-h + r * bh}" width="${x1 - x0}" height="${bh * 0.88}" rx="${w * 0.01}" fill="#c25b3f" stroke="#8a3b27" stroke-width="${w * 0.006}"/>`;
    }
  }
  return bricks + (p.label ? `<rect x="${-w * 0.3}" y="${-h * 0.66}" width="${w * 0.6}" height="${h * 0.32}" rx="${w * 0.03}" fill="#ffffff" stroke="#8a3b27" stroke-width="${w * 0.01}"/>` +
    tx(p.label, 0, -h * 0.5, Math.min(h * 0.2, (w * 0.56) / Math.max(1, String(p.label).length) * 1.8), "#8a3b27", 800) : "");
}

const SEG_COLORS = ["#3a7bd5", "#f29f05", "#2fa35b", "#e2558f", "#7b61ff", "#2a9d8f", "#c0563f", "#9b6b43"];
const idxList = (v) => String(v || "").split(/[,\s]+/).filter(Boolean).map((x) => parseInt(x, 10) - 1).filter((x) => x >= 0);
function segmentedBar(p) {
  // parts: "label:value;label:value" (values are shares; widths follow them). cross / hide / glow: 1-based part numbers.
  const w = p.w || 520, h = p.h || w * 0.16;
  const parts = String(p.parts || "खाना:46;ईंधन:7;बाकी:47").split(";").map((t) => { const [l, v] = t.split(":"); return { l: (l || "").trim(), v: Math.max(0, Number(v) || 0) }; }).filter((x) => x.l || x.v);
  const hide = new Set(idxList(p.hide)), cross = new Set(idxList(p.cross)), glow = new Set(idxList(p.glow));
  const shown = parts.map((x, i) => ({ ...x, i })).filter((x) => !hide.has(x.i));
  const total = shown.reduce((a, x) => a + x.v, 0) || 1, full = parts.reduce((a, x) => a + x.v, 0) || 1;
  const bw = p.shrink === false ? w : w * (total / full);
  let x = -w / 2, out = "", narrow = 0;
  for (const s of shown) {
    const sw = (s.v / total) * bw, c = SEG_COLORS[s.i % SEG_COLORS.length], fs = Math.min(h * 0.34, (sw * 0.9) / Math.max(1, s.l.length) * 1.7);
    out += `<rect x="${x}" y="${-h / 2}" width="${sw}" height="${h}" fill="${c}" stroke="#ffffff" stroke-width="${Math.max(2, w * 0.006)}"/>` +
      (fs >= h * 0.22 ? tx(s.l, x + sw / 2, -h * 0.12, fs, "#ffffff", 800) + (p.values === false ? "" : tx(String(s.v) + (p.unit ?? "%"), x + sw / 2, h * 0.24, fs * 0.8, "#ffffff", 700))
        : (() => { const below = (narrow++ % 2) === 0, fo = h * 0.3, yy = below ? h / 2 + fo * 1.1 : -h / 2 - fo * 1.1;
            const txt = s.l + (p.values === false ? "" : " " + String(s.v) + (p.unit ?? "%"));
            return `<path d="M${x + sw / 2} ${below ? h / 2 : -h / 2} L${x + sw / 2} ${below ? yy - fo * 0.55 : yy + fo * 0.55}" stroke="${c}" stroke-width="3"/>` + tx(txt, x + sw / 2, yy, fo, c, 800); })()) +
      (glow.has(s.i) ? `<rect x="${x - 4}" y="${-h / 2 - 4}" width="${sw + 8}" height="${h + 8}" fill="none" stroke="#f2c14e" stroke-width="${Math.max(4, h * 0.08)}"/>` : "") +
      (cross.has(s.i) ? `<path d="M${x + sw * 0.15} ${-h * 0.4} L${x + sw * 0.85} ${h * 0.4} M${x + sw * 0.85} ${-h * 0.4} L${x + sw * 0.15} ${h * 0.4}" stroke="#e5484d" stroke-width="${Math.max(4, h * 0.1)}" stroke-linecap="round"/>` : "");
    x += sw;
  }
  return `<rect x="${-w / 2 - 3}" y="${-h / 2 - 3}" width="${bw + 6}" height="${h + 6}" rx="${h * 0.12}" fill="none" stroke="#2d3748" stroke-width="3"/>` + out +
    (p.label ? tx(p.label, -w / 2 + bw / 2, -h / 2 - h * 0.4, Math.min(h * 0.4, (w * 0.8) / Math.max(1, String(p.label).length) * 1.8), INK, 800) : "");
}

function cart(p) {
  // a hand cart (thela) or fund cart: a flat bed on two wheels with what it carries and a board.
  const w = p.w || 260, bh = w * 0.14, bedY = -w * 0.3, content = p.content || "veg", R = w * 0.11;
  let load = "";
  if (content === "veg") {
    const cols = ["#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e5484d", "#2fa35b", "#f29f05"];
    for (let i = 0; i < 7; i++) load += `<circle cx="${-w * 0.36 + i * w * 0.12}" cy="${bedY - w * 0.06 - (i % 2) * w * 0.05}" r="${w * 0.065}" fill="${cols[i]}" stroke="${shade(cols[i])}" stroke-width="${w * 0.008}"/>`;
  } else if (content === "notes") {
    for (let i = 0; i < 3; i++) load += `<g transform="translate(${-w * 0.26 + i * w * 0.26},${bedY - w * 0.08})">${noteBundle({ w: w * 0.24, value: 500 })}</g>`;
  } else if (content === "goods") {
    for (let i = 0; i < 4; i++) load += `<rect x="${-w * 0.4 + i * w * 0.2}" y="${bedY - w * 0.16 - (i % 2) * w * 0.04}" width="${w * 0.17}" height="${w * 0.16 + (i % 2) * w * 0.04}" rx="${w * 0.01}" fill="#c8a06a" stroke="#8a6d3b" stroke-width="${w * 0.008}"/>`;
  }
  const wheel = (x) => `<circle cx="${x}" cy="${-R}" r="${R}" fill="#4a5568" stroke="#2d3748" stroke-width="${w * 0.012}"/><circle cx="${x}" cy="${-R}" r="${R * 0.3}" fill="#cbd5e0"/>`;
  return load + `<rect x="${-w * 0.46}" y="${bedY}" width="${w * 0.92}" height="${bh}" rx="${w * 0.02}" fill="#a8763f" stroke="#7d5427" stroke-width="${w * 0.01}"/>` +
    `<path d="M${w * 0.46} ${bedY + bh * 0.4} L${w * 0.62} ${bedY - w * 0.04}" stroke="#7d5427" stroke-width="${w * 0.025}" stroke-linecap="round"/>` +
    wheel(-w * 0.26) + wheel(w * 0.26) +
    (p.label ? `<rect x="${-w * 0.25}" y="${bedY + bh * 0.12}" width="${w * 0.5}" height="${bh * 0.76}" rx="${w * 0.015}" fill="#f7efe0"/>` + tx(p.label, 0, bedY + bh * 0.5, Math.min(bh * 0.55, (w * 0.46) / Math.max(1, String(p.label).length) * 1.8), "#6b4a22", 800) : "");
}

function piggyBank(p) {
  const w = p.w || 180, h = w * 0.62, c = p.color || "#f08bb0";
  return `<ellipse cx="0" cy="${-h * 0.55}" rx="${w * 0.42}" ry="${h * 0.42}" fill="${c}" stroke="${shade(c)}" stroke-width="${w * 0.015}"/>` +
    `<ellipse cx="${w * 0.4}" cy="${-h * 0.55}" rx="${w * 0.09}" ry="${h * 0.14}" fill="${shade(c, 0.9)}" stroke="${shade(c)}" stroke-width="${w * 0.012}"/>` +
    `<circle cx="${w * 0.38}" cy="${-h * 0.58}" r="${w * 0.015}" fill="${shade(c, 0.5)}"/><circle cx="${w * 0.42}" cy="${-h * 0.52}" r="${w * 0.015}" fill="${shade(c, 0.5)}"/>` +
    `<circle cx="${w * 0.2}" cy="${-h * 0.75}" r="${w * 0.025}" fill="#2d3748"/>` +
    `<path d="M${w * 0.08} ${-h * 0.97} L${w * 0.16} ${-h * 1.12} L${w * 0.24} ${-h * 0.92} Z" fill="${shade(c, 0.85)}"/>` +
    `<rect x="${-w * 0.12}" y="${-h * 0.98}" width="${w * 0.2}" height="${h * 0.05}" rx="${h * 0.02}" fill="${shade(c, 0.5)}"/>` +
    [-0.26, -0.1, 0.1, 0.24].map((x) => `<rect x="${x * w - w * 0.04}" y="${-h * 0.22}" width="${w * 0.08}" height="${h * 0.22}" rx="${w * 0.02}" fill="${shade(c, 0.85)}"/>`).join("") +
    (p.label ? tx(p.label, -w * 0.04, -h * 0.5, Math.min(h * 0.24, (w * 0.62) / Math.max(1, String(p.label).length) * 1.8), "#ffffff", 800) : "");
}

function ruler(p) {
  // a min-max ruler: where a value sits between a minimum and a maximum (goalposts, normalised index, caps)
  const w = p.w || 520, h = w * 0.09, lo = Number(p.min ?? 0), hi = Number(p.max ?? 100), v = Number(p.value ?? 60);
  const f = hi > lo ? Math.max(0, Math.min(1, (v - lo) / (hi - lo))) : 0, capped = v < lo || v > hi, x = -w / 2 + f * w;
  let ticks = "";
  for (let i = 0; i <= 10; i++) ticks += `<path d="M${-w / 2 + (i * w) / 10} ${-h / 2} L${-w / 2 + (i * w) / 10} ${-h / 2 + (i % 5 ? h * 0.35 : h * 0.6)}" stroke="#7d5427" stroke-width="${w * 0.004}"/>`;
  const fs = Math.max(22, h * 0.6);
  return `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${h * 0.15}" fill="#f2d39b" stroke="#a8763f" stroke-width="${w * 0.005}"/>` + ticks +
    `<rect x="${-w / 2}" y="${-h / 2}" width="${f * w}" height="${h}" rx="${h * 0.15}" fill="#2fa35b" opacity="0.35"/>` +
    `<path d="M${x} ${-h / 2 - h * 0.1} L${x - h * 0.45} ${-h / 2 - h * 0.8} L${x + h * 0.45} ${-h / 2 - h * 0.8} Z" fill="${capped ? "#e5484d" : "#2d3748"}"/>` +
    tx(String(p.text ?? v), x, -h / 2 - h * 0.8 - fs * 0.7, fs, capped ? "#e5484d" : INK, 800) +
    tx(String(p.minLabel ?? lo), -w / 2, h / 2 + fs * 0.8, fs * 0.85, "#6b4a22", 700) + tx(String(p.maxLabel ?? hi), w / 2, h / 2 + fs * 0.8, fs * 0.85, "#6b4a22", 700);
}

function hands(p) {
  // a giving hand above-left and an open receiving hand below-right with the thing passed between them
  // (lend/borrow, fund surplus to fund need, payment); labels name the two sides.
  const w = p.w || 420, s = w * 0.22, skin = p.skin || "#d39a6a", cuffL = p.colorFrom || "#3a7bd5", cuffR = p.colorTo || "#e07b24";
  const hand = (x, y, flip, cuff) => `<g transform="translate(${x},${y}) scale(${flip ? -1 : 1},1)">` +
    `<rect x="${-s * 1.25}" y="${-s * 0.32}" width="${s * 0.55}" height="${s * 0.64}" rx="${s * 0.1}" fill="${cuff}" stroke="${shade(cuff)}" stroke-width="${s * 0.04}"/>` +
    `<path d="M${-s * 0.72} ${-s * 0.3} L${s * 0.15} ${-s * 0.3} Q${s * 0.62} ${-s * 0.3} ${s * 0.62} ${-s * 0.12} Q${s * 0.62} ${s * 0.02} ${s * 0.2} ${s * 0.02} L${s * 0.5} ${s * 0.02} Q${s * 0.68} ${s * 0.04} ${s * 0.66} ${s * 0.16} Q${s * 0.64} ${s * 0.3} ${s * 0.44} ${s * 0.3} L${-s * 0.72} ${s * 0.3} Z" fill="${skin}" stroke="${shade(skin)}" stroke-width="${s * 0.04}"/>` +
    `<path d="M${s * 0.1} ${-s * 0.3} Q${s * 0.3} ${-s * 0.52} ${s * 0.12} ${-s * 0.6} Q${-s * 0.06} ${-s * 0.6} ${-s * 0.12} ${-s * 0.3}" fill="${skin}" stroke="${shade(skin)}" stroke-width="${s * 0.04}"/></g>`;
  const item = p.item || "notes";
  const mid = item === "notes" ? noteBundle({ w: s * 1.1, value: 500 }) : item === "coin" ? coin({ r: s * 0.32 }) : item === "paper" ? paper({ w: s * 0.7, kind: "bond", title: "", lines: 2 }) : "";
  return hand(-w * 0.2, -w * 0.12, false, cuffL) + `<g transform="translate(${w * 0.02},${-w * 0.02})">${mid}</g>` + hand(w * 0.22, w * 0.1, true, cuffR) +
    (p.from ? tx(p.from, -w * 0.3, -w * 0.3, Math.max(24, s * 0.3), shade(cuffL, 0.8), 800) : "") +
    (p.to ? tx(p.to, w * 0.3, w * 0.3, Math.max(24, s * 0.3), shade(cuffR, 0.8), 800) : "");
}

// ---------------------------------------------------------------- marks
export function markSvg(kind, w, color, k = 1) {
  const r = w / 2;
  if (kind === "cross") {
    const c = color || "#e5484d";
    return `<path d="M${-r} ${-r} L${(-r + 2 * r * Math.min(1, k * 2)).toFixed(1)} ${(-r + 2 * r * Math.min(1, k * 2)).toFixed(1)}" stroke="${c}" stroke-width="${w * 0.14}" stroke-linecap="round"/>` +
      (k > 0.5 ? `<path d="M${r} ${-r} L${(r - 2 * r * Math.min(1, (k - 0.5) * 2)).toFixed(1)} ${(-r + 2 * r * Math.min(1, (k - 0.5) * 2)).toFixed(1)}" stroke="${c}" stroke-width="${w * 0.14}" stroke-linecap="round"/>` : "");
  }
  if (kind === "tick") {
    const c = color || "#2fb463";
    return `<circle r="${r}" fill="${c}" opacity="${0.92 * Math.min(1, k * 1.6)}"/>` +
      `<path d="M${-r * 0.42} ${r * 0.02} L${-r * 0.08} ${r * 0.36} L${r * 0.46} ${-r * 0.32}" stroke="#ffffff" stroke-width="${w * 0.12}" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="${r * 2.2}" stroke-dashoffset="${(r * 2.2 * (1 - Math.min(1, k))).toFixed(1)}"/>`;
  }
  if (kind === "question") {
    const c = color || "#e5484d";
    return `<text x="0" y="${r * 0.72}" font-family=${JSON.stringify(FONT)} font-size="${w * 1.45}" font-weight="800" fill="${c}" text-anchor="middle" opacity="${Math.min(1, k * 1.8)}">?</text>`;
  }
  const c = color || "#e5484d"; // circle
  return `<circle r="${r}" fill="none" stroke="${c}" stroke-width="${w * 0.14}" stroke-dasharray="${2 * Math.PI * r}" stroke-dashoffset="${(2 * Math.PI * r * (1 - Math.min(1, k))).toFixed(1)}" transform="rotate(-90)"/>`;
}

// ---------------------------------------------------------------- economy kit, batch 5 (4 Nov 2026)
// The rest of the 57-video needs list: a coin jar that fills, pillars that hold a roof (one can crack), a briefcase,
// a winners' podium, a staircase of steps, a desk with its chair, a chair, and a rope / rod / chain that ties two
// things. Whole places behind the lesson (market, bank hall, port, ...) are the world saancha (worlds.mjs).
export const parts = (s) => String(s ?? "").split(";").map((t) => t.trim());
export const idxSet = (s) => new Set(String(s ?? "").split(",").map((t) => parseInt(t, 10)).filter((v) => v > 0));
export const fit = (t, maxW, cap) => Math.min(cap, (maxW * 0.92) / Math.max(1, String(t).length) * 1.75);

function coinJar(p) {
  const w = p.w || 160, h = w * 1.25, f = clamp01(p.fill == null ? 0.5 : p.fill), lid = p.color || "#c0563f";
  const ch = w * 0.075, rows = Math.floor((h * 0.74 * f) / ch);
  let coins = "";
  for (let r = 0; r < rows; r++) {
    const xs = r % 2 ? [-0.18, 0, 0.18] : [-0.27, -0.09, 0.09, 0.27];
    for (const fx of xs) coins += `<ellipse cx="${fx * w}" cy="${-w * 0.08 - r * ch}" rx="${w * 0.09}" ry="${w * 0.036}" fill="#f2c14e" stroke="#c99a2e" stroke-width="${w * 0.012}"/>`;
  }
  return `<rect x="${-w * 0.42}" y="${-h * 0.86}" width="${w * 0.84}" height="${h * 0.86}" rx="${w * 0.14}" fill="#e3f1fb"/>` + coins +
    `<rect x="${-w * 0.42}" y="${-h * 0.86}" width="${w * 0.84}" height="${h * 0.86}" rx="${w * 0.14}" fill="#dcefff" fill-opacity="0.25" stroke="#8fb3cf" stroke-width="${w * 0.025}"/>` +
    `<path d="M${-w * 0.3} ${-h * 0.74} L${-w * 0.3} ${-h * 0.3}" stroke="#ffffff" stroke-width="${w * 0.035}" stroke-linecap="round" opacity="0.7"/>` +
    `<rect x="${-w * 0.36}" y="${-h * 0.97}" width="${w * 0.72}" height="${h * 0.12}" rx="${w * 0.04}" fill="${lid}" stroke="${shade(lid)}" stroke-width="${w * 0.015}"/>` +
    `<rect x="${-w * 0.14}" y="${-h * 0.93}" width="${w * 0.28}" height="${h * 0.03}" rx="${h * 0.015}" fill="${shade(lid, 0.5)}"/>` +
    (p.label ? `<rect x="${-w * 0.36}" y="${-h * 0.56}" width="${w * 0.72}" height="${h * 0.17}" rx="${w * 0.04}" fill="#ffffff" opacity="0.92"/>` +
      tx(p.label, 0, -h * 0.475, fit(p.label, w * 0.7, w * 0.15), INK, 800) : "");
}

function pillars(p) {
  const labels = parts(p.labels), w = p.w || 520, h = w * 0.75, c = p.color || "#e9e2d2";
  const n = Math.max(1, Math.min(6, Math.round(p.n || (p.labels ? labels.length : 3))));
  const broken = idxSet(p.broken), glow = idxSet(p.glow), slot = w / n, pw = Math.min(slot * 0.42, w * 0.14);
  let cols = "";
  for (let i = 0; i < n; i++) {
    const cx = -w / 2 + (i + 0.5) * slot, y0 = -h * 0.76, y1 = -h * 0.09, bad = broken.has(i + 1), fill = bad ? shade(c, 0.82) : c;
    let fl = "";
    for (let k = 1; k < 4; k++) fl += `<path d="M${cx - pw / 2 + (k * pw) / 4} ${y0 + h * 0.04} L${cx - pw / 2 + (k * pw) / 4} ${y1 - h * 0.03}" stroke="${shade(c, 0.85)}" stroke-width="${w * 0.004}"/>`;
    cols += `<rect x="${cx - pw / 2}" y="${y0}" width="${pw}" height="${y1 - y0}" fill="${fill}" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.005}"/>` + fl +
      `<rect x="${cx - pw * 0.65}" y="${y0 - h * 0.03}" width="${pw * 1.3}" height="${h * 0.035}" fill="${shade(c, 0.9)}"/>` +
      `<rect x="${cx - pw * 0.65}" y="${y1 - h * 0.005}" width="${pw * 1.3}" height="${h * 0.035}" fill="${shade(c, 0.9)}"/>` +
      (bad ? `<path d="M${cx - pw * 0.45} ${y0 + (y1 - y0) * 0.38} L${cx - pw * 0.05} ${y0 + (y1 - y0) * 0.46} L${cx - pw * 0.25} ${y0 + (y1 - y0) * 0.55} L${cx + pw * 0.2} ${y0 + (y1 - y0) * 0.62} L${cx + pw * 0.05} ${y0 + (y1 - y0) * 0.7} L${cx + pw * 0.45} ${y0 + (y1 - y0) * 0.76}" fill="none" stroke="#5a4636" stroke-width="${w * 0.008}" stroke-linejoin="round"/>` : "") +
      (glow.has(i + 1) ? `<rect x="${cx - pw * 0.75}" y="${y0 - h * 0.05}" width="${pw * 1.5}" height="${y1 - y0 + h * 0.1}" fill="none" stroke="#f2c14e" stroke-width="${w * 0.012}" rx="${w * 0.01}"/>` : "") +
      (labels[i] ? `<rect x="${cx - slot * 0.46}" y="${(y0 + y1) / 2 - h * 0.06}" width="${slot * 0.92}" height="${h * 0.12}" rx="${h * 0.02}" fill="#ffffff" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.004}"/>` +
        tx(labels[i], cx, (y0 + y1) / 2, fit(labels[i], slot * 0.88, w * 0.055), INK, 800) : "");
  }
  return `<rect x="${-w * 0.5}" y="${-h * 0.06}" width="${w}" height="${h * 0.06}" fill="${shade(c, 0.8)}"/><rect x="${-w * 0.47}" y="${-h * 0.1}" width="${w * 0.94}" height="${h * 0.045}" fill="${shade(c, 0.9)}"/>` +
    cols + `<rect x="${-w * 0.5}" y="${-h * 0.86}" width="${w}" height="${h * 0.08}" fill="${shade(c, 0.9)}" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.005}"/>` +
    `<path d="M${-w * 0.52} ${-h * 0.86} L0 ${-h * 1.02} L${w * 0.52} ${-h * 0.86} Z" fill="${c}" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.006}"/>` +
    (p.title ? tx(p.title, 0, -h * 0.82, fit(p.title, w * 0.9, h * 0.065), INK, 800) : "");
}

function briefcase(p) {
  const w = p.w || 180, h = w * 0.68, c = p.color || "#8a3b2a", open = p.open === true;
  const papers = open ? [0, 1, 2].map((k) => `<rect x="${-w * 0.32 + k * w * 0.2}" y="${-h * 1.15 + k * h * 0.06}" width="${w * 0.26}" height="${h * 0.42}" fill="#ffffff" stroke="#c9ccd1" stroke-width="${w * 0.01}" transform="rotate(${(k - 1) * 8} ${-w * 0.19 + k * w * 0.2} ${-h * 0.8})"/>`).join("") : "";
  return (open ? `<path d="M${-w * 0.48} ${-h * 0.72} L${-w * 0.4} ${-h * 1.2} L${w * 0.4} ${-h * 1.2} L${w * 0.48} ${-h * 0.72} Z" fill="${shade(c, 0.8)}" stroke="${shade(c, 0.6)}" stroke-width="${w * 0.015}"/>` + papers : "") +
    `<path d="M${-w * 0.16} ${-h * 0.76} L${-w * 0.16} ${-h * 0.96} Q${-w * 0.16} ${-h * 1.04} ${-w * 0.08} ${-h * 1.04} L${w * 0.08} ${-h * 1.04} Q${w * 0.16} ${-h * 1.04} ${w * 0.16} ${-h * 0.96} L${w * 0.16} ${-h * 0.76}" fill="none" stroke="${shade(c, 0.6)}" stroke-width="${w * 0.045}" stroke-linejoin="round"/>` +
    `<rect x="${-w * 0.5}" y="${-h * 0.78}" width="${w}" height="${h * 0.78}" rx="${w * 0.06}" fill="${c}" stroke="${shade(c, 0.6)}" stroke-width="${w * 0.015}"/>` +
    (open ? "" : `<path d="M${-w * 0.5} ${-h * 0.56} L${w * 0.5} ${-h * 0.56}" stroke="${shade(c, 0.6)}" stroke-width="${w * 0.012}"/>`) +
    [-0.3, 0.3].map((fx) => `<rect x="${fx * w - w * 0.05}" y="${-h * 0.62}" width="${w * 0.1}" height="${h * 0.1}" rx="${w * 0.015}" fill="#e6c25a" stroke="#a7862d" stroke-width="${w * 0.008}"/>`).join("") +
    (p.label ? `<rect x="${-w * 0.3}" y="${-h * 0.42}" width="${w * 0.6}" height="${h * 0.22}" rx="${w * 0.03}" fill="#f7efe0"/>` + tx(p.label, 0, -h * 0.31, fit(p.label, w * 0.58, h * 0.17), INK, 800) : "");
}

function podium(p) {
  const w = p.w || 480, labels = parts(p.labels), unit = w / 3, hs = [w * 0.36, w * 0.25, w * 0.17];
  const cols = ["#f2c14e", "#c9ced6", "#d9925a"], at = [0, -1, 1];
  let out = "";
  for (let r = 0; r < 3; r++) {
    const x = at[r] * unit - unit / 2, h = hs[r], c = cols[r];
    out += `<rect x="${x}" y="${-h}" width="${unit}" height="${h}" fill="${c}" stroke="${shade(c)}" stroke-width="${w * 0.006}"/>` +
      `<rect x="${x}" y="${-h}" width="${unit}" height="${w * 0.02}" fill="${shade(c, 1.12)}"/>` +
      tx(String(r + 1), x + unit / 2, -h + Math.min(h * 0.32, unit * 0.32), Math.min(h * 0.4, unit * 0.4), shade(c, 0.55), 800) +
      (labels[r] ? tx(labels[r], x + unit / 2, -h * 0.22, fit(labels[r], unit * 0.9, unit * 0.15), INK, 800) : "");
  }
  return out;
}

function staircase(p) {
  const labels = parts(p.labels), w = p.w || 560, h = w * 0.6, c = p.color || "#5b7fb8", down = p.dir === "down";
  const n = Math.max(2, Math.min(8, Math.round(p.n || (p.labels ? labels.length : 4)))), sw = w / n, sh = h / n, at = Math.round(p.at || 0);
  let out = "";
  for (let i = 0; i < n; i++) {
    const x = down ? w / 2 - (i + 1) * sw : -w / 2 + i * sw, top = -(i + 1) * sh, col = i % 2 ? shade(c, 1.15) : c;
    out += `<rect x="${x}" y="${top}" width="${sw}" height="${-top}" fill="${col}" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.004}"/>` +
      `<rect x="${x}" y="${top}" width="${sw}" height="${Math.max(4, sh * 0.12)}" fill="${shade(c, 1.35)}"/>` +
      (labels[i] ? tx(labels[i], x + sw / 2, top + sh * 0.55, fit(labels[i], sw * 0.9, Math.min(sh * 0.5, sw * 0.3)), "#ffffff", 800) : "") +
      (at === i + 1 ? `<rect x="${x - 4}" y="${top - 4}" width="${sw + 8}" height="${sh + 8}" fill="none" stroke="#f2c14e" stroke-width="${Math.max(5, w * 0.012)}" rx="${w * 0.01}"/>` : "");
  }
  return out;
}

function desk(p) {
  const w = p.w || 320, h = w * 0.42, c = p.color || "#a8763f", chairOn = p.chair !== false;
  return (chairOn ? `<rect x="${-w * 0.16}" y="${-h * 1.75}" width="${w * 0.32}" height="${h * 0.95}" rx="${w * 0.05}" fill="#3d4a5c" stroke="#28313d" stroke-width="${w * 0.01}"/>` : "") +
    `<rect x="${-w * 0.5}" y="${-h}" width="${w}" height="${h * 0.12}" rx="${w * 0.01}" fill="${shade(c, 1.1)}" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.008}"/>` +
    `<rect x="${-w * 0.44}" y="${-h * 0.88}" width="${w * 0.88}" height="${h * 0.66}" fill="${c}" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.008}"/>` +
    `<rect x="${-w * 0.44}" y="${-h * 0.22}" width="${w * 0.06}" height="${h * 0.22}" fill="${shade(c, 0.7)}"/><rect x="${w * 0.38}" y="${-h * 0.22}" width="${w * 0.06}" height="${h * 0.22}" fill="${shade(c, 0.7)}"/>` +
    (p.label ? `<rect x="${-w * 0.3}" y="${-h * 0.72}" width="${w * 0.6}" height="${h * 0.3}" rx="${w * 0.02}" fill="#f7efe0" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.006}"/>` +
      tx(p.label, 0, -h * 0.57, fit(p.label, w * 0.58, h * 0.22), INK, 800) : "");
}

function chair(p) {
  const w = p.w || 140, c = p.color || (p.kind === "big" ? "#8a2b3a" : "#3d4a5c"), kind = ["plain", "office", "big"].includes(p.kind) ? p.kind : "plain";
  const back = kind === "big" ? w * 1.5 : kind === "office" ? w * 0.85 : w * 0.75, seatY = -w * 0.55;
  const legs = kind === "office"
    ? `<path d="M0 ${seatY + w * 0.08} L0 ${-w * 0.08}" stroke="#4a5568" stroke-width="${w * 0.06}"/><path d="M${-w * 0.3} 0 L${w * 0.3} 0" stroke="#4a5568" stroke-width="${w * 0.05}" stroke-linecap="round"/>` +
      [-0.3, 0, 0.3].map((fx) => `<circle cx="${fx * w}" cy="${-w * 0.02}" r="${w * 0.04}" fill="#2d3748"/>`).join("")
    : `<path d="M${-w * 0.36} ${seatY} L${-w * 0.36} 0 M${w * 0.36} ${seatY} L${w * 0.36} 0" stroke="${shade(c, 0.7)}" stroke-width="${w * 0.06}" stroke-linecap="round"/>`;
  return legs + `<rect x="${-w * 0.36}" y="${seatY - back}" width="${w * 0.72}" height="${back}" rx="${w * (kind === "big" ? 0.2 : 0.08)}" fill="${c}" stroke="${shade(c, 0.6)}" stroke-width="${w * 0.02}"/>` +
    (kind === "big" ? `<rect x="${-w * 0.26}" y="${seatY - back + w * 0.12}" width="${w * 0.52}" height="${back - w * 0.24}" rx="${w * 0.14}" fill="${shade(c, 1.2)}"/>` +
      [-0.36, 0.36].map((fx) => `<circle cx="${fx * w}" cy="${seatY - back + w * 0.02}" r="${w * 0.07}" fill="#e6c25a"/>`).join("") : "") +
    `<rect x="${-w * 0.46}" y="${seatY - w * 0.06}" width="${w * 0.92}" height="${w * 0.14}" rx="${w * 0.05}" fill="${shade(c, 0.85)}" stroke="${shade(c, 0.6)}" stroke-width="${w * 0.02}"/>` +
    (p.label ? tx(p.label, 0, seatY - back * 0.55, fit(p.label, w * 0.62, w * 0.2), "#ffffff", 800) : "");
}

function rope(p) {
  const w = p.w || 400, kind = ["rope", "rod", "chain"].includes(p.kind) ? p.kind : "rope", ang = Number(p.angle) || 0;
  const sag = kind === "rod" ? 0 : clamp01(p.sag == null ? 0.15 : p.sag) * w * 0.35, x0 = -w / 2, x1 = w / 2;
  const at = (t) => [x0 + (x1 - x0) * t, 4 * sag * t * (1 - t)];
  let body;
  if (kind === "rod") {
    body = `<path d="M${x0} 0 L${x1} 0" stroke="#7a838f" stroke-width="${Math.max(6, w * 0.03)}" stroke-linecap="round"/><path d="M${x0} ${-w * 0.004} L${x1} ${-w * 0.004}" stroke="#c7ccd3" stroke-width="${Math.max(2, w * 0.008)}"/>` +
      [x0, x1].map((x) => `<circle cx="${x}" cy="0" r="${Math.max(6, w * 0.03)}" fill="#4a5568"/>`).join("");
  } else if (kind === "chain") {
    const links = Math.max(4, Math.round(w / 34));
    body = [...Array(links).keys()].map((k) => { const t0 = k / links, t1 = (k + 1) / links, [ax, ay] = at(t0), [bx, by] = at(t1);
      const mx = (ax + bx) / 2, my = (ay + by) / 2, a = (Math.atan2(by - ay, bx - ax) * 180) / Math.PI, len = Math.hypot(bx - ax, by - ay);
      return `<ellipse cx="${mx}" cy="${my}" rx="${len * 0.62}" ry="${Math.max(4, len * 0.28)}" fill="none" stroke="${k % 2 ? "#9aa5b1" : "#6b7280"}" stroke-width="${Math.max(3, len * 0.16)}" transform="rotate(${a} ${mx} ${my})"/>`; }).join("");
  } else {
    const d = `M${x0} 0 Q0 ${2 * sag} ${x1} 0`;
    body = `<path d="${d}" fill="none" stroke="#8a5a2b" stroke-width="${Math.max(6, w * 0.025)}" stroke-linecap="round"/>` +
      `<path d="${d}" fill="none" stroke="#c9965a" stroke-width="${Math.max(2, w * 0.01)}" stroke-dasharray="${Math.max(6, w * 0.02)} ${Math.max(6, w * 0.02)}" stroke-linecap="round"/>`;
  }
  const fs = Math.max(28, w * 0.07), lab = p.label ? tx(p.label, 0, Math.min(0, sag) - fs, fit(p.label, w * 0.8, fs), INK, 800) : "";
  return `<g transform="rotate(${ang})">${body}${lab}</g>`;
}

// A process world: nodes (buildings, banks, people, the world, boxes) joined by arrows along which coins, notes or
// goods keep moving (circular flow of income, credit creation, a policy passing through banks to people, money
// leaving and coming back). The engine passes _t (seconds since the item appeared), so the tokens travel in the video;
// without it (a still) they sit mid-way. Edges can be lit one by one through the item's steps (active).
const FLOW_NODE = (kind, s) => {
  if (BUILDING_KINDS[kind]) return `<g transform="translate(0,${s * 0.5})">${building({ kind, w: s })}</g>`;
  if (kind === "bank") return `<g transform="translate(0,${s * 0.45})">${bank({ w: s })}</g>`;
  if (kind === "centralBank") return `<g transform="translate(0,${s * 0.45})">${centralBank({ w: s * 1.1 })}</g>`;
  if (kind === "people") return `<g transform="translate(0,${s * 0.45})">${crowd({ w: s, n: 9, cols: 3 })}</g>`;
  if (kind === "globe") return `<circle r="${s * 0.42}" fill="#9fd0f0" stroke="#3a7bd5" stroke-width="${s * 0.03}"/>` +
    `<ellipse rx="${s * 0.18}" ry="${s * 0.42}" fill="none" stroke="#3a7bd5" stroke-width="${s * 0.02}"/><path d="M${-s * 0.42} 0 L${s * 0.42} 0 M${-s * 0.36} ${-s * 0.2} L${s * 0.36} ${-s * 0.2} M${-s * 0.36} ${s * 0.2} L${s * 0.36} ${s * 0.2}" stroke="#3a7bd5" stroke-width="${s * 0.02}"/>` +
    `<path d="M${-s * 0.2} ${-s * 0.1} q${s * 0.1} ${-s * 0.15} ${s * 0.22} ${-s * 0.05} q${s * 0.05} ${s * 0.15} ${-s * 0.1} ${s * 0.2} Z" fill="#7cc47a"/>`;
  return `<rect x="${-s * 0.45}" y="${-s * 0.32}" width="${s * 0.9}" height="${s * 0.64}" rx="${s * 0.1}" fill="#eef3fb" stroke="#5b7fb8" stroke-width="${s * 0.03}"/>`;
};
const FLOW_KINDS = new Set([...Object.keys(BUILDING_KINDS), "bank", "centralBank", "people", "globe"]);
const FLOW_BOXES = { has: (k) => !FLOW_KINDS.has(k) };
const FLOW_TOKEN = (kind, r) => kind === "note" ? `<rect x="${-r * 1.4}" y="${-r * 0.75}" width="${r * 2.8}" height="${r * 1.5}" rx="${r * 0.2}" fill="#6cbf7f" stroke="#2f7a45" stroke-width="${r * 0.18}"/>`
  : kind === "goods" ? `<rect x="${-r}" y="${-r}" width="${2 * r}" height="${2 * r}" rx="${r * 0.15}" fill="#c8a06a" stroke="#8a6d3b" stroke-width="${r * 0.18}"/><path d="M${-r} ${-r * 0.2} L${r} ${-r * 0.2}" stroke="#8a6d3b" stroke-width="${r * 0.15}"/>`
  : kind === "dot" ? `<circle r="${r * 0.8}" fill="#e5484d"/>`
  : `<circle r="${r}" fill="#f2c14e" stroke="#c99a2e" stroke-width="${r * 0.2}"/>` + tx("₹", 0, 0, r * 1.2, "#8a6a1c", 800);

function flow(p) {
  const w = p.w || 1200, nodes = parts(p.nodes).filter(Boolean).slice(0, 8).map((t) => { const [l, k] = t.split(":"); return { label: (l || "").trim(), kind: (k || "box").trim() }; });
  if (!nodes.length) nodes.push({ label: "", kind: "house" }, { label: "", kind: "warehouse" });
  const n = nodes.length, layout = ["ring", "row", "hub"].includes(p.layout) ? p.layout : "ring";
  nodes.forEach((nd, i) => {
    if (layout === "row") { nd.x = n === 1 ? 0 : -w * 0.42 + (i * w * 0.84) / (n - 1); nd.y = 0; }
    else if (layout === "hub" && i === 0) { nd.x = 0; nd.y = 0; }
    else { const m = layout === "hub" ? n - 1 : n, k = layout === "hub" ? i - 1 : i, a = -Math.PI / 2 + (2 * Math.PI * k) / Math.max(1, m) + (m === 2 ? Math.PI / 2 : 0);
      nd.x = Math.cos(a) * w * 0.4; nd.y = Math.sin(a) * w * (layout === "hub" ? 0.3 : 0.27); }
  });
  let near = Infinity;
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) near = Math.min(near, Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y));
  const s = Math.min(w * 0.13, Number.isFinite(near) ? near * 0.42 : w * 0.13);
  const active = idxSet(p.active), col = p.color || "#2459a6", speed = p.speed == null ? 0.35 : Math.max(0, Number(p.speed) || 0), t = Number(p._t);
  const bend = p.bend == null ? 0.25 : Math.max(-1, Math.min(1, Number(p.bend) || 0)), r = w * 0.012;
  let edges = "", tokens = "", labels = "";
  parts(p.edges).filter(Boolean).forEach((e, j) => {
    const m = e.match(/^\s*(\d+)\s*>\s*(\d+)\s*(?::(.*))?$/);
    if (!m) return;
    const A = nodes[+m[1] - 1], B = nodes[+m[2] - 1];
    if (!A || !B || A === B) return;
    const on = !active.size || active.has(j + 1), dx = B.x - A.x, dy = B.y - A.y, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
    const gap = s * 0.66, ax = A.x + ux * gap, ay = A.y + uy * gap, bx = B.x - ux * gap, by = B.y - uy * gap;
    const cx = (ax + bx) / 2 - uy * bend * L * 0.5, cy = (ay + by) / 2 + ux * bend * L * 0.5;
    const q = (u) => [(1 - u) * (1 - u) * ax + 2 * (1 - u) * u * cx + u * u * bx, (1 - u) * (1 - u) * ay + 2 * (1 - u) * u * cy + u * u * by];
    const [hx, hy] = q(0.94), ang = (Math.atan2(by - hy, bx - hx) * 180) / Math.PI, c = on ? col : "#b8c0cc";
    edges += `<path d="M${ax} ${ay} Q${cx} ${cy} ${bx} ${by}" fill="none" stroke="${c}" stroke-width="${w * (on ? 0.008 : 0.005)}" stroke-linecap="round"${on ? "" : ` stroke-dasharray="${w * 0.012} ${w * 0.01}"`}/>` +
      `<path d="M${-w * 0.022} ${-w * 0.014} L0 0 L${-w * 0.022} ${w * 0.014}" fill="none" stroke="${c}" stroke-width="${w * 0.008}" stroke-linecap="round" stroke-linejoin="round" transform="translate(${bx},${by}) rotate(${ang})"/>`;
    let lab = (m[3] || "").trim(), tok = p.token;
    const at = lab.lastIndexOf("@");
    if (at >= 0 && ["coin", "note", "goods", "dot"].includes(lab.slice(at + 1).trim())) { tok = lab.slice(at + 1).trim(); lab = lab.slice(0, at).trim(); }
    if (lab) {
      const fs = fit(lab, w * 0.2, w * 0.028), [mx, my] = q(0.5), off = fs * 1.25;
      const c1 = [mx - uy * off, my + ux * off], c2 = [mx + uy * off, my - ux * off];      // the label sits outside:
      const [lx, ly] = layout === "row" ? (c1[1] < c2[1] ? c1 : c2)                         // above a row, away from
        : Math.hypot(...c1) >= Math.hypot(...c2) ? c1 : c2, bw = lab.length * fs * 0.6 + fs * 0.8; // a ring's centre
      labels += `<rect x="${lx - bw / 2}" y="${ly - fs * 0.75}" width="${bw}" height="${fs * 1.5}" rx="${fs * 0.3}" fill="#ffffff" stroke="${c}" stroke-width="${Math.max(2, w * 0.002)}"/>` + tx(lab, lx, ly, fs, on ? INK : "#8a94a3", 800);
    }
    if (on) for (let k = 0; k < 3; k++) {
      const u = Number.isFinite(t) ? (((t * speed + k / 3) % 1) + 1) % 1 : 0.2 + k * 0.3, [px, py] = q(u);
      tokens += `<g transform="translate(${px.toFixed(1)},${py.toFixed(1)})">${FLOW_TOKEN(tok, r * 1.6)}</g>`;
    }
  });
  const nodeSvg = nodes.map((nd) => `<g transform="translate(${nd.x},${nd.y})">${FLOW_NODE(nd.kind, s)}</g>`).join("");
  const nodeLabels = nodes.map((nd) => {
    if (!nd.label) return "";
    const fs = fit(nd.label, s * 1.6, w * 0.03);
    return `<g transform="translate(${nd.x},${nd.y})">` + (FLOW_BOXES.has(nd.kind) ? tx(nd.label, 0, 0, fit(nd.label, s * 0.85, w * 0.032), INK, 800)
      : `<rect x="${-s * 0.85}" y="${s * 0.55}" width="${s * 1.7}" height="${fs * 1.45}" rx="${fs * 0.3}" fill="#ffffff" opacity="0.92"/>` + tx(nd.label, 0, s * 0.55 + fs * 0.72, fs, INK, 800)) + `</g>`;
  }).join("");
  return edges + nodeSvg + tokens + labels + nodeLabels;                 // words stay on top of moving tokens
}

// ---------------------------------------------------------------- economy kit, batch 5b (4 Nov 2026)
// From the batch-5 cards (E58–E69): a zone scale whose bands run from good to bad with a pointer (types of inflation,
// safe and risky ranges), a fork (one lever, two directions, each with its condition and result) and gap bars (what
// goes out against what comes in, the hatched gap named: fiscal deficit, trade deficit, a savings gap).
const RAMP = ["#2fa35b", "#8cc152", "#f2c14e", "#f08a3c", "#e5484d", "#a3273a"];
const rampAt = (i, n) => RAMP[Math.round((n <= 1 ? 0 : i / (n - 1)) * (RAMP.length - 1))];

function bands(p) {
  const zones = parts(p.zones).filter(Boolean).slice(0, 8).map((z) => { const [l, r] = z.split(":"); return { label: (l || "").trim(), range: (r || "").trim() }; });
  if (!zones.length) zones.push({ label: "", range: "" }, { label: "", range: "" }, { label: "", range: "" });
  const w = p.w || 760, h = w * 0.13, n = zones.length, zw = w / n, glow = idxSet(p.glow), unit = p.unit ?? "";
  const nums = (z) => { const m = z.range.match(/^(-?[\d.]+)?\s*(?:-|–|to)?\s*(-?[\d.]+)?\s*(\+)?$/); return m ? [m[1] != null ? +m[1] : null, m[2] != null ? +m[2] : null, !!m[3]] : [null, null, false]; };
  let out = "";
  zones.forEach((z, i) => {
    const x = -w / 2 + i * zw, c = p.reverse ? rampAt(n - 1 - i, n) : rampAt(i, n);
    out += `<rect x="${x}" y="${-h / 2}" width="${zw}" height="${h}" fill="${c}" stroke="#ffffff" stroke-width="${w * 0.004}"/>` +
      (z.label ? tx(z.label, x + zw / 2, 0, fit(z.label, zw * 0.92, h * 0.42), "#ffffff", 800) : "") +
      (z.range ? (() => { const r = !unit || /[a-z%]\+?$/i.test(z.range) ? z.range : z.range.endsWith("+") ? z.range.slice(0, -1) + unit + "+" : z.range + unit;
        return tx(r, x + zw / 2, h * 0.5 + h * 0.36, fit(r, zw * 0.9, h * 0.34), INK, 700); })() : "") +
      (glow.has(i + 1) ? `<rect x="${x + 3}" y="${-h / 2 - 6}" width="${zw - 6}" height="${h + 12}" fill="none" stroke="#2b2b33" stroke-width="${Math.max(4, w * 0.008)}" rx="${w * 0.008}"/>` : "");
  });
  if (p.value != null && p.value !== "") {
    const v = Number(p.value); let at = null;
    zones.forEach((z, i) => { const [a, b, plus] = nums(z); if (at != null) return;
      if (a != null && b != null && v >= a && v <= b) at = -w / 2 + (i + (b > a ? (v - a) / (b - a) : 0.5)) * zw;
      else if (a != null && (plus || b == null) && v >= a && i === n - 1) at = -w / 2 + (i + 0.5) * zw; });
    if (at == null) at = v < (nums(zones[0])[0] ?? 0) ? -w / 2 : w / 2;
    const t = p.text ? String(p.text) : `${v}${unit}`;
    out += `<path d="M${at} ${-h / 2 - 4} l${-h * 0.22} ${-h * 0.34} l${h * 0.44} 0 Z" fill="${INK}"/>` + tx(t, at, -h / 2 - h * 0.62, fit(t, w * 0.3, h * 0.42), INK, 800);
  }
  return out + (p.title ? tx(p.title, 0, -h / 2 - h * (p.value != null && p.value !== "" ? 1.25 : 0.6), fit(p.title, w * 0.9, h * 0.45), INK, 800) : "");
}

function fork(p) {
  const w = p.w || 640, h = w * 0.62, c = p.color || "#2459a6", glow = String(p.glow || ""), sx = -w * 0.08;
  const branch = (dir, lab, note, res) => {
    const y = dir * h * 0.36, on = !glow || glow === (dir < 0 ? "up" : "down"), col = on ? c : "#b8c0cc", ex = w * 0.3;
    return `<path d="M${sx} 0 C${sx + w * 0.12} 0 ${sx + w * 0.1} ${y} ${ex - w * 0.02} ${y}" fill="none" stroke="${col}" stroke-width="${w * 0.016}" stroke-linecap="round"/>` +
      `<path d="M${ex - w * 0.05} ${y - w * 0.03} L${ex} ${y} L${ex - w * 0.05} ${y + w * 0.03}" fill="none" stroke="${col}" stroke-width="${w * 0.016}" stroke-linecap="round" stroke-linejoin="round"/>` +
      (lab ? `<rect x="${sx + w * 0.05}" y="${y * 0.62 - h * 0.075}" width="${w * 0.2}" height="${h * 0.15}" rx="${h * 0.04}" fill="#ffffff" stroke="${col}" stroke-width="${w * 0.004}"/>` +
        tx(lab, sx + w * 0.15, y * 0.62, fit(lab, w * 0.18, h * 0.09), on ? INK : "#8a94a3", 800) : "") +
      (note ? tx(note, sx + w * 0.2, y + (dir < 0 ? -1 : 1) * h * 0.13, fit(note, w * 0.44, h * 0.085), on ? "#4a5568" : "#9aa5b1", 700) : "") +
      (res ? `<rect x="${ex + w * 0.01}" y="${y - h * 0.09}" width="${w * 0.19}" height="${h * 0.18}" rx="${h * 0.04}" fill="${on ? shade(c, 1.9) : "#eef0f3"}" stroke="${col}" stroke-width="${w * 0.005}"/>` +
        tx(res, ex + w * 0.105, y, fit(res, w * 0.17, h * 0.085), on ? INK : "#8a94a3", 800) : "");
  };
  return `<path d="M${-w * 0.48} 0 L${sx} 0" stroke="${c}" stroke-width="${w * 0.016}" stroke-linecap="round"/>` +
    (p.from ? `<rect x="${-w * 0.5}" y="${-h * 0.1}" width="${w * 0.3}" height="${h * 0.2}" rx="${h * 0.05}" fill="${c}"/>` + tx(p.from, -w * 0.35, 0, fit(p.from, w * 0.27, h * 0.1), "#ffffff", 800) : "") +
    `<circle cx="${sx}" cy="0" r="${w * 0.018}" fill="${c}"/>` + branch(-1, p.up, p.upNote, p.upResult) + branch(1, p.down, p.downNote, p.downResult);
}

function gapBars(p) {
  const w = p.w || 520, h = w * 0.9, [al, av] = String(p.a ?? "").split(":"), [bl, bv] = String(p.b ?? "").split(":");
  const A = Math.max(0, Number(av) || 0), B = Math.max(0, Number(bv) || 0), top = Math.max(A, B) || 1, u = p.unit ?? "";
  const bw = w * 0.3, ha = (A / top) * h * 0.78, hb = (B / top) * h * 0.78, xa = -w * 0.36, xb = w * 0.06, ca = p.colorA || "#e07b24", cb = p.colorB || "#2459a6";
  const gap = Math.abs(A - B), low = A < B ? "a" : "b", gx = low === "a" ? xa : xb, gy0 = -Math.max(ha, hb), gy1 = -Math.min(ha, hb);
  let hatch = "";
  for (let c = gy0 + w * 0.035; gap && c < gy1 + bw * 0.5; c += w * 0.035) {         // parallel lines clipped to the gap
    let x0 = gx, y0 = c, x1 = gx + bw, y1 = c - bw * 0.5;
    if (y0 > gy1) { x0 = gx + (c - gy1) / 0.5; y0 = gy1; }
    if (y1 < gy0) { x1 = gx + (c - gy0) / 0.5; y1 = gy0; }
    if (x1 > x0) hatch += `<path d="M${x0} ${y0} L${x1} ${y1}" stroke="#e5484d" stroke-width="${w * 0.006}" opacity="0.6"/>`;
  }
  const bar = (x, hh, c, l, v) => `<rect x="${x}" y="${-hh}" width="${bw}" height="${hh}" fill="${c}" rx="${w * 0.01}"/>` +
    (l ? tx(l, x + bw / 2, w * 0.06, fit(l, bw * 1.2, w * 0.06), INK, 800) : "") + (v !== undefined && v !== "" ? tx(`${v}${u}`, x + bw / 2, -hh + w * 0.05, fit(`${v}${u}`, bw * 0.9, w * 0.055), "#ffffff", 800) : "");
  const gl = p.gap ? `${p.gap}${p.showGap === false ? "" : ` ${+(gap.toFixed(2))}${u}`}` : (p.showGap === false ? "" : `${+(gap.toFixed(2))}${u}`);
  return `<path d="M${-w * 0.48} 0 L${w * 0.48} 0" stroke="#9aa5b1" stroke-width="${w * 0.006}"/>` + bar(xa, ha, ca, al, av) + bar(xb, hb, cb, bl, bv) +
    (gap ? `<rect x="${gx}" y="${gy0}" width="${bw}" height="${gy1 - gy0}" fill="#ffffff" stroke="#e5484d" stroke-width="${w * 0.008}" stroke-dasharray="${w * 0.02} ${w * 0.012}"/>` + hatch +
      (gl ? `<rect x="${gx + bw + w * 0.02}" y="${(gy0 + gy1) / 2 - w * 0.045}" width="${w * 0.36}" height="${w * 0.09}" rx="${w * 0.02}" fill="#e5484d"/>` +
        tx(gl, gx + bw + w * 0.2, (gy0 + gy1) / 2, fit(gl, w * 0.34, w * 0.055), "#ffffff", 800) : "") : "");
}

// ---------------------------------------------------------------- diagrams of the 57-video needs list (4 Nov 2026)
// The economy videos carry most meaning by diagram (39% of segments): a timeline (62 segment-uses), a table (55) and a
// graph (35) led the needs list, and the scene-plan engine had none. Each is one parametric saancha whose parts can be
// revealed through steps (upto) and highlighted (at, glow); a graph's curves draw themselves (drawIn seconds).
export const DIAG = ["#2459a6", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#2a9d8f"];
export const isNum = (v) => v !== "" && v != null && Number.isFinite(Number(v));

function timeline(p) {
  const w = p.w || 1500, h = w * 0.3, ev = parts(p.events).filter(Boolean).slice(0, 12).map((e) => { const i = e.indexOf(":");
    return i < 0 ? { year: e.trim(), label: "" } : { year: e.slice(0, i).trim(), label: e.slice(i + 1).trim() }; });
  const n = ev.length, upto = p.upto ? Math.max(0, Math.round(p.upto)) : n, at = Math.round(p.at || 0), x0 = -w * 0.46, x1 = w * 0.44;
  const nums = ev.every((e) => isNum(e.year)) && n > 1 && !p.even, lo = nums ? Math.min(...ev.map((e) => +e.year)) : 0, hi = nums ? Math.max(...ev.map((e) => +e.year)) : 1;
  const X = (y, i) => (nums ? x0 + ((+y - lo) / ((hi - lo) || 1)) * (x1 - x0) : n === 1 ? (x0 + x1) / 2 : x0 + (i * (x1 - x0)) / (n - 1));
  let out = "";
  parts(p.zones).filter(Boolean).slice(0, 6).forEach((z, k) => {
    const m = z.match(/^\s*(-?[\d.]+)\s*-\s*(-?[\d.]+)\s*(?::(.*))?$/);
    if (!m || !nums) return;
    const a = Math.max(x0, X(+m[1])), b = Math.min(x1 + w * 0.03, X(+m[2])), c = DIAG[k % DIAG.length];
    if (b <= a) return;
    out += `<rect x="${a}" y="${h * 0.2}" width="${b - a}" height="${h * 0.12}" rx="${h * 0.03}" fill="${c}" opacity="0.22"/>` +
      `<rect x="${a}" y="${h * 0.2}" width="${b - a}" height="${h * 0.025}" fill="${c}"/>` + (m[3] ? tx(m[3].trim(), (a + b) / 2, h * 0.27, fit(m[3].trim(), b - a, h * 0.075), shade(c, 0.7), 800) : "");
  });
  out += `<path d="M${x0 - w * 0.02} 0 L${x1 + w * 0.04} 0" stroke="${INK}" stroke-width="${w * 0.004}"/><path d="M${x1 + w * 0.025} ${-h * 0.035} L${x1 + w * 0.045} 0 L${x1 + w * 0.025} ${h * 0.035}" fill="none" stroke="${INK}" stroke-width="${w * 0.004}"/>`;
  const slot = n > 1 ? Math.min(w * 0.2, ((x1 - x0) / (n - 1)) * 1.8) : w * 0.25;
  ev.forEach((e, i) => {
    if (i >= upto) return;
    const x = X(e.year, i), hot = at === i + 1, c = hot ? "#e5484d" : "#2459a6", tier = i % 2 ? -h * 0.5 : -h * 0.24;
    out += `<circle cx="${x}" cy="0" r="${hot ? w * 0.011 : w * 0.007}" fill="${c}" stroke="#ffffff" stroke-width="${w * 0.002}"/>` +
      tx(e.year, x, h * 0.1, fit(e.year, slot * 0.6, h * 0.075), hot ? c : INK, 800);
    if (e.label) {
      const fs = fit(e.label, slot * 0.95, h * 0.07), bw = Math.min(slot, e.label.length * fs * 0.6 + fs);
      out += `<path d="M${x} ${-w * 0.008} L${x} ${tier + fs * 0.75}" stroke="${c}" stroke-width="${w * 0.002}"/>` +
        `<rect x="${x - bw / 2}" y="${tier - fs * 0.75}" width="${bw}" height="${fs * 1.5}" rx="${fs * 0.3}" fill="${hot ? "#fdecec" : "#ffffff"}" stroke="${c}" stroke-width="${w * 0.002}"/>` +
        tx(e.label, x, tier, fs, INK, 800);
    }
  });
  return out + (p.title ? tx(p.title, 0, -h * 0.72, fit(p.title, w * 0.8, h * 0.09), INK, 800) : "");
}

function table(p) {
  const cols = parts(p.cols).filter((c, i, a) => a.length > 1 || c), rows = parts(p.rows).filter((r, i, a) => a.length > 1 || r);
  const cells = String(p.cells ?? "").split("|").map((r) => r.split(";").map((c) => c.trim()));
  const nc = Math.max(1, cols.length, ...cells.map((r) => r.length)), nr = Math.max(1, rows.length, cells.length);
  const w = p.w || 900, rowW = rows.some(Boolean) ? w * 0.3 : 0, cw = (w - rowW) / nc, rh = Math.min(w * 0.085, (w * 0.62) / (nr + 1));
  const H = (nr + 1) * rh, x0 = -w / 2, y0 = -H / 2, upto = p.upto ? Math.max(0, Math.round(p.upto)) : nr;
  const gr = idxSet(p.glowRow), gc = idxSet(p.glowCol), fs = rh * 0.42;
  // fill "c:n;…": column c shows only its first n cells, so a step fills a column cell by cell on the voice
  const fillTo = new Map(String(p.fill ?? "").split(";").map((t) => t.split(":").map((v) => Math.round(Number(v))))
    .filter(([c, n]) => Number.isFinite(c) && Number.isFinite(n)));
  let out = `<rect x="${x0}" y="${y0}" width="${w}" height="${rh}" fill="#2d3748" rx="${rh * 0.15}"/>`;
  cols.forEach((c, j) => { if (c) out += tx(c, x0 + rowW + (j + 0.5) * cw, y0 + rh / 2, fit(c, cw * 0.9, fs), "#ffffff", 800); });
  if (p.corner) out += tx(p.corner, x0 + rowW / 2, y0 + rh / 2, fit(p.corner, rowW * 0.9, fs), "#ffffff", 800);
  for (let i = 0; i < nr; i++) {
    const y = y0 + (i + 1) * rh, shown = i < upto;
    out += `<rect x="${x0}" y="${y}" width="${w}" height="${rh}" fill="${gr.has(i + 1) ? "#fff3c4" : i % 2 ? "#f1f4f8" : "#ffffff"}" stroke="#d5dbe1" stroke-width="${Math.max(1, w * 0.0015)}"/>`;
    if (!shown) continue;
    if (rows[i]) out += tx(rows[i], x0 + rowW / 2, y + rh / 2, fit(rows[i], rowW * 0.92, fs), INK, 800);
    for (let j = 0; j < nc; j++) {
      const v = fillTo.has(j + 1) && i >= fillTo.get(j + 1) ? "" : (cells[i] || [])[j] || "", cx = x0 + rowW + (j + 0.5) * cw, cy = y + rh / 2;
      if (/^(✓|✔|y|yes|tick)$/i.test(v)) out += `<g transform="translate(${cx},${cy})">${markSvg("tick", rh * 0.6, "#2fa35b", 1)}</g>`;
      else if (/^(✗|✘|x|no|cross)$/i.test(v)) out += `<g transform="translate(${cx},${cy})">${markSvg("cross", rh * 0.55, "#e5484d", 1)}</g>`;
      else if (v) out += tx(v, cx, cy, fit(v, cw * 0.9, fs), INK, 700);
    }
  }
  gc.forEach((j) => { if (j >= 1 && j <= nc) out += `<rect x="${x0 + rowW + (j - 1) * cw + 2}" y="${y0 + 2}" width="${cw - 4}" height="${H - 4}" fill="none" stroke="#f2c14e" stroke-width="${Math.max(4, w * 0.006)}" rx="${rh * 0.15}"/>`; });
  return out + `<rect x="${x0}" y="${y0}" width="${w}" height="${H}" fill="none" stroke="#9aa5b1" stroke-width="${Math.max(2, w * 0.003)}" rx="${rh * 0.15}"/>` +
    (rowW ? `<path d="M${x0 + rowW} ${y0} L${x0 + rowW} ${y0 + H}" stroke="#9aa5b1" stroke-width="${Math.max(2, w * 0.003)}"/>` : "");
}

export function smoothPath(pts) {
  if (pts.length < 3) return pts.map((q, i) => `${i ? "L" : "M"}${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(" ");
  let d = `M${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[i], c = pts[i + 1], e = pts[Math.min(pts.length - 1, i + 2)];
    d += ` C${(b[0] + (c[0] - a[0]) / 6).toFixed(1)} ${(b[1] + (c[1] - a[1]) / 6).toFixed(1)} ${(c[0] - (e[0] - b[0]) / 6).toFixed(1)} ${(c[1] - (e[1] - b[1]) / 6).toFixed(1)} ${c[0].toFixed(1)} ${c[1].toFixed(1)}`;
  }
  return d;
}

function graph(p) {
  // The economics graph (Sloman: most of its 343 figures). Everything is in data units and can change on a cue word
  // through the item's steps: show reveals lines one by one, grow draws the newly shown lines and areas over drawIn
  // seconds after the step (_s), a dot glides from where it was (x,y<x0,y0), areas shade surplus, revenue or loss,
  // hlines/vlines are price floors and ceilings, arrows are shifts, gaps are shortages and surpluses, xTicks/yTicks
  // name P1, Q1 on the axes.
  const w = p.w || 900, h = w * 0.62, L = -w / 2 + w * 0.09, R = w / 2 - w * 0.05, T = -h / 2 + h * 0.06, B = h / 2 - h * 0.13;
  const xmin = isNum(p.xmin) ? +p.xmin : 0, xmax = isNum(p.xmax) && +p.xmax > xmin ? +p.xmax : xmin + 10;
  const ymin = isNum(p.ymin) ? +p.ymin : 0, ymax = isNum(p.ymax) && +p.ymax > ymin ? +p.ymax : ymin + 10;
  const X = (v) => L + ((v - xmin) / (xmax - xmin)) * (R - L), Y = (v) => B - ((v - ymin) / (ymax - ymin)) * (B - T);
  const t = Number(p._t), sinceStep = p._s === null || p._s === undefined || p._s === "" ? t : Number(p._s);
  const drawIn = Math.max(0, Number(p.drawIn) || 0);
  const grow = new Set(parts(p.grow).map((g) => g.trim()).filter(Boolean));
  const progAll = drawIn && Number.isFinite(t) ? Math.min(1, t / drawIn) : 1;
  const progStep = drawIn && Number.isFinite(sinceStep) ? Math.min(1, Math.max(0, sinceStep) / drawIn) : 1;
  const progOf = (key) => (grow.size ? (grow.has(key) ? progStep : 1) : progAll);
  const dashed = idxSet(p.dashed), bold = idxSet(p.bold), fs = h * 0.055;
  const shown = p.show === undefined || p.show === null || String(p.show).trim() === "" ? null : idxSet(p.show);
  const colors = {};
  parts(p.colors).forEach((c) => { const i = c.indexOf(":"); if (i > 0) colors[c.slice(0, i).trim()] = c.slice(i + 1).trim(); });
  const xy = (q) => q.split(",").map(Number);
  const ok = (q) => q.length === 2 && q.every(Number.isFinite);
  const lab = (s) => { const i = s.indexOf(":"); return i >= 0 ? [s.slice(0, i).trim(), s.slice(i + 1).trim()] : [s.trim(), ""]; };
  let out = "";
  // shaded areas first, under everything: "label:x,y x,y x,y@#color"
  parts(p.areas).filter(Boolean).slice(0, 6).forEach((ar, k) => {
    const at = ar.lastIndexOf("@"), col = at > 0 && ar.slice(at + 1).trim().startsWith("#") ? ar.slice(at + 1).trim() : AREA[k % AREA.length];
    const body = at > 0 && ar.slice(at + 1).trim().startsWith("#") ? ar.slice(0, at) : ar;
    const i = body.indexOf(":"), name = i >= 0 ? body.slice(0, i).trim() : "", pts = (i >= 0 ? body.slice(i + 1) : body).trim().split(/\s+/)
      .map(xy).filter(ok).map(([a, b]) => [X(a), Y(b)]);
    if (pts.length < 3) return;
    const pr = progOf(`a${k + 1}`);
    const cx = pts.reduce((s2, q) => s2 + q[0], 0) / pts.length, cy = pts.reduce((s2, q) => s2 + q[1], 0) / pts.length;
    out += `<path d="${pts.map((q, j) => `${j ? "L" : "M"}${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(" ")} Z" fill="${col}" fill-opacity="${(0.42 * pr).toFixed(3)}" stroke="${col}" stroke-width="${w * 0.002}" stroke-opacity="${pr.toFixed(3)}"/>`;
    if (name && pr >= 1) out += tx(name, cx, cy, fit(name, Math.max(w * 0.08, (Math.max(...pts.map((q) => q[0])) - Math.min(...pts.map((q) => q[0]))) * 0.9), fs * 0.9), INK, 800);
  });
  out += `<path d="M${L} ${T - h * 0.03} L${L} ${B} L${R + w * 0.02} ${B}" fill="none" stroke="${INK}" stroke-width="${w * 0.004}"/>` +
    `<path d="M${L - w * 0.012} ${T} L${L} ${T - h * 0.035} L${L + w * 0.012} ${T}" fill="none" stroke="${INK}" stroke-width="${w * 0.004}"/>` +
    `<path d="M${R + w * 0.005} ${B - h * 0.02} L${R + w * 0.025} ${B} L${R + w * 0.005} ${B + h * 0.02}" fill="none" stroke="${INK}" stroke-width="${w * 0.004}"/>`;
  if (ymin < 0 && ymax > 0) out += `<path d="M${L} ${Y(0)} L${R} ${Y(0)}" stroke="#9aa5b1" stroke-width="${w * 0.002}" stroke-dasharray="${w * 0.01} ${w * 0.008}"/>`;
  const xt = parts(p.xTicks).some(Boolean), yt = parts(p.yTicks).some(Boolean);      // named axis points push the axis names out
  if (p.xLabel) out += tx(p.xLabel, (L + R) / 2, B + h * (xt ? 0.115 : 0.08), fit(p.xLabel, w * 0.6, fs), INK, 800);
  if (p.yLabel) out += `<g transform="translate(${L - w * (yt ? 0.1 : 0.05)},${(T + B) / 2}) rotate(-90)">${tx(p.yLabel, 0, 0, fit(p.yLabel, h * 0.7, fs), INK, 800)}</g>`;
  if (p.ticks) out += tx(String(xmin), L, B + h * 0.035, fs * 0.7, "#4a5568", 700) + tx(String(xmax), R, B + h * 0.035, fs * 0.7, "#4a5568", 700) +
    tx(String(ymax), L - w * 0.02, T, fs * 0.7, "#4a5568", 700) + (ymin !== 0 ? tx(String(ymin), L - w * 0.02, B, fs * 0.7, "#4a5568", 700) : "");
  // named points on the axes: "2:Q1;5:Q2" and "4:P1"
  parts(p.xTicks).filter(Boolean).slice(0, 8).forEach((tk) => { const [v, n] = lab(tk); if (!isNum(v)) return;
    out += `<path d="M${X(+v)} ${B} L${X(+v)} ${B + h * 0.02}" stroke="${INK}" stroke-width="${w * 0.003}"/>` + (n ? tx(n, X(+v), B + h * 0.045, fit(n, w * 0.1, fs * 0.8), INK, 800) : ""); });
  parts(p.yTicks).filter(Boolean).slice(0, 8).forEach((tk) => { const [v, n] = lab(tk); if (!isNum(v)) return;
    out += `<path d="M${L - w * 0.012} ${Y(+v)} L${L} ${Y(+v)}" stroke="${INK}" stroke-width="${w * 0.003}"/>` + (n ? tx(n, L - w * 0.04, Y(+v), fit(n, w * 0.05, fs * 0.8), INK, 800) : ""); });
  // price ceilings and floors, and fixed quantities: "6:न्यूनतम मूल्य" (y) and "4:quota" (x)
  parts(p.hlines).filter(Boolean).slice(0, 4).forEach((hl) => { const [v, n] = lab(hl); if (!isNum(v)) return;
    out += `<path d="M${L} ${Y(+v)} L${R} ${Y(+v)}" stroke="#c0392b" stroke-width="${w * 0.004}" stroke-dasharray="${w * 0.014} ${w * 0.008}"/>` +
      (n ? tx(n, R - w * 0.12, Y(+v) - h * 0.035, fit(n, w * 0.22, fs * 0.85), "#c0392b", 800) : ""); });
  parts(p.vlines).filter(Boolean).slice(0, 4).forEach((vl) => { const [v, n] = lab(vl); if (!isNum(v)) return;
    out += `<path d="M${X(+v)} ${T} L${X(+v)} ${B}" stroke="#7b61ff" stroke-width="${w * 0.004}" stroke-dasharray="${w * 0.014} ${w * 0.008}"/>` +
      (n ? tx(n, X(+v), T + h * 0.02, fit(n, w * 0.2, fs * 0.85), "#7b61ff", 800) : ""); });
  // a curve that moves on the cue word: "2:-2,0" slides line 2 from 2 units left into place; morph "2:1,9 9,1" reshapes
  // line 2 from those points into its own (a pivot, a new slope); both over glide seconds after the step (_s)
  const gl = Math.max(0.1, Number(p.glide) || 1.2);
  const moveE = Number.isFinite(sinceStep) ? easeIO(Math.min(1, Math.max(0, sinceStep) / gl)) : 1;
  const slide = {}, morph = {};
  parts(p.slide).forEach((sl) => { const [k, v] = lab(sl); const d = xy(v || ""); if (k && ok(d)) slide[k] = d; });
  parts(p.morph).forEach((mo) => { const [k, v] = lab(mo); const q = (v || "").trim().split(/\s+/).map(xy).filter(ok); if (k && q.length >= 2) morph[k] = q; });
  const resample = (q, n) => Array.from({ length: n }, (_, j) => { const f = (j / (n - 1)) * (q.length - 1), a = Math.floor(f), b2 = Math.min(q.length - 1, a + 1), u = f - a;
    return [q[a][0] + (q[b2][0] - q[a][0]) * u, q[a][1] + (q[b2][1] - q[a][1]) * u]; });
  const linePts = {};                          // data points of each drawn line (after slide and morph), for "along"
  parts(p.lines).filter(Boolean).slice(0, 6).forEach((ln, k) => {
    if (shown && !shown.has(k + 1)) return;
    const i = ln.indexOf(":"), name = i >= 0 ? ln.slice(0, i).trim() : "";
    let dpts = (i >= 0 ? ln.slice(i + 1) : ln).trim().split(/\s+/).map(xy).filter(ok);
    if (dpts.length < 2) return;
    const key = String(k + 1);
    if (morph[key] && moveE < 1) {
      const n = Math.max(dpts.length, morph[key].length, 12), A = resample(morph[key], n), Bq = resample(dpts, n);
      dpts = A.map((q, j) => [q[0] + (Bq[j][0] - q[0]) * moveE, q[1] + (Bq[j][1] - q[1]) * moveE]);
    }
    if (slide[key] && moveE < 1) dpts = dpts.map(([a, b2]) => [a + slide[key][0] * (1 - moveE), b2 + slide[key][1] * (1 - moveE)]);
    linePts[key] = dpts;
    const pts = dpts.map(([a, b2]) => [X(a), Y(b2)]);
    const prog = progOf(String(k + 1));
    const c = colors[String(k + 1)] || DIAG[k % DIAG.length], d = p.smooth === false ? pts.map((q, j) => `${j ? "L" : "M"}${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(" ") : smoothPath(pts);
    const sw = w * (bold.has(k + 1) ? 0.012 : 0.007);
    out += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="${dashed.has(k + 1) ? "0.02 0.015" : `${prog} 1`}"${dashed.has(k + 1) && prog < 1 ? ` opacity="${prog}"` : ""}/>`;
    if (name && prog >= 1) { const [ex, ey] = pts[pts.length - 1]; out += tx(name, Math.min(R, ex + w * 0.03), ey - h * 0.04, fit(name, w * 0.16, fs), c, 800); }
  });
  // shifts: "3,5>6,5:माँग बढ़ी"
  parts(p.arrows).filter(Boolean).slice(0, 4).forEach((ar) => { const [body, n] = lab(ar), [a, b2] = body.split(">");
    if (!a || !b2) return; const p1 = xy(a), p2 = xy(b2); if (!ok(p1) || !ok(p2)) return;
    const x1 = X(p1[0]), y1 = Y(p1[1]), x2 = X(p2[0]), y2 = Y(p2[1]), ang = Math.atan2(y2 - y1, x2 - x1), hl = w * 0.028;
    out += `<path d="M${x1} ${y1} L${x2} ${y2}" stroke="#e76f51" stroke-width="${w * 0.008}" stroke-linecap="round"/>` +
      `<path d="M${x2 - hl * Math.cos(ang - 0.45)} ${y2 - hl * Math.sin(ang - 0.45)} L${x2} ${y2} L${x2 - hl * Math.cos(ang + 0.45)} ${y2 - hl * Math.sin(ang + 0.45)}" fill="none" stroke="#e76f51" stroke-width="${w * 0.008}" stroke-linecap="round" stroke-linejoin="round"/>` +
      (n ? tx(n, (x1 + x2) / 2, Math.min(y1, y2) - h * 0.045, fit(n, w * 0.3, fs * 0.85), "#e76f51", 800) : ""); });
  // shortages and surpluses: "3,7@4:कमी (shortage)"
  parts(p.gaps).filter(Boolean).slice(0, 3).forEach((gp) => { const [body, n] = lab(gp), [xs, yv] = body.split("@"); if (!xs || !isNum(yv)) return;
    const [a, b2] = xy(xs); if (![a, b2].every(Number.isFinite)) return;
    const x1 = X(Math.min(a, b2)), x2 = X(Math.max(a, b2)), y = Y(+yv), tk = h * 0.025;
    out += `<path d="M${x1} ${y - tk} L${x1} ${y + tk} M${x1} ${y} L${x2} ${y} M${x2} ${y - tk} L${x2} ${y + tk}" stroke="#d62828" stroke-width="${w * 0.006}" stroke-linecap="round"/>` +
      (n ? tx(n, (x1 + x2) / 2, y + h * 0.055, fit(n, Math.max(w * 0.12, x2 - x1), fs * 0.85), "#d62828", 800) : ""); });
  // plain dashed segments: a chord, a tangent, a reading line "x1,y1>x2,y2:label"
  parts(p.segs).filter(Boolean).slice(0, 6).forEach((sg) => { const [body, n] = lab(sg), [a, b2] = body.split(">");
    if (!a || !b2) return; const p1 = xy(a), p2 = xy(b2); if (!ok(p1) || !ok(p2)) return;
    out += `<path d="M${X(p1[0])} ${Y(p1[1])} L${X(p2[0])} ${Y(p2[1])}" stroke="#5c677d" stroke-width="${w * 0.004}" stroke-dasharray="${w * 0.012} ${w * 0.008}"/>` +
      (n ? tx(n, (X(p1[0]) + X(p2[0])) / 2, (Y(p1[1]) + Y(p2[1])) / 2 - h * 0.04, fit(n, w * 0.22, fs * 0.8), "#5c677d", 800) : ""); });
  // a lettered adjustment path "x,y:a;x,y:b;x,y:c": points joined by arrows, pathUpto reveals the first n points
  const pathPts = parts(p.path).filter(Boolean).slice(0, 8).map((pp) => { const [body, n] = lab(pp); const q = xy(body); return ok(q) ? [X(q[0]), Y(q[1]), n] : null; }).filter(Boolean);
  const upto = isNum(p.pathUpto) ? Math.max(0, Math.min(pathPts.length, Math.round(+p.pathUpto))) : pathPts.length;
  pathPts.slice(0, upto).forEach(([x, y, n], j) => {
    if (j > 0) { const [x0, y0] = pathPts[j - 1], ang = Math.atan2(y - y0, x - x0), hl = w * 0.022, ex = x - Math.cos(ang) * w * 0.012, ey = y - Math.sin(ang) * w * 0.012;
      out += `<path d="M${x0} ${y0} L${ex} ${ey}" stroke="#7b2cbf" stroke-width="${w * 0.006}" stroke-linecap="round"/>` +
        `<path d="M${ex - hl * Math.cos(ang - 0.45)} ${ey - hl * Math.sin(ang - 0.45)} L${ex} ${ey} L${ex - hl * Math.cos(ang + 0.45)} ${ey - hl * Math.sin(ang + 0.45)}" fill="none" stroke="#7b2cbf" stroke-width="${w * 0.006}" stroke-linecap="round" stroke-linejoin="round"/>`; }
    out += `<circle cx="${x}" cy="${y}" r="${w * 0.011}" fill="#7b2cbf"/>` + (n ? tx(n, x - w * 0.03, y - h * 0.045, fit(n, w * 0.08, fs), "#7b2cbf", 800) : "");
  });
  // a point on a curve "2@0.4:E" (a fraction along line 2's points), gliding along the curve from "2@0.1" after the step;
  // {x} and {y} in its label read the point's values live
  parts(p.along).filter(Boolean).slice(0, 3).forEach((al) => {
    const [body, n] = lab(al), [to, from] = body.split("<"), [k, f] = (to || "").split("@");
    const q = linePts[(k || "").trim()]; if (!q || !isNum(f)) return;
    const f0 = from && isNum(from.split("@")[1]) ? +from.split("@")[1] : +f, ff = f0 + (+f - f0) * moveE;
    const at = (fr) => { const g = Math.max(0, Math.min(1, fr)) * (q.length - 1), a = Math.floor(g), b2 = Math.min(q.length - 1, a + 1), u = g - a;
      return [q[a][0] + (q[b2][0] - q[a][0]) * u, q[a][1] + (q[b2][1] - q[a][1]) * u]; };
    const [dx, dy] = at(ff), x = X(dx), y = Y(dy);
    const nm = (n || "").replace("{x}", _num(dx)).replace("{y}", _num(dy));
    out += (p.drop === false ? "" : `<path d="M${x} ${y} L${x} ${B} M${x} ${y} L${L} ${y}" stroke="#4a5568" stroke-width="${w * 0.0025}" stroke-dasharray="${w * 0.008} ${w * 0.006}"/>`) +
      `<circle cx="${x}" cy="${y}" r="${w * 0.012}" fill="#e63946" stroke="#ffffff" stroke-width="${w * 0.003}"/>` + (nm ? tx(nm, x + w * 0.05, y - h * 0.055, fit(nm, w * 0.24, fs), "#e63946", 800) : "");
  });
  if (progAll >= 1 || grow.size) parts(p.dots).filter(Boolean).slice(0, 6).forEach((dt) => {
    const [body, n] = lab(dt), [to, from] = body.split("<"), q = xy(to);
    if (!ok(q)) return;
    let [a, b2] = q;
    if (from && ok(xy(from))) { const f = xy(from), g = Math.max(0.1, Number(p.glide) || 1.2), e = Number.isFinite(sinceStep) ? easeIO(Math.min(1, Math.max(0, sinceStep) / g)) : 1;
      a = f[0] + (a - f[0]) * e; b2 = f[1] + (b2 - f[1]) * e; }
    const x = X(a), y = Y(b2);
    out += (p.drop === false ? "" : `<path d="M${x} ${y} L${x} ${B} M${x} ${y} L${L} ${y}" stroke="#4a5568" stroke-width="${w * 0.0025}" stroke-dasharray="${w * 0.008} ${w * 0.006}"/>`) +
      `<circle cx="${x}" cy="${y}" r="${w * 0.009}" fill="${INK}" stroke="#ffffff" stroke-width="${w * 0.002}"/>` + (n ? tx(n, x + w * 0.04, y - h * 0.05, fit(n, w * 0.2, fs), INK, 800) : "");
  });
  return out + (p.title ? tx(p.title, 0, T - h * 0.07, fit(p.title, w * 0.8, fs * 1.2), INK, 800) : "");
}
const _num = (v) => (Math.abs(v - Math.round(v)) < 0.05 ? String(Math.round(v)) : v.toFixed(1));
export const easeIO = (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
const AREA = ["#f4a261", "#2a9d8f", "#e76f51", "#8ecae6", "#b5838d", "#90be6d"];

// A funnel (much goes in, a part comes out: reserve money into the money multiplier, many inputs into one result)
// and a road map (the lesson's agenda: items in order, the current one framed, the done ones ticked) from E63/E64/E59.
function funnel(p) {
  const w = p.w || 320, h = w * 1.1, c = p.color || "#5b7fb8", flip = p.flip === true;
  const top = -h, mid = -h * 0.38, wTop = w * 0.5, wNeck = w * 0.09;
  const body = `<path d="M${-wTop} ${top} L${wTop} ${top} L${wNeck} ${mid} L${wNeck} ${-h * 0.08} L${-wNeck} ${-h * 0.08} L${-wNeck} ${mid} Z" fill="${shade(c, 1.5)}" stroke="${c}" stroke-width="${w * 0.02}" stroke-linejoin="round"/>` +
    `<ellipse cx="0" cy="${top}" rx="${wTop}" ry="${h * 0.05}" fill="${shade(c, 1.25)}" stroke="${c}" stroke-width="${w * 0.02}"/>`;
  const drops = [0, 1, 2].map((k) => `<circle cx="${(k - 1) * w * 0.012}" cy="${-h * 0.04 + k * h * 0.02}" r="${w * 0.018}" fill="${p.dropColor || "#f2c14e"}"/>`).join("");
  const labs = (p.top ? tx(p.top, 0, top - h * 0.11, fit(p.top, w * 1.1, w * 0.1), INK, 800) : "") +
    (p.label ? tx(p.label, 0, (top + mid) / 2, fit(p.label, w * 0.75, w * 0.09), "#ffffff", 800) : "") +
    (p.bottom ? tx(p.bottom, 0, h * 0.06, fit(p.bottom, w * 1.1, w * 0.09), INK, 800) : "");
  return flip ? `<g transform="translate(0,${-h * 1.06}) scale(1,-1)">${body}${drops}</g>` + labs : body + drops + labs;
}

function roadmap(p) {
  const given = parts(p.items).filter(Boolean).slice(0, 10), items = given.length ? given : ["", "", ""];
  const w = p.w || 420, n = items.length, rh = Math.min(w * 0.2, 700 / n);
  const at = Math.round(p.at || 0), done = p.done == null || p.done === "" ? at - 1 : Math.round(p.done), c = p.color || "#2a9d8f";
  let out = p.title ? tx(p.title, 0, -n * rh / 2 - rh * 0.55, fit(p.title, w, rh * 0.5), INK, 800) : "";
  items.forEach((it, i) => {
    const y = -n * rh / 2 + i * rh, cur = i + 1 === at, ok = i + 1 <= done && !cur, fs = fit(it || " ", w * 0.66, rh * 0.36);
    const cx = -w / 2 + rh * 0.5, cy = y + rh / 2, r = rh * 0.26;
    out += `<rect x="${-w / 2}" y="${y + rh * 0.08}" width="${w}" height="${rh * 0.84}" rx="${rh * 0.18}" fill="${cur ? "#fff8e1" : "#ffffff"}" stroke="${cur ? c : "#d5dbe1"}" stroke-width="${cur ? w * 0.012 : w * 0.004}"/>` +
      `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${ok ? "#2fa35b" : cur ? c : "#d5dbe1"}"/>` +
      (ok ? `<path d="M${cx - r * 0.5} ${cy + r * 0.02} L${cx - r * 0.12} ${cy + r * 0.4} L${cx + r * 0.52} ${cy - r * 0.38}" fill="none" stroke="#ffffff" stroke-width="${r * 0.28}" stroke-linecap="round" stroke-linejoin="round"/>`
        : tx(String(i + 1), cx, cy, rh * 0.3, cur ? "#ffffff" : "#4a5568", 800)) +
      `<g transform="translate(${-w / 2 + rh * 0.95 + (w - rh * 1.05) / 2},0)">${tx(it, 0, y + rh / 2, fs, ok ? "#6b7280" : INK, cur ? 800 : 700)}</g>`;
  });
  return out;
}

// A plant that grows from a seed to a tree, coins or notes as its fruit (venture and seed funding, growth, compounding).
function plant(p) {
  const w = p.w || 240, g = clamp01(p.stage == null ? 0.6 : p.stage), h = w * (0.25 + g * 1.1), fruit = p.fruit || "coin";
  const pot = `<path d="M${-w * 0.2} ${-w * 0.22} L${w * 0.2} ${-w * 0.22} L${w * 0.15} 0 L${-w * 0.15} 0 Z" fill="#c0563f" stroke="#8a3b2a" stroke-width="${w * 0.015}"/>` +
    `<rect x="${-w * 0.23}" y="${-w * 0.27}" width="${w * 0.46}" height="${w * 0.07}" rx="${w * 0.02}" fill="#d9734f"/>`;
  if (g < 0.08) return pot + `<ellipse cx="0" cy="${-w * 0.28}" rx="${w * 0.05}" ry="${w * 0.035}" fill="#8a5a2b"/>` + (p.label ? tx(p.label, 0, w * 0.1, fit(p.label, w, w * 0.12), INK, 800) : "");
  const stem = `<path d="M0 ${-w * 0.27} C${w * 0.03} ${-w * 0.27 - h * 0.4} ${-w * 0.03} ${-w * 0.27 - h * 0.7} 0 ${-w * 0.27 - h}" fill="none" stroke="${g > 0.6 ? "#8a5a2b" : "#4f9a4a"}" stroke-width="${w * (0.02 + g * 0.05)}" stroke-linecap="round"/>`;
  const top = -w * 0.27 - h, leaves = g < 0.45
    ? [-1, 1].map((d) => `<ellipse cx="${d * w * 0.09}" cy="${top + w * 0.04}" rx="${w * 0.1}" ry="${w * 0.045}" fill="#7cc47a" transform="rotate(${d * -25} ${d * w * 0.09} ${top + w * 0.04})"/>`).join("")
    : `<circle cx="0" cy="${top}" r="${w * (0.18 + g * 0.22)}" fill="#8fbf5a"/><circle cx="${-w * 0.16 * g}" cy="${top + w * 0.08}" r="${w * (0.12 + g * 0.14)}" fill="#7cb24f"/><circle cx="${w * 0.17 * g}" cy="${top + w * 0.06}" r="${w * (0.12 + g * 0.15)}" fill="#9dca6b"/>`;
  const n = fruit === "none" || g < 0.45 ? 0 : Math.round(2 + g * 5), r = w * 0.045;
  const fr = [...Array(n).keys()].map((k) => { const a = (k / n) * Math.PI * 2 + 0.4, x = Math.cos(a) * w * 0.2 * g, y = top + Math.sin(a) * w * 0.17 * g;
    return fruit === "note" ? `<rect x="${x - r * 1.3}" y="${y - r * 0.7}" width="${r * 2.6}" height="${r * 1.4}" rx="${r * 0.2}" fill="#6cbf7f" stroke="#2f7a45" stroke-width="${r * 0.18}"/>`
      : `<circle cx="${x}" cy="${y}" r="${r}" fill="#f2c14e" stroke="#c99a2e" stroke-width="${r * 0.2}"/>`; }).join("");
  return stem + leaves + fr + pot + (p.label ? tx(p.label, 0, w * 0.1, fit(p.label, w, w * 0.12), INK, 800) : "");
}

// ---------------------------------------------------------------- registry
// anchor "bottom": the drawing stands on its origin; "center": centred on it.
export const DRAWS = {
  sack: { fn: sack, anchor: "bottom" },
  clothRoll: { fn: clothRoll, anchor: "center" },
  clothStack: { fn: clothStack, anchor: "bottom" },
  saltPacket: { fn: saltPacket, anchor: "bottom", lift: 0.65 },
  note: { fn: note, anchor: "center" },
  noteBundle: { fn: noteBundle, anchor: "center" },
  coin: { fn: coin, anchor: "center" },
  coinStack: { fn: coinStack, anchor: "bottom" },
  goldBar: { fn: goldBar, anchor: "bottom" },
  oilTin: { fn: oilTin, anchor: "bottom" },
  matka: { fn: matka, anchor: "bottom" },
  bowl: { fn: bowl, anchor: "bottom" },
  veg: { fn: veg, anchor: "center" },
  wheat: { fn: wheat, anchor: "center" },
  charpai: { fn: charpai, anchor: "bottom" },
  saw: { fn: saw, anchor: "center" },
  calendar: { fn: calendar, anchor: "center" },
  bugs: { fn: bugs, anchor: "center" },
  sweat: { fn: sweat, anchor: "center" },
  heap: { fn: heap, anchor: "bottom" },
  teaBrick: { fn: teaBrick, anchor: "bottom" },
  tobacco: { fn: tobacco, anchor: "center" },
  cowries: { fn: cowries, anchor: "center" },
  cheque: { fn: cheque, anchor: "center" },
  accountCard: { fn: accountCard, anchor: "center" },
  bank: { fn: bank, anchor: "bottom" },
  qrStand: { fn: qrStand, anchor: "bottom" },
  phone: { fn: phone, anchor: "center" },
  mark: { fn: (p) => markSvg(p.kind || "tick", p.w || 100, p.color, 1), anchor: "center" },
  institutionBadge: { fn: institutionBadge, anchor: "center" },
  paper: { fn: paper, anchor: "center" },
  disc: { fn: disc, anchor: "center" },
  vault: { fn: vault, anchor: "bottom" },
  crowd: { fn: crowd, anchor: "bottom" },
  centralBank: { fn: centralBank, anchor: "bottom" },
  committee: { fn: committee, anchor: "bottom" },
  moneyBag: { fn: moneyBag, anchor: "bottom" },
  building: { fn: building, anchor: "bottom" },
  priceTag: { fn: priceTag, anchor: "center" },
  gauge: { fn: gauge, anchor: "bottom" },
  foreignNote: { fn: foreignNote, anchor: "center" },
  barrier: { fn: barrier, anchor: "bottom" },
  segmentedBar: { fn: segmentedBar, anchor: "center" },
  cart: { fn: cart, anchor: "bottom" },
  piggyBank: { fn: piggyBank, anchor: "bottom" },
  ruler: { fn: ruler, anchor: "center" },
  hands: { fn: hands, anchor: "center" },
  coinJar: { fn: coinJar, anchor: "bottom" },
  pillars: { fn: pillars, anchor: "bottom" },
  briefcase: { fn: briefcase, anchor: "bottom" },
  podium: { fn: podium, anchor: "bottom" },
  staircase: { fn: staircase, anchor: "bottom" },
  desk: { fn: desk, anchor: "bottom" },
  chair: { fn: chair, anchor: "bottom" },
  rope: { fn: rope, anchor: "center" },
  world: { fn: world, anchor: "center" },
  flow: { fn: flow, anchor: "center" },
  bands: { fn: bands, anchor: "center" },
  fork: { fn: fork, anchor: "center" },
  gapBars: { fn: gapBars, anchor: "bottom" },
  timeline: { fn: timeline, anchor: "center" },
  table: { fn: table, anchor: "center" },
  graph: { fn: graph, anchor: "center" },
  funnel: { fn: funnel, anchor: "bottom" },
  roadmap: { fn: roadmap, anchor: "center" },
  plant: { fn: plant, anchor: "bottom" },
  ...FAMILY_DRAWS,                       // the families of saanche (families/index.mjs, manifests in saanche.d/)
};

export function drawSaancha(name, p = {}) {
  const d = DRAWS[name];
  if (!d) return `<g><rect x="-40" y="-40" width="80" height="80" fill="none" stroke="#e5484d" stroke-width="4"/><text y="8" text-anchor="middle" font-size="22" fill="#e5484d">${esc(name)}</text></g>`;
  return d.fn(p);
}

/** The box rule (Navin, 5 November 2026): a saancha's own box and the boxes of the words inside it, with each word's font
 *  px, in the saancha's coordinates (origin as drawn: "bottom" ones stand on it, "center" ones are centred on it) —
 *  measured from the very SVG drawSaancha returns, so every saancha, old or new, gives its box the same way. */
export function boxOf(name, p = {}) {
  return svgBounds(drawSaancha(name, p));
}

export const _test = { shade, rnd, qrModules };
