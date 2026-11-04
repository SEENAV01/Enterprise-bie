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

const KINDS = {
  market(W, H, p) {
    const gy = H * 0.12, n = countOf(p, 4, 2, 6), signs = signsOf(p);
    const aw = ["#e5484d", "#3a7bd5", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f"];
    let back = "";
    for (let i = -7; i <= 7; i++) { const h = H * (0.22 + ((((i * 7 + 21) % 5) + 5) % 5) * 0.04); back += rect(i * W * 0.14 - W * 0.06, gy - h, W * 0.12, h, i % 2 ? "#e9dcc5" : "#e2d3b8", ' stroke="#cdbb98" stroke-width="3"'); }
    let stalls = "";
    for (let i = 0; i < n; i++) {
      const x = -W * 0.42 + (i + 0.5) * (W * 0.84 / n), sw = (W * 0.84 / n) * 0.86, a = aw[i % aw.length], y = gy + H * 0.02;
      let awning = "";
      for (let k = 0; k < 6; k++) { const l = x - sw / 2 + k * sw / 6, r = l + sw / 6;
        awning += `<path d="M${l} ${y - H * 0.3} L${r} ${y - H * 0.3} L${r} ${y - H * 0.24} Q${(l + r) / 2} ${y - H * 0.21} ${l} ${y - H * 0.24} Z" fill="${k % 2 ? "#f7efe2" : a}"/>`; }
      stalls += rect(x - sw / 2, y - H * 0.3, 10, H * 0.3, "#8a5a2b") + rect(x + sw / 2 - 10, y - H * 0.3, 10, H * 0.3, "#8a5a2b") +
        rect(x - sw / 2, y - H * 0.06, sw, H * 0.06, "#a9713c", ' stroke="#7a4e22" stroke-width="3"') + awning +
        [0, 1, 2].map((k) => `<circle cx="${x - sw * 0.25 + k * sw * 0.25}" cy="${y - H * 0.08}" r="${sw * 0.07}" fill="${aw[(i + k + 2) % aw.length]}" opacity="0.9"/>`).join("") +
        smallSign(signs[i], x, y - H * 0.17, sw * 0.8, 40);
    }
    return skyGround(W, H, "#cfe8f5", "#eaf4f9", "#d9c288", gy) + cloud(-W * 0.3, -H * 0.36, 1.2) + cloud(W * 0.25, -H * 0.3, 1) + back +
      (p.crowd ? crowdBand(-W, W, gy + H * 0.02, H * 0.09, 3) : "") + stalls +
      `<ellipse cx="0" cy="${H * 0.36}" rx="${W * 0.44}" ry="${H * 0.1}" fill="#cdb67f" opacity="0.4"/>` + board(p.label, 0, -H * 0.4, W * 0.4, "#8a5a2b");
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
    return wallFloor(W, H, wall, "#d8cbb3", gy) + win + (p.crowd ? crowdBand(-W, -W * 0.5, gy + H * 0.1, H * 0.1, 2) : "") + counter +
      rect(vx - r * 1.25, vy - r * 1.3, r * 2.5, gy - (vy - r * 1.3), "#8e96a1", ` rx="${r * 0.12}"`) + vaultDoor(vx, vy, r, p.open === true, false) + posts +
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
    return wallFloor(W, H, "#24303b", "#3a4652", gy) + rect(-W * 0.36, -H * 0.42, W * 0.72, H * 0.38, "#0f171e", ` rx="${W * 0.01}" stroke="#4a5568" stroke-width="6"`) +
      `<path d="M${pts.map((q) => q.join(" ")).join(" L")}" fill="none" stroke="${c}" stroke-width="8" stroke-linejoin="round"/>` + ticker +
      (p.crowd ? crowdBand(-W, W, gy + H * 0.02, H * 0.08, 5) : "") + desks + board(p.label, 0, -H * 0.445, W * 0.36, "#2a9d8f");
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
    const smoke = p.smoke === false ? "" : [0, 1, 2, 3].map((k) => `<circle cx="${W * 0.27 + k * W * 0.03}" cy="${-H * 0.38 - k * H * 0.04}" r="${H * (0.03 + k * 0.012)}" fill="#c7ccd3" opacity="${0.8 - k * 0.15}"/>`).join("");
    const belt = rect(-W * 0.2, gy + H * 0.08, W * 0.5, H * 0.03, "#4a5568") + [...Array(8).keys()].map((k) => `<circle cx="${-W * 0.19 + k * W * 0.068}" cy="${gy + H * 0.125}" r="${H * 0.014}" fill="#2d3748"/>`).join("") +
      [0, 1, 2, 3].map((k) => rect(-W * 0.16 + k * W * 0.11, gy + H * 0.035, W * 0.05, H * 0.045, "#c8a06a", ' stroke="#8a6d3b" stroke-width="3"')).join("");
    return skyGround(W, H, "#dfe9ef", "#eef3f5", "#c9c4b8", gy) + sheds + rect(W * 0.25, -H * 0.36, W * 0.035, gy + H * 0.36, "#9b4a3a") + smoke + belt + board(p.label, -W * 0.1, -H * 0.42, W * 0.4, "#4a5568");
  },
  village(W, H, p) {
    const gy = H * 0.1, crop = p.season === "harvest" ? "#d9b34a" : "#8fbf5a";
    let rows = "";
    for (let i = 0; i < 9; i++) rows += `<path d="M${-W} ${gy + H * 0.03 + i * H * 0.04} L${W} ${gy + H * 0.03 + i * H * 0.04}" stroke="${shade(crop, 0.85)}" stroke-width="${6 + i}" opacity="0.6"/>`;
    const hut = (x, s) => `<g transform="translate(${x},${gy}) scale(${s})">${rect(-90, -100, 180, 100, "#e4cf9f", ' stroke="#bfa871" stroke-width="4"')}<path d="M-110 -100 L0 -170 L110 -100 Z" fill="#c98850" stroke="#a5693a" stroke-width="4"/>${rect(-22, -62, 44, 62, "#8a5a2b")}</g>`;
    const tree = (x, s) => `<g transform="translate(${x},${gy}) scale(${s})">${rect(-10, -70, 20, 70, "#8a5a2b")}<circle cx="0" cy="-100" r="56" fill="#9dbb6e"/><circle cx="-42" cy="-74" r="40" fill="#8fae5f"/><circle cx="42" cy="-74" r="40" fill="#a8c47e"/></g>`;
    const well = `<g transform="translate(${W * 0.28},${gy + H * 0.02})">${rect(-40, -50, 80, 50, "#b9b2a4", ' stroke="#8a8172" stroke-width="4"')}<path d="M-46 -90 L46 -90" stroke="#8a5a2b" stroke-width="8"/><path d="M-40 -90 L-40 -50 M40 -90 L40 -50" stroke="#8a5a2b" stroke-width="6"/></g>`;
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
      (p.crowd ? crowdBand(-W, W, gy + H * 0.04, H * 0.08, 7) : "") + board(p.label, 0, -H * 0.42, W * 0.4, "#4a5568");
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
};

const LIGHT = { evening: ["#ff8a3c", 0.16], night: ["#0b1d3a", 0.45] };

export function world(p = {}) {
  const W = Math.max(200, +p.w || 3840) / 2, H = W * 0.5625, kind = KINDS[p.kind] ? p.kind : "market";
  const light = LIGHT[p.light] ? rect(-W, -H / 2, 2 * W, H, LIGHT[p.light][0], ` opacity="${LIGHT[p.light][1]}"`) : "";
  return `<g>${KINDS[kind](W, H, p)}${light}</g>`;
}

export const WORLD_KINDS = Object.keys(KINDS);
