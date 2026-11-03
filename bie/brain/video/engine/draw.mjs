// The first saanche of BIE's showing engine: parametric drawing functions (Phase 1, agreement §2.2; rebuilt from the
// v2 demo's builder.py vocabulary — dist/draw.js itself was never committed). Every saancha is a pure function of its
// parameters returning an SVG string; "bottom"-anchored ones stand on their origin (the floor), "center" ones are
// centred on it. No real currency designs (notes carry ₹ and a value in BIE's own colours), no real persons.

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const FONT = "'Noto Sans', 'Noto Sans Devanagari', sans-serif";
const INK = "#2b2b33";

function shade(hex, f = 0.72) {
  const n = parseInt(hex.slice(1), 16);
  const c = (v) => Math.max(0, Math.min(255, Math.round(v * f)));
  return `#${((c(n >> 16) << 16) | (c((n >> 8) & 255) << 8) | c(n & 255)).toString(16).padStart(6, "0")}`;
}

function rnd(seed) {
  let x = seed >>> 0 || 1;
  return () => ((x = (x * 1103515245 + 12345) >>> 0), x / 4294967296);
}

const label = (text, y, size, fill = INK, weight = 700) =>
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
    `<text x="${-w * 0.28}" y="${h * 0.12}" font-family=${JSON.stringify(FONT)} font-size="${h * 0.42}" font-weight="800" fill="${col}" text-anchor="middle">₹</text>` +
    `<text x="${w * 0.14}" y="${h * 0.18}" font-family=${JSON.stringify(FONT)} font-size="${h * 0.52}" font-weight="800" fill="#f7f1e5" text-anchor="middle">${vs}</text>` +
    `<rect x="${w * 0.38}" y="${-h * 0.42}" width="${w * 0.05}" height="${h * 0.84}" fill="#f7f1e5" opacity="0.5"/>`;
}

function noteBundle(p) {
  const w = p.w || 190, v = p.value == null ? 500 : p.value, h = w * 0.46;
  const col = NOTE_COLORS[v] || "#1f8a70";
  const blank = (dy) => `<rect x="${-w * 0.5}" y="${-h * 0.5 + dy}" width="${w}" height="${h}" rx="${w * 0.03}" fill="${shade(col, 0.88)}" stroke="${shade(col, 0.7)}" stroke-width="${w * 0.015}"/>`;
  return blank(w * 0.1) + blank(w * 0.05) + note({ w, value: v }) +
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
    (p.label ? `<g transform="translate(0,${h * 0.12})"><rect x="${-w * 0.36}" y="${-h * 0.1}" width="${w * 0.72}" height="${h * 0.14}" rx="${h * 0.04}" fill="${INK}"/>` + label(p.label, 0, 0, "#ffffff", 700) + `</g>` : "");
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
};

export function drawSaancha(name, p = {}) {
  const d = DRAWS[name];
  if (!d) return `<g><rect x="-40" y="-40" width="80" height="80" fill="none" stroke="#e5484d" stroke-width="4"/><text y="8" text-anchor="middle" font-size="22" fill="#e5484d">${esc(name)}</text></g>`;
  return d.fn(p);
}

export const _test = { shade, rnd, qrModules };
