// Economy worlds (Navin, 4 Nov 2026: a "process duniya" BIE's scene plan can modify). A world paints a whole place
// behind the lesson: a market, a bank hall, the central bank, an exchange floor, a port, a factory, a village, an
// office, a court, a city street, an assembly hall. It is centred on its origin; at its default w = 3840 it covers
// the 1920x1080 stage plus half a stage on each side, so camera pans never show an edge. Place it at the stage centre
// (x 960, y 540) on the lowest layer (z 1); people stand on its floor (feet at y 885, the person default). Its
// parameters (signs, open vault, market trend, crowd, smoke, season, light) can change inside a scene through the
// item's steps. Generic places only: no real building, emblem, logo, index name or flag. 2.5D: depth by overlap,
// perspective floors and light; words on it come only from the plan (signs, label), so it serves every language.

const FONT = "'Noto Sans', 'Noto Sans Devanagari', sans-serif";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
function shade(hex, f = 0.72) {
  const n = parseInt(String(hex).slice(1), 16);
  const c = (v) => Math.max(0, Math.min(255, Math.round(v * f)));
  return `#${((c(n >> 16) << 16) | (c((n >> 8) & 255) << 8) | c(n & 255)).toString(16).padStart(6, "0")}`;
}
const okColor = (c, d) => (/^#[0-9a-fA-F]{6}$/.test(String(c || "")) ? c : d);
const text = (t, x, y, size, fill = "#2b2b33", weight = 800) => (t ? `<text x="${x}" y="${y}" font-family=${JSON.stringify(FONT)} font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="middle">${esc(t)}</text>` : "");
const rect = (x, y, w, h, fill, extra = "") => `<rect x="${x}" y="${y}" width="${Math.max(0, w)}" height="${Math.max(0, h)}" fill="${fill}"${extra}/>`;
const signsOf = (p) => String(p.signs || "").split(";").map((s) => s.trim()).filter(Boolean);
const countOf = (p, d, lo, hi) => Math.max(lo, Math.min(hi, Math.round(Number.isFinite(+p.count) && +p.count > 0 ? +p.count : signsOf(p).length || d)));

function skyGround(W, H, top, bottom, ground, gy) {
  const sky = gy + H / 2;
  return rect(-W, -H / 2, 2 * W, sky, top) + rect(-W, -H / 2 + sky * 0.55, 2 * W, sky * 0.45, bottom, ' opacity="0.7"') +
    rect(-W, gy, 2 * W, H / 2 - gy, ground);
}
function wallFloor(W, H, wall, floor, gy) {
  let tiles = "";
  for (let i = -12; i <= 12; i++) tiles += `<path d="M${i * W * 0.04} ${gy} L${i * W * 0.16} ${H / 2}" stroke="${shade(floor, 0.9)}" stroke-width="3"/>`;
  for (let k = 1; k < 5; k++) { const y = gy + (H / 2 - gy) * (k * k) / 25; tiles += `<path d="M${-W} ${y} L${W} ${y}" stroke="${shade(floor, 0.9)}" stroke-width="3"/>`; }
  return rect(-W, -H / 2, 2 * W, gy + H / 2, wall) + rect(-W, gy, 2 * W, H / 2 - gy, floor) + tiles + rect(-W, gy - 14, 2 * W, 14, shade(wall, 0.85));
}
function cloud(x, y, s) {
  return `<g opacity="0.85"><ellipse cx="${x}" cy="${y}" rx="${90 * s}" ry="${30 * s}" fill="#ffffff"/><ellipse cx="${x + 50 * s}" cy="${y - 18 * s}" rx="${60 * s}" ry="${28 * s}" fill="#ffffff"/></g>`;
}
function board(label, x, y, w, bg = "#2d3748", fg = "#ffffff") {
  if (!label) return "";
  const fs = Math.min(w * 0.12, 64), bw = Math.max(w * 0.3, String(label).length * fs * 0.62 + fs);
  return rect(x - bw / 2, y - fs * 0.95, bw, fs * 1.45, bg, ` rx="${fs * 0.25}"`) + text(label, x, y + fs * 0.1, fs, fg);
}
function smallSign(label, x, y, maxW, fs) {
  if (!label) return "";
  const f = Math.min(fs, (maxW * 0.9) / Math.max(1, String(label).length) * 1.7);
  return rect(x - maxW / 2, y - f * 0.95, maxW, f * 1.4, "#ffffff", ` rx="${f * 0.2}" opacity="0.92"`) + text(label, x, y + f * 0.05, f, "#2b2b33", 800);
}
function crowdBand(x0, x1, y, s, seed = 1) {
  const cols = ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f"], skins = ["#c68a5c", "#d39a6a", "#b97c50", "#a8714a"];
  let out = "";
  for (let i = 0, x = x0; x < x1; i++, x += s * (0.8 + ((i * 37 + seed * 13) % 7) * 0.05)) {
    const c = cols[(i + seed) % cols.length], dy = ((i * 29) % 5) * s * 0.03;
    out += `<path d="M${x - s * 0.24} ${y + dy} L${x - s * 0.24} ${y + dy - s * 0.5} Q${x} ${y + dy - s * 0.72} ${x + s * 0.24} ${y + dy - s * 0.5} L${x + s * 0.24} ${y + dy} Z" fill="${c}"/>` +
      `<circle cx="${x}" cy="${y + dy - s * 0.86}" r="${s * 0.17}" fill="${skins[(i + seed) % skins.length]}"/>`;
  }
  return `<g opacity="0.5">${out}</g>`;
}
function vaultDoor(x, y, r, open, gold) {
  const stack = [0, 1, 2].map((k) => rect(x - r * 0.62, y - r * 0.5 + k * r * 0.4, r * 1.24, r * 0.24, gold ? "#f3cf6a" : "#2fa35b", ` stroke="${gold ? "#c99a2e" : "#1f7a42"}" stroke-width="3"`)).join("");
  if (open) return `<circle cx="${x}" cy="${y}" r="${r}" fill="#3b3326"/>` + stack + `<ellipse cx="${x - r * 1.1}" cy="${y}" rx="${r * 0.32}" ry="${r}" fill="#c7ccd3" stroke="#4a5568" stroke-width="6"/>`;
  const spokes = [0, 60, 120].map((a) => { const c = Math.cos(a * Math.PI / 180) * r * 0.5, s = Math.sin(a * Math.PI / 180) * r * 0.5;
    return `<path d="M${x - c} ${y - s} L${x + c} ${y + s}" stroke="#4a5568" stroke-width="8"/>`; }).join("");
  return `<circle cx="${x}" cy="${y}" r="${r}" fill="#c7ccd3" stroke="#4a5568" stroke-width="9"/><circle cx="${x}" cy="${y}" r="${r * 0.33}" fill="none" stroke="#4a5568" stroke-width="8"/>` + spokes;
}

// ---------------------------------------------------------------- the state of a place (Sloman book, 5 Nov 2026)
// A world's state is its parameters: counts (people, taken, part, goods, vehicles, running, seats), levels (level; one
// per spot in levels), per-spot lists separated by ; (prices, levels, counts) and sets (shut, glow: "2,3", "all" or spot
// names). A step changes them on its cue word. `was` (key:value parts separated by |) says what they were just before
// the step: a board shows the old value struck beside the new one, and counts, levels and shutters move from it over
// `glide` seconds after the step (_s): people walk to the truck, sacks drop on the heap, a shutter rolls down. Processes
// (belts, smoke, rain, water, fish, ticker pulses) move with _t. Everything is a pure function of p, _t and _s.
const tOf = (p) => (Number.isFinite(+p._t) ? +p._t : 0);
const c01 = (v) => Math.max(0, Math.min(1, v));
const easeIO = (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
const rnd = (i, seed = 0) => { const v = Math.sin(i * 127.1 + seed * 311.7) * 43758.5453; return v - Math.floor(v); };
const isN = (v) => v !== undefined && v !== null && v !== "" && typeof v !== "boolean" && Number.isFinite(+v);
const listOf = (v) => (v === undefined || v === null || v === "" ? [] : String(v).split(";").map((s) => s.trim()));
const fitFs = (t, maxW, cap) => Math.min(cap, (maxW * 0.92) / Math.max(1, String(t).length) * 1.75);
const r1 = (v) => Math.round(v * 10) / 10;
function wasOf(p) {
  const o = {};
  for (const part of String(p.was || "").split("|")) { const m = /^\s*([A-Za-z]+)\s*:(.*)$/.exec(part); if (m) o[m[1]] = m[2].trim(); }
  return o;
}
function phase(p) {                                          // 0 at the step, 1 once glide seconds have passed (or no times)
  const s = p._s;
  if (s === undefined || s === null || s === "" || !Number.isFinite(+s)) return 1;
  return easeIO(c01(+s / Math.max(0.1, +p.glide || 1.5)));
}
function nv(p, key, d) {                                     // a count or level now (d for -1 or left out), moving from was
  const now = isN(p[key]) && +p[key] >= 0 ? +p[key] : d, w = wasOf(p)[key];
  return isN(w) && +w >= 0 ? +w + (now - +w) * phase(p) : now;
}
function lv(p, key, i, d) {                                  // entry i of a ; list now, moving from the was list
  const a = listOf(p[key])[i], now = isN(a) ? +a : d, w = wasOf(p)[key];
  if (w === undefined) return now;
  const b = listOf(w)[i];
  return isN(b) ? +b + (now - +b) * phase(p) : now;
}
const hasList = (p, key) => listOf(p[key]).some(isN) || wasOf(p)[key] !== undefined;
function inSet(v, i, name) {
  const s = String(v ?? "").toLowerCase().split(/[,;\s]+/).filter(Boolean);
  return s.includes("all") || s.includes(String(i)) || (!!name && s.includes(String(name).toLowerCase()));
}
function sv(p, key, i, name) {                               // 0..1: part i (or the named part) in the set now, moving from was
  const now = inSet(p[key], i, name) ? 1 : 0, w = wasOf(p)[key];
  if (w === undefined) return now;
  const b = inSet(w, i, name) ? 1 : 0;
  return b + (now - b) * phase(p);
}
function boardOf(p, key, i) {                                // [the value now, the old value to strike (if it changed)]
  const now = listOf(p[key])[i] || "", w = wasOf(p)[key], old = w === undefined ? "" : listOf(w)[i] || "";
  return [now, old && old !== now ? old : ""];
}
function rollValue(p) {                                      // a counter's text: digits roll from the was value after a step
  const v = p.value === undefined || p.value === null ? "" : String(p.value), w = wasOf(p).value;
  const num = (s) => { const m = /^\s*(-?\d[\d,]*(?:\.\d+)?)(.*)$/.exec(String(s)); return m ? [parseFloat(m[1].replace(/,/g, "")), m[2], m[1].includes(","), (m[1].split(".")[1] || "").length] : null; };
  const a = num(v), b = w === undefined ? null : num(w), e = phase(p);
  if (!a || !b || e >= 1) return v;
  const parts = (b[0] + (a[0] - b[0]) * e).toFixed(a[3]).split(".");
  if (a[2]) parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return parts.join(".") + a[1];
}
const textA = (t, x, y, size, fill, weight, anchor) => (t ? `<text x="${r1(x)}" y="${r1(y)}" font-family=${JSON.stringify(FONT)} font-size="${r1(size)}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}">${esc(t)}</text>` : "");
function struck(t, x, y, fs, fill, anchor = "middle") {
  if (!t) return "";
  const w = String(t).length * fs * 0.56, x0 = anchor === "end" ? x - w : anchor === "start" ? x : x - w / 2;
  return textA(t, x, y, fs, fill, 700, anchor) + `<path d="M${r1(x0 - fs * 0.1)} ${r1(y - fs * 0.32)} L${r1(x0 + w + fs * 0.1)} ${r1(y - fs * 0.32)}" stroke="#e5484d" stroke-width="${r1(Math.max(3, fs * 0.09))}"/>`;
}
// A framed board: the value big, the old value struck beside it, an optional title line and a trend arrow outside.
function chalk(x, y, w, h, now, old, o = {}) {
  const k = o.k || 1, fg = o.fg || "#f5f1e3";
  let s = rect(x - w / 2, y, w, h, o.bg || "#2f4a3a", ` rx="${8 * k}" stroke="${o.frame || "#8a5a2b"}" stroke-width="${6 * k}"`), top = y;
  if (o.title) { const f = fitFs(o.title, w * 0.88, Math.max(36 * k, Math.min(46 * k, h * 0.3))); s += textA(o.title, x, y + f * 1.05, f, "#cfe0c8", 700, "middle"); top = y + f * 1.25; }
  const avail = y + h - top, mid = top + avail / 2;
  if (old && avail > 110 * k && String(old).length + String(now).length > 9) {     // a long value: the old one struck above the new
    const fo = fitFs(old, w * 0.86, Math.min(avail * 0.34, 46 * k)), fn = fitFs(now, w * 0.86, Math.min(avail * 0.5, 80 * k));
    s += struck(old, x, top + avail * 0.32 + fo * 0.2, fo, "#f0b4b4") + textA(now, x, top + avail * 0.8, fn, fg, 800, "middle");
  } else if (old) {
    const fo = fitFs(old, w * 0.4, Math.min(avail * 0.55, 60 * k)), fn = fitFs(now, w * 0.48, Math.min(avail * 0.72, 88 * k));
    s += struck(old, x - w * 0.25, mid + fo * 0.35, fo, "#f0b4b4") + textA(now, x + w * 0.22, mid + fn * 0.36, fn, fg, 800, "middle");
  } else if (now) { const f = fitFs(now, w * 0.86, Math.min(avail * 0.72, 92 * k)); s += textA(now, x, mid + f * 0.36, f, fg, 800, "middle"); }
  if (o.trend === "up" || o.trend === "down") {
    const up = o.trend === "up", a = Math.min(h * 0.3, 42 * k), ax = x + w / 2 + a * 0.95, ay = y + h / 2, d = up ? 1 : -1;
    s += `<path d="M${ax - a * 0.62} ${ay + d * a * 0.45} L${ax} ${ay - d * a * 0.55} L${ax + a * 0.62} ${ay + d * a * 0.45} Z" fill="${up ? "#2fb463" : "#e5484d"}" stroke="#ffffff" stroke-width="${3 * k}"/>`;
  }
  return s;
}
// Rows of a board: names (left) and values (right, the old value struck before it).
function rowsBoard(x0, y0, x1, y1, names, p, key, n, k) {
  const rh = (y1 - y0 - 16 * k) / Math.max(1, n), bw = x1 - x0;
  let g = rect(x0, y0, bw, y1 - y0, "#22302a", ` rx="${10 * k}" stroke="#8a5a2b" stroke-width="${6 * k}"`);
  for (let j = 0; j < n; j++) {
    const yc = y0 + 8 * k + (j + 0.5) * rh, [now, old] = boardOf(p, key, j), nm = names[j] || "", fs = Math.min(48 * k, rh * 0.66);
    if (j) g += `<path d="M${x0 + 18 * k} ${yc - rh / 2} L${x1 - 18 * k} ${yc - rh / 2}" stroke="#4d5f55" stroke-width="${2 * k}" stroke-dasharray="${8 * k} ${8 * k}"/>`;
    if (!names.length) {                                     // whole rows (an item and its price in one): the old row struck after it
      const fn = fitFs(now, bw * (old ? 0.55 : 0.9), fs);
      g += textA(now, x0 + 22 * k, yc + fs * 0.36, fn, "#ffd36b", 800, "start") + (old ? struck(old, x1 - 22 * k, yc + fs * 0.36, fitFs(old, bw * 0.36, fs * 0.8), "#f0b4b4", "end") : "");
      continue;
    }
    g += textA(nm, x0 + 22 * k, yc + fs * 0.36, fitFs(nm, bw * (old ? 0.4 : 0.56), fs), "#f5f1e3", 700, "start");
    g += textA(now, x1 - 22 * k, yc + fs * 0.36, fitFs(now, bw * 0.26, fs), "#ffd36b", 800, "end");
    if (old) g += struck(old, x1 - 34 * k - bw * 0.27, yc + fs * 0.36, fitFs(old, bw * 0.2, fs * 0.85), "#f0b4b4", "end");
  }
  return g;
}
function paperNote(x, y, t, k, maxW) {                       // a pinned paper with the plan's words, top centre at (x, y)
  if (!t) return "";
  const f0 = 42 * k, w = Math.min(maxW, String(t).length * f0 * 0.6 + 50 * k), f = fitFs(t, w * 0.95, f0), h = Math.max(f * 1.75, 64 * k);
  return rect(x - w / 2, y, w, h, "#fbf8ef", ` stroke="#cfc6b4" stroke-width="${3 * k}"`) + `<circle cx="${x}" cy="${y + 9 * k}" r="${7 * k}" fill="#e5484d"/>` +
    textA(t, x, y + h / 2 + f * 0.38, f, "#2b2b33", 800, "middle");
}
function counterBox(x, y, p, k, fs = 56) {                   // a digital counter (value), top centre at (x, y)
  const v = rollValue(p);
  if (!v) return "";
  const f = fs * k, w = Math.max(170 * k, String(v).length * f * 0.62 + 44 * k), h = f * 1.45;
  return rect(x - w / 2, y, w, h, "#111a22", ` rx="${10 * k}" stroke="#4a5568" stroke-width="${5 * k}"`) + textA(v, x, y + h * 0.72, f, "#7dffb0", 800, "middle");
}
function shutterG(x, y, w, h, f, k = 1) {                    // a rolling shutter down to f of its height
  if (f <= 0.002) return "";
  const hh = h * c01(f);
  let g = rect(x, y, w, hh, "#a3adb8");
  for (let yy = y + 14 * k; yy < y + hh - 6 * k; yy += 18 * k) g += `<path d="M${r1(x)} ${r1(yy)} L${r1(x + w)} ${r1(yy)}" stroke="#7d8793" stroke-width="${3 * k}"/>`;
  return g + rect(x, y + Math.max(0, hh - 10 * k), w, Math.min(hh, 10 * k), "#5f6873");
}
function glowBox(x0, y0, x1, y1, f, k) {                     // a highlight round a part (a stall in focus, a fixed factor)
  return f > 0.01 ? rect(x0, y0, x1 - x0, y1 - y0, "#f2c14e", ` rx="${14 * k}" fill-opacity="${r1(0.16 * f * 10) / 10}" stroke="#f2a900" stroke-width="${8 * k}" stroke-dasharray="${22 * k} ${12 * k}" opacity="${r1(f * 10) / 10}"`) : "";
}
const TOPS = ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f", "#2a9d8f", "#d96a2b", "#5b7fb8", "#c2447a"];
const SKINS = ["#c68a5c", "#d39a6a", "#b97c50", "#a8714a", "#c98850"];
const BOTS = ["#2e3440", "#4a3b2a", "#e9dfc6", "#3d4f6b", "#6b4a26"];
// A plain countable person of the place (feet at x, y; h tall): pose stand | sit | walk | work | carry; o.op fades it.
function fig(x, y, h, i = 0, o = {}) {
  const s = h / 100, top = o.col || TOPS[(i * 7 + 3) % TOPS.length], skin = SKINS[(i * 3 + 1) % SKINS.length], bot = o.bot || BOTS[(i * 5 + 2) % BOTS.length];
  const pose = o.pose || "stand", sit = pose === "sit", hip = y - (sit ? 30 : 40) * s, sh = hip - 34 * s, hy = sh - 13 * s;
  const sw = pose === "walk" ? Math.sin((o.t || 0) * 9 + i) * 9 * s : 0, arm = shade(top, 0.8), L = (a) => a.map(r1).join(" ");
  let g = sit
    ? `<path d="M${L([x - 6 * s, hip])} L${L([x + 10 * s, hip + 2 * s])} L${L([x + 10 * s, y])}" stroke="${bot}" stroke-width="${r1(10 * s)}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`
    : `<path d="M${L([x - 5 * s, hip])} L${L([x - 5 * s - sw, y - 3 * s])} M${L([x + 5 * s, hip])} L${L([x + 5 * s + sw, y - 3 * s])}" stroke="${bot}" stroke-width="${r1(10 * s)}" stroke-linecap="round"/>`;
  g += `<path d="M${L([x - 13 * s, hip + 3 * s])} L${L([x - 15 * s, sh + 6 * s])} Q${L([x, sh - 4 * s])} ${L([x + 15 * s, sh + 6 * s])} L${L([x + 13 * s, hip + 3 * s])} Z" fill="${top}"/>`;
  const arms = pose === "work" ? [[-13, 7, -5, -8], [13, 7, 6, -8]] : pose === "carry" ? [[-13, 6, -13, -40], [13, 6, 13, -40]] : [[-14, 6, -17, -4], [14, 6, 17, -4]];
  g += `<path d="${arms.map(([a, b, c, d]) => `M${L([x + a * s, sh + b * s])} L${L([x + c * s, (d < -30 ? hy + (d + 40) * s - 12 * s : hip + d * s)])}`).join(" ")}" stroke="${arm}" stroke-width="${r1(7 * s)}" stroke-linecap="round"/>`;
  g += `<circle cx="${r1(x)}" cy="${r1(hy)}" r="${r1(11 * s)}" fill="${skin}"/>`;
  const hw = (i * 3) % 5;
  if (hw === 0 || hw === 3) g += `<path d="M${L([x - 11 * s, hy - 1 * s])} Q${L([x, hy - 18 * s])} ${L([x + 11 * s, hy - 1 * s])} Z" fill="#2b2017"/>`;
  else if (hw === 1) g += `<path d="M${L([x - 12 * s, hy - 3 * s])} Q${L([x, hy - 20 * s])} ${L([x + 12 * s, hy - 3 * s])} Z" fill="${o.hat || "#f1e3c6"}"/>`;
  else if (hw === 2) g += `<path d="M${L([x - 11 * s, hy - 2 * s])} Q${L([x, hy - 17 * s])} ${L([x + 11 * s, hy - 2 * s])} L${L([x + 12 * s, hy + 9 * s])} L${L([x + 8 * s, hy + 2 * s])} Z" fill="#241b12"/>`;
  if (pose === "carry") g += sackG(x, hy - 8 * s, 0.5 * s);
  if (o.tool && i % 3 === 0) g += `<path d="M${L([x + 20 * s, y - 2 * s])} L${L([x + 22 * s, sh - 14 * s])}" stroke="#8a5a2b" stroke-width="${r1(4 * s)}"/><path d="M${L([x + 14 * s, y - 2 * s])} L${L([x + 26 * s, y - 2 * s])} L${L([x + 24 * s, y - 16 * s])} L${L([x + 16 * s, y - 16 * s])} Z" fill="#8d96a0"/>`;
  if (o.tool && i % 3 === 1) g += `<ellipse cx="${r1(x)}" cy="${r1(hy - 14 * s)}" rx="${r1(13 * s)}" ry="${r1(6 * s)}" fill="#d8c49a" stroke="#a8925e" stroke-width="${r1(2 * s)}"/>`;
  if (o.basket) g += `<path d="M${L([x - 10 * s, sh + 2 * s])} L${L([x + 16 * s, sh - 6 * s])} L${L([x + 22 * s, hip - 4 * s])} L${L([x + 2 * s, hip])} Z" fill="#c9a46a" stroke="#8a6d3b" stroke-width="${r1(2 * s)}"/>`;
  if (o.sweat) g += [0, 1].map((j) => { const u = ((o.t || 0) * 1.3 + j * 0.5) % 1; return `<ellipse cx="${r1(x + (j ? 14 : -14) * s)}" cy="${r1(hy - 4 * s + u * 26 * s)}" rx="${r1(2.6 * s)}" ry="${r1(4 * s)}" fill="#6cc4f0" opacity="${r1((1 - u) * 10) / 10}"/>`; }).join("");
  return o.op !== undefined && o.op < 1 ? `<g opacity="${(+o.op).toFixed(3)}">${g}</g>` : g;
}
// Stable places for a counted crowd: slot j grows from the middle outwards, front row first, so one leaving never
// reshuffles the others; n may be fractional (the last one fades), back rows are drawn first.
function slotOf(j, cx, yFront, h, perRow) {
  const row = Math.floor(j / perRow), c = j % perRow, off = c === 0 ? 0 : (c % 2 ? (c + 1) / 2 : -c / 2), sc = Math.pow(0.92, row);
  return { x: cx + off * h * 0.34 * sc + (rnd(j, 3) - 0.5) * h * 0.08 + (row % 2) * h * 0.17, y: yFront - row * h * 0.15, h: h * sc, row };
}
function crowdAt(n, cx, yFront, h, perRow, o = {}) {
  const whole = Math.floor(n + 1e-6), frac = n - whole, items = [];
  for (let j = 0; j < Math.ceil(n - 1e-6); j++) items.push({ j, ...slotOf(j, cx, yFront, h, perRow), op: j < whole ? 1 : frac });
  items.sort((a, b) => b.row - a.row || a.j - b.j);
  return items.map((s) => fig(s.x, s.y, s.h, s.j + (o.seed || 0), { ...o, op: s.op })).join("");
}
function sackG(x, y, s, col = "#d8c49a", glow = false) {     // a grain sack standing on y, about 60 s wide
  const L = (a) => a.map(r1).join(" ");
  return `<path d="M${L([x - 27 * s, y])} Q${L([x - 34 * s, y - 28 * s])} ${L([x - 18 * s, y - 46 * s])} L${L([x + 18 * s, y - 46 * s])} Q${L([x + 34 * s, y - 28 * s])} ${L([x + 27 * s, y])} Z" fill="${col}" stroke="${glow ? "#f2a900" : shade(col, 0.72)}" stroke-width="${r1((glow ? 6 : 3) * s)}"/>` +
    `<path d="M${L([x - 13 * s, y - 46 * s])} L${L([x, y - 55 * s])} L${L([x + 13 * s, y - 46 * s])} Z" fill="${shade(col, 0.9)}"/><path d="M${L([x - 19 * s, y - 20 * s])} L${L([x + 19 * s, y - 20 * s])}" stroke="${shade(col, 0.8)}" stroke-width="${r1(2 * s)}"/>`;
}
function heapG(n, cx, y, s, o = {}) {                       // a pyramid of n sacks; a fractional last one drops in
  const whole = Math.floor(n + 1e-6), frac = n - whole, total = Math.ceil(n - 1e-6);
  if (total <= 0) return "";
  let base = 1, out = "", j = 0;
  while ((base * (base + 1)) / 2 < total) base++;
  for (let r = 0; r < base && j < total; r++) {
    const m = base - r;
    for (let c = 0; c < m && j < total; c++, j++) {
      const x = cx + (c - (m - 1) / 2) * 52 * s, yy = y - r * 40 * s, op = j < whole ? 1 : frac;
      const one = (o.item && o.item !== "sack") ? itemG(o.item, x, yy, s * 1.1) : sackG(x, yy, s, o.col, o.glow);
      out += op < 1 ? `<g opacity="${op.toFixed(3)}" transform="translate(0,${r1(-(1 - op) * 70 * s)})">${one}</g>` : one;
    }
  }
  return out;
}
// One made thing standing on y (about 54 s wide): what a belt carries, a godown stores, a counter shows.
function itemG(kind, x, y, s, i = 0) {
  const L = (a) => a.map(r1).join(" "), R = (x0, y0, w, h, f, ex = "") => rect(r1(x0), r1(y0), r1(w), r1(h), f, ex);
  switch (kind) {
    case "sack": return sackG(x, y, s * 0.85);
    case "shirt": return `<path d="M${L([x - 24 * s, y])} L${L([x - 24 * s, y - 30 * s])} L${L([x - 10 * s, y - 36 * s])} L${L([x, y - 30 * s])} L${L([x + 10 * s, y - 36 * s])} L${L([x + 24 * s, y - 30 * s])} L${L([x + 24 * s, y])} Z" fill="${TOPS[i % TOPS.length]}" stroke="${shade(TOPS[i % TOPS.length], 0.7)}" stroke-width="${r1(2 * s)}"/>`;
    case "cloth": return R(x - 26 * s, y - 24 * s, 52 * s, 24 * s, TOPS[(i + 2) % TOPS.length], ` rx="${r1(12 * s)}"`) + `<ellipse cx="${r1(x + 22 * s)}" cy="${r1(y - 12 * s)}" rx="${r1(5 * s)}" ry="${r1(12 * s)}" fill="${shade(TOPS[(i + 2) % TOPS.length], 0.75)}"/>`;
    case "chair": return `<path d="M${L([x - 14 * s, y])} L${L([x - 14 * s, y - 44 * s])} M${L([x - 14 * s, y - 20 * s])} L${L([x + 16 * s, y - 20 * s])} L${L([x + 16 * s, y])}" stroke="#8a5a2b" stroke-width="${r1(6 * s)}" fill="none" stroke-linecap="round"/>`;
    case "glass": return R(x - 20 * s, y - 40 * s, 40 * s, 40 * s, "#bfe3f5", ` stroke="#7fb3cf" stroke-width="${r1(3 * s)}"`) + `<path d="M${L([x - 10 * s, y - 32 * s])} L${L([x + 2 * s, y - 12 * s])}" stroke="#ffffff" stroke-width="${r1(3 * s)}"/>`;
    case "bolt": return `<path d="M${L([x - 14 * s, y])} L${L([x - 20 * s, y - 12 * s])} L${L([x - 14 * s, y - 24 * s])} L${L([x + 14 * s, y - 24 * s])} L${L([x + 20 * s, y - 12 * s])} L${L([x + 14 * s, y])} Z" fill="#9aa5b1" stroke="#5f6873" stroke-width="${r1(2 * s)}"/>`;
    case "pot": return `<path d="M${L([x - 22 * s, y - 30 * s])} L${L([x + 22 * s, y - 30 * s])} Q${L([x + 26 * s, y])} ${L([x, y])} Q${L([x - 26 * s, y])} ${L([x - 22 * s, y - 30 * s])} Z" fill="#c98850" stroke="#8a5a2b" stroke-width="${r1(2 * s)}"/>`;
    case "roti": return `<ellipse cx="${r1(x)}" cy="${r1(y - 5 * s)}" rx="${r1(24 * s)}" ry="${r1(6 * s)}" fill="#e2b874" stroke="#b88a47" stroke-width="${r1(2 * s)}"/>`;
    case "samosa": return `<path d="M${L([x - 22 * s, y])} L${L([x, y - 30 * s])} L${L([x + 22 * s, y])} Z" fill="#e0a43a" stroke="#a8721e" stroke-width="${r1(2 * s)}" stroke-linejoin="round"/>`;
    case "jalebi": return `<path d="M${L([x, y - 14 * s])} m${r1(-4 * s)} 0 a${r1(4 * s)} ${r1(4 * s)} 0 1 1 ${r1(8 * s)} 0 a${r1(9 * s)} ${r1(9 * s)} 0 1 1 ${r1(-18 * s)} 0 a${r1(14 * s)} ${r1(13 * s)} 0 1 1 ${r1(28 * s)} 0" stroke="#f08a1c" stroke-width="${r1(5 * s)}" fill="none"/>`;
    case "bread": return R(x - 24 * s, y - 24 * s, 48 * s, 24 * s, "#d9a35e", ` rx="${r1(11 * s)}" stroke="#a8721e" stroke-width="${r1(2 * s)}"`);
    case "tea": return `<path d="M${L([x - 14 * s, y - 28 * s])} L${L([x + 14 * s, y - 28 * s])} L${L([x + 10 * s, y])} L${L([x - 10 * s, y])} Z" fill="#f7efe2" stroke="#b9a576" stroke-width="${r1(2 * s)}"/><rect x="${r1(x - 12 * s)}" y="${r1(y - 25 * s)}" width="${r1(24 * s)}" height="${r1(6 * s)}" fill="#b0703a"/>`;
    case "mithai": return `<circle cx="${r1(x)}" cy="${r1(y - 14 * s)}" r="${r1(14 * s)}" fill="#f2a33a" stroke="#c97a14" stroke-width="${r1(2 * s)}"/>`;
    case "tiffin": return [0, 1, 2].map((r) => R(x - 18 * s, y - (r + 1) * 14 * s, 36 * s, 13 * s, "#c7ccd3", ` rx="${r1(3 * s)}" stroke="#8d96a0" stroke-width="${r1(2 * s)}"`)).join("") + `<path d="M${L([x - 14 * s, y - 42 * s])} Q${L([x, y - 58 * s])} ${L([x + 14 * s, y - 42 * s])}" stroke="#8d96a0" stroke-width="${r1(3 * s)}" fill="none"/>`;
    case "car": return carG(x, y, s * 0.24, TOPS[i % TOPS.length]);
    default: return R(x - 24 * s, y - 36 * s, 48 * s, 36 * s, "#c8a06a", ` stroke="#8a6d3b" stroke-width="${r1(3 * s)}"`) + `<path d="M${L([x, y - 36 * s])} L${L([x, y])}" stroke="#e8d3a8" stroke-width="${r1(5 * s)}"/>`;
  }
}
// A stack of n things in a box (godown, shelf), bottom-left first; fractional last one fades in.
function stackIn(n, x0, y0, x1, y1, kind, k) {
  const total = Math.ceil(n - 1e-6), whole = Math.floor(n + 1e-6);
  if (total <= 0) return "";
  let cols = 4;
  while (Math.ceil(total / cols) * ((x1 - x0) / cols) > (y1 - y0) && cols < 40) cols++;
  const u = (x1 - x0) / cols, s = Math.min(u / 58, 1.4 * k);
  let out = "";
  for (let j = 0; j < total; j++) {
    const c = j % cols, r = Math.floor(j / cols), one = itemG(kind, x0 + (c + 0.5) * u, y1 - r * u * (kind === "roti" ? 0.35 : 0.82), s, j);
    out += j < whole ? one : `<g opacity="${(n - whole).toFixed(3)}">${one}</g>`;
  }
  return out;
}
// Vehicles, side view, wheels on the ground at y; dir 1 faces right.
function truckG(x, y, s, col = "#2f7fc0", dir = 1) {         // a lorry 420 s long; its open bed spans local x -205..70, floor -50, top -150
  return `<g transform="translate(${r1(x)},${r1(y)}) scale(${r1(s * dir * 1000) / 1000},${r1(s * 1000) / 1000})">` +
    `<rect x="-205" y="-150" width="275" height="100" fill="${col}" stroke="${shade(col, 0.7)}" stroke-width="5"/>` +
    [1, 2, 3].map((i) => `<path d="M${-205 + i * 69} -150 L${-205 + i * 69} -50" stroke="${shade(col, 0.78)}" stroke-width="4"/>`).join("") +
    `<rect x="-212" y="-50" width="414" height="18" fill="#3a4049"/><path d="M78 -50 L78 -172 L150 -172 L202 -112 L202 -50 Z" fill="${shade(col, 0.88)}" stroke="${shade(col, 0.65)}" stroke-width="5"/>` +
    `<path d="M94 -158 L146 -158 L182 -116 L94 -116 Z" fill="#cfe3f0"/>` + [-150, -62, 150].map((cx) => `<circle cx="${cx}" cy="-30" r="30" fill="#2d3748"/><circle cx="${cx}" cy="-30" r="12" fill="#9aa5b1"/>`).join("") + `</g>`;
}
function cartG(x, y, s, col = "#a9713c", dir = 1) {          // a hand cart 300 s long, bed top at -100 s
  return `<g transform="translate(${r1(x)},${r1(y)}) scale(${r1(s * dir * 1000) / 1000},${r1(s * 1000) / 1000})">` +
    `<path d="M120 -86 L190 -40" stroke="#5e3b17" stroke-width="10" stroke-linecap="round"/><rect x="-140" y="-100" width="260" height="24" fill="${col}" stroke="${shade(col, 0.7)}" stroke-width="4"/>` +
    `<circle cx="-30" cy="-40" r="40" fill="none" stroke="#5e3b17" stroke-width="10"/><path d="M-70 -40 L10 -40 M-30 -80 L-30 0" stroke="#5e3b17" stroke-width="5"/></g>`;
}
function carG(x, y, s, col = "#e5484d", dir = 1) {           // a car 244 s long, 100 s tall
  return `<g transform="translate(${r1(x)},${r1(y)}) scale(${r1(s * dir * 1000) / 1000},${r1(s * 1000) / 1000})">` +
    `<path d="M-122 -28 L-122 -60 Q-118 -70 -92 -72 L-62 -72 L-32 -100 L48 -100 L84 -72 L108 -68 Q122 -64 122 -50 L122 -28 Z" fill="${col}" stroke="${shade(col, 0.7)}" stroke-width="4"/>` +
    `<path d="M-26 -94 L4 -94 L4 -75 L-46 -75 Z M12 -94 L44 -94 L70 -75 L12 -75 Z" fill="#cfe3f0"/>` + [-70, 72].map((cx) => `<circle cx="${cx}" cy="-26" r="24" fill="#2d3748"/><circle cx="${cx}" cy="-26" r="9" fill="#9aa5b1"/>`).join("") + `</g>`;
}
function busG(x, y, s, col, dir = 1, fill = 0, seed = 0) {   // a bus 540 s long, 230 s tall; fill 0..1 of its windows show heads
  let heads = "";
  const nw = 7, lit = Math.round(c01(fill) * nw);
  for (let i = 0; i < nw; i++) if (i < lit) heads += `<circle cx="${-206 + i * 58}" cy="-150" r="14" fill="${SKINS[(i + seed) % SKINS.length]}"/><rect x="${-220 + i * 58}" y="-136" width="28" height="12" fill="${TOPS[(i * 3 + seed) % TOPS.length]}"/>`;
  return `<g transform="translate(${r1(x)},${r1(y)}) scale(${r1(s * dir * 1000) / 1000},${r1(s * 1000) / 1000})">` +
    `<rect x="-270" y="-230" width="540" height="196" rx="22" fill="${col}" stroke="${shade(col, 0.7)}" stroke-width="5"/>` +
    [...Array(nw).keys()].map((i) => `<rect x="${-232 + i * 58}" y="-196" width="50" height="70" rx="6" fill="#cfe3f0"/>`).join("") + heads +
    `<rect x="190" y="-196" width="62" height="150" rx="6" fill="#9fb8cc" stroke="${shade(col, 0.7)}" stroke-width="4"/><rect x="-270" y="-112" width="540" height="10" fill="${shade(col, 0.82)}"/>` +
    [-170, 170].map((cx) => `<circle cx="${cx}" cy="-34" r="34" fill="#2d3748"/><circle cx="${cx}" cy="-34" r="13" fill="#9aa5b1"/>`).join("") + `</g>`;
}
// One plant of a crop on y; g its growth 0..1; dry (drought) wilts it, ripe (harvest) turns it gold.
function plantG(x, y, s, crop, g, dry, ripe) {
  const h = (14 + 46 * g) * s, green = dry ? "#b9a65a" : ripe ? "#d2b04a" : "#5fa548", L = (a) => a.map(r1).join(" "), lean = dry ? 9 * s : 0;
  switch (crop) {
    case "wheat": case "rice": {
      let out = `<path d="M${L([x - 6 * s, y])} Q${L([x - 8 * s, y - h * 0.6])} ${L([x - 10 * s + lean, y - h])} M${L([x, y])} L${L([x + lean, y - h * 1.08])} M${L([x + 6 * s, y])} Q${L([x + 8 * s, y - h * 0.6])} ${L([x + 10 * s + lean, y - h])}" stroke="${green}" stroke-width="${r1(3 * s)}" fill="none" stroke-linecap="round"/>`;
      if (crop === "wheat" && g > 0.45) out += [-10, 0, 10].map((dx, j) => `<ellipse cx="${r1(x + dx * s + lean)}" cy="${r1(y - h - (j === 1 ? 6 : 2) * s)}" rx="${r1(3.5 * s)}" ry="${r1(8 * s)}" fill="${ripe || dry ? "#d9a93a" : "#c9c25a"}"/>`).join("");
      if (crop === "rice" && g > 0.5) out += `<path d="M${L([x + lean, y - h])} q${r1(9 * s)} ${r1(4 * s)} ${r1(12 * s)} ${r1(15 * s)}" stroke="${ripe ? "#d9b34a" : "#b8c95a"}" stroke-width="${r1(4 * s)}" fill="none"/>`;
      return out;
    }
    case "tea": case "cotton": case "potato": {
      const r = (8 + 10 * g) * s, c = crop === "tea" ? (dry ? "#9a9a52" : "#3f8a3a") : green;
      let out = `<circle cx="${r1(x - r * 0.6)}" cy="${r1(y - r * 0.8)}" r="${r1(r * 0.8)}" fill="${shade(c, 0.85)}"/><circle cx="${r1(x + r * 0.6)}" cy="${r1(y - r * 0.8)}" r="${r1(r * 0.8)}" fill="${shade(c, 0.9)}"/><circle cx="${r1(x)}" cy="${r1(y - r * 1.2)}" r="${r1(r)}" fill="${c}"/>`;
      if (crop === "cotton" && g > 0.5) out += [-0.6, 0.2, 0.7].map((d) => `<circle cx="${r1(x + d * r)}" cy="${r1(y - r * 1.3 + Math.abs(d) * r * 0.4)}" r="${r1(r * 0.3)}" fill="#ffffff"/>`).join("");
      if (crop === "potato" && g > 0.6) out += `<circle cx="${r1(x - r * 0.3)}" cy="${r1(y - r * 1.5)}" r="${r1(r * 0.18)}" fill="#f4f0d0"/>`;
      return out;
    }
    case "cauliflower": return `<path d="M${L([x - 16 * s, y])} Q${L([x - 20 * s, y - h * 0.5])} ${L([x - 6 * s, y - h * 0.55])} M${L([x + 16 * s, y])} Q${L([x + 20 * s, y - h * 0.5])} ${L([x + 6 * s, y - h * 0.55])}" stroke="${green}" stroke-width="${r1(7 * s)}" fill="none"/>` +
      (g > 0.4 ? `<circle cx="${r1(x)}" cy="${r1(y - h * 0.45)}" r="${r1((6 + 8 * g) * s)}" fill="${dry ? "#e3dcc0" : "#f6f2e4"}" stroke="#d8cfae" stroke-width="${r1(2 * s)}"/>` : "");
    case "onion": return `<path d="M${L([x, y - 4 * s])} L${L([x - 8 * s + lean, y - h])} M${L([x, y - 4 * s])} L${L([x + lean, y - h * 1.1])} M${L([x, y - 4 * s])} L${L([x + 8 * s + lean, y - h])}" stroke="${green}" stroke-width="${r1(3 * s)}" stroke-linecap="round"/>` +
      (g > 0.6 ? `<ellipse cx="${r1(x)}" cy="${r1(y - 4 * s)}" rx="${r1(8 * s)}" ry="${r1(6 * s)}" fill="#b05a7a"/>` : "");
    case "carrot": return `<path d="M${L([x, y - 3 * s])} Q${L([x - 12 * s, y - h * 0.7])} ${L([x - 10 * s + lean, y - h])} M${L([x, y - 3 * s])} Q${L([x + 12 * s, y - h * 0.7])} ${L([x + 10 * s + lean, y - h])} M${L([x, y - 3 * s])} L${L([x + lean, y - h])}" stroke="${green}" stroke-width="${r1(4 * s)}" fill="none" stroke-dasharray="${r1(3 * s)} ${r1(2 * s)}"/>` +
      (g > 0.5 ? `<path d="M${L([x - 6 * s, y - 3 * s])} L${L([x + 6 * s, y - 3 * s])} L${L([x, y + 4 * s])} Z" fill="#ef8a2b"/>` : "");
    default: return "";
  }
}
// Festive lights strung across a place: wedding bulbs that twinkle, or Diwali lanterns and marigold strings.
function festiveG(W, H, kind, t, y) {
  if (kind !== "wedding" && kind !== "diwali") return "";
  const k = W / 1920, warm = ["#ffd36b", "#ff8a3c", "#fff3b0", "#ff6f91"];
  let g = "";
  for (let st = 0; st < (kind === "wedding" ? 3 : 1); st++) {
    const y0 = y + st * 30 * k, sag = 46 * k;
    g += `<path d="M${-W} ${r1(y0)} Q${-W / 2} ${r1(y0 + sag * 2)} 0 ${r1(y0)} Q${W / 2} ${r1(y0 + sag * 2)} ${W} ${r1(y0)}" stroke="${kind === "wedding" ? "#7a6a4a" : "#f08a1c"}" stroke-width="${(kind === "wedding" ? 2 : 6) * k}" fill="none" opacity="0.8"/>`;
    for (let i = 0; i <= 80; i++) {
      const u = (i % 40) / 40, x = -W + (i / 80) * 2 * W, yy = y0 + 2 * u * (1 - u) * sag * 2;
      if (kind === "wedding") g += `<circle cx="${r1(x)}" cy="${r1(yy + 6 * k)}" r="${r1(7 * k)}" fill="${warm[(i + st) % 4]}" opacity="${r1((0.55 + 0.45 * (0.5 + 0.5 * Math.sin(t * 3 + i * 1.7 + st))) * 100) / 100}"/>`;
      else g += `<circle cx="${r1(x)}" cy="${r1(yy + 4 * k)}" r="${r1(8 * k)}" fill="${i % 2 ? "#f2a900" : "#f08a1c"}"/>`;
    }
  }
  if (kind === "diwali") for (let i = -4; i <= 4; i++) {
    const x = i * W * 0.22 + W * 0.11, sw = Math.sin(t * 1.6 + i) * 4 * k, yy = y + 100 * k;
    g += `<path d="M${r1(x)} ${r1(y + 46 * k)} L${r1(x + sw)} ${r1(yy - 34 * k)}" stroke="#7a4e22" stroke-width="${2 * k}"/>` +
      `<path d="M${r1(x + sw)} ${r1(yy - 34 * k)} L${r1(x + sw + 26 * k)} ${r1(yy)} L${r1(x + sw)} ${r1(yy + 40 * k)} L${r1(x + sw - 26 * k)} ${r1(yy)} Z" fill="${i % 2 ? "#e5484d" : "#f29f05"}" stroke="#ffd36b" stroke-width="${3 * k}"/>` +
      `<circle cx="${r1(x + sw)}" cy="${r1(yy)}" r="${r1(9 * k)}" fill="#fff3b0" opacity="${r1((0.6 + 0.4 * Math.sin(t * 4 + i)) * 100) / 100}"/>`;
  }
  return g;
}
const diyas = (x0, x1, y, k, t) => { let g = ""; for (let x = x0; x <= x1; x += 90 * k) g += `<path d="M${r1(x - 18 * k)} ${r1(y)} Q${r1(x)} ${r1(y + 16 * k)} ${r1(x + 18 * k)} ${r1(y)} Z" fill="#b5652b"/><ellipse cx="${r1(x)}" cy="${r1(y - 10 * k)}" rx="${r1(5 * k)}" ry="${r1((10 + 3 * Math.sin(t * 7 + x)) * k)}" fill="#ffcf4a"/>`; return g; };

// The city's traffic (vehicles: cars on the road, moving) and smog (level 0..1: a haze over the street).
function cityLife(W, H, p, gy) {
  const kk = W / 1920, t = tOf(p), n = Math.round(Math.min(12, nv(p, "vehicles", 0)));
  let g = "";
  for (let j = 0; j < n; j++) { const dir = j % 2 ? -1 : 1, x = ((j * 0.37 * W + t * 160 * kk) % (2.4 * W)) - 1.2 * W;
    g += carG(dir > 0 ? x : -x, gy + H * (dir > 0 ? 0.2 : 0.12), 0.7 * kk, TOPS[(j * 3) % TOPS.length], dir); }
  const lev = isN(p.level) && +p.level >= 0 || wasOf(p).level !== undefined ? c01(nv(p, "level", 0)) : 0;
  if (lev > 0) g += rect(-W, -H / 2, 2 * W, H, "#8d8775", ` opacity="${r1(lev * 0.62 * 100) / 100}"`) + rect(-W, gy - H * 0.3, 2 * W, H * 0.3, "#a39a7e", ` opacity="${r1(lev * 0.35 * 100) / 100}"`);
  return g;
}

const KINDS = {
  market(W, H, p) {
    const gy = H * 0.12, n = countOf(p, 4, 2, 6), signs = signsOf(p), kk = W / 1920, t = tOf(p), stock = hasList(p, "levels");
    const aw = ["#e5484d", "#3a7bd5", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f"];
    let back = "";
    for (let i = -7; i <= 7; i++) { const h = H * (0.22 + ((((i * 7 + 21) % 5) + 5) % 5) * 0.04); back += rect(i * W * 0.14 - W * 0.06, gy - h, W * 0.12, h, i % 2 ? "#e9dcc5" : "#e2d3b8", ' stroke="#cdbb98" stroke-width="3"'); }
    let stalls = "", queues = "";
    for (let i = 0; i < n; i++) {
      const x = -W * 0.42 + (i + 0.5) * (W * 0.84 / n), sw = (W * 0.84 / n) * 0.86, a = aw[i % aw.length], y = gy + H * 0.02;
      let awning = "";
      for (let k = 0; k < 6; k++) { const l = x - sw / 2 + k * sw / 6, r = l + sw / 6;
        awning += `<path d="M${l} ${y - H * 0.3} L${r} ${y - H * 0.3} L${r} ${y - H * 0.24} Q${(l + r) / 2} ${y - H * 0.21} ${l} ${y - H * 0.24} Z" fill="${k % 2 ? "#f7efe2" : a}"/>`; }
      let goods = [0, 1, 2].map((k) => `<circle cx="${x - sw * 0.25 + k * sw * 0.25}" cy="${y - H * 0.08}" r="${sw * 0.07}" fill="${aw[(i + k + 2) % aw.length]}" opacity="0.9"/>`).join("");
      if (stock) {                                           // the stall's unsold stock: a heap that grows or shrinks
        const lev = c01(lv(p, "levels", i, 0.5)), m = Math.round(lev * 15), r = Math.min(sw * 0.075, 18 * kk);
        goods = "";
        for (let j = 0, row = 0, left = m; left > 0; row++) { const per = Math.min(left, Math.max(1, 6 - row));
          for (let c = 0; c < per; c++, j++) goods += `<circle cx="${r1(x + (c - (per - 1) / 2) * r * 2.1)}" cy="${r1(y - H * 0.06 - r - row * r * 1.7)}" r="${r1(r)}" fill="${aw[(i + j + 2) % aw.length]}" stroke="${shade(aw[(i + j + 2) % aw.length], 0.75)}" stroke-width="2"/>`;
          left -= per; }
      }
      const [now, old] = boardOf(p, "prices", i), f = sv(p, "shut", i + 1), q = lv(p, "counts", i, 0);
      stalls += glowBox(x - sw / 2 - 12 * kk, y - H * 0.32, x + sw / 2 + 12 * kk, y + H * 0.01, sv(p, "glow", i + 1), kk) +
        rect(x - sw / 2, y - H * 0.3, 10, H * 0.3, "#8a5a2b") + rect(x + sw / 2 - 10, y - H * 0.3, 10, H * 0.3, "#8a5a2b") +
        rect(x - sw / 2, y - H * 0.06, sw, H * 0.06, "#a9713c", ' stroke="#7a4e22" stroke-width="3"') + awning + goods +
        smallSign(signs[i], x, y - H * 0.17, sw * 0.8, 40) + shutterG(x - sw / 2 + 10, y - H * 0.24, sw - 20, H * 0.24, f, kk) +
        (now ? chalk(x, y - H * 0.062, Math.min(sw * 0.92, 320 * kk), H * 0.066, now, old, { k: kk }) : "");
      for (let j = Math.ceil(q - 1e-6) - 1; j >= 0; j--) queues += fig(x - sw * 0.3 + j * Math.min(34 * kk, sw * 0.6 / Math.max(1, q)), y + H * 0.175 + (j % 2) * H * 0.012, H * 0.16, i * 5 + j, { op: j < Math.floor(q + 1e-6) ? 1 : q - Math.floor(q) });
    }
    const buyers = crowdAt(nv(p, "people", 0), 0, gy + H * 0.23, H * 0.16, 16, { seed: 4 });   // buyers stand clear of the price boards
    return skyGround(W, H, "#cfe8f5", "#eaf4f9", "#d9c288", gy) + cloud(-W * 0.3, -H * 0.36, 1.2) + cloud(W * 0.25, -H * 0.3, 1) + back +
      (p.crowd ? crowdBand(-W, W, gy + H * 0.02, H * 0.09, 3) : "") + stalls +
      `<ellipse cx="0" cy="${H * 0.36}" rx="${W * 0.44}" ry="${H * 0.1}" fill="#cdb67f" opacity="0.4"/>` + buyers + queues +
      festiveG(W, H, p.festive, t, -H * 0.34) + board(p.label, 0, -H * 0.4, W * 0.4, "#8a5a2b");
  },
  bankHall(W, H, p) {
    const gy = H * 0.14, n = countOf(p, 3, 1, 5), signs = signsOf(p), wall = okColor(p.color, "#e8e1d3");
    let win = "";
    for (let i = 0; i < 9; i++) win += rect(-W * 0.86 + i * W * 0.2, -H * 0.42, W * 0.12, H * 0.3, "#cfe3f0", ` rx="${W * 0.01}" stroke="${shade(wall, 0.8)}" stroke-width="6"`);
    let counter = rect(-W * 0.48, gy - H * 0.2, W * 0.62, H * 0.2, "#b98b52", ' stroke="#8a5a2b" stroke-width="4"');
    const cw = W * 0.56 / n;
    for (let i = 0; i < n; i++) {
      const x = -W * 0.42 + i * cw;
      counter += rect(x, gy - H * 0.38, cw - W * 0.02, H * 0.18, "#dfeef7", ' opacity="0.75" stroke="#8a9bb0" stroke-width="4"') +
        smallSign(signs[i], x + (cw - W * 0.02) / 2, gy - H * 0.41, cw - W * 0.04, 40);
    }
    const posts = [0, 1, 2].map((k) => rect(-W * 0.3 + k * W * 0.12, gy + H * 0.12, 8, H * 0.1, "#9aa5b1") + `<circle cx="${-W * 0.3 + k * W * 0.12 + 4}" cy="${gy + H * 0.12}" r="10" fill="#9aa5b1"/>`).join("") +
      `<path d="M${-W * 0.3 + 4} ${gy + H * 0.13} L${-W * 0.06 + 4} ${gy + H * 0.13}" stroke="#d6454f" stroke-width="6"/>`;
    const vx = W * 0.33, r = H * 0.17, vy = gy - r * 1.25;
    let fill = "";                                           // the vault's money (level 0..1): it empties in a run on the bank
    if (p.open === true && (isN(p.level) && +p.level >= 0 || wasOf(p).level !== undefined)) {
      const m = Math.round(c01(nv(p, "level", 0.5)) * 12);
      fill = `<circle cx="${vx}" cy="${vy}" r="${r}" fill="#3b3326"/>` + [...Array(m).keys()].map((j) => rect(vx - r * 0.66 + (j % 3) * r * 0.45, vy + r * 0.62 - Math.floor(j / 3) * r * 0.3, r * 0.4, r * 0.24, "#2fa35b", ' stroke="#1f7a42" stroke-width="3"')).join("");
    }
    const q = nv(p, "people", 0);
    let queue = "";                                          // the queue at the counters, out of the door when it is long
    for (let j = Math.ceil(q - 1e-6) - 1; j >= 0; j--) { const row = Math.floor(j / 18), c = j % 18;
      queue += fig(-W * 0.08 - c * W * 0.042, gy + H * 0.13 + row * H * 0.05, H * 0.17, j, { op: j < Math.floor(q + 1e-6) ? 1 : q - Math.floor(q) }); }
    return wallFloor(W, H, wall, "#d8cbb3", gy) + win + (p.crowd ? crowdBand(-W, -W * 0.5, gy + H * 0.1, H * 0.1, 2) : "") + counter +
      rect(vx - r * 1.25, vy - r * 1.3, r * 2.5, gy - (vy - r * 1.3), "#8e96a1", ` rx="${r * 0.12}"`) + vaultDoor(vx, vy, r, p.open === true, false) + fill + posts + queue +
      board(p.label, -W * 0.17, -H * 0.4, W * 0.4, "#2459a6");
  },
  centralBank(W, H, p) {
    const gy = H * 0.16, wall = okColor(p.color, "#ece6da");
    let cols = "";
    for (let i = -8; i <= 8; i++) if (Math.abs(i) > 1) cols += rect(i * W * 0.11 - W * 0.022, -H * 0.36, W * 0.044, gy + H * 0.36, "#f7f4ee", ' stroke="#cfc6b4" stroke-width="4"') + rect(i * W * 0.11 - W * 0.03, -H * 0.38, W * 0.06, H * 0.03, "#d8d0bf");
    const r = H * 0.2, vy = gy - r * 1.15;
    return wallFloor(W, H, wall, "#d6cdbb", gy) + rect(-W, -H * 0.5, 2 * W, H * 0.12, "#0f6e6e") + cols +
      `<circle cx="0" cy="${-H * 0.44}" r="${H * 0.045}" fill="#f3cf6a" stroke="#c99a2e" stroke-width="5"/>` + text("₹", 0, -H * 0.425, H * 0.05, "#8a6a1c") +
      rect(-r * 1.4, vy - r * 1.25, r * 2.8, gy - (vy - r * 1.25), "#7a838f", ` rx="${r * 0.1}"`) + vaultDoor(0, vy, r, p.open === true, true) +
      board(p.label, 0, -H * 0.345, W * 0.3, "#0f6e6e");
  },
  exchangeFloor(W, H, p) {
    const gy = H * 0.16, up = p.trend !== "down", c = up ? "#2fb463" : "#e5484d";
    const pts = [...Array(9).keys()].map((i) => [-W * 0.3 + i * W * 0.075, -H * 0.24 - (up ? 1 : -1) * (i - 4) * H * 0.02 + ((((i * 37) % 5) + 5) % 5 - 2) * H * 0.01]);
    let ticker = "";
    for (let i = 0; i < 14; i++) {
      const u = (((i * 5) % 4) !== 0) === up, x = -W * 0.34 + i * W * 0.05;
      ticker += rect(x, -H * 0.075, W * 0.032, H * 0.012, "#4a5568") +
        `<path d="M${x + W * 0.036} ${-H * 0.062} l${W * 0.006} ${u ? -H * 0.016 : H * 0.016} l${W * 0.006} ${u ? H * 0.016 : -H * 0.016} Z" fill="${u ? "#2fb463" : "#e5484d"}"/>`;
    }
    let desks = "";
    for (let r = 0; r < 2; r++) for (let i = -3; i <= 3; i++) {
      const x = i * W * 0.13 + r * W * 0.065, y = gy + H * (0.06 + r * 0.13);
      desks += rect(x - W * 0.05, y - H * 0.065, W * 0.1, H * 0.045, "#1f2a33") + rect(x - W * 0.045, y - H * 0.058, W * 0.04, H * 0.032, (i + r) % 2 ? "#2fb463" : "#3a7bd5", ' opacity="0.8"') +
        rect(x + W * 0.005, y - H * 0.058, W * 0.04, H * 0.032, (i + r) % 2 ? "#3a7bd5" : "#e5484d", ' opacity="0.8"') + rect(x - W * 0.06, y - H * 0.02, W * 0.12, H * 0.02, "#4a5568");
    }
    const rows = signsOf(p).slice(0, 5), pts2 = listOf(p.points).filter(isN).map(Number), kk = W / 1920;
    let live = "";
    if (rows.length || pts2.length || p.value) {             // the live board: ticker rows (name:price), an index line, its value
      const oldRows = {};
      listOf(wasOf(p).signs).forEach((r) => { const [nm, v] = r.split(":"); if (nm) oldRows[nm.trim()] = parseFloat(v); });
      const rh = H * 0.3 / 5, fs = Math.min(46 * kk, rh * 0.66), x1 = pts2.length ? -W * 0.02 : W * 0.33;
      rows.forEach((r, i) => {
        const [nm, v = ""] = r.split(":"), yc = -H * 0.36 + (i + 0.5) * rh, before = oldRows[nm.trim()], up = isN(before) && isN(v) ? +v >= before : !(p.trend === "down");
        live += textA(nm.trim(), -W * 0.33, yc + fs * 0.36, fitFs(nm.trim(), W * 0.17, fs), "#e6edf3", 700, "start") + textA(v.trim(), x1 - W * 0.05, yc + fs * 0.36, fitFs(v.trim(), W * 0.1, fs), up ? "#2fb463" : "#e5484d", 800, "end") +
          `<path d="M${r1(x1 - W * 0.035)} ${r1(yc + (up ? fs * 0.25 : -fs * 0.25))} l${r1(fs * 0.3)} ${r1(up ? -fs * 0.55 : fs * 0.55)} l${r1(fs * 0.3)} ${r1(up ? fs * 0.55 : -fs * 0.55)} Z" fill="${up ? "#2fb463" : "#e5484d"}"/>`;
      });
      if (pts2.length) {
        const lo = Math.min(...pts2), hi = Math.max(...pts2), gx0 = rows.length ? W * 0.02 : -W * 0.32, gx1 = W * 0.33, gy0 = -H * 0.3, gy1 = -H * 0.08;
        const xy = pts2.map((v, i) => [r1(gx0 + (pts2.length > 1 ? i / (pts2.length - 1) : 0.5) * (gx1 - gx0)), r1(gy1 - (hi > lo ? (v - lo) / (hi - lo) : 0.5) * (gy1 - gy0))]);
        const rise = pts2[pts2.length - 1] >= pts2[0], col = rise ? "#2fb463" : "#e5484d", e = wasOf(p).points !== undefined ? phase(p) : 1;
        live += `<path d="M${gx0} ${gy1} L${gx1} ${gy1}" stroke="#4a5568" stroke-width="${3 * kk}"/><path d="M${xy.map((q) => q.join(" ")).join(" L")}" pathLength="1" stroke-dasharray="${e.toFixed(3)} 1" fill="none" stroke="${col}" stroke-width="${8 * kk}" stroke-linejoin="round" stroke-linecap="round"/>`;
      }
      if (p.value) live += textA(rollValue(p), W * 0.32, -H * 0.34, 54 * kk, p.trend === "down" ? "#e5484d" : "#2fb463", 800, "end");
    }
    return wallFloor(W, H, "#24303b", "#3a4652", gy) + rect(-W * 0.36, -H * 0.42, W * 0.72, H * 0.38, "#0f171e", ` rx="${W * 0.01}" stroke="#4a5568" stroke-width="6"`) +
      (live || `<path d="M${pts.map((q) => q.join(" ")).join(" L")}" fill="none" stroke="${c}" stroke-width="8" stroke-linejoin="round"/>` + ticker) +
      (p.crowd ? crowdBand(-W, W, gy + H * 0.02, H * 0.08, 5) : "") + crowdAt(nv(p, "people", 0), 0, gy + H * 0.07, H * 0.17, 12, { seed: 2 }) + desks + board(p.label, 0, -H * 0.445, W * 0.36, "#2a9d8f");
  },
  port(W, H, p) {
    const gy = H * 0.1, n = countOf(p, 8, 1, 12), cc = ["#e5484d", "#3a7bd5", "#2fa35b", "#f29f05", "#7b61ff", "#2a9d8f"];
    let cont = "";
    for (let i = 0; i < n; i++) { const col = i % 6, row = Math.floor(i / 6);
      cont += rect(-W * 0.25 + col * W * 0.06, gy - H * 0.13 - row * H * 0.055, W * 0.055, H * 0.05, cc[i % cc.length], ` stroke="${shade(cc[i % cc.length])}" stroke-width="3"`); }
    const ship = `<path d="M${-W * 0.32} ${gy - H * 0.08} L${W * 0.14} ${gy - H * 0.08} L${W * 0.1} ${gy + H * 0.02} L${-W * 0.29} ${gy + H * 0.02} Z" fill="#c0392b" stroke="#7d2a20" stroke-width="4"/>` +
      rect(-W * 0.32, gy - H * 0.08, W * 0.46, H * 0.02, "#2d3748") + rect(W * 0.05, gy - H * 0.22, W * 0.07, H * 0.14, "#f7f4ee", ' stroke="#9aa5b1" stroke-width="3"') + cont;
    const crane = `<g stroke="#f2c14e" stroke-width="10" fill="none"><path d="M${W * 0.3} ${gy + H * 0.06} L${W * 0.3} ${-H * 0.3} L${W * 0.02} ${-H * 0.3}"/><path d="M${W * 0.3} ${-H * 0.22} L${W * 0.22} ${-H * 0.3}"/><path d="M${W * 0.08} ${-H * 0.3} L${W * 0.08} ${-H * 0.2}" stroke-width="5"/></g>` +
      rect(W * 0.06, -H * 0.2, W * 0.045, H * 0.04, cc[(n + 1) % cc.length]);
    let waves = "";
    for (let i = -10; i < 10; i++) waves += `<path d="M${i * W * 0.1} ${gy + H * 0.06} q${W * 0.025} ${-H * 0.012} ${W * 0.05} 0 t${W * 0.05} 0" stroke="#ffffff" stroke-width="3" fill="none" opacity="0.5"/>`;
    return rect(-W, -H / 2, 2 * W, gy + H / 2, "#cfe8f5") + cloud(-W * 0.38, -H * 0.38, 1.1) + rect(-W, gy - H * 0.04, 2 * W, H * 0.16, "#4f8fc0") + waves + ship + crane +
      rect(-W, gy + H * 0.12, 2 * W, H / 2 - gy - H * 0.12, "#b9b2a4") + rect(-W, gy + H * 0.12, 2 * W, 10, "#8a8172") + board(p.label, -W * 0.06, -H * 0.4, W * 0.4, "#1d5e8a");
  },
  factory(W, H, p) {
    const gy = H * 0.12, signs = signsOf(p);
    let sheds = "";
    for (let i = 0; i < 3; i++) {
      const x = -W * 0.42 + i * W * 0.22;
      sheds += rect(x, gy - H * 0.26, W * 0.2, H * 0.26, "#d9d3c6", ' stroke="#a39a88" stroke-width="4"') +
        [0, 1, 2].map((k) => `<path d="M${x + k * W * 0.067} ${gy - H * 0.26} L${x + (k + 0.6) * W * 0.067} ${gy - H * 0.34} L${x + (k + 1) * W * 0.067} ${gy - H * 0.26} Z" fill="#a39a88"/>`).join("") +
        rect(x + W * 0.07, gy - H * 0.12, W * 0.06, H * 0.12, "#6b7280") + smallSign(signs[i], x + W * 0.1, gy - H * 0.19, W * 0.16, 40);
    }
    const kk = W / 1920, t = tOf(p), lev = isN(p.level) && +p.level >= 0 || wasOf(p).level !== undefined ? c01(nv(p, "level", 0.5)) : null;
    let smoke = "";
    if (p.smoke !== false && lev === null) smoke = [0, 1, 2, 3].map((k) => `<circle cx="${W * 0.27 + k * W * 0.03}" cy="${-H * 0.38 - k * H * 0.04}" r="${H * (0.03 + k * 0.012)}" fill="#c7ccd3" opacity="${0.8 - k * 0.15}"/>`).join("");
    else if (p.smoke !== false) {                            // the emission level (0..1) sets the puffs; a filter thins and whitens them
      const amt = lev * (p.filter === true ? 0.35 : 1), m = 2 + Math.round(amt * 7), col = p.filter === true ? "#e3e7ec" : amt > 0.6 ? "#7d7f86" : "#b4b9c1";
      for (let j = 0; j < m; j++) { const u = (t * 0.25 + j / m) % 1;
        smoke += `<circle cx="${r1(W * 0.268 + u * W * 0.12 + Math.sin(j * 2.1 + t) * 10 * kk)}" cy="${r1(-H * 0.37 - u * H * 0.13)}" r="${r1(H * (0.02 + amt * 0.03) * (0.6 + u))}" fill="${col}" opacity="${r1((0.85 - u * 0.6) * 100) / 100}"/>`; }
    }
    const filter = p.filter === true ? rect(W * 0.242, -H * 0.4, W * 0.051, H * 0.05, "#5b7fb8", ` rx="${6 * kk}" stroke="#2d3748" stroke-width="${4 * kk}"`) : "";
    const limit = p.notice ? `<path d="M${W * 0.2} ${-H * 0.3} L${W * 0.33} ${-H * 0.3}" stroke="${lev !== null && lev > 0.6 ? "#e5484d" : "#2d3748"}" stroke-width="${6 * kk}" stroke-dasharray="${16 * kk} ${10 * kk}"/>` + paperNote(W * 0.1, -H * 0.335, p.notice, kk, W * 0.18) : "";
    const rate = isN(p.rate) && +p.rate > 0 ? +p.rate : 0, span = W * 0.44;
    const belt = rect(-W * 0.2, gy + H * 0.08, W * 0.5, H * 0.03, "#4a5568") + [...Array(8).keys()].map((k) => `<circle cx="${-W * 0.19 + k * W * 0.068}" cy="${gy + H * 0.125}" r="${H * 0.014}" fill="#2d3748"/>`).join("") +
      [0, 1, 2, 3].map((k) => rect(-W * 0.16 + ((k * W * 0.11 + t * rate * 220 * kk) % span), gy + H * 0.035, W * 0.05, H * 0.045, "#c8a06a", ' stroke="#8a6d3b" stroke-width="3"')).join("");
    return skyGround(W, H, "#dfe9ef", "#eef3f5", "#c9c4b8", gy) + sheds + rect(W * 0.25, -H * 0.36, W * 0.035, gy + H * 0.36, "#9b4a3a") + filter + smoke + limit + belt +
      counterBox(-W * 0.31, gy + H * 0.03, p, kk, 48) + board(p.label, -W * 0.1, -H * 0.42, W * 0.4, "#4a5568");
  },
  village(W, H, p) {
    const gy = H * 0.1, crop = p.season === "harvest" ? "#d9b34a" : "#8fbf5a";
    let rows = "";
    for (let i = 0; i < 9; i++) rows += `<path d="M${-W} ${gy + H * 0.03 + i * H * 0.04} L${W} ${gy + H * 0.03 + i * H * 0.04}" stroke="${shade(crop, 0.85)}" stroke-width="${6 + i}" opacity="0.6"/>`;
    const k = W / 1920, hut = (x, s) => `<g transform="translate(${x},${gy}) scale(${s * k})">${rect(-90, -100, 180, 100, "#e4cf9f", ' stroke="#bfa871" stroke-width="4"')}<path d="M-110 -100 L0 -170 L110 -100 Z" fill="#c98850" stroke="#a5693a" stroke-width="4"/>${rect(-22, -62, 44, 62, "#8a5a2b")}</g>`;
    const tree = (x, s) => `<g transform="translate(${x},${gy}) scale(${s * k})">${rect(-10, -70, 20, 70, "#8a5a2b")}<circle cx="0" cy="-100" r="56" fill="#9dbb6e"/><circle cx="-42" cy="-74" r="40" fill="#8fae5f"/><circle cx="42" cy="-74" r="40" fill="#a8c47e"/></g>`;
    const well = `<g transform="translate(${W * 0.28},${gy + H * 0.02}) scale(${k})">${rect(-40, -50, 80, 50, "#b9b2a4", ' stroke="#8a8172" stroke-width="4"')}<path d="M-46 -90 L46 -90" stroke="#8a5a2b" stroke-width="8"/><path d="M-40 -90 L-40 -50 M40 -90 L40 -50" stroke="#8a5a2b" stroke-width="6"/></g>`;
    return skyGround(W, H, "#cfe8f5", "#eaf4f9", crop, gy) + `<circle cx="${W * 0.36}" cy="${-H * 0.36}" r="${H * 0.07}" fill="#ffd95a"/>` + cloud(-W * 0.2, -H * 0.34, 1.2) + rows +
      hut(-W * 0.36, 1) + hut(-W * 0.18, 0.72) + hut(-W * 0.8, 0.9) + tree(W * 0.12, 1.1) + tree(W * 0.42, 0.85) + tree(W * 0.75, 1) + well + board(p.label, 0, -H * 0.4, W * 0.4, "#8a5a2b");
  },
  office(W, H, p) {
    const gy = H * 0.14, n = countOf(p, 5, 1, 6), signs = signsOf(p), wall = okColor(p.color, "#eef1f4");
    let view = "";
    for (let i = 0; i < 5; i++) {
      const x = -W * 0.72 + i * W * 0.3;
      view += rect(x, -H * 0.4, W * 0.24, H * 0.36, "#cfe3f0", ' stroke="#a9b6c4" stroke-width="8"') +
        [0, 1, 2, 3].map((k) => rect(x + W * 0.02 + k * W * 0.055, -H * 0.4 + H * (0.12 + (k % 2) * 0.06), W * 0.04, H * (0.24 - (k % 2) * 0.06), "#9fb4c8")).join("");
    }
    let desks = "";
    for (let i = 0; i < n; i++) {
      const x = (i - (n - 1) / 2) * W * 0.2;
      desks += rect(x - W * 0.08, gy + H * 0.04, W * 0.16, H * 0.03, "#b98b52") + rect(x - W * 0.07, gy + H * 0.07, 8, H * 0.08, "#8a5a2b") + rect(x + W * 0.07, gy + H * 0.07, 8, H * 0.08, "#8a5a2b") +
        rect(x - W * 0.03, gy - H * 0.02, W * 0.06, H * 0.06, "#2d3748", ' rx="6"') + smallSign(signs[i], x, gy - H * 0.05, W * 0.15, 36);
    }
    return wallFloor(W, H, wall, "#d5dbe1", gy) + view + desks + board(p.label, 0, -H * 0.45, W * 0.4, "#5b7fb8");
  },
  court(W, H, p) {
    const gy = H * 0.16, wall = okColor(p.color, "#e9dcc7"), s = H * 0.12;
    const scale = `<g transform="translate(0,${-H * 0.33})" stroke="#c99a2e" stroke-width="8" fill="none"><path d="M0 ${-s * 0.6} L0 ${s * 0.6} M${-s} ${-s * 0.4} L${s} ${-s * 0.4}"/>` +
      `<path d="M${-s * 1.3} ${s * 0.25} Q${-s} ${s * 0.6} ${-s * 0.7} ${s * 0.25} M${s * 0.7} ${s * 0.25} Q${s} ${s * 0.6} ${s * 1.3} ${s * 0.25}"/>` +
      `<path d="M${-s} ${-s * 0.4} L${-s * 1.25} ${s * 0.25} M${-s} ${-s * 0.4} L${-s * 0.75} ${s * 0.25} M${s} ${-s * 0.4} L${s * 0.75} ${s * 0.25} M${s} ${-s * 0.4} L${s * 1.25} ${s * 0.25}"/></g>`;
    let benches = "";
    for (let i = -2; i <= 2; i++) if (i) benches += rect(i * W * 0.26 - W * 0.09, gy + H * 0.08, W * 0.18, H * 0.04, "#8a5a2b") + rect(i * W * 0.26 - W * 0.09, gy + H * 0.12, W * 0.18, H * 0.02, "#5e3b17");
    return wallFloor(W, H, wall, "#c9b48f", gy) + rect(-W, -H * 0.5, 2 * W, H * 0.06, "#7a4e22") +
      rect(-W * 0.3, gy - H * 0.24, W * 0.6, H * 0.24, "#8a5a2b", ' stroke="#5e3b17" stroke-width="5"') + rect(-W * 0.32, gy - H * 0.27, W * 0.64, H * 0.04, "#6b4422") +
      rect(-W * 0.05, gy - H * 0.36, W * 0.1, H * 0.1, "#5e3b17", ' rx="8"') + scale +
      rect(-W * 0.46, gy - H * 0.12, W * 0.1, H * 0.12, "#a8763f") + rect(W * 0.36, gy - H * 0.12, W * 0.1, H * 0.12, "#a8763f") + benches +
      board(p.label, 0, -H * 0.15, W * 0.3, "#5e3b17");
  },
  city(W, H, p) {
    const gy = H * 0.18, signs = signsOf(p);
    let b = "";
    for (let i = -9; i <= 9; i++) {
      const h = H * (0.22 + ((((i * 53 + 31) % 7) + 7) % 7) * 0.05), x = i * W * 0.1, c = ["#c9d3dd", "#d8dee5", "#bcc7d2", "#e2e6ea"][((i % 4) + 4) % 4];
      b += rect(x - W * 0.045, gy - h, W * 0.09, h, c, ' stroke="#a9b6c4" stroke-width="3"');
      for (let r = 0; r < Math.floor(h / (H * 0.06)); r++) b += rect(x - W * 0.032, gy - h + H * 0.025 + r * H * 0.06, W * 0.02, H * 0.03, "#f2e7b0", ' opacity="0.8"') + rect(x + W * 0.012, gy - h + H * 0.025 + r * H * 0.06, W * 0.02, H * 0.03, "#f2e7b0", ' opacity="0.8"');
    }
    const shops = [-0.3, 0, 0.3].map((f, i) => smallSign(signs[i], f * W, gy - H * 0.05, W * 0.08, 34)).join("");
    return rect(-W, -H / 2, 2 * W, gy + H / 2, "#d6e8f3") + cloud(W * 0.3, -H * 0.4, 1) + b + shops + rect(-W, gy, 2 * W, H / 2 - gy, "#7d8590") +
      [...Array(16).keys()].map((i) => rect(-W + i * W * 0.13, gy + H * 0.14, W * 0.06, 8, "#f2f2f2")).join("") + rect(-W, gy, 2 * W, H * 0.04, "#b9b2a4") +
      (p.crowd ? crowdBand(-W, W, gy + H * 0.04, H * 0.08, 7) : "") + cityLife(W, H, p, gy) + board(p.label, 0, -H * 0.42, W * 0.4, "#4a5568");
  },
  assembly(W, H, p) {
    const gy = H * 0.16, wall = okColor(p.color, "#efe7da"), cols = ["#2fa35b", "#3a7bd5", "#e07b24", "#7b61ff"];
    let tiers = "";
    for (let r = 3; r >= 0; r--) {
      const rx = W * (0.34 + r * 0.1), ry = H * (0.16 + r * 0.075), cy = gy + H * 0.02, a0 = -2.25, a1 = -0.89;
      const pt = (a) => `${(Math.cos(a) * rx).toFixed(1)} ${(cy + Math.sin(a) * ry).toFixed(1)}`;
      tiers += `<path d="M${pt(a0)} A${rx} ${ry} 0 0 1 ${pt(a1)}" fill="none" stroke="${shade(cols[r], 0.75)}" stroke-width="${H * 0.05}"/>` +
        `<path d="M${pt(a0)} A${rx} ${ry} 0 0 1 ${pt(a1)}" fill="none" stroke="${cols[r]}" stroke-width="${H * 0.03}" stroke-dasharray="${W * 0.018} ${W * 0.008}"/>`;
    }
    return wallFloor(W, H, wall, "#d8c8a8", gy) + `<path d="M${-W * 0.7} ${-H * 0.5} Q0 ${-H * 0.75} ${W * 0.7} ${-H * 0.5} Z" fill="#e07b24" opacity="0.2"/>` + tiers +
      rect(-W * 0.09, gy - H * 0.17, W * 0.18, H * 0.17, "#8a5a2b", ' stroke="#5e3b17" stroke-width="4"') + rect(-W * 0.1, gy - H * 0.19, W * 0.2, H * 0.03, "#6b4422") +
      board(p.label, 0, -H * 0.42, W * 0.3, "#e07b24");
  },
  twoCountries(W, H, p) {
    const gy = H * 0.08, signs = signsOf(p), k = W / 1920;
    const houses = (x0, dir, c) => [0, 1, 2, 3].map((i) => { const x = x0 + dir * i * W * 0.08, hh = H * (0.08 + ((i * 7) % 3) * 0.03);
      return rect(x - W * 0.03, gy - hh, W * 0.06, hh, c, ' stroke="#b9ad90" stroke-width="3"') + `<path d="M${x - W * 0.035} ${gy - hh} L${x} ${gy - hh - H * 0.04} L${x + W * 0.035} ${gy - hh} Z" fill="${shade(c, 0.8)}"/>`; }).join("");
    let road = rect(-W, gy + H * 0.16, 2 * W, H * 0.07, "#8d8a84");
    for (let i = -12; i < 12; i++) road += rect(i * W * 0.09, gy + H * 0.192, W * 0.04, 6 * k, "#f2f2f2");
    const gate = `<g transform="translate(0,${gy + H * 0.16})">${rect(-W * 0.012, -H * 0.12, W * 0.024, H * 0.12, "#6b7280")}<path d="M${W * 0.012} ${-H * 0.1} L${W * 0.11} ${-H * 0.1}" stroke="#e5484d" stroke-width="${10 * k}" stroke-dasharray="${18 * k} ${14 * k}"/></g>`;
    return rect(-W, -H / 2, 2 * W, gy + H / 2, "#d6e8f3") + cloud(-W * 0.3, -H * 0.36, 1.1 * k) + cloud(W * 0.3, -H * 0.3, 1 * k) +
      rect(-W, gy, W, H / 2 - gy, "#dcc58f") + rect(0, gy, W, H / 2 - gy, "#bfd79a") + houses(-W * 0.15, -1, "#f1e3c6") + houses(W * 0.15, 1, "#e6eef5") +
      `<path d="M0 ${-H * 0.2} L0 ${H / 2}" stroke="#4a5568" stroke-width="${8 * k}" stroke-dasharray="${26 * k} ${18 * k}"/>` + road + gate +
      board(signs[0], -W * 0.25, gy + H * 0.34, W * 0.3, "#8a5a2b") + board(signs[1], W * 0.25, gy + H * 0.34, W * 0.3, "#2459a6") + board(p.label, 0, -H * 0.4, W * 0.4, "#4a5568");
  },
  forexCounter(W, H, p) {
    const gy = H * 0.14, wall = okColor(p.color, "#e6edf2"), rows = signsOf(p).slice(0, 4), k = W / 1920;
    let boardRows = "";
    rows.forEach((r, i) => { boardRows += text(r, W * 0.2, -H * 0.3 + i * H * 0.075, Math.min(H * 0.05, (W * 0.3) / Math.max(1, r.length) * 1.7), "#f2c14e", 800); });
    if (!rows.length) for (let i = 0; i < 3; i++) boardRows += rect(W * 0.07, -H * 0.33 + i * H * 0.075, W * 0.26, H * 0.03, "#f2c14e", ' opacity="0.5"');
    const stacks = ["#6cbf7f", "#7aa6d8", "#d9a46a", "#b58ad6"].map((c, i) => [0, 1, 2].map((j) =>
      rect(-W * 0.38 + i * W * 0.08, gy - H * 0.22 - j * H * 0.018, W * 0.06, H * 0.016, c, ` stroke="${shade(c)}" stroke-width="2"`)).join("")).join("");
    return wallFloor(W, H, wall, "#d5dbe1", gy) + rect(W * 0.05, -H * 0.42, W * 0.3, H * 0.34, "#1f2a33", ` rx="${12 * k}" stroke="#4a5568" stroke-width="${6 * k}"`) + boardRows +
      rect(-W * 0.46, gy - H * 0.2, W * 0.5, H * 0.2, "#7a8fa3", ' stroke="#55687b" stroke-width="4"') + rect(-W * 0.44, gy - H * 0.46, W * 0.46, H * 0.24, "#dfeef7", ' opacity="0.7" stroke="#8a9bb0" stroke-width="4"') + stacks +
      (p.crowd ? crowdBand(W * 0.05, W, gy + H * 0.1, H * 0.1, 4) : "") + board(p.label, -W * 0.21, -H * 0.4, W * 0.36, "#2a9d8f");
  },
  // ---- the Sloman book's places (5 Nov 2026): each one's state is its parameters, changed by steps on the cue word
  mandi(W, H, p) {
    const k = W / 1920, gy = H * 0.1, t = tOf(p), n = countOf(p, 3, 1, 5), signs = signsOf(p);
    let g = skyGround(W, H, "#d3e9f4", "#eef5f7", "#cbc3b2", gy) + cloud(-W * 0.62, -H * 0.4, 1.1 * k) + cloud(W * 0.6, -H * 0.36, k);
    g += rect(-W, -H * 0.24, 2 * W, gy + H * 0.24, "#eadfc8") + rect(-W, gy - H * 0.05, 2 * W, H * 0.05, "#d8c8a6") + rect(-W, -H * 0.3, 2 * W, H * 0.06, "#9aa5b1");
    for (let i = -40; i <= 40; i++) g += `<path d="M${r1(i * W * 0.025)} ${r1(-H * 0.3)} L${r1(i * W * 0.025)} ${r1(-H * 0.24)}" stroke="#7f8a96" stroke-width="${3 * k}"/>`;
    for (let i = -5; i <= 5; i++) g += rect(i * W * 0.2 - 7 * k, -H * 0.24, 14 * k, gy + H * 0.24, "#6b7280");
    const goods = nv(p, "goods", 18), each = goods / n;
    g += crowdAt(nv(p, "people", 8), 0, gy + H * 0.06, H * 0.16, 12, { seed: 1, t });           // buyers: the demand
    const nc = Math.min(12, nv(p, "vehicles", 1));                                                 // carts rolling in
    for (let j = Math.ceil(nc - 1e-6) - 1; j >= 0; j--) {
      const f = j < Math.floor(nc + 1e-6) ? 1 : nc - Math.floor(nc), x = -W * 0.38 - j * W * 0.17 - (1 - f) * W * 0.5, y = gy + H * 0.17;
      g += cartG(x, y, 1.15 * k, "#a9713c", 1) + heapG(3, x - 50 * k, y - 116 * k, 0.85 * k, { col: "#d2a96a" });
    }
    if (p.notice) {                                                                                 // the government truck takes the heap
      const tx = W * 0.36, ty = gy + H * 0.05;
      g += truckG(tx, ty, 0.95 * k, "#2a7a5a", -1) + heapG(nv(p, "taken", 0), tx + 70 * k, ty - 150 * 0.95 * k, 0.7 * k, { col: "#d2a96a" });
      g += paperNote(W * 0.3, -H * 0.21, p.notice, k, W * 0.28);
    }
    for (let i = 0; i < n; i++) {                                                                   // the heaps: the supply
      const x = (i - (n - 1) / 2) * W * 0.22, y = gy + H * 0.16, m = hasList(p, "counts") ? lv(p, "counts", i, each) : each, gl = sv(p, "glow", i + 1, `heap${i + 1}`);
      let base = 1;
      while ((base * (base + 1)) / 2 < Math.ceil(m)) base++;
      const hs = Math.min(1, 6.2 / Math.max(base, 1)) * k;
      if (gl > 0.01) g += `<ellipse cx="${r1(x)}" cy="${r1(y - base * 20 * hs)}" rx="${r1(base * 30 * hs + 40 * k)}" ry="${r1(base * 24 * hs + 30 * k)}" fill="#f2c14e" opacity="${r1(gl * 0.4 * 100) / 100}"/>`;
      g += heapG(m, x, y, hs, { glow: gl > 0.5, col: "#d2a96a" }) + smallSign(signs[i], x, y - base * 40 * hs - 40 * k, W * 0.16, 40);
    }
    const [now, old] = boardOf(p, "prices", 0);
    g += chalk(0, -H * 0.22, W * 0.3, H * 0.16, now, old, { k, trend: p.trend === "up" || p.trend === "down" ? p.trend : "" });
    return g + board(p.label, 0, -H * 0.4, W * 0.4, "#8a5a2b");
  },
  foodStreet(W, H, p) {
    const k = W / 1920, gy = H * 0.1, t = tOf(p), n = countOf(p, 5, 1, 12), signs = signsOf(p), night = p.light === "night" || p.light === "evening";
    let g = skyGround(W, H, "#cfe3ef", "#eef4f6", "#cbb991", gy);
    for (let i = -9; i <= 9; i++) { const h = H * (0.24 + ((((i * 5 + 17) % 4) + 4) % 4) * 0.05), x = i * W * 0.11;
      g += rect(x - W * 0.05, gy - h, W * 0.1, h, ["#e8d8bd", "#dccbb0", "#e9dcc8"][((i % 3) + 3) % 3], ' stroke="#c7b493" stroke-width="3"');
      for (let r = 0; r < 3; r++) g += rect(x - W * 0.03, gy - h + H * (0.04 + r * 0.07), W * 0.022, H * 0.035, night ? "#ffd76a" : "#cfe3f0") + rect(x + W * 0.008, gy - h + H * (0.04 + r * 0.07), W * 0.022, H * 0.035, night ? "#ffd76a" : "#cfe3f0"); }
    g += rect(-W, gy, 2 * W, H * 0.03, "#b9a77f");
    const span = W * 0.92, sp = span / n, cw = Math.min(sp * 0.86, W * 0.2), seats = Math.round(Math.max(0, Math.min(4, isN(p.seats) && +p.seats >= 0 ? +p.seats : 2)));
    let front = "";
    for (let i = 0; i < n; i++) {
      const x = -span / 2 + (i + 0.5) * sp, y = gy + H * 0.06, col = TOPS[(i * 3 + 1) % TOPS.length], shut = sv(p, "shut", i + 1);
      let c = glowBox(x - cw / 2 - 10 * k, y - H * 0.32, x + cw / 2 + 10 * k, y + H * 0.02, sv(p, "glow", i + 1), k);
      c += rect(x - 4 * k, y - H * 0.3, 8 * k, H * 0.2, "#6b5a45");                                        // the canopy on its pole
      c += `<path d="M${r1(x - cw * 0.6)} ${r1(y - H * 0.22)} L${r1(x - cw * 0.45)} ${r1(y - H * 0.31)} L${r1(x + cw * 0.45)} ${r1(y - H * 0.31)} L${r1(x + cw * 0.6)} ${r1(y - H * 0.22)} Z" fill="${col}"/>` +
        rect(x - cw * 0.6, y - H * 0.235, cw * 1.2, H * 0.05, "#fbf6ea", ` stroke="${shade(col, 0.8)}" stroke-width="${3 * k}"`) + smallSign(signs[i], x, y - H * 0.2, cw * 1.1, 40);
      c += rect(x - cw / 2, y - H * 0.11, cw, H * 0.09, shade(col, 0.75), ` rx="${8 * k}"`) + rect(x - cw / 2 - 6 * k, y - H * 0.12, cw + 12 * k, H * 0.018, "#8a5a2b");
      const kinds = ["samosa", "jalebi", "roti", "tea", "mithai", "bread"];
      for (let j = 0; j < 4; j++) c += itemG(kinds[(i + j) % kinds.length], x - cw * 0.33 + j * cw * 0.22, y - H * 0.122, Math.min(0.8 * k, cw / 300), j);
      if (shut < 0.5) c += [0, 1].map((j) => { const u = (t * 0.5 + j * 0.5 + i * 0.13) % 1; return `<circle cx="${r1(x - cw * 0.2 + j * cw * 0.3 + Math.sin(t * 2 + j) * 6 * k)}" cy="${r1(y - H * 0.16 - u * H * 0.06)}" r="${r1((8 + u * 10) * k)}" fill="#ffffff" opacity="${r1((0.6 - u * 0.6) * 100) / 100}"/>`; }).join("");
      if (night || p.festive) c += [-0.4, -0.13, 0.13, 0.4].map((d, j) => `<circle cx="${r1(x + d * cw)}" cy="${r1(y - H * 0.24)}" r="${r1(7 * k)}" fill="${["#ffd36b", "#fff3b0"][j % 2]}" opacity="${r1((0.7 + 0.3 * Math.sin(t * 3 + i + j)) * 100) / 100}"/>`).join("");
      c += [0, 1].map((w) => `<circle cx="${r1(x + (w ? 0.36 : -0.36) * cw)}" cy="${r1(y - H * 0.018)}" r="${r1(H * 0.018)}" fill="#2d3748"/>`).join("");
      const [now, old] = boardOf(p, "prices", i);
      if (now) c += chalk(x, y - H * 0.385, Math.min(cw * 1.05, 300 * k), H * 0.066, now, old, { k });   // the price board stands on the canopy
      c += shut > 0.002 ? `<path d="M${r1(x - cw * 0.58)} ${r1(y - H * 0.22)} L${r1(x + cw * 0.58)} ${r1(y - H * 0.22)} L${r1(x + cw * 0.55)} ${r1(y - H * 0.22 + shut * H * 0.22)} L${r1(x - cw * 0.55)} ${r1(y - H * 0.22 + shut * H * 0.22)} Z" fill="#5b6f86" opacity="0.96"/>` : "";
      g += c;
      const occ = c01(lv(p, "levels", i, 0.5)) * seats, q = lv(p, "counts", i, 0);           // stools (some taken) and the queue
      for (let j = 0; j < seats; j++) { const sx = x - (seats - 1) * 0.5 * Math.min(cw * 0.3, 70 * k) + j * Math.min(cw * 0.3, 70 * k), sy = y + H * 0.09, on = c01(occ - j);
        front += (on < 0.5 && inSet(p.glow, 0, "seats") ? `<ellipse cx="${r1(sx)}" cy="${r1(sy - H * 0.035)}" rx="${r1(26 * k)}" ry="${r1(14 * k)}" fill="#f2c14e" opacity="0.7"/>` : "") +
          rect(sx - 4 * k, sy - H * 0.03, 8 * k, H * 0.03, "#6b5a45") + `<ellipse cx="${r1(sx)}" cy="${r1(sy - H * 0.032)}" rx="${r1(18 * k)}" ry="${r1(7 * k)}" fill="#c0392b"/>` +
          (on > 0.01 ? fig(sx, sy - H * 0.03, H * 0.14, i * 4 + j, { pose: "sit", op: on }) : ""); }
      for (let j = Math.ceil(q - 1e-6) - 1; j >= 0; j--) front += fig(x + cw * 0.42 + j * 22 * k, y + H * 0.13 + j * H * 0.02, H * 0.16, i * 7 + j + 2, { op: j < Math.floor(q + 1e-6) ? 1 : q - Math.floor(q) });
    }
    return g + crowdAt(nv(p, "people", 0), 0, gy + H * 0.22, H * 0.16, 14, { seed: 6, t }) + front + festiveG(W, H, p.festive, t, -H * 0.36) + board(p.label, 0, -H * 0.42, W * 0.4, "#c0392b");
  },
  labourChowk(W, H, p) {
    const k = W / 1920, gy = H * 0.1, t = tOf(p);
    let g = skyGround(W, H, "#f3dcc8", "#fbeee2", "#d6c49a", gy);
    for (let i = -10; i <= 10; i++) { const x = i * W * 0.13;                                 // closed shops behind the corner
      g += rect(x - W * 0.06, -H * 0.27, W * 0.12, gy + H * 0.23, ["#e6d6bb", "#ddcdb1", "#eadcc4"][((i % 3) + 3) % 3], ' stroke="#c4b08e" stroke-width="3"') + shutterG(x - W * 0.045, -H * 0.17, W * 0.09, gy + H * 0.13, 1, k); }
    g += rect(-W, gy - H * 0.04, 2 * W, H * 0.04, "#bfae8a");
    const sx = -W * 0.38;                                                                           // a tea stall, open since dawn
    g += rect(sx - W * 0.06, -H * 0.17, W * 0.12, gy + H * 0.13, "#6b4a26") + rect(sx - W * 0.07, -H * 0.2, W * 0.14, H * 0.04, "#d96a2b") + rect(sx - W * 0.06, gy - H * 0.1, W * 0.12, H * 0.06, "#a9713c") +
      `<path d="M${r1(sx - 20 * k)} ${r1(gy - H * 0.1)} L${r1(sx - 14 * k)} ${r1(gy - H * 0.15)} L${r1(sx + 14 * k)} ${r1(gy - H * 0.15)} L${r1(sx + 20 * k)} ${r1(gy - H * 0.1)} Z" fill="#c7ccd3"/>` +
      [0, 1, 2].map((j) => { const u = (t * 0.4 + j / 3) % 1; return `<circle cx="${r1(sx + Math.sin(t + j) * 8 * k)}" cy="${r1(gy - H * 0.16 - u * H * 0.1)}" r="${r1((8 + u * 14) * k)}" fill="#ffffff" opacity="${r1((0.7 - u * 0.7) * 100) / 100}"/>`; }).join("");
    const bar = sv(p, "shut", 1, "road");                                                           // the entry road closed
    if (bar > 0.01) g += `<g opacity="${r1(bar * 100) / 100}">` + [-0.47, -0.27].map((f) => `<path d="M${r1(f * W - 30 * k)} ${r1(gy + H * 0.02)} L${r1(f * W)} ${r1(gy - H * 0.08)} L${r1(f * W + 30 * k)} ${r1(gy + H * 0.02)}" stroke="#4a5568" stroke-width="${8 * k}" fill="none"/>`).join("") +
      rect(-W * 0.49, gy - H * 0.1 - (1 - bar) * H * 0.1, W * 0.24, H * 0.035, "#e5484d") + [0, 1, 2, 3, 4, 5].map((j) => rect(-W * 0.49 + j * W * 0.04, gy - H * 0.1 - (1 - bar) * H * 0.1, W * 0.02, H * 0.035, "#ffffff")).join("") + `</g>`;
    const [now, old] = boardOf(p, "prices", 0), bx = W * 0.08;                                      // the wage board on its pole
    g += rect(bx - 6 * k, -H * 0.13, 12 * k, gy + H * 0.25, "#6b7280") + chalk(bx, -H * 0.3, W * 0.22, H * 0.17, now, old, { k });
    const nT = Math.round(Math.max(0, Math.min(3, nv(p, "vehicles", 1)))), ts = 1.2 * k, ty = gy + H * 0.13, tv = nv(p, "taken", 0), cap = 6;
    const bedAt = (m) => { const j = Math.min(nT - 1, Math.floor(m / cap)), q = m - j * cap, X = W * 0.3 + j * W * 0.42, row = Math.floor(q / 3), col = q % 3;
      return [X - 70 * ts + (col + 0.5) * (275 * ts / 3) + row * 40 * k, ty - 50 * ts - row * 14 * k, row]; };
    for (let j = 0; j < nT; j++) {
      const X = W * 0.3 + j * W * 0.42;
      g += fig(X - 250 * ts, ty + H * 0.03, H * 0.21, 9, { col: "#f5f2ea", bot: "#e3ddcf", hat: "#ffffff" });  // the contractor
      const on = Math.max(0, Math.min(cap, Math.floor(tv + 1e-6) - j * cap)), men = [];
      for (let m = 0; m < on; m++) { const [x, y, row] = bedAt(j * cap + m); men.push([row, fig(x, y, H * 0.2, 20 + j * cap + m)]); }
      men.sort((a, b) => b[0] - a[0]);
      g += men.map((m) => m[1]).join("") + truckG(X, ty, ts, "#c0392b", -1);
    }
    const whole = Math.floor(tv + 1e-6), fr = tv - whole;
    for (let m = nT * cap; m < whole; m++) g += fig(W * 0.3 + (nT - 1) * W * 0.42 + 160 * k + (m - nT * cap) * 30 * k, ty + H * 0.03, H * 0.17, 20 + m);
    if (nT && fr > 0.002) { const [x1, y1] = whole < nT * cap ? bedAt(whole) : [W * 0.4, ty], x0 = -W * 0.02, y0 = gy + H * 0.15, e = fr;
      g += fig(x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, H * (0.19 + 0.01 * e), 20 + whole, { pose: "walk", t }); }
    g += crowdAt(nv(p, "people", 14), -W * 0.2, gy + H * 0.15, H * 0.19, 7, { tool: true, t });
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#8a5a2b");
  },
  factoryFloor(W, H, p) {
    const k = W / 1920, gy = H * 0.06, t = tOf(p), n = countOf(p, 4, 1, 8), signs = signsOf(p), item = p.item && p.item !== "auto" ? p.item : "box";
    const style = item === "shirt" ? "sew" : item === "cloth" ? "loom" : "press", run = Math.max(0, Math.min(n, nv(p, "running", n))), strain = c01(nv(p, "level", 0));
    let g = wallFloor(W, H, "#e6e1d5", "#cbc5b7", gy);
    for (let i = -9; i <= 9; i++) g += rect(i * W * 0.11 - W * 0.04, -H * 0.46, W * 0.08, H * 0.1, "#cfe3f0", ` stroke="#a9b6c4" stroke-width="${5 * k}"`);
    g += `<path d="M${-W} ${-H * 0.34} L${W} ${-H * 0.34}" stroke="#8d96a0" stroke-width="${8 * k}"/>`;
    const people = nv(p, "people", Math.round(run)), ops = Math.min(people, run), slot = W * 0.58 / n, base = gy + H * 0.14, ms = Math.min(slot * 0.8 / 240, 1.15 * k);
    for (let i = 0; i < n; i++) {
      const mx = -W * 0.46 + (i + 0.5) * slot, on = c01(run - i), op = c01(ops - i), L = (a) => a.map(r1).join(" "), body = on > 0.5 ? "#5b7fb8" : "#9aa5b1";
      if (on > 0.01 && strain > 0.01) g += `<ellipse cx="${r1(mx)}" cy="${r1(base - 70 * ms)}" rx="${r1(150 * ms)}" ry="${r1(110 * ms)}" fill="#ff5a3c" opacity="${r1(strain * 0.45 * on * 100) / 100}"/>`;
      const bob = on > 0.5 ? Math.abs(Math.sin(t * 5 + i)) : 0;
      if (style === "sew") {
        if (op > 0.01) g += fig(mx, base - 4 * k, H * 0.15, i, { pose: "sit", op, sweat: strain > 0.5, t });
        g += rect(mx - 110 * ms, base - 108 * ms, 220 * ms, 14 * ms, "#a9713c") + rect(mx - 100 * ms, base - 94 * ms, 10 * ms, 94 * ms, "#6b4a26") + rect(mx + 90 * ms, base - 94 * ms, 10 * ms, 94 * ms, "#6b4a26") +
          `<path d="M${L([mx - 60 * ms, base - 108 * ms])} L${L([mx - 60 * ms, base - 160 * ms])} L${L([mx + 50 * ms, base - 160 * ms])} L${L([mx + 50 * ms, base - 128 * ms])}" stroke="${body}" stroke-width="${r1(22 * ms)}" fill="none" stroke-linejoin="round"/>` +
          rect(mx + 46 * ms, base - 128 * ms + bob * 10 * ms, 6 * ms, 18 * ms, "#2d3748") + itemG("cloth", mx + 10 * ms, base - 108 * ms, ms * 0.9, i);
      } else if (style === "loom") {
        if (op > 0.01) g += fig(mx + 125 * ms, base, H * 0.17, i, { pose: "work", op, sweat: strain > 0.5, t });
        g += rect(mx - 110 * ms, base - 170 * ms, 220 * ms, 170 * ms, "none", ` stroke="#8a5a2b" stroke-width="${r1(12 * ms)}"`) +
          [...Array(9).keys()].map((j) => `<path d="M${L([mx - 90 * ms + j * 22 * ms, base - 160 * ms])} L${L([mx - 90 * ms + j * 22 * ms, base - 40 * ms])}" stroke="#d8cfae" stroke-width="${r1(3 * ms)}"/>`).join("") +
          rect(mx - 95 * ms + (on > 0.5 ? (Math.sin(t * 3 + i) * 0.5 + 0.5) * 150 * ms : 0), base - 110 * ms, 40 * ms, 14 * ms, body) + rect(mx - 100 * ms, base - 40 * ms, 200 * ms, 30 * ms, TOPS[(i + 2) % TOPS.length], ` rx="${r1(14 * ms)}"`);
      } else {
        if (op > 0.01) g += fig(mx + 125 * ms, base, H * 0.17, i, { pose: "work", op, sweat: strain > 0.5, t });
        g += rect(mx - 100 * ms, base - 110 * ms, 200 * ms, 110 * ms, body, ` rx="${r1(10 * ms)}" stroke="${shade(body, 0.7)}" stroke-width="${r1(5 * ms)}"`) + rect(mx - 12 * ms, base - 200 * ms, 24 * ms, 70 * ms, "#6b7280") +
          rect(mx - 60 * ms, base - 150 * ms + bob * 26 * ms, 120 * ms, 34 * ms, shade(body, 0.8), ` rx="${r1(6 * ms)}"`) + rect(mx - 120 * ms, base - 210 * ms, 240 * ms, 18 * ms, "#4a5568");
      }
      if (on < 0.99) g += `<path d="M${L([mx - 118 * ms, base])} L${L([mx - 104 * ms, base - 186 * ms])} Q${L([mx, base - 236 * ms])} ${L([mx + 104 * ms, base - 186 * ms])} L${L([mx + 118 * ms, base])} Z" fill="#b8bec6" opacity="${r1((1 - on) * 0.85 * 100) / 100}"/>`;
      g += `<circle cx="${r1(mx - 80 * ms)}" cy="${r1(base - 220 * ms)}" r="${r1(13 * ms)}" fill="${on > 0.5 ? "#3ddc84" : "#e5484d"}" stroke="#2d3748" stroke-width="${r1(3 * ms)}"/>`;
      if (on > 0.5 && strain > 0.7) g += [0, 1, 2].map((j) => { const u = (t * 0.6 + j / 3) % 1; return `<circle cx="${r1(mx + Math.sin(t + j) * 12 * k)}" cy="${r1(base - 230 * ms - u * H * 0.12)}" r="${r1((10 + u * 18) * k)}" fill="#8d8f96" opacity="${r1((0.7 - u * 0.7) * 100) / 100}"/>`; }).join("");
      g += smallSign(signs[i], mx, base + H * 0.035, Math.min(slot * 0.9, W * 0.15), 38);
    }
    g += crowdAt(Math.max(0, people - ops), W * 0.2, base, H * 0.17, 3, { seed: 30, t });          // workers with no machine stand by
    const bx0 = -W * 0.47, bx1 = W * 0.3, by = gy + H * 0.22, len = bx1 - bx0, gap = W * 0.09, speed = (run / n) * (90 + 150 * strain) * k;
    g += rect(bx0, by, len, H * 0.025, "#4a5568") + [...Array(12).keys()].map((j) => `<circle cx="${r1(bx0 + 20 * k + j * len / 12)}" cy="${r1(by + H * 0.035)}" r="${r1(H * 0.012)}" fill="#2d3748"/>`).join("");
    for (let j = 0; j < Math.floor(len / gap); j++) g += itemG(item, bx0 + ((((j * gap + t * speed) % len) + len) % len), by, 1.05 * k, j);
    const gx0 = W * 0.29, gx1 = W * 0.49, gy0 = -H * 0.18, gy1 = gy + H * 0.24;                                    // the godown
    g += rect(gx0, gy0, gx1 - gx0, gy1 - gy0, "#b8ab92", ` stroke="#7a6a4a" stroke-width="${6 * k}"`) + stackIn(nv(p, "goods", 10), gx0 + 14 * k, gy0 + 30 * k, gx1 - 14 * k, gy1 - 8 * k, item, k) +
      [...Array(7).keys()].map((j) => `<path d="M${r1(gx0 + (j + 0.5) * (gx1 - gx0) / 7)} ${r1(gy0)} L${r1(gx0 + (j + 0.5) * (gx1 - gx0) / 7)} ${r1(gy1)}" stroke="#7a6a4a" stroke-width="${2 * k}" opacity="0.45"/>`).join("") +
      rect(gx0 - 8 * k, gy0 - 14 * k, gx1 - gx0 + 16 * k, 18 * k, "#7a6a4a");
    g += counterBox(-W * 0.33, -H * 0.3, p, k, 56);
    if (p.notice) g += chalk(W * 0.07, -H * 0.3, W * 0.26, H * 0.13, String(p.notice), "", { k });
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#4a5568");
  },
  farm(W, H, p) {
    const k = W / 1920, gy = -H * 0.07, t = tOf(p), n = countOf(p, 2, 1, 6), signs = signsOf(p), crop = p.crop && p.crop !== "auto" ? p.crop : "wheat";
    const w = p.weather || "none", dry = w === "drought", ripe = p.season === "harvest", grow = c01(nv(p, "level", 0.8));
    let g = skyGround(W, H, "#cfe8f5", "#eaf4f9", "#9fbe72", gy) + (w === "rain" || w === "drought" ? "" : `<circle cx="${W * 0.42}" cy="${-H * 0.37}" r="${H * 0.065}" fill="#ffd95a"/>`) + cloud(-W * 0.2, -H * 0.36, 1.1 * k);
    g += `<path d="M${-W} ${gy} Q${-W * 0.6} ${gy - H * 0.16} ${-W * 0.2} ${gy - H * 0.05} T${W * 0.5} ${gy - H * 0.08} T${W} ${gy} Z" fill="#b7cf93"/>`;
    const hut = (x, s) => `<g transform="translate(${r1(x)},${r1(gy)}) scale(${r1(s * k * 100) / 100})">${rect(-90, -100, 180, 100, "#e4cf9f", ' stroke="#bfa871" stroke-width="4"')}<path d="M-110 -100 L0 -170 L110 -100 Z" fill="#c98850"/>${rect(-22, -62, 44, 62, "#8a5a2b")}</g>`;
    g += hut(-W * 0.62, 0.6) + hut(W * 0.6, 0.55);
    const fx0 = -W * 0.47, fx1 = W * 0.27, fy0 = gy + H * 0.04, fy1 = H * 0.28, soil = dry ? "#d1b07a" : w === "flood" ? "#8fa9b8" : "#b98d5a";
    g += rect(fx0, fy0, fx1 - fx0, fy1 - fy0, soil);
    const R = 6, rowY = (r) => fy0 + (fy1 - fy0) * Math.pow((r + 0.75) / R, 1.2);
    for (let r = 0; r < R; r++) g += `<path d="M${r1(fx0)} ${r1(rowY(r) + 4 * k)} L${r1(fx1)} ${r1(rowY(r) + 4 * k)}" stroke="${shade(soil, 0.85)}" stroke-width="${r1((3 + r) * k)}"/>`;
    if (dry) for (let j = 0; j < 30; j++) { const x = fx0 + rnd(j, 5) * (fx1 - fx0), y = fy0 + rnd(j, 6) * (fy1 - fy0);
      g += `<path d="M${r1(x)} ${r1(y)} l${r1(14 * k)} ${r1(6 * k)} l${r1(-6 * k)} ${r1(10 * k)} l${r1(16 * k)} ${r1(4 * k)}" stroke="#9a7a45" stroke-width="${2 * k}" fill="none"/>`; }
    for (let i = 0; i < n; i++) {
      const px0 = fx0 + i * (fx1 - fx0) / n, px1 = px0 + (fx1 - fx0) / n, share = c01(lv(p, "levels", i, 1));
      if (crop !== "none") for (let r = 0; r < R; r++) {
        const y = rowY(r), sc = (0.95 + 0.75 * (y - fy0) / (fy1 - fy0)) * k, cols = Math.max(3, Math.round((px1 - px0) / (50 * sc)));
        for (let c = 0; c < cols; c++) if ((c + 0.5) / cols <= share + 1e-6) g += plantG(px0 + (c + 0.5) * (px1 - px0) / cols, y, sc, crop, Math.max(0.15, grow), dry, ripe);
      }
      if (i) g += rect(px0 - 6 * k, fy0, 12 * k, fy1 - fy0, "#8a6a3e");
      g += glowBox(px0 + 4 * k, fy0 + 4 * k, px1 - 4 * k, fy1 - 4 * k, sv(p, "glow", i + 1, `plot${i + 1}`), k) + smallSign(signs[i], (px0 + px1) / 2, fy0 - H * 0.025, Math.min(px1 - px0, W * 0.3) * 0.8, 40);
    }
    if (w === "flood") g += rect(fx0, fy0 + (fy1 - fy0) * 0.3, fx1 - fx0, (fy1 - fy0) * 0.7, "#5f9fcf", ' opacity="0.55"');
    if (w === "pests") for (let j = 0; j < 70; j++) { const x = fx0 + rnd(j, 7) * (fx1 - fx0) + Math.sin(t * 3 + j) * 14 * k, y = fy0 + rnd(j, 8) * (fy1 - fy0) * 0.9 + Math.cos(t * 4 + j) * 8 * k;
      g += `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(5 * k)}" ry="${r1(3.5 * k)}" fill="#2b2b33"/><path d="M${r1(x - 6 * k)} ${r1(y - 4 * k)} L${r1(x + 6 * k)} ${r1(y - 4 * k)}" stroke="#7a7f88" stroke-width="${2 * k}" opacity="${r1((0.5 + 0.5 * Math.sin(t * 20 + j)) * 100) / 100}"/>`; }
    const pw = nv(p, "people", 0);                                                                              // the workers, each on a strip
    if (pw > 0) {
      const strip = (fx1 - fx0) / Math.max(1, pw), crowd = c01((W * 0.16 - strip) / (W * 0.1)), whole = Math.floor(pw + 1e-6);
      for (let j = 1; j < Math.ceil(pw - 1e-6); j++) g += `<path d="M${r1(fx0 + j * strip)} ${r1(fy0)} L${r1(fx0 + j * strip)} ${r1(fy1)}" stroke="#ffffff" stroke-width="${4 * k}" stroke-dasharray="${14 * k} ${10 * k}" opacity="0.75"/>`;
      for (let j = 0; j < Math.ceil(pw - 1e-6); j++) g += fig(fx0 + (j + 0.5) * strip + (crowd > 0 ? (rnd(j, 9) - 0.5) * strip * 0.6 : 0), fy0 + (fy1 - fy0) * 0.7, H * 0.17, j,
        { pose: rnd(j, 11) < crowd * 0.55 ? "stand" : "work", op: j < whole ? 1 : pw - whole, hat: "#f1e3c6" });
    }
    g += heapG(nv(p, "goods", 4), W * 0.38, fy1, Math.min(1.1, 7 / Math.max(1, Math.sqrt(2 * nv(p, "goods", 4)))) * k, { col: ripe ? "#e2c27a" : "#d2a96a" });
    const fg = sv(p, "glow", 0, "fence"), fy = fy1 + H * 0.012;                                                  // the fence: the fixed land
    if (fg > 0.01) g += rect(fx0 - 14 * k, fy - H * 0.06, fx1 - fx0 + 28 * k, H * 0.075, "#f2c14e", ` opacity="${r1(fg * 0.45 * 100) / 100}" rx="${10 * k}"`);
    for (let x = fx0; x <= fx1 + 1; x += (fx1 - fx0) / 16) g += rect(x - 5 * k, fy - H * 0.05, 10 * k, H * 0.055, fg > 0.5 ? "#c98a00" : "#8a5a2b");
    g += [0.035, 0.018].map((d) => `<path d="M${r1(fx0)} ${r1(fy - H * d)} L${r1(fx1)} ${r1(fy - H * d)}" stroke="${fg > 0.5 ? "#f2a900" : "#6b5a45"}" stroke-width="${(fg > 0.5 ? 5 : 3) * k}"/>`).join("");
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#5e7a34");
  },
  riverTown(W, H, p) {
    const k = W / 1920, gy = -H * 0.1, t = tOf(p), lev = c01(nv(p, "level", 0)), L = (a) => a.map(r1).join(" ");
    let g = skyGround(W, H, "#d6e8f2", "#eef5f7", "#b9cf8f", gy) + cloud(W * 0.1, -H * 0.38, k);
    for (let i = 0; i < 9; i++) g += rect(W * (0.1 + i * 0.05), gy - H * (0.05 + ((i * 3) % 4) * 0.025), W * 0.04, H * (0.05 + ((i * 3) % 4) * 0.025), "#c9d3dd");
    const fx = -W * 0.36;                                                                            // the factory up the river
    g += rect(fx - W * 0.12, -H * 0.27, W * 0.24, H * 0.27, "#d9d3c6", ` stroke="#a39a88" stroke-width="${4 * k}"`) + [0, 1, 2].map((j) => `<path d="M${L([fx - W * 0.12 + j * W * 0.08, -H * 0.27])} L${L([fx - W * 0.07 + j * W * 0.08, -H * 0.34])} L${L([fx - W * 0.04 + j * W * 0.08, -H * 0.27])} Z" fill="#a39a88"/>`).join("") +
      rect(fx + W * 0.06, -H * 0.38, W * 0.03, H * 0.11, "#9b4a3a") + (p.filter === true ? rect(fx + W * 0.054, -H * 0.405, W * 0.042, H * 0.035, "#5b7fb8") : "");
    if (p.smoke !== false) for (let j = 0; j < 6; j++) { const u = (t * 0.22 + j / 6) % 1, a = p.filter === true ? 0.35 : 1;
      g += `<circle cx="${r1(fx + W * 0.075 + u * W * 0.14)}" cy="${r1(-H * 0.4 - u * H * 0.04)}" r="${r1(H * (0.02 + 0.03 * a) * (0.6 + u))}" fill="${p.filter === true ? "#e3e7ec" : "#a8adb5"}" opacity="${r1((0.8 - u * 0.6) * 100) / 100}"/>`; }
    g += counterBox(fx - W * 0.03, -H * 0.2, p, k, 48);
    const ry0 = H * 0.02, ry1 = H * 0.2, px = -W * 0.2, clear = [95, 176, 220], dirt = [61, 59, 44];
    const mix = (u) => `#${clear.map((c, i) => Math.round(c + (dirt[i] - c) * u).toString(16).padStart(2, "0")).join("")}`;
    g += `<path d="M${-W} ${ry0} Q${-W * 0.5} ${ry0 - H * 0.02} 0 ${ry0} T${W} ${ry0} L${W} ${ry1} Q${W * 0.5} ${ry1 + H * 0.02} 0 ${ry1} T${-W} ${ry1} Z" fill="${mix(lev * 0.35)}"/>`;
    const spread = c01(lev * 1.7);                                                                   // dirty water spreads downstream
    if (lev > 0.001) for (let j = 0; j < 6; j++) g += rect(px, ry0 + 4 * k, (W * 1.4) * spread * (1 - j * 0.12), ry1 - ry0 - 8 * k, mix(lev), ` opacity="${r1(0.32 * 100) / 100}"`);
    for (let i = -14; i < 14; i++) { const x = ((i * W * 0.09 + t * 60 * k) % (2 * W) + 2 * W) % (2 * W) - W;
      g += `<path d="M${r1(x)} ${r1(ry0 + H * 0.05 + (i % 3) * H * 0.04)} q${r1(W * 0.02)} ${r1(-H * 0.01)} ${r1(W * 0.04)} 0" stroke="#ffffff" stroke-width="${3 * k}" fill="none" opacity="${r1((0.5 - lev * 0.35) * 100) / 100}"/>`; }
    const rate = isN(p.rate) && +p.rate >= 0 ? +p.rate : 0.5;                                       // the pipe pours the waste
    g += rect(-W * 0.255, -H * 0.06, W * 0.05, H * 0.025, "#6b7280") + rect(px - W * 0.012, -H * 0.06, W * 0.024, ry0 - (-H * 0.06) + 6 * k, "#6b7280");
    if (rate > 0) for (let j = 0; j < 5; j++) { const u = (t * 1.5 + j / 5) % 1; g += `<ellipse cx="${r1(px)}" cy="${r1(ry0 + 6 * k + u * H * 0.05)}" rx="${r1((6 + rate * 16) * k)}" ry="${r1((5 + rate * 8) * k)}" fill="#4a4636" opacity="${r1((0.9 - u * 0.7) * 100) / 100}"/>`; }
    g += [0, 1].map((j) => `<g transform="translate(${r1(px - W * 0.05 - j * W * 0.035)},${r1(ry0 - 4 * k)}) rotate(${j ? -70 : 0})">${rect(-24 * k, -54 * k, 48 * k, 54 * k, "#3a7bd5", ` rx="${6 * k}"`)}${rect(-24 * k, -38 * k, 48 * k, 6 * k, "#24466e")}</g>`).join("");
    const alive = nv(p, "goods", 6), dead = nv(p, "part", 0);
    for (let j = 0; j < Math.ceil(alive - 1e-6); j++) { const dir = j % 2 ? -1 : 1, x = ((j * 0.17 * W + dir * t * 50 * k) % (0.62 * W) + 0.62 * W) % (0.62 * W) - 0.15 * W, y = ry0 + H * (0.06 + (j % 3) * 0.035);
      g += `<g opacity="${j < Math.floor(alive + 1e-6) ? 1 : (alive % 1).toFixed(3)}" transform="translate(${r1(x)},${r1(y)}) scale(${dir * k},${k})"><ellipse cx="0" cy="0" rx="26" ry="11" fill="#f29f05"/><path d="M-24 0 L-40 -11 L-40 11 Z" fill="#e07b24"/><circle cx="14" cy="-3" r="3" fill="#2b2b33"/></g>`; }
    for (let j = 0; j < Math.ceil(dead - 1e-6); j++) { const x = ((j * 0.21 * W + t * 14 * k) % (0.6 * W)) - 0.1 * W, y = ry0 + H * 0.03 + (j % 2) * H * 0.02;
      g += `<g opacity="${j < Math.floor(dead + 1e-6) ? 1 : (dead % 1).toFixed(3)}" transform="translate(${r1(x)},${r1(y)}) scale(${k},${-k})"><ellipse cx="0" cy="0" rx="26" ry="10" fill="#c9cdc3"/><path d="M-24 0 L-38 -10 L-38 10 Z" fill="#aeb3a8"/><path d="M10 -6 l8 8 m0 -8 l-8 8" stroke="#2b2b33" stroke-width="3"/></g>`; }
    if (lev > 0.5) for (let j = 0; j < 6; j++) { const u = (t * 0.5 + j / 6) % 1, x = -W * 0.1 + j * W * 0.09;
      g += `<path d="M${r1(x)} ${r1(ry0 - u * H * 0.12)} q${r1(10 * k)} ${r1(-12 * k)} 0 ${r1(-24 * k)} t0 ${r1(-24 * k)}" stroke="#7d8f3a" stroke-width="${4 * k}" fill="none" opacity="${r1((lev - 0.5) * 2 * (1 - u) * 100) / 100}"/>`; }
    for (let s = 0; s < 5; s++) g += rect(W * 0.2 + s * W * 0.03, -H * 0.01 + s * H * 0.03, W * 0.3 - s * W * 0.03, H * 0.03, s % 2 ? "#cdbf9e" : "#bfb08d");  // the ghat's steps
    g += crowdAt(nv(p, "people", 3), W * 0.36, H * 0.09, H * 0.14, 5, { seed: 12, t });
    const boats = Math.round(Math.min(3, nv(p, "vehicles", 0)));
    for (let j = 0; j < boats; j++) { const bx = -W * 0.02 + j * W * 0.12 + Math.sin(t * 0.8 + j) * 6 * k, by = ry0 + H * 0.12;
      g += fig(bx, by - 8 * k, H * 0.13, 40 + j, { pose: "work" }) + `<path d="M${r1(bx - 70 * k)} ${r1(by - 14 * k)} L${r1(bx + 70 * k)} ${r1(by - 14 * k)} L${r1(bx + 52 * k)} ${r1(by + 8 * k)} L${r1(bx - 52 * k)} ${r1(by + 8 * k)} Z" fill="#8a5a2b"/>` +
        `<path d="M${r1(bx + 30 * k)} ${r1(by - 40 * k)} L${r1(bx + 90 * k)} ${r1(by + 10 * k)}" stroke="#d8cfae" stroke-width="${3 * k}" stroke-dasharray="${6 * k} ${4 * k}"/>`; }
    g += rect(-W, ry1, 2 * W, H / 2 - ry1, "#a9c47f") + `<path d="M${-W} ${ry1 + H * 0.12} Q0 ${ry1 + H * 0.08} ${W} ${ry1 + H * 0.13}" stroke="#cdb67f" stroke-width="${30 * k}" fill="none" opacity="0.6"/>`;
    return g + board(p.label, 0, -H * 0.4, W * 0.4, "#1d5e8a");
  },
  mohalla(W, H, p) {
    const k = W / 1920, gy = H * 0.1, n = countOf(p, 5, 1, 8), signs = signsOf(p), night = p.light === "night" || p.light === "evening", t = tOf(p);
    let g = skyGround(W, H, "#d3e7f2", "#eef5f7", "#cfc5b0", gy) + cloud(-W * 0.35, -H * 0.38, k) + cloud(W * 0.4, -H * 0.33, 0.8 * k);
    for (let i = -9; i <= 9; i++) g += rect(i * W * 0.11 - W * 0.045, gy - H * (0.3 + ((i * 7 + 20) % 3) * 0.04), W * 0.09, H * 0.3, "#e3e8ec", ' opacity="0.7"');
    const win = night ? "#ffd76a" : "#cfe3f0", sw = W * 0.92 / n, dflt = [0.15, 0.35, 0.55, 0.75, 0.95];
    const house = (type, x, a, i) => {
      const L = (q) => q.map(r1).join(" "), c = ["#e7c9a0", "#a9c4e0", "#f0d9a8", "#e9b8a8", "#f4efe4"][type], w2 = a * [0.3, 0.34, 0.4, 0.42, 0.5][type];
      if (type === 0) return rect(x - w2, gy - H * 0.13, 2 * w2, H * 0.13, "#d9b98a", ` stroke="#a8875a" stroke-width="${3 * k}"`) + `<path d="M${L([x - w2 * 1.2, gy - H * 0.12])} L${L([x, gy - H * 0.22])} L${L([x + w2 * 1.2, gy - H * 0.12])} Z" fill="#b8954f"/>` + rect(x - w2 * 0.25, gy - H * 0.08, w2 * 0.5, H * 0.08, "#6b4a26");
      if (type === 1) return rect(x - w2, gy - H * 0.17, 2 * w2, H * 0.17, c, ` stroke="${shade(c, 0.75)}" stroke-width="${3 * k}"`) + `<path d="M${L([x - w2 * 1.1, gy - H * 0.16])} L${L([x + w2 * 1.1, gy - H * 0.2])} L${L([x + w2 * 1.1, gy - H * 0.18])} L${L([x - w2 * 1.1, gy - H * 0.14])} Z" fill="#8d96a0"/>` +
        rect(x - w2 * 0.7, gy - H * 0.1, w2 * 0.45, H * 0.1, "#5e7a96") + rect(x + w2 * 0.15, gy - H * 0.12, w2 * 0.5, H * 0.05, win);
      if (type === 2) { let s = rect(x - w2, gy - H * 0.34, 2 * w2, H * 0.34, c, ` stroke="${shade(c, 0.75)}" stroke-width="${3 * k}"`);
        for (let f = 0; f < 3; f++) s += [0, 1].map((j) => rect(x - w2 * 0.8 + j * w2 * 0.95, gy - H * (0.31 - f * 0.1), w2 * 0.65, H * 0.055, win)).join("") + rect(x - w2 * 1.05, gy - H * (0.245 - f * 0.1), 2.1 * w2, H * 0.012, shade(c, 0.7));
        return s + rect(x - w2 * 0.2, gy - H * 0.07, w2 * 0.4, H * 0.07, "#6b4a26"); }
      if (type === 3) return rect(x - w2, gy - H * 0.26, 2 * w2, H * 0.26, c, ` stroke="${shade(c, 0.75)}" stroke-width="${3 * k}"`) + `<path d="M${L([x - w2 * 1.15, gy - H * 0.26])} L${L([x, gy - H * 0.36])} L${L([x + w2 * 1.15, gy - H * 0.26])} Z" fill="#b5523b"/>` +
        [0, 1].map((j) => rect(x - w2 * 0.75 + j * w2 * 0.95, gy - H * 0.22, w2 * 0.55, H * 0.06, win)).join("") + rect(x + w2 * 0.2, gy - H * 0.11, w2 * 0.55, H * 0.06, win) + rect(x - w2 * 0.6, gy - H * 0.11, w2 * 0.4, H * 0.11, "#6b4a26");
      return rect(x - w2, gy - H * 0.2, 2 * w2, H * 0.2, c, ` stroke="${shade(c, 0.75)}" stroke-width="${3 * k}"`) + rect(x - w2 * 1.05, gy - H * 0.235, 2.1 * w2, H * 0.04, "#7a8fa3") + rect(x - w2 * 0.35, gy - H * 0.31, w2 * 0.7, H * 0.08, shade(c, 0.95), ` stroke="${shade(c, 0.75)}" stroke-width="${3 * k}"`) +
        [0, 1, 2].map((j) => rect(x - w2 * 0.85 + j * w2 * 0.62, gy - H * 0.16, w2 * 0.42, H * 0.07, win)).join("") + rect(x - w2 * 0.15, gy - H * 0.27, w2 * 0.3, H * 0.04, win) +
        `<ellipse cx="${r1(x - w2 * 0.95)}" cy="${r1(gy - H * 0.02)}" rx="${r1(w2 * 0.22)}" ry="${r1(H * 0.04)}" fill="#6fae5a"/><ellipse cx="${r1(x + w2 * 0.95)}" cy="${r1(gy - H * 0.02)}" rx="${r1(w2 * 0.22)}" ry="${r1(H * 0.04)}" fill="#6fae5a"/>`;
    };
    const typeOf = (L) => Math.max(0, Math.min(4, Math.floor(c01(L) * 5 - 1e-9)));
    let cars = "";
    for (let i = 0; i < n; i++) {
      const x = -W * 0.46 + (i + 0.5) * sw, a = Math.min(sw * 0.95, W * 0.24), now = lv(p, "levels", i, dflt[i % 5]), e = phase(p), wl = listOf(wasOf(p).levels)[i];
      g += glowBox(x - sw * 0.48, gy - H * 0.38, x + sw * 0.48, gy + H * 0.01, sv(p, "glow", i + 1), k);
      if (isN(wl) && typeOf(+wl) !== typeOf(now) && e < 1) g += `<g opacity="${(1 - e).toFixed(3)}">${house(typeOf(+wl), x, a, i)}</g><g opacity="${e.toFixed(3)}">${house(typeOf(now), x, a, i)}</g>`;
      else g += house(typeOf(now), x, a, i);
      g += smallSign(signs[i], x, gy + H * 0.035, Math.min(sw * 0.86, W * 0.2), 40);
      const nc = hasList(p, "counts") ? lv(p, "counts", i, 0) : now >= 0.9 ? 2 : now >= 0.65 ? 1 : 0;
      for (let j = 0; j < Math.min(3, Math.ceil(nc - 1e-6)); j++) { const one = carG(x - sw * 0.2 + j * sw * 0.4 / Math.max(1, Math.ceil(nc) - 1 || 1), gy + H * 0.13, Math.min(0.42 * k, sw / 700), TOPS[(i * 3 + j) % TOPS.length]);
        cars += j < Math.floor(nc + 1e-6) ? one : `<g opacity="${(nc % 1).toFixed(3)}">${one}</g>`; }
    }
    return g + rect(-W, gy + H * 0.065, 2 * W, H * 0.008, "#b3a88f") + cars + crowdAt(nv(p, "people", 0), 0, gy + H * 0.22, H * 0.16, 14, { seed: 8, t }) + festiveG(W, H, p.festive, t, -H * 0.37) +
      board(p.label, 0, -H * 0.42, W * 0.4, "#6b4a26");
  },
  canteen(W, H, p) {
    const k = W / 1920, gy = H * 0.1, n = countOf(p, 3, 1, 6), t = tOf(p);
    let g = wallFloor(W, H, "#f4e7d0", "#d8c7a4", gy) + rowsBoard(W * 0.04, -H * 0.34, W * 0.46, -H * 0.02, signsOf(p), p, "prices", n, k);
    if (p.notice) g += rect(-W * 0.38, -H * 0.36, W * 0.16, H * 0.15, "#ffffff", ` stroke="#cfc6b4" stroke-width="${3 * k}"`) + rect(-W * 0.38, -H * 0.36, W * 0.16, H * 0.035, "#e5484d") +
      textA(p.notice, -W * 0.3, -H * 0.255, fitFs(p.notice, W * 0.15, 46 * k), "#2b2b33", 800, "middle");
    g += rect(-W * 0.48, gy - H * 0.12, W * 0.42, H * 0.14, "#b5834a", ` stroke="#8a5a2b" stroke-width="${5 * k}"`) + rect(-W * 0.49, gy - H * 0.135, W * 0.44, H * 0.02, "#8a5a2b");
    const kinds = ["samosa", "tea", "bread", "mithai", "roti", "jalebi"];
    for (let i = 0; i < Math.min(n, 4); i++) {
      const x = -W * 0.42 + i * W * 0.1, y = gy - H * 0.135, m = Math.round(c01(lv(p, "levels", i, 0.8)) * 6);
      g += rect(x - W * 0.042, y - 6 * k, W * 0.084, 8 * k, "#c7ccd3");
      for (let j = 0; j < m; j++) g += itemG(kinds[i], x + ((j % 3) - 1) * 46 * k, y - 6 * k - Math.floor(j / 3) * 34 * k, 0.85 * k, j);
    }
    g += [0, 1, 2].map((j) => { const u = (t * 0.5 + j / 3) % 1; return `<circle cx="${r1(-W * 0.32 + Math.sin(t + j) * 6 * k)}" cy="${r1(gy - H * 0.2 - u * H * 0.08)}" r="${r1((8 + u * 12) * k)}" fill="#ffffff" opacity="${r1((0.6 - u * 0.6) * 100) / 100}"/>`; }).join("");
    const pv = nv(p, "people", 5), seated = Math.min(pv, 9);
    for (let tb = 0; tb < 3; tb++) {
      const tx = -W * 0.02 + tb * W * 0.19, ty = gy + H * 0.12;
      for (let j = 0; j < 3; j++) { const q = tb * 3 + j, on = c01(seated - q); if (on > 0.01) g += fig(tx + (j - 1) * W * 0.045, ty - H * 0.03, H * 0.15, q, { pose: "sit", op: on }); }
      g += `<ellipse cx="${r1(tx)}" cy="${r1(ty - H * 0.05)}" rx="${r1(W * 0.075)}" ry="${r1(H * 0.025)}" fill="#c98850" stroke="#8a5a2b" stroke-width="${3 * k}"/>` + rect(tx - 6 * k, ty - H * 0.05, 12 * k, H * 0.07, "#6b4a26");
    }
    g += crowdAt(Math.max(0, pv - seated), -W * 0.3, gy + H * 0.14, H * 0.17, 5, { seed: 20, t });
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#c0392b");
  },
  home(W, H, p) {
    const k = W / 1920, gy = H * 0.12, t = tOf(p), night = p.light === "night" || p.light === "evening", on = p.on === true;
    let g = rect(-W, -H / 2, 2 * W, H, "#efe6d6") + rect(-W, -H * 0.44, W * 0.83, gy + H * 0.44, "#f3e3c3") + rect(-W * 0.17, -H * 0.44, W * 0.34, gy + H * 0.44, "#e3eef3") + rect(W * 0.17, -H * 0.44, W * 0.83, gy + H * 0.44, "#efe4f3") +
      rect(-W, -H / 2, 2 * W, H * 0.06, "#d8cbb3") + rect(-W, gy, 2 * W, H / 2 - gy, "#d9c8a6");
    for (let i = -20; i <= 20; i++) g += `<path d="M${r1(i * W * 0.05)} ${r1(gy)} L${r1(i * W * 0.07)} ${r1(H / 2)}" stroke="#c9b793" stroke-width="${3 * k}"/>`;
    g += rect(-W * 0.175, -H * 0.44, W * 0.012, gy + H * 0.44, "#cfc6b4") + rect(W * 0.163, -H * 0.44, W * 0.012, gy + H * 0.44, "#cfc6b4");
    const glow = (name, x0, y0, x1, y1) => glowBox(x0, y0, x1, y1, sv(p, "glow", 0, name), k);
    g += glow("kitchen", -W * 0.5, -H * 0.43, -W * 0.18, gy) + glow("living", -W * 0.16, -H * 0.43, W * 0.16, gy) + glow("study", W * 0.18, -H * 0.43, W * 0.5, gy);
    const sky = night ? "#22345a" : "#cfe8f5";                                                         // kitchen
    g += rect(-W * 0.34, -H * 0.3, W * 0.12, H * 0.13, sky, ` stroke="#b9a576" stroke-width="${6 * k}"`);
    g += glow("fridge", -W * 0.475, gy - H * 0.38, -W * 0.365, gy + 6 * k) + rect(-W * 0.465, gy - H * 0.37, W * 0.09, H * 0.37, "#e9eef2", ` rx="${10 * k}" stroke="#aab4be" stroke-width="${4 * k}"`) + rect(-W * 0.455, gy - H * 0.33, W * 0.07, H * 0.16, "#cfe3f0");
    const fill = Math.round(c01(nv(p, "level", 0.6)) * 9);
    for (let j = 0; j < fill; j++) g += rect(-W * 0.45 + (j % 3) * W * 0.022, gy - H * 0.2 - Math.floor(j / 3) * H * 0.045, W * 0.018, H * 0.035, TOPS[(j * 3) % TOPS.length], ` rx="${3 * k}"`);
    g += glow("counter", -W * 0.375, gy - H * 0.15, -W * 0.185, gy + 6 * k) + rect(-W * 0.365, gy - H * 0.13, W * 0.17, H * 0.13, "#b98b52") + rect(-W * 0.37, gy - H * 0.145, W * 0.18, H * 0.02, "#7a6a4a") +
      rect(-W * 0.35, gy - H * 0.11, W * 0.06, H * 0.1, "#9a6b38") + `<rect x="${r1(-W * 0.34)}" y="${r1(gy - H * 0.1)}" width="${r1(W * 0.035)}" height="${r1(H * 0.09)}" rx="${r1(12 * k)}" fill="#d64545"/>`;
    g += glow("stove", -W * 0.36, gy - H * 0.24, -W * 0.27, gy - H * 0.13) + rect(-W * 0.36, gy - H * 0.165, W * 0.1, H * 0.022, "#2d3748") + itemG("pot", -W * 0.335, gy - H * 0.165, 1.5 * k) + itemG("pot", -W * 0.285, gy - H * 0.165, 1.1 * k);
    if (on) g += [0, 1, 2].map((j) => `<path d="M${r1(-W * 0.335 + j * 12 * k)} ${r1(gy - H * 0.165)} q${r1(-6 * k)} ${r1(-(14 + 6 * Math.sin(t * 12 + j)) * k)} ${r1(4 * k)} ${r1(-(22 + 6 * Math.sin(t * 12 + j)) * k)}" fill="#ff8a3c"/>`).join("") +
      [0, 1, 2].map((j) => { const u = (t * 0.5 + j / 3) % 1; return `<circle cx="${r1(-W * 0.325 + Math.sin(t + j) * 8 * k)}" cy="${r1(gy - H * 0.22 - u * H * 0.1)}" r="${r1((8 + u * 14) * k)}" fill="#ffffff" opacity="${r1((0.7 - u * 0.7) * 100) / 100}"/>`; }).join("");
    g += stackIn(nv(p, "goods", 0), -W * 0.265, gy - H * 0.36, -W * 0.19, gy - H * 0.145, "tiffin", k);
    g += glow("tv", -W * 0.09, -H * 0.29, W * 0.09, -H * 0.15) + rect(-W * 0.08, -H * 0.28, W * 0.16, H * 0.12, "#1f2a33", ` rx="${6 * k}"`) +           // living room
      rect(-W * 0.072, -H * 0.27, W * 0.144, H * 0.1, on ? "#7ec8e3" : "#2d3748") + (on ? [0, 1, 2, 3].map((j) => rect(-W * 0.06 + j * W * 0.032, -H * 0.24 + Math.sin(t * 2 + j) * 6 * k, W * 0.024, H * 0.05, TOPS[j], ' opacity="0.7"')).join("") : "");
    g += glow("sofa", -W * 0.14, gy - H * 0.13, W * 0.14, gy + 6 * k) + rect(-W * 0.13, gy - H * 0.12, W * 0.26, H * 0.07, "#5b7fb8", ` rx="${16 * k}"`) + rect(-W * 0.13, gy - H * 0.06, W * 0.26, H * 0.05, "#4a6aa0", ` rx="${12 * k}"`) +
      rect(-W * 0.145, gy - H * 0.09, W * 0.03, H * 0.09, "#3d5a8a", ` rx="${10 * k}"`) + rect(W * 0.115, gy - H * 0.09, W * 0.03, H * 0.09, "#3d5a8a", ` rx="${10 * k}"`);
    g += rect(W * 0.21, -H * 0.33, W * 0.14, H * 0.2, "#c9a46a", ` stroke="#8a6d3b" stroke-width="${4 * k}"`) + [0, 1, 2].map((r) => [...Array(7).keys()].map((j) => rect(W * 0.215 + j * W * 0.019, -H * 0.32 + r * H * 0.065, W * 0.014, H * 0.055, TOPS[(j + r * 3) % TOPS.length], ' opacity="0.85"')).join("")).join("");
    g += glow("desk", W * 0.2, gy - H * 0.13, W * 0.38, gy + 6 * k) + rect(W * 0.21, gy - H * 0.11, W * 0.16, H * 0.02, "#8a5a2b") + rect(W * 0.22, gy - H * 0.09, W * 0.01, H * 0.09, "#6b4a26") + rect(W * 0.35, gy - H * 0.09, W * 0.01, H * 0.09, "#6b4a26") +
      `<path d="M${r1(W * 0.33)} ${r1(gy - H * 0.11)} L${r1(W * 0.33)} ${r1(gy - H * 0.18)} L${r1(W * 0.35)} ${r1(gy - H * 0.2)}" stroke="#4a5568" stroke-width="${4 * k}" fill="none"/><path d="M${r1(W * 0.335)} ${r1(gy - H * 0.2)} L${r1(W * 0.37)} ${r1(gy - H * 0.21)} L${r1(W * 0.36)} ${r1(gy - H * 0.18)} Z" fill="${night ? "#ffd76a" : "#9aa5b1"}"/>` +
      (night ? `<ellipse cx="${r1(W * 0.355)} " cy="${r1(gy - H * 0.13)}" rx="${r1(W * 0.05)}" ry="${r1(H * 0.04)}" fill="#ffd76a" opacity="0.35"/>` : "");
    g += glow("door", W * 0.385, gy - H * 0.31, W * 0.485, gy + 6 * k) + rect(W * 0.395, gy - H * 0.3, W * 0.08, H * 0.3, "#8a5a2b", ` stroke="#5e3b17" stroke-width="${4 * k}"`) + `<circle cx="${r1(W * 0.46)}" cy="${r1(gy - H * 0.15)}" r="${r1(7 * k)}" fill="#f2c14e"/>`;
    if (p.notice) g += rect(W * 0.36, gy - H * 0.06, W * 0.13, H * 0.06, "#c98850") + paperNote(W * 0.43, -H * 0.4, p.notice, k, W * 0.14);
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#6b4a26");
  },
  teaEstate(W, H, p) {
    const k = W / 1920, gy = H * 0.12, t = tOf(p), night = p.light === "night" || p.light === "evening", L = (a) => a.map(r1).join(" ");
    let g = skyGround(W, H, "#d4e9ef", "#eef6f2", "#c9c08f", gy) + cloud(-W * 0.1, -H * 0.42, k);
    [["#a9cc7e", -0.26], ["#8fbf68", -0.16], ["#7bb05a", -0.06]].forEach(([c, top], h) => {
      g += `<path d="M${-W} ${gy} L${-W} ${r1(H * top + H * 0.06)} Q${r1(-W * 0.4)} ${r1(H * top - H * 0.04)} ${r1(W * 0.1 * (h - 1))} ${r1(H * top)} T${W} ${r1(H * top + H * 0.05)} L${W} ${gy} Z" fill="${c}"/>`;
      for (let r = 0; r < 3; r++) g += `<path d="M${-W} ${r1(H * top + H * (0.1 + r * 0.04))} Q${r1(-W * 0.4)} ${r1(H * top + H * (r * 0.04))} ${r1(W * 0.1 * (h - 1))} ${r1(H * top + H * (0.04 + r * 0.04))} T${W} ${r1(H * top + H * (0.09 + r * 0.04))}" stroke="${shade(c, 0.72)}" stroke-width="${24 * k}" stroke-dasharray="0.1 ${30 * k}" stroke-linecap="round" fill="none"/>`;
    });
    g += crowdAt(nv(p, "people", 8), -W * 0.27, -H * 0.1, H * 0.1, 10, { seed: 14, basket: true, t });   // the pluckers in the rows
    for (let i = 0; i < 5; i++) { const x = -W * 0.46 + i * W * 0.06;                               // the workers' lines
      g += rect(x, gy - H * 0.1, W * 0.055, H * 0.1, "#e6dcc5", ` stroke="#b9ad90" stroke-width="${3 * k}"`) + `<path d="M${L([x - 4 * k, gy - H * 0.1])} L${L([x + W * 0.0275, gy - H * 0.14])} L${L([x + W * 0.055 + 4 * k, gy - H * 0.1])} Z" fill="#8d96a0"/>` + rect(x + W * 0.018, gy - H * 0.06, W * 0.018, H * 0.06, "#6b4a26"); }
    g += rect(W * 0.22, -H * 0.2, W * 0.24, gy + H * 0.2, "#d9d3c6", ` stroke="#a39a88" stroke-width="${4 * k}"`) + rect(W * 0.41, -H * 0.36, W * 0.03, H * 0.16, "#9b4a3a") +   // the estate factory
      [0, 1, 2, 3].map((j) => rect(W * 0.24 + j * W * 0.055, -H * 0.14, W * 0.04, H * 0.06, night ? "#ffd76a" : "#cfe3f0")).join("");
    const gx0 = -W * 0.15, gx1 = W * 0.05, f = sv(p, "shut", 1, "gate");                            // the estate gate
    g += rect(gx0 - W * 0.02, gy - H * 0.21, W * 0.02, H * 0.21, "#b9b2a4") + rect(gx1, gy - H * 0.21, W * 0.02, H * 0.21, "#b9b2a4") + rect(gx0 - W * 0.025, gy - H * 0.225, gx1 - gx0 + W * 0.05, H * 0.02, "#8a8172");
    const leaf = (x0, x1) => rect(Math.min(x0, x1), gy - H * 0.15, Math.abs(x1 - x0), H * 0.14, "none", ` stroke="#4a5568" stroke-width="${6 * k}"`) + [1, 2, 3].map((j) => `<path d="M${r1(x0 + (x1 - x0) * j / 4)} ${r1(gy - H * 0.15)} L${r1(x0 + (x1 - x0) * j / 4)} ${r1(gy - H * 0.01)}" stroke="#4a5568" stroke-width="${5 * k}"/>`).join("");
    const half = (gx1 - gx0) / 2, open = 1 - f;
    g += leaf(gx0, gx0 + half * (1 - open * 0.8)) + leaf(gx1, gx1 - half * (1 - open * 0.8));
    const [now, old] = boardOf(p, "prices", 0);
    g += [-0.13, 0.03].map((f) => rect(W * f, -H * 0.125, 8 * k, H * 0.025, "#6b7280")).join("") + chalk(-W * 0.05, -H * 0.23, W * 0.2, H * 0.11, now, old, { k });
    if (p.notice) { const ux = W * 0.145;                                                            // the union office and its flag
      g += rect(ux - W * 0.06, gy - H * 0.12, W * 0.12, H * 0.12, "#efe4cf", ` stroke="#b9ad90" stroke-width="${3 * k}"`) + rect(ux - W * 0.012, gy - H * 0.07, W * 0.024, H * 0.07, "#6b4a26") +
        rect(ux + W * 0.055, gy - H * 0.3, 6 * k, H * 0.3, "#6b7280") + `<path d="M${r1(ux + W * 0.055 + 6 * k)} ${r1(gy - H * 0.3)} q${r1(W * 0.03)} ${r1(Math.sin(t * 3) * 8 * k)} ${r1(W * 0.06)} 0 l0 ${r1(H * 0.06)} q${r1(-W * 0.03)} ${r1(Math.sin(t * 3 + 1) * 8 * k)} ${r1(-W * 0.06)} 0 Z" fill="#e5484d"/>` +
        paperNote(ux, gy - H * 0.2, p.notice, k, W * 0.16); }
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#2f6b3a");
  },
  busStand(W, H, p) {
    const k = W / 1920, gy = H * 0.12, t = tOf(p), n = countOf(p, 2, 1, 4), signs = signsOf(p), cols = ["#d64545", "#2f7fc0", "#2fa35b", "#f29f05"];
    let g = skyGround(W, H, "#d6e8f2", "#eef5f7", "#9d978b", gy) + rect(-W, -H * 0.3, 2 * W, gy + H * 0.27, "#e6e0d2") + rect(-W, gy - H * 0.03, 2 * W, H * 0.03, "#c9c1ad") +
      rect(-W, -H * 0.36, 2 * W, H * 0.05, "#5b6b7d");
    for (let i = -6; i <= 6; i++) g += rect(i * W * 0.17 - 6 * k, -H * 0.31, 12 * k, gy + H * 0.28, "#8d96a0");
    const bw = W * 0.9 / n;
    let front = "";
    for (let i = 0; i < n; i++) {
      const bx = -W * 0.45 + (i + 0.5) * bw, s = Math.min(bw * 0.9 / 540, 1.1 * k), gone = sv(p, "shut", i + 1), x = bx + easeIO(gone) * W * 1.4, col = cols[i % 4];
      const [now, old] = boardOf(p, "prices", i);
      g += rect(bx - 3 * k, -H * 0.31, 6 * k, H * 0.02, "#5b6b7d") + chalk(bx, -H * 0.295, Math.min(bw * 0.72, W * 0.26), H * (signs[i] ? 0.14 : 0.1), now, old, { k, title: signs[i] || "" });
      g += busG(x, gy, s, col, -1, c01(lv(p, "levels", i, 0.4)), i);
      if (signs[i]) g += textA(signs[i], x, gy - 70 * s, fitFs(signs[i], 380 * s, 42 * k), "#ffffff", 800, "middle");
      const q = lv(p, "counts", i, 0);
      for (let j = Math.ceil(q - 1e-6) - 1; j >= 0; j--) front += fig(bx - bw * 0.3 + j * Math.min(30 * k, bw * 0.6 / Math.max(1, q)), gy + H * 0.13 + (j % 2) * H * 0.012, H * 0.17, i * 9 + j, { op: j < Math.floor(q + 1e-6) ? 1 : q - Math.floor(q) });
    }
    return g + front + counterBox(W * 0.38, -H * 0.49, p, k, 46) + board(p.label, 0, -H * 0.42, W * 0.4, "#5b6b7d");
  },
  petrolPump(W, H, p) {
    const k = W / 1920, gy = H * 0.08, n = countOf(p, 2, 1, 4), signs = signsOf(p), night = p.light === "night" || p.light === "evening";
    let g = skyGround(W, H, "#d6e8f2", "#eef5f7", "#b9b4aa", gy) + cloud(-W * 0.4, -H * 0.4, k);
    g += rect(-W * 0.46, -H * 0.3, W * 0.74, H * 0.08, "#2a9d8f") + rect(-W * 0.46, -H * 0.23, W * 0.74, H * 0.012, "#f7f4ee") + (night ? rect(-W * 0.44, -H * 0.218, W * 0.7, H * 0.012, "#fff3b0") + rect(-W * 0.46, -H * 0.21, W * 0.74, gy + H * 0.27, "#fff3b0", ' opacity="0.14"') : "");
    for (const f of [-0.4, -0.09, 0.22]) g += rect(W * f - 9 * k, -H * 0.22, 18 * k, gy + H * 0.28, "#c7ccd3");
    const pw = W * 0.66 / n;
    for (let i = 0; i < n; i++) {
      const px = -W * 0.4 + (i + 0.5) * pw, base = gy + H * 0.06, q = lv(p, "counts", i, 1), shut = sv(p, "shut", i + 1);
      for (let j = Math.min(5, Math.ceil(q - 1e-6)) - 1; j >= 0; j--) {                              // the queue at this pump, going back
        const one = carG(px + 150 * k + j * 46 * k, base + H * 0.03 - j * H * 0.065, 0.8 * k * Math.pow(0.85, j), TOPS[(i * 4 + j * 3) % TOPS.length], -1);
        g += j < Math.floor(q + 1e-6) ? one : `<g opacity="${(q % 1).toFixed(3)}">${one}</g>`;
      }
      g += rect(px - 85 * k, base - 16 * k, 170 * k, 24 * k, "#8d96a0") + rect(px - 58 * k, base - 196 * k, 116 * k, 180 * k, shut > 0.5 ? "#9aa5b1" : "#e5484d", ` rx="${10 * k}"`) + rect(px - 40 * k, base - 150 * k, 80 * k, 50 * k, "#f7f4ee", ` rx="${5 * k}"`) +
        `<path d="M${r1(px + 58 * k)} ${r1(base - 140 * k)} q${r1(50 * k)} ${r1(12 * k)} ${r1(38 * k)} ${r1(100 * k)}" stroke="#2d3748" stroke-width="${7 * k}" fill="none"/>`;
      const [now, old] = p.numbers === false ? ["", ""] : boardOf(p, "prices", i);     // numbers: false keeps the boards blank
      g += rect(px - 85 * k, base - 272 * k, 170 * k, 72 * k, "#111a22", ` rx="${8 * k}"`) + (old ? struck(old, px - 140 * k, base - 222 * k, 38 * k, "#c0392b", "end") : "") + textA(now, px, base - 222 * k, fitFs(now, 160 * k, 46 * k), "#ffcf4a", 800, "middle") +
        smallSign(signs[i], px, base - 312 * k, Math.min(pw * 0.9, 240 * k), 40);
    }
    const tx = W * 0.4;                                                                              // the totem with the litre counter
    g += rect(tx - 10 * k, -H * 0.2, 20 * k, gy + H * 0.26, "#6b7280") + rect(tx - W * 0.075, -H * 0.36, W * 0.15, H * 0.17, "#2a9d8f", ` rx="${10 * k}"`) + (p.numbers === false ? "" : counterBox(tx, -H * 0.32, p, k, 50));
    return g + board(p.label, -W * 0.08, -H * 0.42, W * 0.4, "#2a9d8f");
  },
  venue(W, H, p) {
    const k = W / 1920, gy = H * 0.14, t = tOf(p);
    let g = rect(-W, -H / 2, W * 0.79, H, "#efe4cf") + rect(-W, gy, W * 0.79, H / 2 - gy, "#d8c7a4") + rect(-W * 0.21, -H / 2, W * 1.21, H, "#2b2433") + rect(-W * 0.21, gy + H * 0.12, W * 1.21, H / 2 - gy - H * 0.12, "#3a3042");
    g += rowsBoard(-W * 0.47, -H * 0.36, -W * 0.25, -H * 0.22, signsOf(p), p, "prices", Math.max(1, Math.min(3, Math.max(signsOf(p).length, listOf(p.prices).length))), k);
    g += rect(-W * 0.44, -H * 0.2, W * 0.16, H * 0.16, "#cfe3f0", ` stroke="#8a5a2b" stroke-width="${8 * k}"`) + [1, 2, 3, 4].map((j) => `<path d="M${r1(-W * 0.44 + j * W * 0.032)} ${r1(-H * 0.2)} L${r1(-W * 0.44 + j * W * 0.032)} ${r1(-H * 0.04)}" stroke="#8a5a2b" stroke-width="${3 * k}"/>`).join("") +
      rect(-W * 0.46, -H * 0.05, W * 0.2, H * 0.025, "#8a5a2b");
    const on = p.on !== false, sc = on ? "#f8f4e6" : "#6b6375";                                    // the screen or the stage
    g += rect(-W * 0.1, -H * 0.42, W * 0.52, H * 0.18, sc, ` stroke="#1a1520" stroke-width="${8 * k}"`) + (on ? `<path d="M${r1(-W * 0.1)} ${r1(-H * 0.24)} L${r1(-W * 0.18)} ${r1(gy)} L${r1(W * 0.5)} ${r1(gy)} L${r1(W * 0.42)} ${r1(-H * 0.24)} Z" fill="#fff6d8" opacity="0.06"/>` : "");
    const C = Math.round(Math.max(1, Math.min(600, nv(p, "seats", 120)))), R = Math.max(2, Math.round(Math.sqrt(C / 2.2))), cols = Math.ceil(C / R);
    const sx0 = -W * 0.16, sx1 = W * 0.48, sy0 = -H * 0.2, sy1 = gy + H * 0.11, taken = nv(p, "taken", 0), part = Math.min(taken, nv(p, "part", 0));
    for (let r = 0; r < R; r++) {
      const ws = 0.82 + 0.18 * r / Math.max(1, R - 1), y = sy0 + (r + 0.5) * (sy1 - sy0) / R, cw = (sx1 - sx0) / cols * ws, sz = Math.min(cw, (sy1 - sy0) / R) * 0.78;
      for (let c = 0; c < cols; c++) {
        const q = r * cols + c;
        if (q >= C) break;
        const x = (sx0 + sx1) / 2 + (c - (cols - 1) / 2) * cw, full = c01(taken - q), kid = q < part;
        g += rect(x - sz * 0.45, y - sz * 0.35, sz * 0.9, sz * 0.7, full > 0.5 ? (kid ? "#f29f05" : "#3a7bd5") : "#7a2e3a", ` rx="${r1(sz * 0.2)}"`);
        if (full > 0.01) g += `<circle cx="${r1(x)}" cy="${r1(y - sz * (kid ? 0.45 : 0.55))}" r="${r1(sz * (kid ? 0.24 : 0.3))}" fill="${SKINS[q % SKINS.length]}" opacity="${full.toFixed(3)}"/>`;
      }
    }
    const f = sv(p, "shut", 1, "door"), dx0 = -W * 0.235, dx1 = -W * 0.185;                          // the door between foyer and hall
    g += rect(dx0, gy - H * 0.28, dx1 - dx0, H * 0.28, "#1a1520") + rect(dx0, gy - H * 0.28, (dx1 - dx0) * f, H * 0.28, "#8a5a2b", ` stroke="#5e3b17" stroke-width="${4 * k}"`);
    if (p.notice) g += paperNote((dx0 + dx1) / 2, gy - H * 0.36, p.notice, k, W * 0.2);
    g += crowdAt(nv(p, "people", 0), -W * 0.36, gy + H * 0.13, H * 0.18, 4, { seed: 25, t });
    return g + board(p.label, W * 0.16, -H * 0.47, W * 0.36, "#7a2e3a");
  },
  godown(W, H, p) {
    const k = W / 1920, gy = H * 0.12, t = tOf(p), L = (a) => a.map(r1).join(" ");
    let g = skyGround(W, H, "#d3e9f4", "#eef5f7", "#cdbb92", gy) + cloud(W * 0.42, -H * 0.4, k);
    const x0 = -W * 0.3, x1 = W * 0.32;
    g += `<path d="M${L([x0 - W * 0.02, -H * 0.3])} L${L([(x0 + x1) / 2, -H * 0.4])} L${L([x1 + W * 0.02, -H * 0.3])} Z" fill="#9aa5b1"/>` + rect(x0, -H * 0.3, x1 - x0, gy + H * 0.3, "#d9d0bc", ` stroke="#a39a88" stroke-width="${5 * k}"`);
    const sx0 = x0 + W * 0.02, sx1 = W * 0.1, sy0 = -H * 0.22, slots = 72, filled = c01(nv(p, "level", 0.4)) * slots, colsN = 12, u = (sx1 - sx0) / colsN;
    g += rect(sx0, sy0, sx1 - sx0, gy - sy0, "#6b5a45");
    for (let j = 0; j < Math.ceil(filled - 1e-6); j++) { const c = j % colsN, r = Math.floor(j / colsN), one = sackG(sx0 + (c + 0.5) * u, gy - r * u * 0.72, u / 62, "#d8c49a");
      g += j < Math.floor(filled + 1e-6) ? one : `<g opacity="${(filled % 1).toFixed(3)}">${one}</g>`; }
    const f = sv(p, "shut", 1, "door"), dx0 = W * 0.12, dx1 = W * 0.3;                              // the sliding door
    g += rect(dx0, -H * 0.18, dx1 - dx0, gy + H * 0.18, "#4a3b2a") + rect(dx0 + (dx1 - dx0) * (1 - f) * 0.92, -H * 0.18, dx1 - dx0, gy + H * 0.18, "#7d8a96", ` stroke="#5f6873" stroke-width="${4 * k}"`) +
      rect(dx1, -H * 0.19, W * 0.05, gy + H * 0.19, "#d9d0bc");
    const flow = p.flow === "in" || p.flow === "out" ? p.flow : "";
    if (flow && f < 0.5) for (let j = 0; j < 3; j++) { const u2 = (t * 0.12 + j / 3) % 1, x = flow === "in" ? W * 0.58 - u2 * W * 0.4 : W * 0.18 + u2 * W * 0.4;
      g += fig(x, gy + H * 0.1, H * 0.17, 50 + j, { pose: "carry", t }); }
    const [now, old] = boardOf(p, "prices", 0);
    g += rect(-W * 0.395 - 5 * k, -H * 0.05, 10 * k, gy + H * 0.05, "#6b7280") + chalk(-W * 0.395, -H * 0.2, W * 0.19, H * 0.15, now, old, { k, trend: p.trend === "up" || p.trend === "down" ? p.trend : "" });
    g += paperNote(-W * 0.12, -H * 0.295, p.notice, k, W * 0.26) + counterBox(W * 0.21, -H * 0.3, p, k, 44);
    return g + board(p.label, 0, -H * 0.44, W * 0.4, "#7a6a4a");
  },
  island(W, H, p) {
    const k = W / 1920, gy = -H * 0.12, t = tOf(p), crop = p.crop && p.crop !== "auto" ? p.crop : "rice", L = (a) => a.map(r1).join(" ");
    let g = rect(-W, -H / 2, 2 * W, gy + H / 2, "#cfe8f5") + (p.weather === "drought" || p.weather === "rain" ? "" : `<circle cx="${-W * 0.38}" cy="${-H * 0.36}" r="${H * 0.06}" fill="#ffd95a"/>`) + cloud(W * 0.1, -H * 0.4, k) + rect(-W, gy, 2 * W, H / 2 - gy, "#4f97c9");
    for (let i = -16; i < 16; i++) { const x = ((i * W * 0.08 + t * 40 * k) % (2 * W) + 2 * W) % (2 * W) - W;
      g += `<path d="M${r1(x)} ${r1(gy + H * (0.04 + (i % 4) * 0.05))} q${r1(W * 0.02)} ${r1(-H * 0.012)} ${r1(W * 0.04)} 0" stroke="#ffffff" stroke-width="${3 * k}" fill="none" opacity="0.55"/>`; }
    if (p.neighbour === "friendly" || p.neighbour === "hostile") { const nx = W * 0.38, ny = -H * 0.05, hostile = p.neighbour === "hostile";
      g += `<ellipse cx="${nx}" cy="${ny}" rx="${W * 0.1}" ry="${H * 0.04}" fill="#e6d29b"/><ellipse cx="${nx}" cy="${ny - H * 0.005}" rx="${W * 0.08}" ry="${H * 0.03}" fill="#8fbf62"/>` +
        rect(nx - W * 0.02, ny - H * 0.07, W * 0.04, H * 0.05, "#e4cf9f") + `<path d="M${L([nx - W * 0.026, ny - H * 0.07])} L${L([nx, ny - H * 0.1])} L${L([nx + W * 0.026, ny - H * 0.07])} Z" fill="#c98850"/>` +
        rect(nx + W * 0.05, ny - H * 0.16, 5 * k, H * 0.14, "#6b7280") + `<path d="M${r1(nx + W * 0.05 + 5 * k)} ${r1(ny - H * 0.16)} q${r1(W * 0.02)} ${r1(Math.sin(t * 3) * 6 * k)} ${r1(W * 0.045)} 0 l0 ${r1(H * 0.04)} q${r1(-W * 0.02)} ${r1(Math.sin(t * 3 + 1) * 6 * k)} ${r1(-W * 0.045)} 0 Z" fill="${hostile ? "#e5484d" : "#2fb463"}"/>` +
        (hostile ? [...Array(8).keys()].map((j) => `<path d="M${r1(nx - W * 0.07 + j * W * 0.02)} ${r1(ny)} l${r1(6 * k)} ${r1(-24 * k)} l${r1(6 * k)} ${r1(24 * k)}" fill="#6b4a26"/>`).join("") : fig(nx - W * 0.05, ny, H * 0.07, 3, { pose: "carry" })); }
    g += `<ellipse cx="${-W * 0.05}" cy="${H * 0.34}" rx="${W * 0.52}" ry="${H * 0.23}" fill="#ecd9a6"/><ellipse cx="${-W * 0.05}" cy="${H * 0.37}" rx="${W * 0.45}" ry="${H * 0.18}" fill="#9cc66b"/>`;
    const nh = countOf(p, 3, 1, 6), hut = (x, s) => `<g transform="translate(${r1(x)},${r1(H * 0.21)}) scale(${r1(s * k * 100) / 100})">${rect(-90, -100, 180, 100, "#e4cf9f", ' stroke="#bfa871" stroke-width="4"')}<path d="M-110 -100 L0 -170 L110 -100 Z" fill="#c98850"/>${rect(-22, -62, 44, 62, "#8a5a2b")}</g>`;
    for (let i = 0; i < nh; i++) g += hut(-W * 0.36 + i * (W * 0.38 / Math.max(1, nh - 1 || 1)), 0.55);
    const palm = (x, y) => `<path d="M${L([x, y])} Q${L([x + 12 * k, y - H * 0.1])} ${L([x + 6 * k, y - H * 0.2])}" stroke="#8a5a2b" stroke-width="${12 * k}" fill="none"/>` +
      [-1, -0.4, 0.4, 1].map((d) => `<path d="M${L([x + 6 * k, y - H * 0.2])} q${r1(d * 60 * k)} ${r1(-30 * k)} ${r1(d * 110 * k)} ${r1(10 * k)}" stroke="#4f9a3e" stroke-width="${16 * k}" fill="none" stroke-linecap="round"/>`).join("");
    g += palm(-W * 0.44, H * 0.26) + palm(W * 0.12, H * 0.22);
    if (crop !== "none") { const dry = p.weather === "drought";
      g += `<ellipse cx="${-W * 0.08}" cy="${H * 0.28}" rx="${W * 0.13}" ry="${H * 0.045}" fill="${dry ? "#c9a96a" : "#8a6a3e"}"/>`;
      for (let r = 0; r < 2; r++) for (let c = 0; c < 9; c++) g += plantG(-W * 0.18 + c * W * 0.025, H * (0.265 + r * 0.03), 0.6 * k, crop, 0.8, dry, p.season === "harvest"); }
    if (isN(p.level) && +p.level >= 0 || wasOf(p).level !== undefined) { const bx = W * 0.22, by = H * 0.22, fill = Math.round(c01(nv(p, "level", 0.5)) * 6);   // the tiny bank and its vault
      g += rect(bx - W * 0.06, by - H * 0.12, W * 0.12, H * 0.12, "#ece6da", ` stroke="#b9ad90" stroke-width="${3 * k}"`) + `<path d="M${L([bx - W * 0.07, by - H * 0.12])} L${L([bx, by - H * 0.17])} L${L([bx + W * 0.07, by - H * 0.12])} Z" fill="#0f6e6e"/>` +
        `<circle cx="${bx}" cy="${r1(by - H * 0.055)}" r="${r1(H * 0.045)}" fill="#3b3326" stroke="#4a5568" stroke-width="${4 * k}"/>` + [...Array(fill).keys()].map((j) => rect(bx - H * 0.032 + (j % 2) * H * 0.033, by - H * 0.035 - Math.floor(j / 2) * H * 0.02, H * 0.03, H * 0.016, "#f3cf6a")).join(""); }
    const bx = W * 0.38 + Math.sin(t * 0.9) * 6 * k, by = H * 0.18 + Math.sin(t * 1.3) * 3 * k;      // the boat on the shore
    g += `<path d="M${L([bx - 80 * k, by - 16 * k])} L${L([bx + 80 * k, by - 16 * k])} L${L([bx + 58 * k, by + 10 * k])} L${L([bx - 58 * k, by + 10 * k])} Z" fill="#8a5a2b"/>` + rect(bx - 3 * k, by - 110 * k, 6 * k, 94 * k, "#6b4a26") +
      `<path d="M${L([bx + 3 * k, by - 106 * k])} L${L([bx + 60 * k, by - 30 * k])} L${L([bx + 3 * k, by - 30 * k])} Z" fill="#f7f4ee"/>`;
    const cr = nv(p, "goods", 0);
    for (let j = 0; j < Math.ceil(cr - 1e-6); j++) { const one = rect(-W * 0.46 + j * 54 * k, H * 0.3 - (j % 2) * 10 * k, 46 * k, 40 * k, "#b5834a", ` stroke="#7a4e22" stroke-width="${3 * k}"`) + `<path d="M${r1(-W * 0.46 + j * 54 * k)} ${r1(H * 0.3 - (j % 2) * 10 * k)} l${r1(46 * k)} ${r1(40 * k)}" stroke="#7a4e22" stroke-width="${3 * k}"/>`;
      g += j < Math.floor(cr + 1e-6) ? one : `<g opacity="${(cr % 1).toFixed(3)}">${one}</g>`; }
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#1d5e8a");
  },
  twoSector(W, H, p) {
    const k = W / 1920, gy = H * 0.1, t = tOf(p), signs = signsOf(p), crop = p.crop && p.crop !== "auto" ? p.crop : "wheat";
    let g = skyGround(W, H, "#d3e9f4", "#eef5f7", "#c9d79a", gy) + cloud(-W * 0.3, -H * 0.4, k) + cloud(W * 0.35, -H * 0.36, 0.8 * k);
    g += rect(-W, gy - H * 0.02, W * 0.88, H * 0.2, "#b98d5a");
    for (let r = 0; r < 4; r++) for (let c = 0; c < 14; c++) g += plantG(-W * 0.49 + c * W * 0.027, gy + H * (0.02 + r * 0.045), 0.65 * k, crop, 0.8, p.weather === "drought", p.season === "harvest");
    g += rect(-W * 0.12, gy - H * 0.02, W * 0.24, H / 2 - gy, "#dccb9c");
    g += rect(W * 0.12, -H * 0.24, W * 0.36, gy + H * 0.24, "#e6dccb", ` stroke="#b9ad90" stroke-width="${4 * k}"`) + rect(W * 0.11, -H * 0.28, W * 0.38, H * 0.05, "#8d96a0") + rect(W * 0.14, -H * 0.16, W * 0.32, gy + H * 0.16, "#c9bda5");
    for (let j = 0; j < 3; j++) { const mx = W * 0.19 + j * W * 0.1;
      g += rect(mx - W * 0.04, gy - H * 0.06, W * 0.08, H * 0.012, "#a9713c") + `<path d="M${r1(mx - W * 0.02)} ${r1(gy - H * 0.06)} L${r1(mx - W * 0.02)} ${r1(gy - H * 0.09)} L${r1(mx + W * 0.02)} ${r1(gy - H * 0.09)} L${r1(mx + W * 0.02)} ${r1(gy - H * 0.075)}" stroke="#5b7fb8" stroke-width="${8 * k}" fill="none"/>`; }
    g += smallSign(signs[0], -W * 0.3, -H * 0.2, W * 0.3, 44) + smallSign(signs[1], W * 0.3, -H * 0.2, W * 0.3, 44);
    const P = nv(p, "people", 6), S = Math.min(P, nv(p, "taken", 2)), I = Math.min(P - S, nv(p, "part", 0)), F = Math.max(0, P - S - I);
    for (let j = 0; j < Math.ceil(F - 1e-6); j++) g += fig(-W * 0.44 + (j % 6) * W * 0.06, gy + H * 0.1 + Math.floor(j / 6) * H * 0.05, H * 0.15, j, { pose: "work", op: j < Math.floor(F + 1e-6) ? 1 : F % 1, hat: "#f1e3c6" });
    const Sw = Math.floor(S + 1e-6);
    for (let j = 0; j < Sw; j++) g += j < 3 ? fig(W * 0.19 + j * W * 0.1, gy + H * 0.005, H * 0.13, 30 + j, { pose: "sit" }) : fig(W * 0.17 + (j - 3) * W * 0.05, gy + H * 0.14, H * 0.15, 30 + j);
    if (S - Sw > 0.002) { const e = S - Sw; g += fig(-W * 0.14 + e * W * 0.3, gy + H * 0.12, H * 0.15, 30 + Sw, { pose: "walk", t }); }
    g += rect(-W * 0.07, gy + H * 0.09, W * 0.14, H * 0.015, "#8a5a2b") + rect(-W * 0.065, gy + H * 0.105, 8 * k, H * 0.03, "#6b4a26") + rect(W * 0.06, gy + H * 0.105, 8 * k, H * 0.03, "#6b4a26");
    for (let j = 0; j < Math.ceil(I - 1e-6); j++) g += fig(-W * 0.05 + j * W * 0.035, gy + H * 0.13, H * 0.14, 60 + j, { pose: "sit", op: j < Math.floor(I + 1e-6) ? 1 : I % 1 });
    g += heapG(lv(p, "counts", 0, 4), -W * 0.4, gy + H * 0.26, 0.95 * k) + heapG(lv(p, "counts", 1, 4), W * 0.38, gy + H * 0.26, 0.95 * k, { item: "cloth" });
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#5e7a34");
  },
  dealingRoom(W, H, p) {
    const k = W / 1920, gy = H * 0.12, t = tOf(p), n = countOf(p, 4, 2, 6), signs = signsOf(p), trust = c01(nv(p, "level", 1));
    let g = wallFloor(W, H, "#26313c", "#36424e", gy);
    for (let i = -9; i <= 9; i++) g += rect(i * W * 0.11 - W * 0.04, -H * 0.46, W * 0.08, H * 0.12, "#1a232c", ` stroke="#3d4a57" stroke-width="${3 * k}"`);
    const [vnow] = boardOf(p, "value", 0), vold = wasOf(p).value !== undefined && wasOf(p).value !== String(p.value ?? "") ? wasOf(p).value : "";
    g += chalk(W * 0.32, -H * 0.36, W * 0.26, H * 0.15, vnow, vold, { k, bg: "#0f171e", frame: "#4a5568", fg: "#ffd36b", trend: p.trend === "up" || p.trend === "down" ? p.trend : "" });
    const pos = [...Array(n).keys()].map((i) => [-W * 0.42 + (i + 0.5) * (W * 0.84 / n), gy + H * 0.09 - Math.sin(Math.PI * (i + 0.5) / n) * H * 0.06]), dw = Math.min(W * 0.84 / n * 0.86, W * 0.16);
    const pairs = (v) => listOf(v).map((s) => s.split("-").map((x) => parseInt(x, 10) - 1)).filter(([a, b]) => a >= 0 && b >= 0 && a < n && b < n && a !== b);
    const nowL = pairs(p.links), wl = wasOf(p).links, before = wl === undefined ? null : pairs(wl), key = ([a, b]) => `${Math.min(a, b)}-${Math.max(a, b)}`;
    const all = new Map();
    nowL.forEach((q) => all.set(key(q), [q, before && !before.some((b) => key(b) === key(q)) ? phase(p) : 1]));
    (before || []).forEach((q) => { if (!all.has(key(q))) all.set(key(q), [q, 1 - phase(p)]); });
    for (const [[a, b], op] of all.values()) {                                                       // the lit loan lines between desks
      if (op <= 0.01) continue;
      const [x1, y1] = pos[a], [x2, y2] = pos[b], my = Math.min(y1, y2) - H * 0.36, d = `M${r1(x1)} ${r1(y1 - H * 0.2)} Q${r1((x1 + x2) / 2)} ${r1(my)} ${r1(x2)} ${r1(y2 - H * 0.2)}`;
      g += `<path d="${d}" stroke="#f2c14e" stroke-width="${8 * k}" fill="none" opacity="${r1((0.2 + 0.8 * trust) * op * 100) / 100}"${trust < 0.5 ? ` stroke-dasharray="${18 * k} ${14 * k}"` : ""}/>`;
      if (trust >= 0.3) { const u = (t * 0.6) % 1, bx = (1 - u) * (1 - u) * x1 + 2 * u * (1 - u) * (x1 + x2) / 2 + u * u * x2, by = (1 - u) * (1 - u) * (y1 - H * 0.2) + 2 * u * (1 - u) * my + u * u * (y2 - H * 0.2);
        g += `<circle cx="${r1(bx)}" cy="${r1(by)}" r="${r1(10 * k)}" fill="#fff3b0" opacity="${r1(op * trust * 100) / 100}"/>`; }
    }
    pos.forEach(([x, y], i) => {
      const [now, old] = boardOf(p, "prices", i), bad = trust < 0.4, flick = bad && Math.sin(t * 9 + i * 2) > 0.3;
      g += fig(x, y - H * 0.02, H * 0.15, i * 2 + 1, { pose: "sit" }) + rect(x - dw / 2, y - H * 0.06, dw, H * 0.025, "#1f2a33") + rect(x - dw / 2 + 6 * k, y - H * 0.035, dw - 12 * k, H * 0.05, "#2d3748");
      g += [-1, 1].map((d) => rect(x + d * dw * 0.32 - dw * 0.15, y - H * 0.115, dw * 0.3, H * 0.055, flick ? "#7a2020" : d < 0 ? "#2fb463" : "#3a7bd5", ' opacity="0.9"')).join("");
      g += chalk(x, y - H * 0.27, Math.min(dw * 1.05, W * 0.16), H * 0.09, now, old, { k, bg: "#0f171e", frame: "#4a5568", fg: bad ? "#ff6b6b" : "#7dffb0" }) + smallSign(signs[i], x, y + H * 0.04, dw, 38);
    });
    return g + board(p.label, -W * 0.08, -H * 0.42, W * 0.36, "#2a9d8f");
  },
  hospital(W, H, p) {
    const k = W / 1920, gy = H * 0.12, t = tOf(p), n = countOf(p, 3, 1, 4), signs = signsOf(p);
    let g = wallFloor(W, H, "#e6f0f1", "#cdd8dc", gy) + rect(-W, gy - H * 0.12, 2 * W, H * 0.02, "#7fb7b3");
    g += fig(-W * 0.39, gy - H * 0.04, H * 0.16, 7, { col: "#ffffff", bot: "#e3ddcf" }) + rect(-W * 0.48, gy - H * 0.14, W * 0.18, H * 0.14, "#9fc9c6", ` stroke="#6aa39f" stroke-width="${4 * k}"`) +
      rect(-W * 0.48, gy - H * 0.32, W * 0.18, H * 0.17, "#dff0f2", ` opacity="0.6" stroke="#9fbcc4" stroke-width="${4 * k}"`);
    for (let i = 0; i < n; i++) { const dx = n === 1 ? -W * 0.05 : -W * 0.2 + i * (W * 0.34 / (n - 1));
      g += rect(dx - W * 0.04, gy - H * 0.26, W * 0.08, H * 0.26, "#7fa8c9", ` stroke="#5b84a6" stroke-width="${4 * k}"`) + `<circle cx="${r1(dx + W * 0.028)}" cy="${r1(gy - H * 0.13)}" r="${r1(6 * k)}" fill="#f2c14e"/>` + smallSign(signs[i], dx, gy - H * 0.3, W * 0.13, 40); }
    const pv = nv(p, "people", 8), seated = Math.min(pv, 8);
    for (let b = 0; b < 2; b++) g += rect(-W * 0.24 + b * W * 0.2, gy + H * 0.06, W * 0.18, H * 0.015, "#8a9bb0");
    for (let j = 0; j < Math.ceil(seated - 1e-6); j++) g += fig(-W * 0.22 + (j % 4) * W * 0.045 + Math.floor(j / 4) * W * 0.2, gy + H * 0.09, H * 0.14, j, { pose: "sit", op: j < Math.floor(seated + 1e-6) ? 1 : seated % 1 });
    const standing = Math.max(0, pv - 8);
    for (let j = Math.ceil(standing - 1e-6) - 1; j >= 0; j--) g += fig(-W * 0.27 - (j % 12) * W * 0.035, gy + H * 0.15 + Math.floor(j / 12) * H * 0.04, H * 0.16, 20 + j, { op: j < Math.floor(standing + 1e-6) ? 1 : standing % 1 });
    g += rect(W * 0.19, -H * 0.25, W * 0.01, gy + H * 0.25, "#b9ccd2");                              // the ward
    const beds = Math.round(Math.max(1, Math.min(8, nv(p, "seats", 4)))), occ = nv(p, "taken", 1);
    for (let b = 0; b < beds; b++) { const r = Math.floor(b / 4), c = b % 4, x = W * 0.25 + c * W * 0.065, y = gy - H * 0.03 + r * H * 0.12, full = c01(occ - b);
      g += rect(x - W * 0.028, y - H * 0.03, W * 0.056, H * 0.03, "#ffffff", ` stroke="#9fbcc4" stroke-width="${3 * k}"`) + rect(x - W * 0.028, y, 6 * k, H * 0.03, "#8d96a0") + rect(x + W * 0.028 - 6 * k, y, 6 * k, H * 0.03, "#8d96a0") +
        rect(x - W * 0.025, y - H * 0.045, W * 0.018, H * 0.016, "#dfe9ef", ` rx="${4 * k}"`) +
        (full > 0.01 ? `<g opacity="${full.toFixed(3)}"><circle cx="${r1(x - W * 0.016)}" cy="${r1(y - H * 0.045)}" r="${r1(11 * k)}" fill="${SKINS[b % SKINS.length]}"/>${rect(x - W * 0.008, y - H * 0.045, W * 0.034, H * 0.02, "#7fb7b3", ` rx="${6 * k}"`)}</g>` : ""); }
    return g + board(p.label, 0, -H * 0.42, W * 0.4, "#2a7f7a");
  },
  foodShop(W, H, p) {
    const k = W / 1920, gy = H * 0.04, t = tOf(p), n = countOf(p, 2, 1, 4), signs = signsOf(p), item = p.item && p.item !== "auto" ? p.item : "samosa";
    let g = rect(-W, -H / 2, 2 * W, gy + H / 2, "#f3e6cf") + rect(-W, gy, 2 * W, H / 2 - gy, "#cdb894");
    for (let x = -W; x < W; x += 60 * k) g += `<path d="M${r1(x)} ${r1(-H * 0.18)} L${r1(x)} ${r1(gy)}" stroke="#e2d2b4" stroke-width="${2 * k}"/>`;
    for (let y = -H * 0.18; y < gy; y += 60 * k) g += `<path d="M${-W} ${r1(y)} L${W} ${r1(y)}" stroke="#e2d2b4" stroke-width="${2 * k}"/>`;
    const rowsN = Math.max(1, Math.min(4, listOf(p.prices).length || 2));
    g += rowsBoard(-W * 0.2, -H * 0.37, W * 0.16, -H * 0.37 + H * (0.05 + 0.055 * rowsN), [], p, "prices", rowsN, k);
    const ow = W * 0.62 / n, cooks = nv(p, "people", n), glowSet = (name, i) => sv(p, "glow", i, name);
    const ovenX = (i) => -W * 0.4 + (i + 0.5) * ow;
    g += crowdAt(Math.max(0, cooks - n), -W * 0.09, gy + H * 0.02, H * 0.16, 8, { seed: 40, t });  // more cooks than ovens: they crowd
    for (let i = 0; i < n; i++) {
      const ox = ovenX(i), base = gy + H * 0.1, on = c01(cooks - i), L = (a) => a.map(r1).join(" ");
      g += glowBox(ox - ow * 0.45, gy - H * 0.2, ox + ow * 0.45, base + 8 * k, Math.max(glowSet("oven", i + 1), glowSet("ovens", 0)), k);
      if (on > 0.01) g += fig(ox, base - H * 0.02, H * 0.19, i * 3, { pose: "work", op: on, col: "#f7f4ee", bot: "#4a3b2a", hat: "#ffffff", t });
      if (item === "roti" || item === "bread") {                                                   // a tandoor or a baker's oven
        g += item === "roti" ? `<path d="M${L([ox - 70 * k, base])} L${L([ox - 56 * k, base - 110 * k])} L${L([ox + 56 * k, base - 110 * k])} L${L([ox + 70 * k, base])} Z" fill="#b5652b"/><ellipse cx="${r1(ox)}" cy="${r1(base - 110 * k)}" rx="${r1(56 * k)}" ry="${r1(14 * k)}" fill="#3b2a1a"/><ellipse cx="${r1(ox)}" cy="${r1(base - 110 * k)}" rx="${r1(34 * k)}" ry="${r1(8 * k)}" fill="#ff8a3c" opacity="${r1((0.6 + 0.4 * Math.sin(t * 6 + i)) * 100) / 100}"/>`
          : rect(ox - 80 * k, base - 120 * k, 160 * k, 120 * k, "#a8553a", ` stroke="#6b2f1e" stroke-width="${4 * k}"`) + `<path d="M${L([ox - 40 * k, base - 20 * k])} L${L([ox - 40 * k, base - 70 * k])} Q${L([ox, base - 100 * k])} ${L([ox + 40 * k, base - 70 * k])} L${L([ox + 40 * k, base - 20 * k])} Z" fill="#ff8a3c" opacity="${r1((0.6 + 0.4 * Math.sin(t * 5 + i)) * 100) / 100}"/>`;
      } else if (item === "tea") {
        g += rect(ox - 60 * k, base - 60 * k, 120 * k, 60 * k, "#4a5568") + `<path d="M${L([ox - 40 * k, base - 60 * k])} L${L([ox - 30 * k, base - 120 * k])} L${L([ox + 30 * k, base - 120 * k])} L${L([ox + 40 * k, base - 60 * k])} Z" fill="#c7ccd3"/>` +
          [0, 1, 2].map((j) => { const u = (t * 0.5 + j / 3) % 1; return `<circle cx="${r1(ox + Math.sin(t + j) * 8 * k)}" cy="${r1(base - 130 * k - u * H * 0.08)}" r="${r1((8 + u * 12) * k)}" fill="#ffffff" opacity="${r1((0.7 - u * 0.7) * 100) / 100}"/>`; }).join("");
      } else {                                                                                       // a kadhai of oil on its burner
        g += rect(ox - 50 * k, base - 50 * k, 100 * k, 50 * k, "#4a5568") + `<path d="M${L([ox - 90 * k, base - 80 * k])} Q${L([ox, base - 20 * k])} ${L([ox + 90 * k, base - 80 * k])} Z" fill="#2d3748"/><ellipse cx="${r1(ox)}" cy="${r1(base - 80 * k)}" rx="${r1(90 * k)}" ry="${r1(16 * k)}" fill="#c99a2e"/>` +
          [0, 1, 2, 3].map((j) => `<circle cx="${r1(ox - 50 * k + j * 32 * k)}" cy="${r1(base - 82 * k)}" r="${r1((4 + 3 * Math.abs(Math.sin(t * 5 + j + i))) * k)}" fill="#f7e3a0"/>`).join("") + (item === "mithai" ? "" : itemG(item, ox + 20 * k, base - 80 * k, 0.6 * k));
      }
      g += smallSign(signs[i], ox, base + H * 0.035, Math.min(ow * 0.9, W * 0.16), 38);
    }
    const cy = gy + H * 0.17;                                                                        // the counter with its trays and stacks
    g += glowBox(-W * 0.475, cy - H * 0.05, W * 0.305, cy + H * 0.11, glowSet("counter", 0), k) + rect(-W * 0.47, cy, W * 0.77, H * 0.1, "#a9713c", ` stroke="#7a4e22" stroke-width="${5 * k}"`) + rect(-W * 0.48, cy - H * 0.015, W * 0.79, H * 0.02, "#7a4e22");
    if (hasList(p, "counts")) for (let i = 0; i < n; i++) { const m = lv(p, "counts", i, 0), ox = ovenX(i);
      for (let j = 0; j < Math.ceil(m - 1e-6); j++) { const one = itemG(item, ox, cy - H * 0.015 - j * (item === "roti" ? 9 : 26) * k, 0.8 * k, j); g += j < Math.floor(m + 1e-6) ? one : `<g opacity="${(m % 1).toFixed(3)}">${one}</g>`; } }
    else g += stackIn(nv(p, "goods", 8), -W * 0.45, cy - H * 0.2, W * 0.28, cy - H * 0.015, item, k);
    const tx = W * 0.39, tq = nv(p, "taken", 0);                                                     // the one till and the queue at it
    for (let j = Math.ceil(tq - 1e-6) - 1; j >= 0; j--) g += fig(tx - W * 0.02 + j * 14 * k, cy - H * 0.01 - j * H * 0.035, H * 0.17 * Math.pow(0.94, j), 70 + j, { col: "#f7f4ee", bot: "#4a3b2a", op: j < Math.floor(tq + 1e-6) ? 1 : tq % 1 });
    g += glowBox(tx - W * 0.075, cy - H * 0.13, tx + W * 0.075, cy + H * 0.11, glowSet("till", 0), k) + rect(tx - W * 0.06, cy, W * 0.12, H * 0.1, "#6b7280") + rect(tx - W * 0.05, cy - H * 0.06, W * 0.1, H * 0.06, "#2d3748", ` rx="${6 * k}"`) +
      textA(rollValue(p), tx, cy - H * 0.018, fitFs(rollValue(p), W * 0.09, 40 * k), "#7dffb0", 800, "middle");
    const f = sv(p, "shut", 1, "shutter");
    g += shutterG(-W, -H / 2, 2 * W, H, f, k);
    return g + paperNote(W * 0.33, -H * 0.36, p.notice, k, W * 0.28) + board(p.label, 0, -H * 0.43, W * 0.36, "#c0392b");
  },
};

const LIGHT = { dawn: ["#ff9a76", 0.13], evening: ["#ff8a3c", 0.16], night: ["#0b1d3a", 0.45] };

// Weather over an outdoor place: rain falling, a drought's heat, a flood's water, pests over the crops (a farm draws
// its own flood and pests on its field).
const OUTDOOR = new Set(["market", "port", "factory", "village", "city", "twoCountries", "mandi", "foodStreet", "labourChowk", "farm", "riverTown",
  "mohalla", "teaEstate", "busStand", "petrolPump", "godown", "island", "twoSector"]);
function weatherG(W, H, w, t, kind) {
  const k = W / 1920;
  if (w === "rain") {
    let g = rect(-W, -H / 2, 2 * W, H, "#4d5d70", ' opacity="0.18"') + [-0.78, -0.43, 0.43, 0.78].map((f, i) => `<g opacity="0.9"><ellipse cx="${r1(f * W)}" cy="${r1(-H * 0.42)}" rx="${r1(W * 0.16)}" ry="${r1(H * 0.06)}" fill="#8792a0"/><ellipse cx="${r1(f * W + W * 0.08)}" cy="${r1(-H * 0.45)}" rx="${r1(W * 0.1)}" ry="${r1(H * 0.05)}" fill="#9aa4b0"/></g>`).join("") +
      `<ellipse cx="${r1(W * 0.36)}" cy="${r1(-H * 0.36)}" rx="${r1(W * 0.09)}" ry="${r1(H * 0.09)}" fill="#8f99a6"/>`;   // the sun of a sunny place hides
    for (let i = 0; i < 140; i++) { const x = -W + rnd(i, 1) * 2 * W, y = -H / 2 + (((rnd(i, 2) + t * 1.4) % 1) * H);
      g += `<path d="M${r1(x)} ${r1(y)} l${r1(-10 * k)} ${r1(40 * k)}" stroke="#e4eef7" stroke-width="${3 * k}" opacity="0.75"/>`; }
    return g;
  }
  if (w === "drought") return rect(-W, -H / 2, 2 * W, H, "#e8a23a", ' opacity="0.16"') + `<circle cx="${W * 0.36}" cy="${-H * 0.36}" r="${H * 0.085}" fill="#ffc23a" opacity="0.9"/>` +
    [...Array(12).keys()].map((i) => { const a = i * Math.PI / 6 + t * 0.2; return `<path d="M${r1(W * 0.36 + Math.cos(a) * H * 0.11)} ${r1(-H * 0.36 + Math.sin(a) * H * 0.11)} L${r1(W * 0.36 + Math.cos(a) * H * 0.15)} ${r1(-H * 0.36 + Math.sin(a) * H * 0.15)}" stroke="#ffc23a" stroke-width="${8 * k}" stroke-linecap="round"/>`; }).join("");
  if (w === "flood" && kind !== "farm") { let g = rect(-W, H * 0.16, 2 * W, H * 0.34, "#5f9fcf", ' opacity="0.6"');
    for (let i = -12; i < 12; i++) { const x = ((i * W * 0.1 + t * 50 * k) % (2 * W) + 2 * W) % (2 * W) - W; g += `<path d="M${r1(x)} ${r1(H * 0.2 + (i % 3) * H * 0.07)} q${r1(W * 0.025)} ${r1(-H * 0.015)} ${r1(W * 0.05)} 0" stroke="#ffffff" stroke-width="${3 * k}" fill="none" opacity="0.6"/>`; }
    return g; }
  if (w === "pests" && kind !== "farm") { let g = "";
    for (let i = 0; i < 70; i++) { const x = -W * 0.5 + rnd(i, 3) * W + Math.sin(t * 3 + i) * 16 * k, y = H * 0.02 + rnd(i, 4) * H * 0.22 + Math.cos(t * 4 + i) * 9 * k;
      g += `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(5 * k)}" ry="${r1(3.5 * k)}" fill="#2b2b33"/>`; }
    return g; }
  return "";
}

export function world(p = {}) {
  const W = Math.max(200, +p.w || 3840) / 2, H = W * 0.5625, kind = KINDS[p.kind] ? p.kind : "market";
  const light = LIGHT[p.light] ? rect(-W, -H / 2, 2 * W, H, LIGHT[p.light][0], ` opacity="${LIGHT[p.light][1]}"`) : "";
  return `<g>${KINDS[kind](W, H, p)}${OUTDOOR.has(kind) ? weatherG(W, H, p.weather, tOf(p), kind) : ""}${light}</g>`;
}

export const WORLD_KINDS = Object.keys(KINDS);

// Where things are in a world, for a game board or a plan that points at a place: named boxes as fractions of the
// visible stage (the middle half of the drawing, x and y from 0 to 1). Numbered spots (stall2, counter1, desk3, shed1,
// shop2) are also reachable by their sign's words. bie/brain/game_levels.py names the same spots (a test keeps them equal).
const SPOTS = {
  market: (W, H, p) => { const gy = H * 0.12, n = countOf(p, 4, 2, 6), o = { floor: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const x = -W * 0.42 + (i + 0.5) * (W * 0.84 / n), sw = (W * 0.84 / n) * 0.86; o[`stall${i + 1}`] = [x - sw / 2, gy - H * 0.28, x + sw / 2, gy + H * 0.02]; }
    return o; },
  bankHall: (W, H, p) => { const gy = H * 0.14, n = countOf(p, 3, 1, 5), cw = W * 0.56 / n, r = H * 0.17, vy = gy - r * 1.25;
    const o = { vault: [W * 0.33 - r * 1.25, vy - r * 1.3, W * 0.33 + r * 1.25, gy], queue: [-W * 0.32, gy + H * 0.04, -W * 0.04, gy + H * 0.24], floor: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const x = -W * 0.42 + i * cw; o[`counter${i + 1}`] = [x, gy - H * 0.38, x + cw - W * 0.02, gy]; }
    return o; },
  centralBank: (W, H) => { const gy = H * 0.16, r = H * 0.2, vy = gy - r * 1.15;
    return { vault: [-r * 1.4, vy - r * 1.25, r * 1.4, gy], floor: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] }; },
  exchangeFloor: (W, H) => { const gy = H * 0.16;
    return { board: [-W * 0.36, -H * 0.42, W * 0.36, -H * 0.04], desks: [-W * 0.45, gy, W * 0.5, gy + H * 0.25], floor: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] }; },
  port: (W, H) => { const gy = H * 0.1;
    return { ship: [-W * 0.32, gy - H * 0.24, W * 0.14, gy + H * 0.02], crane: [W * 0.02, -H * 0.3, W * 0.32, gy + H * 0.06], dock: [-W / 2, gy + H * 0.12, W / 2, H * 0.45] }; },
  factory: (W, H) => { const gy = H * 0.12, o = { belt: [-W * 0.2, gy + H * 0.03, W * 0.3, gy + H * 0.14], chimney: [W * 0.24, -H * 0.45, W * 0.3, gy] };
    for (let i = 0; i < 3; i++) { const x = -W * 0.42 + i * W * 0.22; o[`shed${i + 1}`] = [x, gy - H * 0.26, x + W * 0.2, gy]; }
    return o; },
  village: (W, H) => { const gy = H * 0.1, k = W / 1920;
    return { field: [-W / 2, gy + H * 0.02, W / 2, H * 0.45], hut: [-W * 0.36 - 110 * k, gy - 170 * k, -W * 0.36 + 110 * k, gy],
      well: [W * 0.28 - 46 * k, gy + H * 0.02 - 90 * k, W * 0.28 + 46 * k, gy + H * 0.02], tree: [W * 0.12 - 110 * k, gy - 180 * k, W * 0.12 + 110 * k, gy] }; },
  office: (W, H, p) => { const gy = H * 0.14, n = countOf(p, 5, 1, 6), o = { floor: [-W / 2, gy + H * 0.2, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const x = (i - (n - 1) / 2) * W * 0.2; o[`desk${i + 1}`] = [x - W * 0.08, gy - H * 0.05, x + W * 0.08, gy + H * 0.15]; }
    return o; },
  court: (W, H) => { const gy = H * 0.16;
    return { bench: [-W * 0.3, gy - H * 0.27, W * 0.3, gy], left: [-W * 0.46, gy - H * 0.12, -W * 0.36, gy], right: [W * 0.36, gy - H * 0.12, W * 0.46, gy], floor: [-W / 2, gy + H * 0.15, W / 2, H * 0.45] }; },
  city: (W, H) => { const gy = H * 0.18, o = { road: [-W / 2, gy, W / 2, H * 0.45] };
    [-0.3, 0, 0.3].forEach((f, i) => { o[`shop${i + 1}`] = [f * W - W * 0.05, gy - H * 0.2, f * W + W * 0.05, gy]; });
    return o; },
  assembly: (W, H) => { const gy = H * 0.16;
    return { podium: [-W * 0.1, gy - H * 0.19, W * 0.1, gy], seats: [-W * 0.45, gy - H * 0.45, W * 0.45, gy - H * 0.12], floor: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] }; },
  twoCountries: (W, H) => { const gy = H * 0.08;
    return { left: [-W / 2, gy + H * 0.02, -W * 0.02, H * 0.45], right: [W * 0.02, gy + H * 0.02, W / 2, H * 0.45], border: [-W * 0.04, -H * 0.2, W * 0.04, H * 0.45],
      road: [-W / 2, gy + H * 0.15, W / 2, gy + H * 0.24] }; },
  forexCounter: (W, H) => { const gy = H * 0.14;
    return { counter: [-W * 0.46, gy - H * 0.46, W * 0.04, gy], board: [W * 0.05, -H * 0.42, W * 0.35, -H * 0.08], queue: [W * 0.06, gy + H * 0.02, W * 0.46, gy + H * 0.24],
      floor: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] }; },
  // the Sloman book's places: fixed spots first, then the numbered ones (their count follows count, signs, the default)
  mandi: (W, H, p) => { const gy = H * 0.1, n = countOf(p, 3, 1, 5), o = { board: [-W * 0.15, -H * 0.22, W * 0.15, -H * 0.06], yard: [-W * 0.48, gy + H * 0.02, W * 0.48, H * 0.3],
      buyers: [-W * 0.4, gy - H * 0.1, W * 0.4, gy + H * 0.07], road: [-W * 0.5, gy + H * 0.02, -W * 0.28, gy + H * 0.17], truck: [W * 0.2, gy - H * 0.12, W * 0.48, gy + H * 0.05],
      notice: [W * 0.17, -H * 0.21, W * 0.45, -H * 0.12] };
    for (let i = 0; i < n; i++) { const x = (i - (n - 1) / 2) * W * 0.22; o[`heap${i + 1}`] = [x - W * 0.1, gy - H * 0.05, x + W * 0.1, gy + H * 0.16]; }
    return o; },
  foodStreet: (W, H, p) => { const gy = H * 0.1, n = countOf(p, 5, 1, 12), sp = W * 0.92 / n, cw = Math.min(sp * 0.86, W * 0.2), o = { lane: [-W / 2, gy + H * 0.12, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const x = -W * 0.46 + (i + 0.5) * sp; o[`stall${i + 1}`] = [x - cw * 0.6, gy - H * 0.25, x + cw * 0.6, gy + H * 0.06]; }
    return o; },
  labourChowk: (W, H) => { const gy = H * 0.1;
    return { crowd: [-W * 0.42, gy - H * 0.1, W * 0.02, gy + H * 0.16], truck: [W * 0.15, gy - H * 0.12, W * 0.48, gy + H * 0.14], board: [-W * 0.03, -H * 0.3, W * 0.19, -H * 0.13],
      road: [-W / 2, gy - H * 0.04, W / 2, gy + H * 0.02], floor: [-W / 2, gy + H * 0.17, W / 2, H * 0.45] }; },
  factoryFloor: (W, H, p) => { const gy = H * 0.06, n = countOf(p, 4, 1, 8), slot = W * 0.58 / n, o = { belt: [-W * 0.47, gy + H * 0.17, W * 0.3, gy + H * 0.25],
      godown: [W * 0.29, -H * 0.18, W * 0.49, gy + H * 0.24], board: [-W * 0.42, -H * 0.3, -W * 0.24, -H * 0.22], notice: [-W * 0.06, -H * 0.3, W * 0.2, -H * 0.17], floor: [-W / 2, gy + H * 0.26, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const mx = -W * 0.46 + (i + 0.5) * slot; o[`machine${i + 1}`] = [mx - slot * 0.42, gy - H * 0.04, mx + slot * 0.42, gy + H * 0.15]; }
    return o; },
  farm: (W, H, p) => { const fx0 = -W * 0.47, fx1 = W * 0.27, fy0 = -H * 0.03, fy1 = H * 0.28, n = countOf(p, 2, 1, 6),
      o = { field: [fx0, fy0, fx1, fy1], heap: [W * 0.29, H * 0.05, W * 0.47, fy1], fence: [fx0, fy1 - H * 0.04, fx1, fy1 + H * 0.02] };
    for (let i = 0; i < n; i++) { const a = fx0 + i * (fx1 - fx0) / n; o[`plot${i + 1}`] = [a, fy0, a + (fx1 - fx0) / n, fy1]; }
    return o; },
  riverTown: (W, H) => ({ factory: [-W * 0.48, -H * 0.3, -W * 0.24, 0], pipe: [-W * 0.26, -H * 0.08, -W * 0.16, H * 0.05], river: [-W / 2, H * 0.02, W / 2, H * 0.2],
    ghat: [W * 0.2, -H * 0.02, W * 0.49, H * 0.14], bank: [-W / 2, H * 0.22, W / 2, H * 0.45] }),
  mohalla: (W, H, p) => { const gy = H * 0.1, n = countOf(p, 5, 1, 8), sw = W * 0.92 / n, o = { road: [-W / 2, gy + H * 0.06, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const x = -W * 0.46 + (i + 0.5) * sw; o[`house${i + 1}`] = [x - sw * 0.45, gy - H * 0.34, x + sw * 0.45, gy]; }
    return o; },
  canteen: (W, H, p) => { const gy = H * 0.1, n = countOf(p, 3, 1, 6), rh = (H * 0.32 - 16) / n, o = { menu: [W * 0.04, -H * 0.34, W * 0.46, -H * 0.02], counter: [-W * 0.48, gy - H * 0.2, -W * 0.06, gy + H * 0.02],
      tables: [-W * 0.1, gy - H * 0.05, W * 0.46, gy + H * 0.14], notice: [-W * 0.38, -H * 0.36, -W * 0.22, -H * 0.21], floor: [-W / 2, gy + H * 0.17, W / 2, H * 0.45] };
    for (let j = 0; j < n; j++) o[`row${j + 1}`] = [W * 0.04, -H * 0.34 + 8 + j * rh, W * 0.46, -H * 0.34 + 8 + (j + 1) * rh];
    return o; },
  home: (W, H) => { const gy = H * 0.12;
    return { kitchen: [-W / 2, -H * 0.44, -W * 0.17, gy], stove: [-W * 0.36, gy - H * 0.24, -W * 0.27, gy - H * 0.13], fridge: [-W * 0.47, gy - H * 0.37, -W * 0.37, gy],
      counter: [-W * 0.37, gy - H * 0.15, -W * 0.19, gy], living: [-W * 0.17, -H * 0.44, W * 0.17, gy], sofa: [-W * 0.14, gy - H * 0.13, W * 0.14, gy], tv: [-W * 0.08, -H * 0.28, W * 0.08, -H * 0.16],
      study: [W * 0.17, -H * 0.44, W / 2, gy], desk: [W * 0.2, gy - H * 0.13, W * 0.38, gy], door: [W * 0.39, gy - H * 0.3, W * 0.48, gy], floor: [-W / 2, gy + H * 0.04, W / 2, H * 0.45] }; },
  teaEstate: (W, H) => { const gy = H * 0.12;
    return { garden: [-W * 0.45, -H * 0.25, W * 0.2, gy - H * 0.04], factory: [W * 0.22, -H * 0.36, W * 0.46, gy], lines: [-W * 0.47, gy - H * 0.14, -W * 0.18, gy],
      gate: [-W * 0.17, gy - H * 0.23, W * 0.07, gy], board: [-W * 0.15, -H * 0.23, W * 0.05, -H * 0.12], union: [W * 0.08, gy - H * 0.2, W * 0.21, gy], road: [-W / 2, gy + H * 0.06, W / 2, H * 0.45] }; },
  busStand: (W, H, p) => { const gy = H * 0.12, n = countOf(p, 2, 1, 4), bw = W * 0.9 / n, o = { platform: [-W / 2, gy + H * 0.05, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const bx = -W * 0.45 + (i + 0.5) * bw; o[`bay${i + 1}`] = [bx - bw * 0.45, -H * 0.27, bx + bw * 0.45, gy]; }
    return o; },
  petrolPump: (W, H, p) => { const gy = H * 0.08, n = countOf(p, 2, 1, 4), pw = W * 0.66 / n, o = { board: [W * 0.32, -H * 0.36, W * 0.48, -H * 0.19], road: [-W / 2, gy + H * 0.1, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const px = -W * 0.4 + (i + 0.5) * pw; o[`pump${i + 1}`] = [px - pw * 0.4, gy - H * 0.22, px + pw * 0.4, gy + H * 0.08]; }
    return o; },
  venue: (W, H) => { const gy = H * 0.14;
    return { seats: [-W * 0.16, -H * 0.2, W * 0.48, gy + H * 0.11], screen: [-W * 0.1, -H * 0.42, W * 0.42, -H * 0.24], window: [-W * 0.44, -H * 0.2, -W * 0.28, -H * 0.04],
      door: [-W * 0.235, gy - H * 0.28, -W * 0.185, gy], board: [-W * 0.47, -H * 0.36, -W * 0.25, -H * 0.22], foyer: [-W / 2, gy + H * 0.02, -W * 0.22, H * 0.45] }; },
  godown: (W, H) => { const gy = H * 0.12;
    return { store: [-W * 0.28, -H * 0.22, W * 0.1, gy], door: [W * 0.12, -H * 0.18, W * 0.3, gy], board: [-W * 0.49, -H * 0.2, -W * 0.33, -H * 0.06], yard: [-W / 2, gy + H * 0.04, W / 2, H * 0.45] }; },
  island: (W, H) => ({ land: [-W * 0.45, H * 0.12, W * 0.4, H * 0.45], field: [-W * 0.21, H * 0.2, W * 0.05, H * 0.32], huts: [-W * 0.38, H * 0.05, W * 0.06, H * 0.21],
    bank: [W * 0.16, H * 0.05, W * 0.28, H * 0.22], boat: [W * 0.3, H * 0.07, W * 0.46, H * 0.2], sea: [-W / 2, -H * 0.12, W / 2, H * 0.1], neighbour: [W * 0.28, -H * 0.21, W * 0.48, -H * 0.01],
    beach: [-W / 2, H * 0.24, -W * 0.36, H * 0.4] }),
  twoSector: (W, H) => { const gy = H * 0.1;
    return { farm: [-W / 2, gy - H * 0.02, -W * 0.12, gy + H * 0.2], shed: [W * 0.12, -H * 0.24, W * 0.48, gy + H * 0.04], bench: [-W * 0.08, gy + H * 0.04, W * 0.08, gy + H * 0.13], path: [-W * 0.12, gy, W * 0.12, H * 0.45] }; },
  dealingRoom: (W, H, p) => { const gy = H * 0.12, n = countOf(p, 4, 2, 6), dw = Math.min(W * 0.84 / n * 0.86, W * 0.16), o = { board: [W * 0.19, -H * 0.36, W * 0.45, -H * 0.21], floor: [-W / 2, gy + H * 0.16, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const x = -W * 0.42 + (i + 0.5) * (W * 0.84 / n), y = gy + H * 0.09 - Math.sin(Math.PI * (i + 0.5) / n) * H * 0.06; o[`desk${i + 1}`] = [x - dw / 2, y - H * 0.27, x + dw / 2, y + H * 0.06]; }
    return o; },
  hospital: (W, H, p) => { const gy = H * 0.12, n = countOf(p, 3, 1, 4), o = { reception: [-W * 0.48, gy - H * 0.32, -W * 0.3, gy], queue: [-W * 0.26, gy - H * 0.02, W * 0.16, gy + H * 0.16],
      ward: [W * 0.2, -H * 0.2, W * 0.49, gy + H * 0.12], floor: [-W / 2, gy + H * 0.17, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const dx = n === 1 ? -W * 0.05 : -W * 0.2 + i * (W * 0.34 / (n - 1)); o[`cabin${i + 1}`] = [dx - W * 0.05, gy - H * 0.34, dx + W * 0.05, gy]; }
    return o; },
  foodShop: (W, H, p) => { const gy = H * 0.04, n = countOf(p, 2, 1, 4), ow = W * 0.62 / n, o = { counter: [-W * 0.47, gy + H * 0.15, W * 0.3, gy + H * 0.27], till: [W * 0.32, gy + H * 0.04, W * 0.46, gy + H * 0.27],
      board: [-W * 0.2, -H * 0.37, W * 0.16, -H * 0.2], floor: [-W / 2, gy + H * 0.28, W / 2, H * 0.45] };
    for (let i = 0; i < n; i++) { const ox = -W * 0.4 + (i + 0.5) * ow; o[`oven${i + 1}`] = [ox - ow * 0.45, gy - H * 0.1, ox + ow * 0.45, gy + H * 0.1]; }
    return o; },
};
const NUMBERED = { market: "stall", bankHall: "counter", office: "desk", factory: "shed", city: "shop", mandi: "heap", foodStreet: "stall", factoryFloor: "machine",
  farm: "plot", mohalla: "house", canteen: "row", busStand: "bay", petrolPump: "pump", dealingRoom: "desk", hospital: "cabin", foodShop: "oven" };
const NAMED = { twoCountries: ["left", "right"], twoSector: ["farm", "shed"] };   // a sign's words reach a fixed spot too

export function worldSpots(p = {}) {
  const W = 1920, H = 1080, kind = SPOTS[p.kind] ? p.kind : "market", raw = SPOTS[kind](W, H, p), out = {};
  const f = (v, lo, span) => Math.max(0, Math.min(1, (v - lo) / span));
  for (const [name, [x0, y0, x1, y1]] of Object.entries(raw)) {
    const x = f(x0, -W / 2, W), y = f(y0, -H / 2, H);
    out[name] = { x: +x.toFixed(4), y: +y.toFixed(4), w: +(f(x1, -W / 2, W) - x).toFixed(4), h: +(f(y1, -H / 2, H) - y).toFixed(4) };
  }
  const pre = NUMBERED[kind];
  if (pre) signsOf(p).forEach((sg, i) => { if (out[`${pre}${i + 1}`] && !(sg in out)) out[sg] = out[`${pre}${i + 1}`]; });
  if (NAMED[kind]) signsOf(p).forEach((sg, i) => { if (NAMED[kind][i] && !(sg in out)) out[sg] = out[NAMED[kind][i]]; });
  return out;
}

