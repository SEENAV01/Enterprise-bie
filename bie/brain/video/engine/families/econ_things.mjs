// Family "econ_things" (Sloman economics book, 5 November 2026): the everyday things, vehicles, buildings, papers and
// machines of the book's Indian stories, as parametric saanche with states a scene plan can change on the cue word.
// One rich drawing per idea: a sack or heap with its contents and fill, a vehicle with class, fuel, damage and riders,
// a row of houses with tags, boards, fire and flood, a petrol pump with its price, litres and tax share, a godown with
// its stock flowing in and out, headline cards, papers (policy, form, pay slip, ration card, ticket, permit...), a clock
// that runs or stops, chance (coin, spinner, scratch card, dice, ballot), a printing press, a chimney with its smoke and
// filter, food, machines with screens, small goods, stalls with menu boards, public buildings and nature signs.
// Words come only from parameters (labels, titles, items); no logos, emblems, real places or real persons.
// A moving part is a pure function of _t (seconds since the thing appeared) and _s (since its last step); without
// times (a box measurement) a drawing shows its settled state.
import { tx, fit, shade, INK, clamp01, parts, idxSet, inr } from "../draw.mjs";

// ---------------------------------------------------------------- helpers (used inside functions only)
const N = (v, d) => (v === "" || v == null || typeof v === "boolean" || !Number.isFinite(Number(v)) ? d : Number(v));
const I = (v, d, lo, hi) => Math.max(lo, Math.min(hi, Math.round(N(v, d))));
const S = (v) => String(v ?? "");
const r1 = (v) => Math.round(v * 10) / 10;
const tNow = (p) => (p._t == null ? null : Math.max(0, Number(p._t) || 0));
const since = (p) => (p._s == null ? null : Math.max(0, Number(p._s) || 0));
const prog = (p, d) => { const s = since(p); return s == null ? 1 : clamp01(s / Math.max(0.01, d)); };
const amountOf = (v) => { const m = S(v).replace(/,/g, "").match(/-?\d+(?:\.\d+)?/); return m ? Number(m[0]) : null; };
const ease = (x) => { x = clamp01(x); return x * x * (3 - 2 * x); };
const listOf = (v) => parts(v).filter(Boolean);
const word = (text, x, cy, maxW, cap, fill = INK, weight = 800) => (S(text) ? tx(S(text), r1(x), r1(cy), r1(fit(S(text), maxW, cap)), fill, weight) : "");
const rect = (x, y, w, h, fill, rx = 0, stroke = "", sw = 0) =>
  `<rect x="${r1(x)}" y="${r1(y)}" width="${r1(Math.max(0, w))}" height="${r1(Math.max(0, h))}"${rx ? ` rx="${r1(rx)}"` : ""} fill="${fill}"${stroke ? ` stroke="${stroke}" stroke-width="${r1(sw)}"` : ""}/>`;
const circ = (x, y, r, fill, stroke = "", sw = 0, extra = "") =>
  `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(Math.max(0, r))}" fill="${fill}"${stroke ? ` stroke="${stroke}" stroke-width="${r1(sw)}"` : ""}${extra}/>`;
const path = (d, fill, stroke = "", sw = 0, extra = "") => `<path d="${d}" fill="${fill}"${stroke ? ` stroke="${stroke}" stroke-width="${r1(sw)}"` : ""}${extra}/>`;
const line = (x1, y1, x2, y2, stroke, sw, extra = "") => `<path d="M${r1(x1)} ${r1(y1)} L${r1(x2)} ${r1(y2)}" stroke="${stroke}" stroke-width="${r1(sw)}" fill="none"${extra}/>`;
/** A plate with fitted words: a label on a thing (the thing's own words live on plates, never loose on its parts). */
function plate(x, cy, w, h, text, bg = "#ffffff", fg = INK, stroke = "", rx = null) {
  if (!S(text)) return "";
  return rect(x - w / 2, cy - h / 2, w, h, bg, rx == null ? h * 0.22 : rx, stroke || shade(bg, 0.7), Math.max(1, h * 0.05)) + word(text, x, cy, w * 0.92, h * 0.62, fg);
}
/** A hanging price tag (old value struck, new written). */
function tag(x, cy, w, text, old = "", col = "#f2c14e") {
  if (!S(text) && !S(old)) return "";
  const h = w * (S(old) ? 0.62 : 0.42);
  let out = path(`M${r1(x - w / 2)} ${r1(cy - h / 2)} L${r1(x + w * 0.36)} ${r1(cy - h / 2)} L${r1(x + w / 2)} ${r1(cy)} L${r1(x + w * 0.36)} ${r1(cy + h / 2)} L${r1(x - w / 2)} ${r1(cy + h / 2)} Z`, col, shade(col), w * 0.02) +
    circ(x + w * 0.34, cy, h * 0.08, "#ffffff", shade(col), w * 0.01);
  if (S(old)) out += word(old, x - w * 0.08, cy - h * 0.24, w * 0.66, h * 0.32, "#7a5a00", 700) + line(x - w * 0.42, cy - h * 0.24, x + w * 0.26, cy - h * 0.24, "#e5484d", h * 0.06);
  return out + word(text, x - w * 0.08, S(old) ? cy + h * 0.2 : cy, w * 0.72, S(old) ? h * 0.38 : h * 0.6, INK, 800);
}
/** Smoke puffs rising from (x, y): count and darkness by level, drifting with time (settled phases without time). */
function puffs(x, y, w, level, t, dark = false, dx = -0.35, seed = 0) {
  const lv = clamp01(level);
  if (lv <= 0) return "";
  const k = 2 + Math.round(lv * 4), col = dark ? "#6b7078" : "#c7ccd3";
  let out = "";
  for (let i = 0; i < k; i++) {
    const ph = ((t == null ? 0 : t * 0.45) + i / k + seed * 0.13) % 1;
    const rr = w * (0.05 + 0.1 * lv) * (0.5 + ph);
    out += circ(x + dx * w * ph + Math.sin(ph * 6 + i) * w * 0.02, y - w * 0.55 * ph * (0.6 + lv * 0.6), rr, col, "", 0, ` opacity="${r1((0.85 - ph * 0.7) * (0.5 + lv * 0.5) * 100) / 100}"`);
  }
  return out;
}
const WIN = "#9fc7e8";

// ---------------------------------------------------------------- produce: sack, heap, basket, crate, packet, bag
const STUFF = {
  potato: ["#c8955a", "#8a6131", "potato"], onion: ["#b5577a", "#7d2f50", "onion"], tomato: ["#e0533d", "#9e2a1c", "round"],
  apple: ["#d6454f", "#8e1f28", "apple"], orange: ["#f29f05", "#b06f00", "round"], pear: ["#b8c94a", "#7a8a1f", "pear"],
  mango: ["#f2b33d", "#b97a10", "mango"], maize: ["#f2c14e", "#b8860b", "maize"], flower: ["#f29f05", "#c76a00", "flower"],
  coal: ["#3b3b40", "#1c1c20", "coal"], cotton: ["#fbfbf8", "#b9b6ad", "cotton"],
  rice: ["#f7f4ea", "#c9c1a8", "grain"], coarseRice: ["#e6dbc0", "#b0a07a", "grain"], wheat: ["#e0b55a", "#a5793a", "grain"],
  sugar: ["#ffffff", "#b9c3cf", "grain"], atta: ["#f3ead6", "#cdbd98", "powder"], dal: ["#f2b33d", "#c08316", "grain"],
  salt: ["#f2efe6", "#a89f8a", "grain"], tea: ["#5d7a35", "#33461c", "grain"], fertiliser: ["#e8eef5", "#8fa6bb", "grain"], seed: ["#a0703d", "#6b4a26", "grain"],
};
const POLY = { sugar: "#3a7bd5", atta: "#2fa35b", rice: "#e5484d", coarseRice: "#d9822b", fertiliser: "#2459a6", salt: "#3a7bd5", dal: "#c2447a" };

function piece(kind, x, y, r) {
  const [c, d, sh] = STUFF[kind] || STUFF.potato, sw = r * 0.12;
  switch (sh) {
    case "onion": return path(`M${r1(x)} ${r1(y - r * 1.2)} Q${r1(x + r * 0.2)} ${r1(y - r * 0.75)} ${r1(x + r * 0.95)} ${r1(y - r * 0.05)} Q${r1(x + r)} ${r1(y + r * 0.88)} ${r1(x)} ${r1(y + r * 0.9)} Q${r1(x - r)} ${r1(y + r * 0.88)} ${r1(x - r * 0.95)} ${r1(y - r * 0.05)} Q${r1(x - r * 0.2)} ${r1(y - r * 0.75)} ${r1(x)} ${r1(y - r * 1.2)} Z`, c, d, sw) +
      path(`M${r1(x - r * 0.35)} ${r1(y - r * 0.4)} Q${r1(x - r * 0.45)} ${r1(y + r * 0.3)} ${r1(x - r * 0.15)} ${r1(y + r * 0.75)} M${r1(x + r * 0.35)} ${r1(y - r * 0.4)} Q${r1(x + r * 0.45)} ${r1(y + r * 0.3)} ${r1(x + r * 0.15)} ${r1(y + r * 0.75)}`, "none", shade(c, 0.85), sw * 0.8);
    case "round": return circ(x, y, r, c, d, sw) + path(`M${r1(x - r * 0.3)} ${r1(y - r * 0.85)} L${r1(x)} ${r1(y - r * 0.7)} L${r1(x + r * 0.3)} ${r1(y - r * 0.85)} L${r1(x + r * 0.1)} ${r1(y - r * 1.05)}`, "none", "#2f8a3e", sw * 1.4) + circ(x - r * 0.35, y - r * 0.3, r * 0.18, "#ffffff", "", 0, ' opacity="0.45"');
    case "apple": return path(`M${r1(x)} ${r1(y - r * 0.7)} Q${r1(x + r * 1.15)} ${r1(y - r * 1.2)} ${r1(x + r * 0.95)} ${r1(y + r * 0.2)} Q${r1(x + r * 0.7)} ${r1(y + r)} ${r1(x)} ${r1(y + r * 0.85)} Q${r1(x - r * 0.7)} ${r1(y + r)} ${r1(x - r * 0.95)} ${r1(y + r * 0.2)} Q${r1(x - r * 1.15)} ${r1(y - r * 1.2)} ${r1(x)} ${r1(y - r * 0.7)} Z`, c, d, sw) +
      path(`M${r1(x)} ${r1(y - r * 0.7)} Q${r1(x + r * 0.4)} ${r1(y - r * 1.3)} ${r1(x + r * 0.7)} ${r1(y - r * 1.1)} Q${r1(x + r * 0.35)} ${r1(y - r * 0.85)} ${r1(x)} ${r1(y - r * 0.7)} Z`, "#2fa35b");
    case "pear": return path(`M${r1(x)} ${r1(y - r * 1.15)} Q${r1(x + r * 0.5)} ${r1(y - r * 1.1)} ${r1(x + r * 0.45)} ${r1(y - r * 0.35)} Q${r1(x + r * 1.05)} ${r1(y + r * 0.2)} ${r1(x + r * 0.7)} ${r1(y + r * 0.8)} Q${r1(x)} ${r1(y + r * 1.15)} ${r1(x - r * 0.7)} ${r1(y + r * 0.8)} Q${r1(x - r * 1.05)} ${r1(y + r * 0.2)} ${r1(x - r * 0.45)} ${r1(y - r * 0.35)} Q${r1(x - r * 0.5)} ${r1(y - r * 1.1)} ${r1(x)} ${r1(y - r * 1.15)} Z`, c, d, sw) + line(x, y - r * 1.15, x + r * 0.12, y - r * 1.45, "#6b4a26", sw * 1.3);
    case "mango": return `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(r * 1.15)}" ry="${r1(r * 0.82)}" transform="rotate(-25 ${r1(x)} ${r1(y)})" fill="${c}" stroke="${d}" stroke-width="${r1(sw)}"/>` + circ(x + r * 0.55, y - r * 0.45, r * 0.22, "#8cc152");
    case "maize": return `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(r * 0.55)}" ry="${r1(r * 1.15)}" fill="${c}" stroke="${d}" stroke-width="${r1(sw)}"/>` +
      path(`M${r1(x - r * 0.55)} ${r1(y + r * 0.2)} Q${r1(x - r * 0.9)} ${r1(y - r * 0.6)} ${r1(x - r * 0.15)} ${r1(y - r * 1.25)} M${r1(x + r * 0.55)} ${r1(y + r * 0.2)} Q${r1(x + r * 0.9)} ${r1(y - r * 0.6)} ${r1(x + r * 0.15)} ${r1(y - r * 1.25)}`, "none", "#6fa83a", sw * 1.6) +
      [-0.5, 0, 0.5].map((k) => line(x - r * 0.4, y + k * r, x + r * 0.4, y + k * r, d, sw * 0.6)).join("");
    case "flower": { let pet = ""; for (let i = 0; i < 10; i++) { const a = (i / 10) * Math.PI * 2; pet += circ(x + Math.cos(a) * r * 0.62, y + Math.sin(a) * r * 0.62, r * 0.42, i % 2 ? c : shade(c, 1.12), d, sw * 0.5); }
      return pet + circ(x, y, r * 0.4, shade(c, 0.8)); }
    case "coal": return path(`M${r1(x - r)} ${r1(y + r * 0.3)} L${r1(x - r * 0.6)} ${r1(y - r * 0.7)} L${r1(x + r * 0.3)} ${r1(y - r * 0.9)} L${r1(x + r)} ${r1(y - r * 0.1)} L${r1(x + r * 0.6)} ${r1(y + r * 0.8)} L${r1(x - r * 0.4)} ${r1(y + r * 0.85)} Z`, c, d, sw) + line(x - r * 0.3, y - r * 0.5, x + r * 0.2, y - r * 0.6, "#8a8f98", sw);
    case "cotton": return [[-0.45, 0.1], [0.45, 0.1], [0, -0.35], [0, 0.35]].map(([a, b]) => circ(x + a * r, y + b * r, r * 0.58, c, d, sw * 0.6)).join("");
    default: return `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(r * 1.15)}" ry="${r1(r * 0.85)}" fill="${c}" stroke="${d}" stroke-width="${r1(sw)}"/>` +
      circ(x - r * 0.35, y - r * 0.2, r * 0.09, d) + circ(x + r * 0.3, y + r * 0.15, r * 0.08, d) + circ(x + r * 0.05, y - r * 0.4, r * 0.07, d);
  }
}

/** A mound of grain or powder between x0 and x1 standing on y0, height h, speckled (seeded, so always the same). */
function mound(x0, x1, y0, h, kind, seed = 3) {
  const [c, d, sh] = STUFF[kind] || STUFF.wheat, w = x1 - x0, cx = (x0 + x1) / 2;
  let out = path(`M${r1(x0)} ${r1(y0)} Q${r1(x0 + w * 0.22)} ${r1(y0 - h * 1.02)} ${r1(cx)} ${r1(y0 - h)} Q${r1(x1 - w * 0.22)} ${r1(y0 - h * 1.02)} ${r1(x1)} ${r1(y0)} Z`, c, d, Math.max(1, w * 0.012));
  let x = (seed * 9301 + 49297) % 233280;
  const n = Math.max(4, Math.round(w / 14));
  for (let i = 0; i < n; i++) {
    x = (x * 9301 + 49297) % 233280; const a = x / 233280;
    x = (x * 9301 + 49297) % 233280; const b = x / 233280;
    const px = x0 + w * (0.15 + 0.7 * a), top = y0 - h * (1 - Math.pow((px - cx) / (w / 2), 2)) * 0.9;
    const py = y0 - (y0 - top) * (0.15 + 0.75 * b);
    out += sh === "powder" ? circ(px, py, w * 0.008, d, "", 0, ' opacity="0.6"') : `<ellipse cx="${r1(px)}" cy="${r1(py)}" rx="${r1(w * 0.012)}" ry="${r1(w * 0.007)}" fill="${d}"/>`;
  }
  if (kind === "sugar" || kind === "salt") out += path(`M${r1(cx - w * 0.08)} ${r1(y0 - h * 0.7)} l${r1(w * 0.02)} ${r1(-w * 0.04)} l${r1(w * 0.02)} ${r1(w * 0.04)} l${r1(-w * 0.02)} ${r1(w * 0.04)} Z`, "#ffffff", "#c3ccd6", 1);
  return out;
}

/** Pieces in a pile: rows bottom-up (first row widest), the first n of kind a then n2 of kind b. */
function pile(cx, y0, r, count, a, n1, b, maxRow) {
  let out = "", i = 0, row = 0;
  while (i < count && row < 12) {
    const k = Math.max(1, maxRow - row), y = y0 - r * 0.85 - row * r * 1.55;
    for (let j = 0; j < k && i < count; j++, i++) out += piece(i < n1 ? a : b, cx + (j - (k - 1) / 2) * r * 2.05, y, r);
    row++;
  }
  return { svg: out, top: y0 - r * 0.85 - (row - 1) * r * 1.55 - r * 1.2 };
}

function produce(p) {
  const w = N(p.w, 300), kind = p.kind || "sack", content = STUFF[p.content] ? p.content : "potato", f = clamp01(p.fill ?? 1);
  const [c, d, sh] = STUFF[content], grain = sh === "grain" || sh === "powder";
  const c2 = STUFF[p.content2] ? p.content2 : "", n1 = I(p.n, 0, 0, 80), n2 = c2 ? I(p.n2, 0, 0, 80) : 0, lab = S(p.label);
  if (kind === "heap") {
    if (grain && !n1) {
      const h = w * 0.5 * Math.max(0.06, f);
      return mound(-w / 2, w / 2, 0, h, content) + (lab ? line(w * 0.18, -h * 0.55, w * 0.18, -h - w * 0.08, "#7a4e22", w * 0.014) + plate(w * 0.18, -h - w * 0.18, w * 0.62, w * 0.21, lab, "#fffaf0") : "");
    }
    const r = w / 13, count = n1 + n2 || Math.round(f * 21);
    const pl = pile(0, 0, r, count, content, n1 || count, c2 || content, 6);
    return pl.svg + (lab ? line(0, pl.top + r, 0, pl.top - w * 0.06, "#7a4e22", w * 0.014) + plate(0, pl.top - w * 0.15, w * 0.62, w * 0.21, lab, "#fffaf0") : "");
  }
  if (kind === "basket" || kind === "crate") {
    const crate = kind === "crate", stack = crate ? I(p.stack, 1, 1, 5) : 1, bh = crate ? w * 0.42 : w * 0.42;
    let out = "";
    for (let s = 0; s < stack; s++) {
      const y0 = -s * bh;
      if (crate) {
        out += rect(-w / 2, y0 - bh, w, bh, "#c8955a", w * 0.015, "#8a6131", w * 0.014);
        for (let k = 1; k < 3; k++) out += line(-w / 2, y0 - bh * k / 3, w / 2, y0 - bh * k / 3, "#8a6131", w * 0.01);
        out += line(-w * 0.44, y0 - bh, -w * 0.44, y0, "#8a6131", w * 0.02) + line(w * 0.44, y0 - bh, w * 0.44, y0, "#8a6131", w * 0.02);
      } else {
        out += path(`M${r1(-w / 2)} ${r1(-bh)} L${r1(w / 2)} ${r1(-bh)} L${r1(w * 0.36)} 0 L${r1(-w * 0.36)} 0 Z`, "#c99a5b", "#8a6131", w * 0.016);
        for (let k = 1; k < 4; k++) { const y = -bh + (bh * k) / 4, x = w / 2 - (w * 0.14 * k) / 4; out += line(-x, y, x, y, "#a67a40", w * 0.01); }
        for (let k = -3; k <= 3; k++) out += line(k * w * 0.13, -bh, k * w * 0.1, 0, "#a67a40", w * 0.008);
        out += rect(-w * 0.52, -bh - w * 0.03, w * 1.04, w * 0.05, "#b5864a", w * 0.025, "#8a6131", w * 0.01);
      }
    }
    const topY = -stack * bh - (crate ? 0 : w * 0.02), r = w / 13;
    const count = n1 + n2 || Math.round(f * (crate ? 9 : 15));
    let goods = "";
    if (grain && !n1) goods = f > 0 ? mound(-w * 0.46, w * 0.46, topY, w * 0.22 * f, content) : "";
    else goods = pile(0, topY + r * 0.2, r, count, content, n1 || count, c2 || content, crate ? 5 : 6).svg;
    return goods + out + plate(0, -bh * 0.5, w * 0.66, crate ? bh * 0.5 : w * 0.21, lab, "#fffaf0");
  }
  if (kind === "packet") {
    const h = w * 1.25 * (0.6 + 0.4 * f), col = p.color || POLY[content] || "#d9822b";
    let crimp = `M${r1(-w * 0.42)} ${r1(-h)}`;
    for (let i = 0; i <= 12; i++) crimp += ` L${r1(-w * 0.42 + (w * 0.84 * i) / 12)} ${r1(-h - (i % 2 ? w * 0.04 : 0))}`;
    return path(`M${r1(-w * 0.44)} ${r1(-h)} Q${r1(-w * 0.52)} ${r1(-h * 0.5)} ${r1(-w * 0.46)} 0 L${r1(w * 0.46)} 0 Q${r1(w * 0.52)} ${r1(-h * 0.5)} ${r1(w * 0.44)} ${r1(-h)} Z`, col, shade(col), w * 0.02) +
      path(crimp, "none", shade(col, 0.8), w * 0.03) +
      circ(0, -h * 0.32, w * 0.2, "#ffffff", d, w * 0.012) + (grain ? mound(-w * 0.17, w * 0.17, -h * 0.32 + w * 0.1, w * 0.16, content) : piece(content, 0, -h * 0.32, w * 0.11)) +
      plate(0, -h * 0.7, w * 0.8, w * 0.24, lab, "#ffffff", shade(col, 0.6));
  }
  if (kind === "bag") {
    const h = w * 0.85, col = p.color || "#2a9d8f", lvl = f;
    let top = "";
    if (lvl > 0.82) top = [[-0.24, "#e0533d"], [0.02, "#f2c14e"], [0.24, "#2fa35b"]].map(([x, cc], i) => rect(w * x - w * 0.09, -h - w * (0.12 + (i % 2) * 0.05) * ((lvl - 0.82) / 0.18), w * 0.18, w * 0.2, cc, w * 0.03, shade(cc), w * 0.01)).join("");
    return top + path(`M${r1(-w * 0.28)} ${r1(-h)} Q${r1(-w * 0.26)} ${r1(-h - w * 0.36)} ${r1(0)} ${r1(-h - w * 0.36)} Q${r1(w * 0.26)} ${r1(-h - w * 0.36)} ${r1(w * 0.28)} ${r1(-h)}`, "none", shade(col), w * 0.04) +
      path(`M${r1(-w * 0.45)} ${r1(-h)} L${r1(w * 0.45)} ${r1(-h)} L${r1(w * 0.5)} 0 L${r1(-w * 0.5)} 0 Z`, shade(col, 1.25), shade(col), w * 0.02) +
      (lvl > 0 ? path(`M${r1(-w * 0.5 + w * 0.05 * (1 - lvl))} ${r1(-h * lvl)} L${r1(w * 0.5 - w * 0.05 * (1 - lvl))} ${r1(-h * lvl)} L${r1(w * 0.5)} 0 L${r1(-w * 0.5)} 0 Z`, col, "", 0, ' opacity="0.9"') : "") +
      line(-w * 0.47, -h * lvl, w * 0.47, -h * lvl, "#ffffff", w * 0.012, ' stroke-dasharray="6 6" opacity="0.8"') +
      plate(0, -h * 0.5, w * 0.66, w * 0.22, lab, "#ffffff");
  }
  // sack: an open jute (or poly) sack whose top folds down as it empties
  const h = w * 1.05, hs = h * (0.42 + 0.58 * f), poly = POLY[content] && p.jute !== true, body = poly ? "#eef1f4" : "#c9a46a", dk = poly ? "#9aa5b1" : "#8a6d3b";
  let out = path(`M${r1(-w * 0.4)} ${r1(-hs)} C${r1(-w * 0.5)} ${r1(-hs * 0.6)} ${r1(-w * 0.53)} ${r1(-h * 0.25)} ${r1(-w * 0.46)} ${r1(-h * 0.02)} Q0 ${r1(h * 0.03)} ${r1(w * 0.46)} ${r1(-h * 0.02)} C${r1(w * 0.53)} ${r1(-h * 0.25)} ${r1(w * 0.5)} ${r1(-hs * 0.6)} ${r1(w * 0.4)} ${r1(-hs)} Z`, body, dk, w * 0.02);
  if (poly) out += rect(-w * 0.46, -hs * 0.2 - w * 0.03, w * 0.92, w * 0.05, POLY[content], 0) ;
  if (!poly) for (let i = 1; i < 6; i++) out += line(-w * 0.44 + (i * w * 0.88) / 6, -hs * 0.95, -w * 0.45 + (i * w * 0.9) / 6, -h * 0.04, shade(body, 0.9), w * 0.006);
  if (f < 0.6) out += path(`M${r1(-w * 0.36)} ${r1(-hs * 0.7)} Q${r1(-w * 0.1)} ${r1(-hs * 0.6)} ${r1(w * 0.05)} ${r1(-hs * 0.72)} M${r1(w * 0.1)} ${r1(-hs * 0.55)} Q${r1(w * 0.25)} ${r1(-hs * 0.5)} ${r1(w * 0.38)} ${r1(-hs * 0.6)}`, "none", dk, w * 0.012);
  out += `<ellipse cx="0" cy="${r1(-hs)}" rx="${r1(w * 0.41)}" ry="${r1(w * 0.08)}" fill="${f > 0.02 ? c : "#5a4632"}" stroke="${dk}" stroke-width="${r1(w * 0.03)}"/>`;
  if (f > 0.02) {
    if (grain) out += mound(-w * 0.37, w * 0.37, -hs + w * 0.02, w * 0.16 * Math.sqrt(f), content);
    else { const r = w * 0.072; out += pile(0, -hs + r * 0.5, r, f > 0.5 ? 9 : 5, content, 99, content, 5).svg; }
  }
  return out + plate(0, -hs * 0.42, w * 0.66, w * 0.22, lab, "#fffaf0", INK, dk);
}

// ---------------------------------------------------------------- vehicle
const DMG = { new: 0, scratched: 1, crashed: 2, writeoff: 3 };
function wheel(x, y, r, ang, flat = false) {
  const spokes = [0, 60, 120].map((a) => { const t = ((a + ang) * Math.PI) / 180; return line(x - Math.cos(t) * r * 0.55, y - Math.sin(t) * r * 0.55, x + Math.cos(t) * r * 0.55, y + Math.sin(t) * r * 0.55, "#c9ced6", r * 0.1); }).join("");
  return (flat ? `<ellipse cx="${r1(x)}" cy="${r1(y + r * 0.12)}" rx="${r1(r * 1.08)}" ry="${r1(r * 0.88)}" fill="#2b2b33"/>` : circ(x, y, r, "#2b2b33")) + circ(x, y, r * 0.62, "#8a8f98") + spokes + circ(x, y, r * 0.18, "#4a5568");
}
function riderHead(x, y, r, i) {
  const skins = ["#c98850", "#b97745", "#a8663a", "#d39a6a"], hair = "#241b12";
  return circ(x, y, r, skins[i % 4]) + path(`M${r1(x - r)} ${r1(y - r * 0.15)} A${r1(r)} ${r1(r)} 0 0 1 ${r1(x + r)} ${r1(y - r * 0.15)} Z`, hair) +
    path(`M${r1(x - r * 1.2)} ${r1(y + r * 2.2)} Q${r1(x)} ${r1(y + r * 0.7)} ${r1(x + r * 1.2)} ${r1(y + r * 2.2)} Z`, ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05"][i % 4]);
}
function riderSit(x, y, w, i, helmet) {      // a rider sitting on a two-wheeler: hips at (x, y), hands forward to the bar
  const tops = ["#3a7bd5", "#f29f05", "#2fa35b", "#e5484d"], skin = ["#c98850", "#a8663a", "#b97745", "#d39a6a"][i % 4], c = tops[i % 4];
  return line(x, y - w * 0.02, x + w * 0.14, y + w * 0.1, "#2e3440", w * 0.05, ' stroke-linecap="round"') +
    line(x + w * 0.14, y + w * 0.1, x + w * 0.14, y + w * 0.22, "#2e3440", w * 0.045, ' stroke-linecap="round"') +
    path(`M${r1(x - w * 0.06)} ${r1(y)} L${r1(x - w * 0.04)} ${r1(y - w * 0.22)} Q${r1(x + w * 0.02)} ${r1(y - w * 0.26)} ${r1(x + w * 0.07)} ${r1(y - w * 0.21)} L${r1(x + w * 0.06)} ${r1(y)} Z`, c) +
    line(x + w * 0.03, y - w * 0.19, x + w * 0.2, y - w * 0.12, c, w * 0.04, ' stroke-linecap="round"') + circ(x + w * 0.02, y - w * 0.31, w * 0.06, skin) +
    (helmet ? path(`M${r1(x - w * 0.045)} ${r1(y - w * 0.29)} A${r1(w * 0.068)} ${r1(w * 0.07)} 0 0 1 ${r1(x + w * 0.085)} ${r1(y - w * 0.32)} L${r1(x + w * 0.03)} ${r1(y - w * 0.335)} Z`, "#e5484d")
      : path(`M${r1(x - w * 0.04)} ${r1(y - w * 0.31)} A${r1(w * 0.06)} ${r1(w * 0.06)} 0 0 1 ${r1(x + w * 0.08)} ${r1(y - w * 0.32)} Z`, "#241b12"));
}

function fuelBadge(kind, x, y, r) {
  if (!kind || kind === "none") return "";
  const col = { petrol: "#f29f05", diesel: "#4a5568", cng: "#2fa35b", electric: "#2a9d8f" }[kind] || "#8a8f98";
  let g = "";
  if (kind === "electric") g = path(`M${r1(x + r * 0.1)} ${r1(y - r * 0.6)} L${r1(x - r * 0.3)} ${r1(y + r * 0.08)} L${r1(x)} ${r1(y + r * 0.08)} L${r1(x - r * 0.12)} ${r1(y + r * 0.6)} L${r1(x + r * 0.32)} ${r1(y - r * 0.1)} L${r1(x + r * 0.02)} ${r1(y - r * 0.1)} Z`, "#ffffff");
  else if (kind === "cng") g = rect(x - r * 0.22, y - r * 0.5, r * 0.44, r * 1.0, "#ffffff", r * 0.2) + rect(x - r * 0.1, y - r * 0.66, r * 0.2, r * 0.2, "#ffffff");
  else g = path(`M${r1(x)} ${r1(y - r * 0.6)} Q${r1(x + r * 0.5)} ${r1(y)} ${r1(x + r * 0.32)} ${r1(y + r * 0.3)} Q${r1(x)} ${r1(y + r * 0.62)} ${r1(x - r * 0.32)} ${r1(y + r * 0.3)} Q${r1(x - r * 0.5)} ${r1(y)} ${r1(x)} ${r1(y - r * 0.6)} Z`, "#ffffff");
  return circ(x, y, r, col, "#ffffff", r * 0.12) + g;
}

/** Each kind's body (facing right, standing on y 0): svg, wheels, window seats for heads, plate place, top, rear exhaust. */
function vehicleBody(kind, w, col, cls, dmg, load, p) {
  const dk = shade(col), glass = dmg >= 3 ? "#4a5568" : WIN, sw = w * 0.008;
  const B = { svg: "", wheels: [], seats: [], plate: null, top: 0, exhaust: [-w * 0.48, -w * 0.08], wr: w * 0.09, lamp: [w * 0.47, -w * 0.18], rear: [-w * 0.47, -w * 0.18], screen: null };
  if (kind === "car") {
    const lux = cls === "luxury", small = cls === "small", roof = small ? -w * 0.44 : lux ? -w * 0.4 : -w * 0.41;
    const cab = small ? [-w * 0.36, w * 0.14] : lux ? [-w * 0.3, w * 0.24] : [-w * 0.28, w * 0.2];
    B.svg = path(`M${r1(-w * 0.48)} ${r1(-w * 0.1)} L${r1(-w * 0.48)} ${r1(-w * 0.24)} Q${r1(-w * 0.46)} ${r1(-w * 0.28)} ${r1(cab[0] - w * 0.04)} ${r1(-w * 0.28)} L${r1(cab[0] + w * 0.04)} ${r1(roof)} L${r1(cab[1] - w * 0.06)} ${r1(roof)} L${r1(cab[1] + w * 0.06)} ${r1(-w * 0.28)} L${r1(w * 0.42)} ${r1(-w * 0.26)} Q${r1(w * 0.49)} ${r1(-w * 0.24)} ${r1(w * 0.49)} ${r1(-w * 0.15)} L${r1(w * 0.49)} ${r1(-w * 0.1)} Z`, col, dk, sw * 1.5) +
      path(`M${r1(cab[0] + w * 0.035)} ${r1(-w * 0.29)} L${r1(cab[0] + w * 0.065)} ${r1(roof + w * 0.025)} L${r1((cab[0] + cab[1]) / 2 - w * 0.012)} ${r1(roof + w * 0.025)} L${r1((cab[0] + cab[1]) / 2 - w * 0.012)} ${r1(-w * 0.29)} Z M${r1((cab[0] + cab[1]) / 2 + w * 0.012)} ${r1(-w * 0.29)} L${r1((cab[0] + cab[1]) / 2 + w * 0.012)} ${r1(roof + w * 0.025)} L${r1(cab[1] - w * 0.075)} ${r1(roof + w * 0.025)} L${r1(cab[1] + w * 0.04)} ${r1(-w * 0.29)} Z`, glass) +
      (lux ? line(-w * 0.46, -w * 0.2, w * 0.47, -w * 0.2, "#e3e7ec", w * 0.012) + rect(w * 0.44, -w * 0.2, w * 0.05, w * 0.06, "#e3e7ec", w * 0.01) : "") +
      line((cab[0] + cab[1]) / 2, -w * 0.28, (cab[0] + cab[1]) / 2, -w * 0.11, dk, sw);
    B.wheels = [[-w * 0.3, -w * 0.09], [w * 0.3, -w * 0.09]]; B.wr = w * (lux ? 0.095 : 0.085);
    B.seats = [[(cab[0] * 0.6 + cab[1] * 0.4) - w * 0.03, roof + w * 0.07], [(cab[0] + cab[1]) / 2 + w * 0.07, roof + w * 0.07]];
    B.plate = [0, -w * 0.18, w * 0.32, w * 0.1]; B.top = roof; B.screen = [cab[1] + w * 0.015, (roof - w * 0.28) / 2];
  } else if (kind === "scooter" || kind === "bike") {
    const bike = kind === "bike";
    B.svg = bike
      ? path(`M${r1(-w * 0.34)} ${r1(-w * 0.26)} L${r1(w * 0.08)} ${r1(-w * 0.3)} L${r1(w * 0.18)} ${r1(-w * 0.4)} L${r1(w * 0.26)} ${r1(-w * 0.4)} L${r1(w * 0.3)} ${r1(-w * 0.12)}`, "none", "#4a5568", w * 0.03) +
        `<ellipse cx="${r1(-w * 0.02)}" cy="${r1(-w * 0.31)}" rx="${r1(w * 0.14)}" ry="${r1(w * 0.07)}" fill="${col}" stroke="${dk}" stroke-width="${r1(sw)}"/>` +
        rect(-w * 0.32, -w * 0.33, w * 0.24, w * 0.05, "#2b2b33", w * 0.02) + rect(-w * 0.1, -w * 0.24, w * 0.18, w * 0.12, "#8a8f98", w * 0.02)
      : path(`M${r1(-w * 0.44)} ${r1(-w * 0.13)} Q${r1(-w * 0.46)} ${r1(-w * 0.34)} ${r1(-w * 0.22)} ${r1(-w * 0.34)} L${r1(-w * 0.02)} ${r1(-w * 0.3)} L${r1(w * 0.02)} ${r1(-w * 0.13)} Z`, col, dk, sw * 1.4) +
        path(`M${r1(w * 0.02)} ${r1(-w * 0.13)} L${r1(w * 0.16)} ${r1(-w * 0.16)} L${r1(w * 0.22)} ${r1(-w * 0.5)} L${r1(w * 0.3)} ${r1(-w * 0.5)} L${r1(w * 0.3)} ${r1(-w * 0.13)} Z`, col, dk, sw * 1.4) +
        rect(-w * 0.36, -w * 0.39, w * 0.3, w * 0.06, "#2b2b33", w * 0.03) + line(w * 0.2, -w * 0.55, w * 0.34, -w * 0.57, "#2b2b33", w * 0.022) + circ(w * 0.31, -w * 0.46, w * 0.03, "#fff3c4", dk, sw);
    B.wheels = [[-w * 0.3, -w * 0.11], [w * 0.32, -w * 0.11]]; B.wr = w * 0.11; B.sit = [-w * 0.16, -w * 0.39];
    B.plate = [-w * 0.3, -w * 0.21, w * 0.3, w * 0.12]; B.top = -w * 0.58; B.exhaust = [-w * 0.46, -w * 0.12]; B.lamp = [w * 0.31, -w * 0.46];
    B.rear = [-w * 0.44, -w * 0.25];
    if (p.box) B.svg = rect(-w * 0.5, -w * 0.62, w * 0.26, w * 0.24, p.boxColor || "#e5484d", w * 0.02, shade(p.boxColor || "#e5484d"), sw) + B.svg;
  } else if (kind === "cycle") {
    B.svg = path(`M${r1(-w * 0.3)} ${r1(-w * 0.13)} L${r1(-w * 0.05)} ${r1(-w * 0.38)} L${r1(w * 0.22)} ${r1(-w * 0.38)} L${r1(w * 0.3)} ${r1(-w * 0.13)} M${r1(-w * 0.05)} ${r1(-w * 0.38)} L${r1(0)} ${r1(-w * 0.13)} L${r1(-w * 0.3)} ${r1(-w * 0.13)} M${r1(0)} ${r1(-w * 0.13)} L${r1(w * 0.22)} ${r1(-w * 0.38)} M${r1(w * 0.2)} ${r1(-w * 0.38)} L${r1(w * 0.18)} ${r1(-w * 0.48)} L${r1(w * 0.26)} ${r1(-w * 0.5)}`, "none", col, w * 0.025) +
      rect(-w * 0.12, -w * 0.45, w * 0.14, w * 0.04, "#2b2b33", w * 0.02);
    B.wheels = [[-w * 0.3, -w * 0.15], [w * 0.3, -w * 0.15]]; B.wr = w * 0.15; B.sit = [-w * 0.05, -w * 0.46]; B.top = -w * 0.6; B.exhaust = null;
  } else if (kind === "bus") {
    const h = w * 0.3, nw = I(p.seats, 6, 2, 12), wx0 = -w * 0.4, ww = (w * 0.74) / nw;
    B.svg = rect(-w * 0.49, -h - w * 0.06, w * 0.98, h, col, w * 0.03, dk, sw * 1.5) + rect(-w * 0.49, -w * 0.12, w * 0.98, w * 0.035, dk, 0) +
      rect(w * 0.37, -h - w * 0.03, w * 0.1, h * 0.55, glass, w * 0.012) + rect(w * 0.37, -w * 0.2, w * 0.08, w * 0.12, shade(col, 0.85), w * 0.008, dk, sw);
    for (let i = 0; i < nw; i++) { B.svg += rect(wx0 + i * ww + ww * 0.08, -h - w * 0.03, ww * 0.84, h * 0.42, glass, w * 0.008); B.seats.push([wx0 + i * ww + ww * 0.32, -h + w * 0.035], [wx0 + i * ww + ww * 0.68, -h + w * 0.035]); }
    B.wheels = [[-w * 0.32, -w * 0.06], [w * 0.3, -w * 0.06]]; B.wr = w * 0.06; B.top = -h - w * 0.06;
    B.plate = [w * 0.05, -h - w * 0.105, w * 0.5, w * 0.075]; B.dark = true; B.exhaust = [-w * 0.49, -w * 0.07]; B.lamp = [w * 0.48, -w * 0.1]; B.rear = [-w * 0.48, -w * 0.1];
  } else if (kind === "metro" || kind === "train") {
    const h = w * 0.27, nw = I(p.seats, 6, 2, 12), ww = (w * 0.78) / nw, x0 = -w * 0.42;
    B.svg = path(`M${r1(-w * 0.49)} ${r1(-w * 0.04)} L${r1(-w * 0.49)} ${r1(-h - w * 0.04)} L${r1(w * 0.38)} ${r1(-h - w * 0.04)} Q${r1(w * 0.5)} ${r1(-h - w * 0.02)} ${r1(w * 0.5)} ${r1(-w * 0.12)} L${r1(w * 0.5)} ${r1(-w * 0.04)} Z`, kind === "metro" ? "#e9eef3" : col, dk, sw * 1.5) +
      rect(-w * 0.49, -w * 0.12, w * 0.99, w * 0.035, kind === "metro" ? col : "#f2c14e", 0) + path(`M${r1(w * 0.42)} ${r1(-h)} Q${r1(w * 0.48)} ${r1(-h + w * 0.01)} ${r1(w * 0.485)} ${r1(-h * 0.5)} L${r1(w * 0.42)} ${r1(-h * 0.5)} Z`, glass);
    for (let i = 0; i < nw; i++) { B.svg += rect(x0 + i * ww + ww * 0.1, -h + w * 0.01, ww * 0.8, h * 0.4, glass, w * 0.008); B.seats.push([x0 + i * ww + ww * 0.32, -h + w * 0.07], [x0 + i * ww + ww * 0.68, -h + w * 0.07]); }
    for (const dx of [-0.2, 0.15]) B.svg += rect(w * dx, -h * 0.55, w * 0.06, h * 0.42, shade(kind === "metro" ? "#e9eef3" : col, 0.85), w * 0.004, dk, sw);
    B.wheels = [[-w * 0.4, -w * 0.035], [-w * 0.32, -w * 0.035], [w * 0.3, -w * 0.035], [w * 0.38, -w * 0.035]]; B.wr = w * 0.035; B.top = -h - w * 0.04;
    B.plate = [w * 0.05, -h - w * 0.085, w * 0.44, w * 0.075]; B.dark = true; B.exhaust = kind === "train" ? [-w * 0.45, -h - w * 0.04] : null; B.lamp = [w * 0.49, -w * 0.08];
  } else if (kind === "auto" || kind === "erickshaw") {
    const e = kind === "erickshaw";
    B.svg = path(`M${r1(-w * 0.42)} ${r1(-w * 0.1)} L${r1(-w * 0.44)} ${r1(-w * 0.34)} L${r1(w * 0.12)} ${r1(-w * 0.36)} L${r1(w * 0.36)} ${r1(-w * 0.16)} L${r1(w * 0.36)} ${r1(-w * 0.1)} Z`, e ? "#2a9d8f" : "#2fa35b", "#1d6e60", sw * 1.4) +
      path(`M${r1(-w * 0.46)} ${r1(-w * 0.34)} Q${r1(-w * 0.44)} ${r1(-w * 0.66)} ${r1(-w * 0.1)} ${r1(-w * 0.66)} L${r1(w * 0.14)} ${r1(-w * 0.64)} L${r1(w * 0.2)} ${r1(-w * 0.36)} Z`, e ? "#3a7bd5" : col, shade(e ? "#3a7bd5" : col), sw * 1.4) +
      path(`M${r1(w * 0.05)} ${r1(-w * 0.6)} L${r1(w * 0.16)} ${r1(-w * 0.6)} L${r1(w * 0.2)} ${r1(-w * 0.38)} L${r1(w * 0.08)} ${r1(-w * 0.38)} Z`, glass) +
      (e ? rect(-w * 0.4, -w * 0.62, w * 0.04, w * 0.26, "#2b2b33") + rect(w * 0.0, -w * 0.62, w * 0.03, w * 0.26, "#2b2b33") : path(`M${r1(-w * 0.4)} ${r1(-w * 0.6)} L${r1(-w * 0.12)} ${r1(-w * 0.6)} L${r1(-w * 0.12)} ${r1(-w * 0.38)} L${r1(-w * 0.4)} ${r1(-w * 0.38)} Z`, "#2b2b33", "", 0, ' opacity="0.25"'));
    B.wheels = [[-w * 0.3, -w * 0.09], [w * 0.28, -w * 0.09]]; B.wr = w * 0.09; B.seats = [[-w * 0.3, -w * 0.5], [-w * 0.18, -w * 0.5], [w * 0.0, -w * 0.5]];
    B.plate = [-w * 0.08, -w * 0.2, w * 0.36, w * 0.09]; B.top = -w * 0.66; B.exhaust = e ? null : [-w * 0.44, -w * 0.1]; B.lamp = [w * 0.35, -w * 0.15];
  } else if (kind === "truck" || kind === "tanker" || kind === "van") {
    const van = kind === "van", tank = kind === "tanker", h = w * (van ? 0.36 : 0.34);
    const cabX = van ? w * 0.18 : w * 0.24;
    if (van) B.svg = path(`M${r1(-w * 0.48)} ${r1(-w * 0.1)} L${r1(-w * 0.48)} ${r1(-h - w * 0.06)} L${r1(w * 0.22)} ${r1(-h - w * 0.06)} Q${r1(w * 0.34)} ${r1(-h - w * 0.06)} ${r1(w * 0.42)} ${r1(-h * 0.45)} L${r1(w * 0.48)} ${r1(-w * 0.2)} L${r1(w * 0.48)} ${r1(-w * 0.1)} Z`, col, dk, sw * 1.5) +
      path(`M${r1(w * 0.24)} ${r1(-h - w * 0.02)} Q${r1(w * 0.32)} ${r1(-h - w * 0.02)} ${r1(w * 0.39)} ${r1(-h * 0.5)} L${r1(w * 0.24)} ${r1(-h * 0.5)} Z`, glass) + line(w * 0.2, -h - w * 0.05, w * 0.2, -w * 0.11, dk, sw);
    else {
      B.svg = path(`M${r1(cabX)} ${r1(-w * 0.1)} L${r1(cabX)} ${r1(-w * 0.38)} L${r1(w * 0.38)} ${r1(-w * 0.38)} L${r1(w * 0.48)} ${r1(-w * 0.24)} L${r1(w * 0.48)} ${r1(-w * 0.1)} Z`, col, dk, sw * 1.5) +
        path(`M${r1(cabX + w * 0.03)} ${r1(-w * 0.35)} L${r1(w * 0.37)} ${r1(-w * 0.35)} L${r1(w * 0.44)} ${r1(-w * 0.25)} L${r1(cabX + w * 0.03)} ${r1(-w * 0.25)} Z`, glass) +
        rect(-w * 0.48, -w * 0.12, cabX + w * 0.48, w * 0.03, "#4a5568", 0);
      if (tank) {
        const tc = p.tankColor || "#dfe5ec", lv = clamp01(load ?? 1);
        B.svg += rect(-w * 0.47, -w * 0.38, cabX + w * 0.44, w * 0.26, tc, w * 0.13, shade(tc), sw * 1.5) +
          rect(-w * 0.42, -w * 0.12 - w * 0.22 * lv, cabX + w * 0.34, w * 0.22 * lv, shade(tc, 0.92), w * 0.02, "", 0) +
          rect(-w * 0.2, -w * 0.42, w * 0.12, w * 0.05, shade(tc, 0.8), w * 0.01);
        B.plate = [(-w * 0.47 + cabX) / 2 - w * 0.02, -w * 0.25, w * 0.5, w * 0.1];
      } else {
        const lv = clamp01(load ?? 0.6), cw = cabX + w * 0.46, k = Math.round(lv * 12);
        for (let i = 0; i < k; i++) { const col4 = i % 4, row = Math.floor(i / 4);
          B.svg += rect(-w * 0.46 + col4 * w * 0.165, -w * 0.36 - row * w * 0.1, w * 0.15, w * 0.1, "#c8955a", w * 0.008, "#8a6131", sw); }
        B.svg += rect(-w * 0.48, -w * 0.27, cw, w * 0.15, p.boxColor || shade(col, 1.15), w * 0.01, dk, sw * 1.5);
        for (let i = 0; i < 5; i++) B.svg += line(-w * 0.48 + (cw * (i + 0.5)) / 5, -w * 0.27, -w * 0.48 + (cw * (i + 0.5)) / 5, -w * 0.12, dk, sw * 0.8);
        B.plate = [(-w * 0.48 + cabX) / 2, -w * 0.195, w * 0.5, w * 0.1];
      }
    }
    if (van) B.plate = [-w * 0.14, -h * 0.62, w * 0.56, w * 0.1];
    B.wheels = [[-w * 0.32, -w * 0.08], [w * 0.32, -w * 0.08]]; B.wr = w * 0.08; if (!van) B.wheels.splice(1, 0, [-w * 0.15, -w * 0.08]);
    B.top = van ? -h - w * 0.06 : -w * 0.4; B.seats = [[van ? w * 0.3 : w * 0.34, -h * (van ? 0.82 : 0.95)]]; B.exhaust = [-w * 0.48, -w * 0.08]; B.lamp = [w * 0.47, -w * 0.16];
    B.screen = van ? [w * 0.32, -h * 0.7] : [w * 0.36, -w * 0.3];
  } else if (kind === "tractor") {
    B.svg = rect(-w * 0.1, -w * 0.34, w * 0.42, w * 0.14, col, w * 0.02, dk, sw * 1.4) + path(`M${r1(-w * 0.32)} ${r1(-w * 0.2)} L${r1(-w * 0.28)} ${r1(-w * 0.62)} L${r1(-w * 0.04)} ${r1(-w * 0.62)} L${r1(-w * 0.02)} ${r1(-w * 0.2)}`, "none", "#4a5568", w * 0.02) +
      rect(-w * 0.32, -w * 0.66, w * 0.32, w * 0.04, "#4a5568", w * 0.01) + rect(w * 0.16, -w * 0.5, w * 0.03, w * 0.16, "#4a5568") + rect(-w * 0.3, -w * 0.3, w * 0.24, w * 0.08, col, w * 0.01, dk, sw);
    B.wheels = [[-w * 0.2, -w * 0.2], [w * 0.26, -w * 0.11]]; B.wr = w * 0.2; B.bigFront = w * 0.11; B.seats = [[-w * 0.16, -w * 0.52]];
    B.exhaust = [w * 0.175, -w * 0.52]; B.top = -w * 0.66; B.lamp = [w * 0.32, -w * 0.28];
    B.plate = [w * 0.11, -w * 0.27, w * 0.36, w * 0.07];
  } else if (kind === "plane") {
    const cw2 = p.color ? col : "#f4f7fa";
    B.svg = path(`M${r1(-w * 0.36)} ${r1(-w * 0.2)} L${r1(-w * 0.47)} ${r1(-w * 0.4)} L${r1(-w * 0.4)} ${r1(-w * 0.4)} L${r1(-w * 0.28)} ${r1(-w * 0.26)} Z`, col, dk, sw) +
      path(`M${r1(-w * 0.46)} ${r1(-w * 0.2)} Q${r1(-w * 0.46)} ${r1(-w * 0.27)} ${r1(-w * 0.36)} ${r1(-w * 0.27)} L${r1(w * 0.36)} ${r1(-w * 0.27)} Q${r1(w * 0.5)} ${r1(-w * 0.25)} ${r1(w * 0.5)} ${r1(-w * 0.2)} Q${r1(w * 0.48)} ${r1(-w * 0.14)} ${r1(w * 0.36)} ${r1(-w * 0.13)} L${r1(-w * 0.36)} ${r1(-w * 0.13)} Q${r1(-w * 0.46)} ${r1(-w * 0.13)} ${r1(-w * 0.46)} ${r1(-w * 0.2)} Z`, cw2, shade(cw2, 0.7), sw * 1.4) +
      path(`M${r1(-w * 0.05)} ${r1(-w * 0.16)} L${r1(-w * 0.2)} ${r1(-w * 0.04)} L${r1(-w * 0.12)} ${r1(-w * 0.04)} L${r1(w * 0.12)} ${r1(-w * 0.16)} Z`, col, dk, sw) +
      rect(-w * 0.46, -w * 0.205, w * 0.94, w * 0.012, col, 0) + path(`M${r1(w * 0.41)} ${r1(-w * 0.245)} L${r1(w * 0.47)} ${r1(-w * 0.245)} L${r1(w * 0.48)} ${r1(-w * 0.22)} L${r1(w * 0.42)} ${r1(-w * 0.22)} Z`, glass);
    for (let i = 0; i < 14; i++) B.svg += circ(-w * 0.32 + i * w * 0.05, -w * 0.235, w * 0.009, glass);
    B.svg += line(-w * 0.2, -w * 0.13, -w * 0.2, -w * 0.035, "#4a5568", sw) + line(w * 0.3, -w * 0.13, w * 0.3, -w * 0.035, "#4a5568", sw);
    B.wheels = [[-w * 0.2, -w * 0.02], [w * 0.3, -w * 0.02]]; B.wr = w * 0.02; B.top = -w * 0.4; B.exhaust = null; B.plate = [0, -w * 0.335, w * 0.36, w * 0.095];   // a bigger plate: its words stay readable at the smaller default
  }
  return B;
}

function vehicle(p) {
  const kind = p.kind || "car", def = { car: 600, scooter: 380, bike: 380, cycle: 340, bus: 960, metro: 960, train: 960, auto: 440, erickshaw: 440, truck: 800, tanker: 800, van: 660, tractor: 520, plane: 760 };   // plane 760 (was 1000: it filled half the frame at s 1, ch08)
  const w = N(p.w, 0) || def[kind] || 600, dmg = DMG[p.state] || 0, t = tNow(p);
  const col0 = p.color || { car: "#e5484d", scooter: "#3a7bd5", bike: "#2b2b33", cycle: "#2459a6", bus: "#f29f05", metro: "#7b5cd6", train: "#2459a6", auto: "#f2c14e", erickshaw: "#2a9d8f", truck: "#e07b24", tanker: "#3a7bd5", van: "#f4f7fa", tractor: "#e5484d", plane: "#2459a6" }[kind] || "#e5484d";
  const col = dmg >= 3 ? "#9aa0a8" : col0, fs = p.facing === "left" ? -1 : 1, speed = clamp01(p.speed ?? 0);
  const B = vehicleBody(kind, w, col, p.class || "mid", dmg, p.load, p);
  if (!B.svg) return "";
  const ang = t == null ? 0 : -t * speed * 540;
  let body = "";
  // motion lines and exhaust behind
  if (speed > 0) for (let i = 0; i < 3; i++) body += line(-w * 0.52 - w * 0.04 * i, B.top * (0.3 + i * 0.22) - w * 0.02, -w * 0.52 - w * (0.12 + 0.25 * speed) - w * 0.04 * i, B.top * (0.3 + i * 0.22) - w * 0.02, "#8a8f98", w * 0.008, ` stroke-linecap="round" opacity="${r1(0.4 + speed * 0.5)}"`);
  if (B.exhaust && N(p.smoke, 0) > 0) body += puffs(B.exhaust[0], B.exhaust[1], w * 0.6, N(p.smoke, 0), t, N(p.smoke, 0) > 0.6, kind === "tractor" ? -0.15 : -0.5);
  body += B.svg;
  // riders in the windows / on the seat
  const riders = I(p.riders, 0, 0, 60);
  if (B.sit) { if (riders > 0) body += riderSit(B.sit[0], B.sit[1], w, 0, !!p.box || kind === "bike"); }
  else for (let i = 0; i < Math.min(riders, B.seats.length); i++) body += riderHead(B.seats[i][0], B.seats[i][1], w * (B.seats.length > 4 ? 0.022 : kind === "car" ? 0.035 : 0.045), i);
  B.wheels.forEach(([x, y], i) => { body += wheel(x, y, kind === "tractor" && i === 1 ? B.bigFront : B.wr, ang, dmg >= 3 && i === 0); });
  // lamps: brake lights glow red on the brake
  if (B.lamp) body += circ(B.lamp[0], B.lamp[1], w * 0.014, "#fff3c4", shade(col), w * 0.004);
  if (B.rear) body += circ(B.rear[0], B.rear[1], w * (p.pedal === "brake" ? 0.022 : 0.012), p.pedal === "brake" ? "#ff3b30" : "#e5484d", "", 0, p.pedal === "brake" ? ' opacity="0.95"' : "");
  // fuel badge
  if (p.fuel && p.fuel !== "none") body += fuelBadge(p.fuel, kind === "bus" || kind === "metro" || kind === "train" ? -w * 0.42 : -w * 0.2, B.top + w * (kind === "car" ? 0.2 : 0.09), w * (kind === "bus" || kind === "metro" ? 0.03 : 0.045));
  // damage
  if (dmg >= 1) body += path(`M${r1(-w * 0.25)} ${r1(B.top * 0.45)} l${r1(w * 0.06)} ${r1(w * 0.012)} l${r1(w * 0.04)} ${r1(-w * 0.015)} M${r1(w * 0.05)} ${r1(B.top * 0.4)} l${r1(w * 0.07)} ${r1(w * 0.01)}`, "none", "#f4f7fa", w * 0.006, ' opacity="0.9"');
  if (dmg >= 2) body += path(`M${r1(w * 0.47)} ${r1(B.top * 0.62)} l${r1(-w * 0.05)} ${r1(w * 0.03)} l${r1(w * 0.03)} ${r1(w * 0.03)} l${r1(-w * 0.05)} ${r1(w * 0.03)}`, "none", "#2b2b33", w * 0.01) +
    (B.screen ? path(`M${r1(B.screen[0])} ${r1(B.screen[1])} l${r1(w * 0.03)} ${r1(-w * 0.02)} M${r1(B.screen[0])} ${r1(B.screen[1])} l${r1(-w * 0.02)} ${r1(-w * 0.03)} M${r1(B.screen[0])} ${r1(B.screen[1])} l${r1(w * 0.01)} ${r1(w * 0.035)}`, "none", "#ffffff", w * 0.006) : "") +
    [[0.52, 0.5], [0.56, 0.75]].map(([a, b]) => path(`M${r1(w * a)} ${r1(B.top * b)} l${r1(w * 0.012)} ${r1(w * 0.025)} l${r1(w * 0.025)} ${r1(0)} l${r1(-w * 0.02)} ${r1(w * 0.016)} l${r1(w * 0.01)} ${r1(w * 0.025)} l${r1(-w * 0.025)} ${r1(-w * 0.014)}`, "#f2c14e")).join("");
  if (dmg >= 3) body += puffs(w * 0.3, B.top * 0.7, w * 0.6, 0.6, t, true, 0.1, 2);
  const tilt = (dmg >= 2 ? 3 : 0) + (p.pedal === "brake" ? 2.5 : p.pedal === "accelerator" ? -2.5 : 0);
  let words = "";
  if (B.plate && S(p.label)) {
    const [px, py, pw, ph] = B.plate;
    words += plate(px * fs, py, pw, ph, p.label, B.dark ? "#1f2328" : "#fffbe6", B.dark ? "#f2c14e" : INK, B.dark ? "#000000" : "#2b2b33", ph * 0.15);
  }
  if (S(p.sticker) && B.screen) words += plate(B.screen[0] * fs, B.screen[1] + w * 0.005, w * 0.24, w * 0.075, p.sticker, "#fff3c4", "#8a5a00");
  if (S(p.tag) || S(p.old)) words += tag(0, B.top - w * 0.1, Math.min(w * 0.36, 320), p.tag, p.old);
  const rot = tilt ? ` rotate(${r1(tilt * fs)})` : "";
  return `<g transform="translate(0,0)${rot}"><g transform="scale(${fs},1)">${body}</g>${words}</g>`;
}

// ---------------------------------------------------------------- houses: a row or lane with grades, tags, boards, fire and flood
function miniPerson(x, w, i, dir = 1) {
  const skins = ["#c98850", "#b97745", "#a8663a", "#d39a6a"], tops = ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#2a9d8f"];
  const h = w, c = tops[i % 6];
  return line(x - h * 0.05, -h * 0.4, x - h * 0.06, -h * 0.02, "#2e3440", h * 0.08, ' stroke-linecap="round"') + line(x + h * 0.05, -h * 0.4, x + h * 0.06, -h * 0.02, "#2e3440", h * 0.08, ' stroke-linecap="round"') +
    path(`M${r1(x - h * 0.13)} ${r1(-h * 0.38)} L${r1(x - h * 0.11)} ${r1(-h * 0.74)} Q${r1(x)} ${r1(-h * 0.8)} ${r1(x + h * 0.11)} ${r1(-h * 0.74)} L${r1(x + h * 0.13)} ${r1(-h * 0.38)} Z`, c) +
    circ(x + dir * h * 0.01, -h * 0.87, h * 0.11, skins[i % 4]) + path(`M${r1(x - h * 0.1)} ${r1(-h * 0.88)} A${r1(h * 0.11)} ${r1(h * 0.11)} 0 0 1 ${r1(x + h * 0.11)} ${r1(-h * 0.9)} Z`, "#241b12");
}
function flames(x, y, w, t, k = 3, seed = 0) {
  let out = "";
  for (let i = 0; i < k; i++) {
    const fl = t == null ? 0.5 : 0.5 + 0.5 * Math.sin(t * 9 + i * 2.1 + seed), fx = x + (i - (k - 1) / 2) * w * 0.22, fh = w * (0.32 + 0.12 * fl) * (i === 1 ? 1.2 : 1);
    out += path(`M${r1(fx - w * 0.12)} ${r1(y)} Q${r1(fx - w * 0.14)} ${r1(y - fh * 0.6)} ${r1(fx + w * 0.02 * (fl - 0.5))} ${r1(y - fh)} Q${r1(fx + w * 0.14)} ${r1(y - fh * 0.6)} ${r1(fx + w * 0.12)} ${r1(y)} Z`, "#f08a3c", "#e5484d", w * 0.01) +
      path(`M${r1(fx - w * 0.06)} ${r1(y)} Q${r1(fx - w * 0.07)} ${r1(y - fh * 0.35)} ${r1(fx)} ${r1(y - fh * 0.6)} Q${r1(fx + w * 0.07)} ${r1(y - fh * 0.35)} ${r1(fx + w * 0.06)} ${r1(y)} Z`, "#f2c14e");
  }
  return out;
}
function homeOf(grade, x, w, burnt) {
  const wall = burnt ? "#8a7d72" : { hut: "#e8d2a6", small: "#f4ead9", mid: "#f4ead9", big: "#efe6f4", flat: "#e7ecf1" }[grade] || "#f4ead9";
  const roof = burnt ? "#4a3b34" : { hut: "#c9a24b", small: "#9b6b43", mid: "#c0563f", big: "#5b7fb8", flat: "#6c7a8c" }[grade] || "#c0563f", dk = shade(wall, 0.7);
  const win = burnt ? "#3b3b40" : WIN;
  if (grade === "hut") { const h = w * 0.42;
    return { svg: rect(x - w * 0.36, -h, w * 0.72, h, wall, 0, dk, w * 0.01) + path(`M${r1(x - w * 0.46)} ${r1(-h)} Q${r1(x)} ${r1(-h - w * 0.5)} ${r1(x + w * 0.46)} ${r1(-h)} Z`, roof, shade(roof), w * 0.012) +
      rect(x - w * 0.08, -h * 0.62, w * 0.16, h * 0.62, shade(roof, 0.7)), top: -h - w * 0.36 }; }
  if (grade === "small") { const h = w * 0.5;
    return { svg: rect(x - w * 0.4, -h, w * 0.8, h, wall, 0, dk, w * 0.01) + rect(x - w * 0.44, -h - w * 0.06, w * 0.88, w * 0.07, roof) +
      rect(x - w * 0.3, -h * 0.66, w * 0.18, w * 0.14, win, w * 0.01) + rect(x + w * 0.06, -h * 0.6, w * 0.16, h * 0.6, shade(roof, 0.85)), top: -h - w * 0.06 }; }
  if (grade === "big") { const h = w * 0.82;
    return { svg: rect(x - w * 0.46, -h, w * 0.92, h, wall, 0, dk, w * 0.01) + path(`M${r1(x - w * 0.5)} ${r1(-h)} L${r1(x - w * 0.3)} ${r1(-h - w * 0.2)} L${r1(x + w * 0.3)} ${r1(-h - w * 0.2)} L${r1(x + w * 0.5)} ${r1(-h)} Z`, roof, shade(roof), w * 0.012) +
      [-0.32, -0.06, 0.2].map((dx) => rect(x + w * dx, -h * 0.86, w * 0.14, w * 0.14, win, w * 0.01) + rect(x + w * dx, -h * 0.42, w * 0.14, w * 0.14, win, w * 0.01)).join("") +
      rect(x - w * 0.46, -h * 0.55, w * 0.92, w * 0.03, shade(wall, 0.8)) + rect(x - w * 0.07, -w * 0.22, w * 0.14, w * 0.22, shade(roof, 0.8)), top: -h - w * 0.2 }; }
  if (grade === "flat") { const h = w * 1.3;
    let ws = ""; for (let r = 0; r < 5; r++) for (let c = 0; c < 3; c++) ws += rect(x - w * 0.28 + c * w * 0.2, -h + w * 0.08 + r * w * 0.22, w * 0.14, w * 0.13, win, w * 0.01);
    return { svg: rect(x - w * 0.38, -h, w * 0.76, h, wall, w * 0.01, dk, w * 0.01) + rect(x - w * 0.4, -h - w * 0.04, w * 0.8, w * 0.05, roof) + ws, top: -h - w * 0.04 }; }
  const h = w * 0.55;      // mid: a pitched-roof house
  return { svg: rect(x - w * 0.38, -h, w * 0.76, h, wall, 0, dk, w * 0.01) + path(`M${r1(x - w * 0.47)} ${r1(-h)} L${r1(x)} ${r1(-h - w * 0.36)} L${r1(x + w * 0.47)} ${r1(-h)} Z`, roof, shade(roof), w * 0.012) +
    rect(x - w * 0.08, -h * 0.52, w * 0.16, h * 0.52, shade(roof, 0.8)) + rect(x - w * 0.3, -h * 0.75, w * 0.14, w * 0.12, win, w * 0.01) + rect(x + w * 0.16, -h * 0.75, w * 0.14, w * 0.12, win, w * 0.01), top: -h - w * 0.36 };
}
function houses(p) {
  const w = N(p.w, 300), n = I(p.n, 1, 1, 8), lane = p.layout !== "scattered", gap = lane ? w * 0.06 : w * 0.7, t = tNow(p), st = since(p);
  const gl = listOf(S(p.grades).replace(/,/g, ";")), grade0 = p.grade || "mid";
  const total = n * w + (n - 1) * gap, X = (i) => -total / 2 + w / 2 + i * (w + gap);
  const fire = idxSet(p.fire), boards = S(p.board) ? (S(p.boards) ? idxSet(p.boards) : new Set(Array.from({ length: n }, (_, i) => i + 1))) : new Set();
  if (p.spread && lane && fire.size) {          // fire jumps to the neighbours, one house a second after the step
    const reach = st == null ? n : Math.floor(st / 1.0);
    const seeds = [...fire];
    for (let i = 1; i <= n; i++) if (seeds.some((k) => Math.abs(k - i) <= reach)) fire.add(i);
  }
  let out = "", words = "", top = 0;
  for (let i = 0; i < n; i++) {
    const g = gl[i] || grade0, burning = fire.has(i + 1), H = homeOf(g, X(i), w, burning && (st == null || st > 2.5));
    out += H.svg; top = Math.min(top, H.top);
    if (burning) out += flames(X(i), H.top + w * 0.12, w, t, 3, i);
    if (boards.has(i + 1)) {
      const bx = X(i) + w * 0.3;
      out += line(bx, 0, bx, -w * 0.3, "#7a4e22", w * 0.02);
      words += plate(bx, -w * 0.39, w * 0.58, w * 0.2, p.board, p.boardColor || "#e5484d", "#ffffff", "#ffffff");
    }
  }
  const lv = clamp01(p.flood ?? 0);
  if (lv > 0) {
    const fh = w * 0.55 * lv, x0 = -total / 2 - w * 0.1, x1 = total / 2 + w * 0.1, ph = t == null ? 0 : t * 2;
    let d = `M${r1(x0)} ${r1(w * 0.02)} L${r1(x0)} ${r1(-fh)}`;
    for (let x = x0; x <= x1 + 1; x += w * 0.1) d += ` L${r1(Math.min(x, x1))} ${r1(-fh + Math.sin(x / (w * 0.1) + ph) * w * 0.012)}`;
    out += path(d + ` L${r1(x1)} ${r1(w * 0.02)} Z`, "#4a90c8", "#2f6fa3", w * 0.008, ' opacity="0.72"');
  }
  const buyers = I(p.buyers, 0, 0, 12);
  for (let i = 0; i < buyers; i++) out += miniPerson(-total / 2 - w * 0.2 - i * w * 0.2, w * 0.42, i, 1);
  const ti = I(p.tagAt, 1, 1, n) - 1, tw = Math.min(w * 0.8, 340), vx = X(ti);
  const va = amountOf(p.value), la = amountOf(p.loan), neg = va != null && la != null && va < la;
  let ty = top - tw * 0.3;
  if (S(p.loan)) { words += tag(vx, ty, tw, p.loan, "", "#9fb3c8"); ty -= tw * 0.5; }
  if (S(p.value) || S(p.old)) words += tag(vx, ty - (S(p.old) ? tw * 0.08 : 0), tw, p.value, p.old, neg ? "#e5484d" : "#f2c14e");
  return out + words;
}

// ---------------------------------------------------------------- campus: public buildings (school, college, hospital, clinic, police, ration shop)
function campus(p) {
  const kind = p.kind || "school", w = N(p.w, 600), col = p.color || { school: "#f2c14e", college: "#c0563f", hospital: "#2a9d8f", clinic: "#2a9d8f", police: "#2459a6", rationShop: "#e07b24" }[kind] || "#f2c14e";
  const t = tNow(p), band = w * 0.12;
  const H = { school: 0.52, college: 0.5, hospital: 0.78, clinic: 0.42, police: 0.5, rationShop: 0.46 }[kind] * w;
  const wall = { school: "#f7efd9", college: "#efe6d6", hospital: "#f4f7fa", clinic: "#f4f7fa", police: "#eef1f6", rationShop: "#f7efe2" }[kind] || "#f7efd9";
  const bw = kind === "hospital" ? w * 0.76 : w * 0.92, x0 = -bw / 2;
  const plus = (x, y, r) => circ(x, y, r, "#ffffff", col, r * 0.12) + rect(x - r * 0.18, y - r * 0.6, r * 0.36, r * 1.2, col, r * 0.06) + rect(x - r * 0.6, y - r * 0.18, r * 1.2, r * 0.36, col, r * 0.06);
  const door = (x, dw, dh) => rect(x - dw / 2, -dh, dw, dh, p.open === false ? "#6c7a8c" : "#4a3b2a", dw * 0.05) + (p.open === false ? [0.25, 0.5, 0.75].map((k) => line(x - dw / 2, -dh * k, x + dw / 2, -dh * k, "#4a5568", dw * 0.03)).join("") : "");
  const winRows = (y0, y1, xs, ww, wh) => { let o = ""; const rows = Math.max(1, Math.floor((y1 - y0) / (wh * 1.7))); for (let r = 0; r < rows; r++) for (const x of xs) o += rect(x - ww / 2, y0 + r * wh * 1.7, ww, wh, WIN, ww * 0.1); return o; };
  // the facade, a sign band at its top (the name lives there), windows below, a door
  let out = rect(x0, -H, bw, H, wall, w * 0.006, shade(wall, 0.75), w * 0.008) + rect(x0 - w * 0.015, -H - w * 0.015, bw + w * 0.03, band + w * 0.015, col, w * 0.008);
  let top = -H - w * 0.015;
  const side = [-0.36, -0.22, 0.22, 0.36].map((k) => k * bw);
  if (kind === "college") {
    let cols = ""; for (let i = 0; i < 6; i++) cols += rect(x0 + bw * (0.12 + i * 0.152) - w * 0.022, -H + band + w * 0.01, w * 0.044, H - band - w * 0.07, "#f8f2e6", 0, "#c9b683", w * 0.005);
    out += cols + rect(x0 - w * 0.03, -w * 0.06, bw + w * 0.06, w * 0.06, "#e4dac6") + path(`M${r1(x0 - w * 0.03)} ${r1(-H - w * 0.015)} L0 ${r1(-H - w * 0.2)} L${r1(-x0 + w * 0.03)} ${r1(-H - w * 0.015)} Z`, shade(col, 1.1), shade(col), w * 0.008) + door(0, w * 0.1, H * 0.42);
    top = -H - w * 0.2;
  } else if (kind === "rationShop") {
    out += rect(-bw * 0.38, -H + band + w * 0.04, bw * 0.76, H * 0.42, "#5a4632", w * 0.01) +
      [-0.22, 0, 0.22].map((k, i) => `<g transform="translate(${r1(k * bw)},${r1(-H + band + w * 0.04 + H * 0.42)})">` + produce({ w: w * 0.13, content: ["wheat", "rice", "sugar"][i] }) + `</g>`).join("") +
      rect(-bw * 0.42, -H + band + w * 0.04 + H * 0.42, bw * 0.84, w * 0.035, "#a0703d") + door(0, w * 0.12, H * 0.28);
  } else {
    const bottom = kind === "clinic" ? -w * 0.2 : -w * 0.24;
    out += winRows(-H + band + w * 0.05, bottom, side, w * 0.08, w * 0.075) + door(0, w * 0.13, w * 0.2);
    if (kind === "school") out += rect(-w * 0.09, -H - w * 0.19, w * 0.18, w * 0.18, wall, 0, shade(wall, 0.75), w * 0.006) + path(`M${r1(-w * 0.12)} ${r1(-H - w * 0.19)} L0 ${r1(-H - w * 0.28)} L${r1(w * 0.12)} ${r1(-H - w * 0.19)} Z`, "#c0563f") + circ(0, -H - w * 0.1, w * 0.035, "#e6c25a", "#a8862a", w * 0.006) +
      line(-x0 + w * 0.08, 0, -x0 + w * 0.08, -H - w * 0.25, "#8a8f98", w * 0.012) + path(`M${r1(-x0 + w * 0.08)} ${r1(-H - w * 0.25)} L${r1(-x0 + w * 0.2)} ${r1(-H - w * 0.21)} L${r1(-x0 + w * 0.08)} ${r1(-H - w * 0.17)} Z`, p.flag || "#2fa35b");
    if (kind === "school") top = -H - w * 0.28;
    if (kind === "hospital" || kind === "clinic") { out += plus(0, -H - w * 0.1, w * 0.07) + rect(-w * 0.14, -w * 0.25, w * 0.28, w * 0.035, col); top = -H - w * 0.17; }
    if (kind === "police") { const blink = t == null ? 0 : Math.floor(t * 3) % 2;
      out += rect(-w * 0.09, -H - w * 0.07, w * 0.08, w * 0.05, blink ? "#ff6b6b" : "#e5484d", w * 0.01) + rect(w * 0.01, -H - w * 0.07, w * 0.08, w * 0.05, blink ? "#3a7bd5" : "#6fa8ff", w * 0.01); top = -H - w * 0.07; }
  }
  const q = I(p.queue, 0, 0, 12);
  for (let i = 0; i < q; i++) out += miniPerson(-w * 0.13 - i * w * 0.08, w * 0.2, i, 1);
  return out + plate(0, -H + band / 2 - w * 0.008, bw * 0.7, band * 0.82, p.label, "#ffffff", INK, shade(col));
}

// ---------------------------------------------------------------- pump: a petrol pump with price, litres, tax share, nozzles, queue
function miniCar(x, w, col) {
  return path(`M${r1(x - w * 0.48)} ${r1(-w * 0.1)} L${r1(x - w * 0.48)} ${r1(-w * 0.24)} L${r1(x - w * 0.28)} ${r1(-w * 0.26)} L${r1(x - w * 0.18)} ${r1(-w * 0.42)} L${r1(x + w * 0.2)} ${r1(-w * 0.42)} L${r1(x + w * 0.32)} ${r1(-w * 0.26)} L${r1(x + w * 0.48)} ${r1(-w * 0.22)} L${r1(x + w * 0.48)} ${r1(-w * 0.1)} Z`, col, shade(col), w * 0.02) +
    rect(x - w * 0.14, -w * 0.38, w * 0.3, w * 0.1, WIN, w * 0.02) + circ(x - w * 0.28, -w * 0.09, w * 0.09, "#2b2b33") + circ(x + w * 0.28, -w * 0.09, w * 0.09, "#2b2b33");
}
function govtBadge(x, y, r) {
  return circ(x, y, r, "#e07b24", "#ffffff", r * 0.1) + path(`M${r1(x - r * 0.4)} ${r1(y - r * 0.05)} A${r1(r * 0.4)} ${r1(r * 0.4)} 0 0 1 ${r1(x + r * 0.4)} ${r1(y - r * 0.05)} Z`, "#ffffff") +
    [-0.3, -0.1, 0.1, 0.3].map((k) => rect(x + k * r - r * 0.05, y, r * 0.1, r * 0.35, "#ffffff")).join("") + rect(x - r * 0.5, y + r * 0.35, r, r * 0.1, "#ffffff");
}
function pump(p) {
  const w = N(p.w, 820), t = tNow(p), price = N(p.price, 100), tax = Math.max(0, N(p.tax, 0)), closed = p.closed === true;
  const nz = I(p.nozzles, 2, 1, 6), busy = idxSet(p.busy), cx0 = -w * 0.14, cx1 = w * 0.46;
  let out = "", words = "";
  // canopy and its pillars, the dispensers under it
  out += rect(cx0 + w * 0.04, -w * 0.48, w * 0.025, w * 0.48, "#c9ced6") + rect(cx1 - w * 0.065, -w * 0.48, w * 0.025, w * 0.48, "#c9ced6") +
    rect(cx0, -w * 0.56, cx1 - cx0, w * 0.085, closed ? "#9aa0a8" : (p.color || "#2fa35b"), w * 0.01, shade(p.color || "#2fa35b"), w * 0.004) + rect(cx0, -w * 0.485, cx1 - cx0, w * 0.012, "#f2c14e");
  for (let i = 0; i < nz; i++) {
    const x = cx0 + ((i + 0.5) * (cx1 - cx0)) / nz, on = busy.has(i + 1) && !closed;
    out += rect(x - w * 0.03, -w * 0.2, w * 0.06, w * 0.2, closed ? "#b8bec6" : "#f4f7fa", w * 0.008, "#8a8f98", w * 0.003) + rect(x - w * 0.022, -w * 0.18, w * 0.044, w * 0.04, on ? "#2fa35b" : "#4a5568", w * 0.004) +
      path(`M${r1(x + w * 0.03)} ${r1(-w * 0.12)} Q${r1(x + w * 0.06)} ${r1(-w * 0.06)} ${r1(x + w * (on ? 0.07 : 0.035))} ${r1(-w * (on ? 0.1 : 0.04))}`, "none", "#2b2b33", w * 0.006);
    if (on) out += miniCar(x + w * 0.14, w * 0.17, ["#e5484d", "#3a7bd5", "#f29f05", "#7b61ff", "#2a9d8f", "#c2447a"][i % 6]);
  }
  if (closed) out += line(cx0, -w * 0.08, cx1, -w * 0.08, "#e5484d", w * 0.01, ' stroke-dasharray="12 8"') + (S(p.closedLabel) ? "" : "");
  if (closed && S(p.closedLabel)) words += plate((cx0 + cx1) / 2, -w * 0.3, w * 0.34, w * 0.075, p.closedLabel, "#e5484d", "#ffffff", "#ffffff");
  const q = I(p.queue, 0, 0, 10);
  for (let i = 0; i < q; i++) out += miniCar(cx1 + w * 0.1 + i * w * 0.19, w * 0.17, ["#8a9b56", "#c0563f", "#5b7fb8", "#d9822b"][i % 4]);
  // the price board: fuel name, price, tax share, litres
  const bx0 = -w * 0.48, bw = w * 0.28, bxc = bx0 + bw / 2, by0 = -w * 0.74;
  out += rect(bxc - w * 0.012, by0, w * 0.024, -by0, "#8a8f98") + rect(bx0, by0, bw, w * 0.5, "#2d3748", w * 0.015, "#1f2328", w * 0.004);
  words += plate(bxc, by0 + w * 0.05, bw * 0.92, w * 0.076, p.fuel ?? "", "#f2c14e", INK, "#f2c14e");
  const unit = S(p.unit ?? "₹"), ptxt = inr(`${unit}${Number.isInteger(price) ? price : price.toFixed(2)}`);
  out += rect(bx0 + bw * 0.06, by0 + w * 0.1, bw * 0.88, w * 0.11, "#111418", w * 0.01);
  if (p.priceBoard !== false) words += word(ptxt, bxc, by0 + w * 0.155, bw * 0.84, w * 0.085, "#ffb020", 800);   // false: a price nobody says stays off
  if (tax > 0) {      // the price bar, its tax slice coloured; a split of the slice between buyer and seller
    const share = Math.min(1, tax / Math.max(0.01, price)), barX = bx0 + bw * 0.06, barW = bw * 0.88, y = by0 + w * 0.24, bh = w * 0.045;
    out += rect(barX, y, barW, bh, "#2fa35b", bh * 0.2) + rect(barX + barW * (1 - share), y, barW * share, bh, "#e5484d", 0);
    const sp = N(p.split, -1) < 0 ? null : clamp01(p.split);
    if (sp != null) {
      const k = prog(p, 0.8), x0 = barX + barW * (1 - share), sw2 = barW * share;
      out += rect(x0, y + bh * (1 - k) * 0, sw2 * sp, bh, "#f29f05", 0) + rect(x0 + sw2 * sp, y, sw2 * (1 - sp), bh, "#7b5cd6", 0) + line(x0 + sw2 * sp, y - bh * 0.3, x0 + sw2 * sp, y + bh * 1.3, "#ffffff", w * 0.004);
    }
    words += word(p.taxLabel ?? "", bxc, y + bh + w * 0.04, bw * 0.92, w * 0.05, "#ffffff", 700);
  }
  const litres = N(p.litres, 0), lv = p.count ? Math.round(litres * prog(p, N(p.glide, 3))) : litres;
  if (litres > 0 || p.count) { out += rect(bx0 + bw * 0.06, by0 + w * 0.37, bw * 0.88, w * 0.08, "#111418", w * 0.01); words += word(`${lv}${S(p.litreUnit ?? " L")}`, bxc, by0 + w * 0.41, bw * 0.84, w * 0.06, "#7ee08a", 800); }
  // coins to the government badge, one per litre sold
  if (p.coins) {
    const gx = cx1 - w * 0.06, gy = -w * 0.78, sx = bx0 + bw, sy = by0 + w * 0.26;
    out += govtBadge(gx, gy, w * 0.05);
    for (let i = 0; i < 4; i++) {
      const ph = ((t == null ? 0 : t * 0.6) + i / 4) % 1, x = sx + (gx - sx) * ph, y = sy + (gy - sy) * ph - Math.sin(ph * Math.PI) * w * 0.12;
      out += circ(x, y, w * 0.016, "#f2c14e", "#b8860b", w * 0.004);
    }
    words += word(p.govt ?? "", gx, gy - w * 0.09, w * 0.3, w * 0.05, INK, 800);
  }
  return out + plate((cx0 + cx1) / 2, -w * 0.518, (cx1 - cx0) * 0.62, w * 0.078, p.label, "#ffffff", INK, "#ffffff") + words;
}

// ---------------------------------------------------------------- godown: a store whose stock fills and flows in and out
function unitBox(kind, x, y, s) {
  if (kind === "box") return rect(x - s / 2, y - s * 0.8, s, s * 0.8, "#c8955a", s * 0.05, "#8a6131", s * 0.05) + line(x - s / 2, y - s * 0.55, x + s / 2, y - s * 0.55, "#8a6131", s * 0.04);
  if (kind === "crate") return rect(x - s / 2, y - s * 0.75, s, s * 0.75, "#d9a44a", s * 0.04, "#8a6131", s * 0.05) + line(x - s / 2, y - s * 0.375, x + s / 2, y - s * 0.375, "#8a6131", s * 0.04);
  return path(`M${r1(x - s * 0.46)} ${r1(y)} Q${r1(x - s * 0.55)} ${r1(y - s * 0.4)} ${r1(x - s * 0.36)} ${r1(y - s * 0.66)} L${r1(x + s * 0.36)} ${r1(y - s * 0.66)} Q${r1(x + s * 0.55)} ${r1(y - s * 0.4)} ${r1(x + s * 0.46)} ${r1(y)} Z`, "#c9a46a", "#8a6d3b", s * 0.05) +
    line(x - s * 0.3, y - s * 0.6, x + s * 0.3, y - s * 0.6, "#8a6d3b", s * 0.05);
}
function godown(p) {
  const w = N(p.w, 640), kind = p.content || "sack", f = clamp01(p.fill ?? 0.5), t = tNow(p), shelf = p.kind === "shelf";
  const cols = 6, rows = 4, cap = cols * rows, k = Math.round(f * cap);
  let out = "", words = "";
  const fx0 = -w * 0.36, fw = w * 0.72, fh = w * 0.4, s = (fw / cols) * 0.86;
  if (shelf) {
    out += rect(-w * 0.4, -w * 0.62, w * 0.8, w * 0.62, "#a0703d", w * 0.01, "#6b4a26", w * 0.008);
    for (let r = 0; r < rows; r++) out += rect(-w * 0.38, -w * 0.6 + r * w * 0.15, w * 0.76, w * 0.13, "#f4ead9");
  } else {
    out += path(`M${r1(-w * 0.48)} 0 L${r1(-w * 0.48)} ${r1(-w * 0.5)} L0 ${r1(-w * 0.66)} L${r1(w * 0.48)} ${r1(-w * 0.5)} L${r1(w * 0.48)} 0 Z`, "#efe6d6", "#8a6d3b", w * 0.01) +
      path(`M${r1(-w * 0.52)} ${r1(-w * 0.48)} L0 ${r1(-w * 0.69)} L${r1(w * 0.52)} ${r1(-w * 0.48)}`, "none", "#8a6d3b", w * 0.03) + rect(fx0 - w * 0.02, -fh - w * 0.02, fw + w * 0.04, fh + w * 0.02, "#5a4632");
  }
  for (let i = 0; i < k; i++) {
    const r = Math.floor(i / cols), c = i % cols;
    const x = fx0 + (c + 0.5) * (fw / cols), y = shelf ? -w * 0.6 + (rows - r) * w * 0.15 - w * 0.02 : -r * s * 0.68;
    out += unitBox(kind, x, y, shelf ? s * 0.72 : s);
  }
  if (!shelf) {
    const sh = p.open === false ? 1 : 0;
    if (sh) { out += rect(fx0 - w * 0.02, -fh - w * 0.02, fw + w * 0.04, fh + w * 0.02, "#9aa5b1"); for (let i = 1; i < 8; i++) out += line(fx0 - w * 0.02, -fh + (i * fh) / 8, fx0 + fw + w * 0.02, -fh + (i * fh) / 8, "#6c7a8c", w * 0.004); }
  }
  // in and out: things moving along the ground into the door and out of it
  const flow = (rate, from, to, lab, col) => {
    if (!(rate > 0)) return;
    out += line(from, w * 0.06, to, w * 0.06, col, w * 0.012) + path(`M${r1(to)} ${r1(w * 0.035)} L${r1(to + Math.sign(to - from) * w * 0.035)} ${r1(w * 0.06)} L${r1(to)} ${r1(w * 0.085)} Z`, col);
    const n = 3;
    for (let i = 0; i < n; i++) { const ph = ((t == null ? 0 : t * rate * 0.35) + i / n) % 1; out += unitBox(kind, from + (to - from) * ph, w * 0.035, s * 0.6); }
    words += word(lab, (from + to) / 2, w * 0.14, Math.abs(to - from) * 1.1, w * 0.06, col, 800);
  };
  flow(N(p.inflow, 0), -w * 0.9, -w * 0.5, p.inLabel, "#2fa35b");
  flow(N(p.outflow, 0), w * 0.5, w * 0.9, p.outLabel, "#e5484d");
  if (S(p.label)) words += plate(0, shelf ? -w * 0.7 : -w * 0.53, w * 0.44, w * 0.09, p.label, "#ffffff", INK, "#8a6d3b");
  return out + words;
}

// ---------------------------------------------------------------- headlines: newspaper, TV, phone or billboard with headline cards
function glyph(kind, x, y, r) {
  if (kind === "up") return path(`M${r1(x - r)} ${r1(y + r * 0.6)} L${r1(x)} ${r1(y - r * 0.8)} L${r1(x + r)} ${r1(y + r * 0.6)} Z`, "#2fa35b");
  if (kind === "down") return path(`M${r1(x - r)} ${r1(y - r * 0.6)} L${r1(x)} ${r1(y + r * 0.8)} L${r1(x + r)} ${r1(y - r * 0.6)} Z`, "#e5484d");
  if (kind === "!") return circ(x, y, r, "#f29f05") + rect(x - r * 0.12, y - r * 0.6, r * 0.24, r * 0.75, "#ffffff", r * 0.1) + circ(x, y + r * 0.45, r * 0.13, "#ffffff");
  if (kind === "₹" || kind === "rupee") return circ(x, y, r, "#f2c14e", "#b8860b", r * 0.12) + tx("₹", x, y, r * 1.1, "#8a6508", 800);
  if (kind === "?") return circ(x, y, r, "#7b5cd6") + tx("?", x, y, r * 1.3, "#ffffff", 800);
  return kind ? circ(x, y, r * 0.55, "#4a5568") : "";
}
function headlines(p) {
  const w = N(p.w, 960), medium = p.medium || "newspaper", items = listOf(p.items).slice(0, 8), marks = parts(p.marks), t = tNow(p);
  const n = items.length, upto = p.upto ? I(p.upto, 0, 0, 8) : n, at = I(p.at, 0, 0, 8), k = prog(p, 0.5);
  let out = "";
  if (medium === "billboard") {
    const bw = w, bh = w * 0.42, y0 = -bh * 0.8;
    out += rect(-bw * 0.32, y0 + bh, bw * 0.03, bh * 0.5, "#8a8f98") + rect(bw * 0.29, y0 + bh, bw * 0.03, bh * 0.5, "#8a8f98") +
      rect(-bw / 2, y0, bw, bh, p.color || "#2459a6", w * 0.015, "#1f2328", w * 0.006) + rect(-bw * 0.47, y0 + bh * 0.06, bw * 0.94, bh * 0.88, "#ffffff", w * 0.01);
    if (p.lit) for (let i = 0; i < 3; i++) { const lx = -bw * 0.3 + i * bw * 0.3, fl = t == null ? 1 : 0.75 + 0.25 * Math.sin(t * 7 + i);
      out += rect(lx - w * 0.03, y0 - w * 0.05, w * 0.06, w * 0.03, "#4a5568", w * 0.005) + path(`M${r1(lx - w * 0.025)} ${r1(y0 - w * 0.02)} L${r1(lx - w * 0.12)} ${r1(y0 + bh * 0.6)} L${r1(lx + w * 0.12)} ${r1(y0 + bh * 0.6)} L${r1(lx + w * 0.025)} ${r1(y0 - w * 0.02)} Z`, "#fff3a0", "", 0, ` opacity="${r1(0.35 * fl * 100) / 100}"`); }
    out += word(p.title, 0, y0 + bh * 0.28, bw * 0.84, bh * 0.26, p.color || "#2459a6", 800) + word(items[0] || "", 0, y0 + bh * 0.66, bw * 0.86, bh * 0.2, INK, 700);
    return out;
  }
  if (medium === "tv") {
    const sw = w, sh = w * 0.58, y0 = -sh / 2, cur = items[(at || upto) - 1] || "";
    out += rect(-sw / 2, y0, sw, sh, "#1f2328", w * 0.025) + rect(-sw * 0.46, y0 + sh * 0.06, sw * 0.92, sh * 0.84, "#3b5f8a", w * 0.01) +
      path(`M${r1(-sw * 0.46)} ${r1(y0 + sh * 0.6)} L${r1(-sw * 0.3)} ${r1(y0 + sh * 0.42)} L${r1(-sw * 0.18)} ${r1(y0 + sh * 0.52)} L${r1(0)} ${r1(y0 + sh * 0.3)} L${r1(sw * 0.2)} ${r1(y0 + sh * 0.5)} L${r1(sw * 0.46)} ${r1(y0 + sh * 0.36)} L${r1(sw * 0.46)} ${r1(y0 + sh * 0.9)} L${r1(-sw * 0.46)} ${r1(y0 + sh * 0.9)} Z`, "#4f78a8") +
      rect(-sw * 0.06, y0 + sh, sw * 0.12, w * 0.05, "#4a5568") + rect(-sw * 0.2, y0 + sh + w * 0.05, sw * 0.4, w * 0.02, "#4a5568", w * 0.01);
    if (S(p.title)) out += plate(-sw * 0.3, y0 + sh * 0.14, sw * 0.28, sh * 0.11, p.title, "#e5484d", "#ffffff", "#e5484d");
    if (cur) { const dx = (1 - ease(k)) * -sw * 0.5; out += `<g transform="translate(${r1(dx)},0)">` + rect(-sw * 0.46, y0 + sh * 0.6, sw * 0.92, sh * 0.17, "#ffffff") + rect(-sw * 0.46, y0 + sh * 0.6, sw * 0.03, sh * 0.17, "#e5484d") + word(cur, sw * 0.015, y0 + sh * 0.685, sw * 0.84, sh * 0.11, INK, 800) + `</g>`; }
    if (S(p.ticker)) { const tw = sw * 0.92, span = tw * 1.4, off = t == null ? 0 : (((t * w * 0.12) % span) + span) % span, tx0 = ((tw * 0.7 - off + span) % span) - tw * 0.7 + (t == null ? 0 : 0);
      out += `<clipPath id="tk${Math.round(w)}"><rect x="${r1(-sw * 0.46)}" y="${r1(y0 + sh * 0.78)}" width="${r1(tw)}" height="${r1(sh * 0.12)}"/></clipPath>` + rect(-sw * 0.46, y0 + sh * 0.78, tw, sh * 0.12, "#f2c14e") +
        `<g clip-path="url(#tk${Math.round(w)})">` + word(p.ticker, t == null ? 0 : tx0, y0 + sh * 0.84, tw * 0.7, sh * 0.08, INK, 700) + `</g>`; }
    return out;
  }
  const phone = medium === "phone", pw = phone ? w * 0.5 : w, ph = phone ? w * 0.96 : w * 0.64, y0 = -ph / 2, mast = phone ? ph * 0.12 : ph * 0.16;
  out += phone ? rect(-pw / 2 - w * 0.02, y0 - w * 0.03, pw + w * 0.04, ph + w * 0.06, INK, w * 0.05) + rect(-pw / 2, y0, pw, ph, "#f4f7fa", w * 0.025)
    : rect(-pw / 2, y0, pw, ph, "#fbf7ee", w * 0.006, "#c9c1a8", w * 0.004) + line(-pw * 0.47, y0 + mast + w * 0.005, pw * 0.47, y0 + mast + w * 0.005, INK, w * 0.004);
  out += phone ? rect(-pw / 2, y0, pw, mast, "#2459a6", w * 0.025) + word(p.title, 0, y0 + mast / 2, pw * 0.86, mast * 0.55, "#ffffff", 800)
    : word(p.title, 0, y0 + mast / 2, pw * 0.86, mast * 0.66, INK, 800);
  const top = y0 + mast + ph * 0.04, avail = ph - mast - ph * 0.08, rh = Math.min(avail / Math.max(1, n), ph * 0.2);
  for (let i = 0; i < n && i < upto; i++) {
    const hot = at === i + 1, y = top + i * rh, newest = i === upto - 1 && since(p) != null, dx = newest ? (1 - ease(k)) * pw * 0.6 : 0;
    const gx = -pw * 0.46 + rh * 0.4, mk = S(marks[i]);
    out += `<g transform="translate(${r1(dx)},0)">` + rect(-pw * 0.47, y + rh * 0.08, pw * 0.94, rh * 0.84, hot ? "#fff3c4" : "#ffffff", rh * 0.12, hot ? "#f2c14e" : "#e0dccf", hot ? w * 0.005 : w * 0.002) +
      (mk ? glyph(mk, gx, y + rh / 2, rh * 0.26) : "") + word(items[i], mk ? rh * 0.3 : 0, y + rh / 2, pw * (mk ? 0.78 : 0.88), rh * (hot ? 0.56 : 0.46), INK, hot ? 800 : 700) + `</g>`;
  }
  return out;
}

// ---------------------------------------------------------------- slip: papers (policy, form, pay slip, ration card, ticket, fine, permit, envelope, certificate)
const SLIP = { policy: "#2a9d8f", form: "#5b7fb8", payslip: "#2fa35b", rationCard: "#e07b24", ticket: "#7b5cd6", fine: "#e5484d", permit: "#2459a6", envelope: "#a0703d", certificate: "#c9a400" };
function slip(p) {
  const kind = SLIP[p.kind] ? p.kind : "form", w = N(p.w, 440), col = p.color || SLIP[kind], rows = listOf(p.rows).slice(0, 8);
  const upto = p.upto ? I(p.upto, 0, 0, 8) : rows.length, glow = idxSet(p.glow), count = I(p.count, 1, 1, 6);
  let out = "";
  if (kind === "envelope") {
    const h = w * 0.62, sealed = p.sealed !== false, k = sealed ? 0 : prog(p, 0.6);
    let o = sealed ? "" : path(`M${r1(-w / 2)} ${r1(-h / 2)} L0 ${r1(-h / 2 - h * 0.5)} L${r1(w / 2)} ${r1(-h / 2)} Z`, "#dcc293", "#a0703d", w * 0.006);
    if (!sealed) o += rect(-w * 0.4, -h / 2 - h * 0.55 * ease(k), w * 0.8, h * 0.8, "#ffffff", w * 0.01, "#c9c6bd", w * 0.004) + word(p.amount, 0, -h / 2 - h * 0.55 * ease(k) + h * 0.2, w * 0.7, h * 0.24, INK, 800);
    o += rect(-w / 2, -h / 2, w, h, "#e8d3a9", w * 0.015, "#a0703d", w * 0.006) + path(`M${r1(-w / 2)} ${r1(h / 2)} L0 ${r1(0)} L${r1(w / 2)} ${r1(h / 2)}`, "none", "#c9a46a", w * 0.006);
    if (sealed) o += path(`M${r1(-w / 2)} ${r1(-h / 2)} L0 ${r1(h * 0.08)} L${r1(w / 2)} ${r1(-h / 2)} Z`, "#dcc293", "#a0703d", w * 0.006) + circ(0, h * 0.05, w * 0.06, "#c0392b", "#8e2b1f", w * 0.006);
    if (S(p.title)) o += plate(0, h * 0.3, w * 0.6, h * 0.17, p.title, "#ffffff", INK, "#a0703d");
    if (S(p.stamp)) o += `<g transform="translate(${r1(w * 0.28)},${r1(-h * 0.25)}) rotate(-12)">` + rect(-w * 0.16, -h * 0.1, w * 0.32, h * 0.2, "none", w * 0.01, "#d6454f", w * 0.01) + word(p.stamp, 0, 0, w * 0.28, h * 0.13, "#d6454f", 800) + `</g>`;
    return o;
  }
  if (kind === "ticket") {
    // rows "label:value" (ch13: a ticket ignored them) sit in a strip under the ticket face; the face keeps its look
    const H0 = w * 0.46, rh = w * 0.13, h = H0 + (rows.length ? rows.length * rh + w * 0.03 : 0), x0 = -w / 2, y0 = -h / 2, stub = w * 0.26;
    for (let c = count - 1; c > 0; c--) out += rect(x0 + c * w * 0.02, y0 - c * w * 0.02, w, h, shade(col, 1.25), w * 0.02);
    out += rect(x0, y0, w, h, "#fbf7ee", w * 0.02, col, w * 0.006) + rect(x0, y0, w, H0 * 0.26, col, w * 0.02) + line(x0 + w - stub, y0, x0 + w - stub, y0 + h, col, w * 0.005, ' stroke-dasharray="8 6"');
    out += word(p.title, x0 + (w - stub) / 2, y0 + H0 * 0.13, (w - stub) * 0.9, H0 * 0.17, "#ffffff", 800);
    if (S(p.seat)) out += word(p.seat, x0 + (w - stub) / 2, y0 + H0 * 0.45, (w - stub) * 0.86, H0 * 0.15, INK, 700);
    const face = S(p.face), resale = S(p.resale);
    if (face) { out += word(face, x0 + (w - stub) / 2, y0 + H0 * 0.74, (w - stub) * 0.6, H0 * 0.2, resale ? "#8a8f98" : INK, 800);
      if (resale) out += line(x0 + (w - stub) * 0.25, y0 + H0 * 0.74, x0 + (w - stub) * 0.75, y0 + H0 * 0.74, "#e5484d", H0 * 0.035); }
    if (resale) { const k = prog(p, 0.5); out += `<g transform="translate(${r1(x0 + w - stub / 2)},${r1(y0 + H0 * 0.6)}) rotate(-10) scale(${r1(0.4 + 0.6 * ease(k))})">` + rect(-stub * 0.46, -H0 * 0.17, stub * 0.92, H0 * 0.34, "#fff3c4", H0 * 0.06, "#e5484d", w * 0.006) + word(resale, 0, 0, stub * 0.84, H0 * 0.22, "#e5484d", 800) + `</g>`; }
    else if (p.paperless) out += rect(x0 + w - stub * 0.8, y0 + H0 * 0.35, stub * 0.3, H0 * 0.5, INK, w * 0.01) + rect(x0 + w - stub * 0.77, y0 + H0 * 0.4, stub * 0.24, H0 * 0.36, "#9fc7e8", w * 0.004) +
      rect(x0 + w - stub * 0.42, y0 + H0 * 0.45, stub * 0.32, H0 * 0.26, "#ffffff", w * 0.008, "#4a5568", w * 0.004) + circ(x0 + w - stub * 0.33, y0 + H0 * 0.55, H0 * 0.04, "#c98850");
    else for (let i = 0; i < 6; i++) out += rect(x0 + w - stub * 0.75 + (i % 3) * stub * 0.18, y0 + H0 * 0.4 + Math.floor(i / 3) * H0 * 0.2, stub * 0.12, H0 * 0.14, i % 2 ? INK : "#4a5568");
    rows.forEach((r, i) => {
      const y = y0 + H0 + i * rh, j = r.indexOf(":"), lab = j < 0 ? r : r.slice(0, j).trim(), val = j < 0 ? "" : r.slice(j + 1).trim(), lw = w - stub;
      out += rect(x0 + w * 0.03, y + rh * 0.08, lw - w * 0.05, rh * 0.84, glow.has(i + 1) ? "#fff3c4" : i % 2 ? "#f3efe4" : "#fbf7ee", rh * 0.12, glow.has(i + 1) ? "#f2c14e" : "", glow.has(i + 1) ? w * 0.006 : 0);
      if (i >= upto) { out += rect(x0 + w * 0.07, y + rh * 0.42, lw * 0.5, rh * 0.16, "#e6e8ec", rh * 0.08); return; }
      if (val) out += word(lab, x0 + lw * 0.3, y + rh / 2, lw * 0.52, rh * 0.62, "#4a5568", 700) + word(val, x0 + lw * 0.77, y + rh / 2, lw * 0.4, rh * 0.66, INK, 800);
      else out += word(lab, x0 + lw / 2, y + rh / 2, lw * 0.9, rh * 0.62, INK, 700);
    });
    return out;
  }
  // the portrait papers: a header band with the title, then rows label:value, extras by kind
  const rh = w * 0.13, extra = (kind === "rationCard" ? w * 0.3 : kind === "certificate" ? w * 0.16 : 0) + (S(p.stamp) ? w * 0.2 : 0) + (S(p.owner) ? w * 0.12 : 0), h = w * 0.2 + Math.max(2, rows.length) * rh + extra + w * 0.08;
  const x0 = -w / 2, y0 = -h / 2;
  for (let c = count - 1; c > 0; c--) out += rect(x0 + c * w * 0.025, y0 - c * w * 0.025, w, h, shade(col, 1.3), w * 0.02, shade(col, 0.9), w * 0.003);
  out += rect(x0, y0, w, h, kind === "certificate" ? "#fffaf0" : "#ffffff", w * 0.02, shade(col, 0.85), w * 0.006);
  if (kind === "certificate") out += rect(x0 + w * 0.03, y0 + w * 0.03, w * 0.94, h - w * 0.06, "none", w * 0.015, col, w * 0.01);
  out += rect(x0, y0, w, w * 0.17, col, w * 0.02) + rect(x0, y0 + w * 0.12, w, w * 0.05, col);
  out += word(p.title, 0, y0 + w * 0.085, w * 0.88, w * 0.1, "#ffffff", 800);
  rows.forEach((r, i) => {
    const y = y0 + w * 0.2 + i * rh, j = r.indexOf(":"), lab = j < 0 ? r : r.slice(0, j).trim(), val = j < 0 ? "" : r.slice(j + 1).trim();
    out += rect(x0 + w * 0.04, y + rh * 0.08, w * 0.92, rh * 0.84, glow.has(i + 1) ? "#fff3c4" : i % 2 ? "#f6f7f9" : "#ffffff", rh * 0.12, glow.has(i + 1) ? "#f2c14e" : "", glow.has(i + 1) ? w * 0.006 : 0);
    if (i >= upto) { out += rect(x0 + w * 0.08, y + rh * 0.42, w * 0.5, rh * 0.16, "#e6e8ec", rh * 0.08); return; }
    if (val) out += word(lab, x0 + w * 0.3, y + rh / 2, w * 0.48, rh * 0.62, "#4a5568", 700) + word(val, x0 + w * 0.76, y + rh / 2, w * 0.36, rh * 0.66, INK, 800);
    else out += word(lab, 0, y + rh / 2, w * 0.86, rh * 0.62, INK, 700);
  });
  let yb = y0 + w * 0.2 + Math.max(2, rows.length) * rh;
  if (kind === "rationCard") {
    const weeks = I(p.weeks, 8, 1, 12), st = I(p.stamps, 0, 0, 12), cw = (w * 0.88) / Math.min(weeks, 6), rows2 = Math.ceil(weeks / 6);
    for (let i = 0; i < weeks; i++) { const cx = x0 + w * 0.06 + (i % 6) * cw + cw / 2, cy = yb + w * 0.05 + Math.floor(i / 6) * w * 0.12 + w * 0.05;
      out += rect(cx - cw * 0.42, cy - w * 0.05, cw * 0.84, w * 0.1, "#fbf7ee", w * 0.01, "#c9c1a8", w * 0.004);
      if (i < st) { const pop = i === st - 1 ? ease(prog(p, 0.35)) : 1; out += `<g transform="translate(${r1(cx)},${r1(cy)}) rotate(-12) scale(${r1(0.5 + 0.5 * pop)})">` + circ(0, 0, w * 0.04, "none", "#d6454f", w * 0.008) + path(`M${r1(-w * 0.02)} 0 l${r1(w * 0.015)} ${r1(w * 0.015)} l${r1(w * 0.028)} ${r1(-w * 0.03)}`, "none", "#d6454f", w * 0.008) + `</g>`; } }
    yb += rows2 * w * 0.12 + w * 0.04;
  }
  if (kind === "certificate") { out += circ(x0 + w * 0.8, yb + w * 0.06, w * 0.06, "#f2c14e", "#b8860b", w * 0.008) + path(`M${r1(x0 + w * 0.2)} ${r1(yb + w * 0.08)} q${r1(w * 0.05)} ${r1(-w * 0.05)} ${r1(w * 0.1)} 0 t${r1(w * 0.1)} 0`, "none", INK, w * 0.006); }
  if (S(p.owner)) out += plate(0, y0 + h - w * 0.07, w * 0.8, w * 0.1, p.owner, shade(col, 1.35), shade(col, 0.6), col);
  if (S(p.stamp)) { const pop = ease(prog(p, 0.35)); out += `<g transform="translate(${r1(w * 0.12)},${r1(y0 + h - (S(p.owner) ? w * 0.14 : 0) - w * 0.13)}) rotate(-8) scale(${r1(0.6 + 0.4 * pop)})" opacity="0.92">` + rect(-w * 0.26, -w * 0.07, w * 0.52, w * 0.14, "none", w * 0.02, p.stampColor || "#d6454f", w * 0.014) + word(p.stamp, 0, 0, w * 0.46, w * 0.1, p.stampColor || "#d6454f", 800) + `</g>`; }
  return out;
}

// ---------------------------------------------------------------- clock: a wall clock that runs or stops, with charge bands
const hm = (v) => { const m = S(v).match(/^\s*(\d{1,2})(?::(\d{1,2}))?\s*$/); return m ? Number(m[1]) * 60 + Number(m[2] || 0) : null; };
function clock(p) {
  const w = N(p.w, 340), r = w * 0.44, dial = p.dial === "24" ? 24 : 12, st = since(p);
  let mins = I(p.hour, 3, 0, 23) * 60 + I(p.minute, 0, 0, 59);
  const to = hm(p.to);
  if (to != null) mins = mins + (to - mins) * ease(prog(p, N(p.glide, 2)));
  else if (p.running && st != null) mins += N(p.speed, 1) * st;
  const stopped = p.stopped === true;
  let out = circ(0, 0, r * 1.06, stopped ? "#9aa5b1" : (p.color || "#2459a6")) + circ(0, 0, r * 0.96, stopped ? "#e6e8ec" : "#fbfbf8");
  // charge bands as arcs on the rim; the band holding the time lights up
  const bands = listOf(p.bands).map((b) => { const m = b.match(/^\s*(\d{1,2}(?::\d{1,2})?)\s*-\s*(\d{1,2}(?::\d{1,2})?)\s*(?::(.*))?$/); return m ? { a: hm(m[1]), b: hm(m[2]), lab: (m[3] || "").trim() } : null; }).filter(Boolean);
  const per = dial * 60, cur = ((mins % 1440) + 1440) % 1440;
  let lit = null;
  bands.forEach((b, i) => {
    const on = cur >= b.a && cur < b.b, c = ["#f29f05", "#e5484d", "#2fa35b", "#7b5cd6", "#2a9d8f", "#c2447a"][i % 6];
    const a0 = ((b.a % per) / per) * Math.PI * 2 - Math.PI / 2, a1 = (((b.b - b.a) >= per ? b.a + per - 1 : b.b) % per) / per * Math.PI * 2 - Math.PI / 2;
    const rr = r * 0.86, large = ((a1 - a0 + Math.PI * 4) % (Math.PI * 2)) > Math.PI ? 1 : 0;
    out += path(`M${r1(Math.cos(a0) * rr)} ${r1(Math.sin(a0) * rr)} A${r1(rr)} ${r1(rr)} 0 ${large} 1 ${r1(Math.cos(a1) * rr)} ${r1(Math.sin(a1) * rr)}`, "none", c, r * (on ? 0.16 : 0.09), ` opacity="${on ? 1 : 0.5}"`);
    if (on) lit = { ...b, c };
  });
  for (let i = 0; i < 60; i++) { const a = (i / 60) * Math.PI * 2, big = i % 5 === 0;
    out += line(Math.cos(a) * r * (big ? 0.74 : 0.8), Math.sin(a) * r * (big ? 0.74 : 0.8), Math.cos(a) * r * 0.86, Math.sin(a) * r * 0.86, INK, r * (big ? 0.035 : 0.012)); }
  const ha = ((cur % per) / per) * Math.PI * 2 - Math.PI / 2, ma = ((cur % 60) / 60) * Math.PI * 2 - Math.PI / 2;
  out += line(0, 0, Math.cos(ha) * r * 0.48, Math.sin(ha) * r * 0.48, INK, r * 0.07, ' stroke-linecap="round"') + line(0, 0, Math.cos(ma) * r * 0.7, Math.sin(ma) * r * 0.7, INK, r * 0.045, ' stroke-linecap="round"') +
    (p.running && !stopped ? line(0, 0, Math.cos(ma * 7) * r * 0.74, Math.sin(ma * 7) * r * 0.74, "#e5484d", r * 0.018) : "") + circ(0, 0, r * 0.06, "#e5484d");
  if (stopped) out += circ(r * 0.62, -r * 0.62, r * 0.2, "#4a5568") + rect(r * 0.55, -r * 0.72, r * 0.05, r * 0.2, "#ffffff") + rect(r * 0.65, -r * 0.72, r * 0.05, r * 0.2, "#ffffff");
  let y = r * 1.2;
  if (p.digital) { const hh = Math.floor(cur / 60), mm = Math.floor(cur % 60); out += plate(0, y + w * 0.09, w * 0.56, w * 0.17, `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`, "#1f2328", "#7ee08a", "#1f2328"); y += w * 0.21; }
  if (lit && lit.lab) { out += plate(0, y + w * 0.09, w * 0.66, w * 0.17, lit.lab, lit.c, "#ffffff", lit.c); y += w * 0.21; }
  if (S(p.label)) out += plate(0, y + w * 0.09, w * 0.86, w * 0.17, p.label, "#ffffff", INK, INK);
  return out;
}

// ---------------------------------------------------------------- chance: coin toss, spinner, scratch card, dice, ballot box
function coinFace(x, y, r, txt, heads) {
  return circ(x, y, r, heads ? "#f2c14e" : "#d7dde4", heads ? "#b8860b" : "#8d99a6", r * 0.1) + circ(x, y, r * 0.78, "none", heads ? "#b8860b" : "#8d99a6", r * 0.05, ' stroke-dasharray="4 3"') +
    word(txt, x, y, r * 1.3, r * 0.75, heads ? "#7a5a00" : "#4a5568", 800);
}
function chance(p) {
  const kind = p.kind || "coin", w = N(p.w, 340), t = tNow(p), gl = N(p.glide, 1.2), k = prog(p, gl);
  const H = S(p.heads || "₹"), T = S(p.tails || "1");       // the words come from the plan; bare faces show ₹ and 1
  let out = "";
  if (kind === "coin") {
    const r = w * 0.36, heads = (p.face || "heads") === "heads", flying = p.flip && k < 1;
    const lift = flying ? Math.sin(k * Math.PI) * w * 0.7 : 0, spin = flying ? Math.abs(Math.cos(k * Math.PI * 7)) : 1, showH = flying ? Math.floor(k * 14) % 2 === 0 : heads;
    out += `<ellipse cx="0" cy="${r1(r * 1.08)}" rx="${r1(r * (0.9 - lift / w * 0.4))}" ry="${r1(r * 0.12)}" fill="#2b2017" opacity="0.12"/>` +
      `<g transform="translate(0,${r1(-lift)}) scale(1,${r1(Math.max(0.08, spin))})">` + coinFace(0, 0, r, showH ? H : T, showH) + `</g>`;
    const hist = listOf(S(p.history).replace(/,/g, ";")).slice(-10);
    hist.forEach((h, i) => { const hh = /^(h|heads)$/i.test(h) || h === H; out += coinFace((i - (hist.length - 1) / 2) * w * 0.2, r * 1.5, w * 0.085, hh ? H : (/^(t|tails)$/i.test(h) ? T : h), hh); });
    return out;
  }
  if (kind === "spinner") {
    const r = w * 0.44, sec = listOf(p.sectors).map((s) => { const j = s.lastIndexOf(":"); return { lab: j < 0 ? s : s.slice(0, j), wt: j < 0 ? 1 : Math.max(0, N(s.slice(j + 1), 1)) }; });
    const list = sec.length ? sec : [{ lab: "", wt: 1 }, { lab: "", wt: 1 }], tot = list.reduce((a, b) => a + b.wt, 0) || 1, land = I(p.land, 0, 0, list.length);
    let acc = 0; const mids = list.map((s) => { const a = acc; acc += s.wt; return ((a + s.wt / 2) / tot) * 360; });
    const target = land ? -mids[land - 1] : 0, rot = p.spin ? target - 1080 * (1 - ease(k)) * 1.0 - (1 - k) * 0 : target;
    let disc = ""; acc = 0;
    list.forEach((s, i) => { const a0 = (acc / tot) * Math.PI * 2 - Math.PI / 2; acc += s.wt; const a1 = (acc / tot) * Math.PI * 2 - Math.PI / 2, c = ["#2fa35b", "#e5484d", "#f29f05", "#3a7bd5", "#7b5cd6", "#2a9d8f"][i % 6];
      disc += list.length === 1 ? circ(0, 0, r, c) : path(`M0 0 L${r1(Math.cos(a0) * r)} ${r1(Math.sin(a0) * r)} A${r1(r)} ${r1(r)} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${r1(Math.cos(a1) * r)} ${r1(Math.sin(a1) * r)} Z`, c, "#ffffff", w * 0.008);
      const am = (a0 + a1) / 2, frac = s.wt / tot; if (s.lab) disc += `<g transform="translate(${r1(Math.cos(am) * r * 0.6)},${r1(Math.sin(am) * r * 0.6)}) rotate(${r1(-rot)})">` + word(s.lab, 0, 0, r * Math.min(0.9, 0.3 + frac * 2), r * 0.2, "#ffffff", 800) + `</g>`; });
    return circ(0, 0, r * 1.05, "#2d3748") + `<g transform="rotate(${r1(rot)})">${disc}</g>` + circ(0, 0, r * 0.08, "#ffffff", "#2d3748", w * 0.01) +
      path(`M${r1(-w * 0.05)} ${r1(-r * 1.14)} L${r1(w * 0.05)} ${r1(-r * 1.14)} L0 ${r1(-r * 0.86)} Z`, "#2b2b33");
  }
  if (kind === "scratch") {
    const cw = w * 1.3, ch = w * 0.78, x0 = -cw / 2, y0 = -ch / 2, sc = p.scratch ? k : clamp01(p.scratched ?? 0), win = p.win === true;
    out += rect(x0, y0, cw, ch, "#7b5cd6", w * 0.04, "#4a3196", w * 0.008) + rect(x0 + cw * 0.04, y0 + ch * 0.05, cw * 0.92, ch * 0.26, "#9b7ff0", w * 0.02);
    out += word(p.prize, 0, y0 + ch * 0.18, cw * 0.8, ch * 0.17, "#ffffff", 800);
    const px = x0 + cw * 0.08, py = y0 + ch * 0.38, pw = cw * 0.84, phh = ch * 0.5;
    out += rect(px, py, pw, phh, win ? "#e6f6ea" : "#fdeeee", w * 0.02) + word(p.result, 0, py + phh / 2, pw * 0.8, phh * 0.6, win ? "#2fa35b" : "#e5484d", 800);
    if (sc < 1) out += rect(px + pw * sc, py, pw * (1 - sc), phh, "#b9c1cb", w * 0.02) + (sc > 0 && sc < 1 ? path(`M${r1(px + pw * sc)} ${r1(py)} l${r1(-w * 0.03)} ${r1(phh * 0.25)} l${r1(w * 0.03)} ${r1(phh * 0.25)} l${r1(-w * 0.03)} ${r1(phh * 0.25)} l${r1(w * 0.03)} ${r1(phh * 0.25)}`, "#b9c1cb") : "") +
      [0.25, 0.5, 0.75].map((f) => (f > sc ? circ(px + pw * f, py + phh / 2, phh * 0.12, "#d0d6dd") : "")).join("");
    if (S(p.price)) out += `<g transform="translate(${r1(x0 + cw * 0.92)},${r1(y0)}) rotate(14)">` + circ(0, 0, w * 0.13, "#f2c14e", "#b8860b", w * 0.008) + word(p.price, 0, 0, w * 0.2, w * 0.1, INK, 800) + `</g>`;
    return out;
  }
  if (kind === "dice") {
    const s = w * 0.6, face = p.roll && k < 1 ? 1 + (Math.floor(k * 12) % 6) : I(p.pips, 6, 1, 6), rot = p.roll && k < 1 ? (1 - k) * 360 : 0, lift = p.roll && k < 1 ? Math.sin(k * Math.PI) * w * 0.3 : 0;
    const pip = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]], 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]], 5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]], 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] }[face];
    return `<g transform="translate(0,${r1(-lift)}) rotate(${r1(rot)})">` + rect(-s / 2, -s / 2, s, s, "#ffffff", s * 0.16, "#4a5568", w * 0.012) + pip.map(([a, b]) => circ(a * s * 0.27, b * s * 0.27, s * 0.08, face === 1 ? "#e5484d" : INK)).join("") + `</g>`;
  }
  // ballot: a box with name slips going in; drawn slips come out with a tick
  const bw = w, bh = w * 0.7, slips = I(p.slips, 6, 0, 40), drawn = I(p.drawn, 0, 0, 12);
  out += rect(-bw / 2, -bh * 0.4, bw, bh, "#3a7bd5", w * 0.03, "#2459a6", w * 0.01) + rect(-bw * 0.25, -bh * 0.43, bw * 0.5, bh * 0.07, "#1f2328", w * 0.02);
  for (let i = 0; i < Math.min(slips, 8); i++) { const ph = t == null ? 1 : ((t * 0.7 + i / 8) % 1); if (ph < 0.95) out += rect(-w * 0.08 + (i % 3) * w * 0.03, -bh * 0.43 - w * 0.22 * (1 - ph), w * 0.16, w * 0.1, "#fbf7ee", w * 0.01, "#c9c1a8", w * 0.004); }
  for (let i = 0; i < drawn; i++) { const x = bw * 0.62 + (i % 4) * w * 0.2, y = -bh * 0.3 + Math.floor(i / 4) * w * 0.16;
    out += rect(x - w * 0.08, y - w * 0.05, w * 0.16, w * 0.1, "#fbf7ee", w * 0.01, "#c9c1a8", w * 0.004) + path(`M${r1(x - w * 0.03)} ${r1(y)} l${r1(w * 0.02)} ${r1(w * 0.025)} l${r1(w * 0.045)} ${r1(-w * 0.05)}`, "none", "#2fa35b", w * 0.014); }
  return out + plate(0, bh * 0.12, bw * 0.8, bh * 0.2, p.label, "#ffffff", INK, "#2459a6");
}

// ---------------------------------------------------------------- press: a printing press and its note heap, or an electronic-money screen
function bundle(x, y, s) {
  return rect(x - s / 2, y - s * 0.4, s, s * 0.4, "#6cbf7f", s * 0.04, "#2f7a45", s * 0.03) + rect(x - s * 0.08, y - s * 0.42, s * 0.16, s * 0.44, "#e8d9b0");
}
function press(p) {
  const w = N(p.w, 620), t = tNow(p), run = p.running === true;
  let out = "", words = "";
  if (p.mode === "screen") {
    const sw = w * 0.7, sh = w * 0.42, y0 = -w * 0.62, k = prog(p, N(p.glide, 2)), amt = amountOf(p.amount), shown = p.count && amt != null ? S(p.amount).replace(/[\d,.]+/, Math.round(amt * ease(k)).toLocaleString("en-IN")) : S(p.amount);
    out += rect(-w * 0.45, -w * 0.12, w * 0.9, w * 0.04, "#a0703d") + rect(-w * 0.4, -w * 0.08, w * 0.04, w * 0.08, "#8a6131") + rect(w * 0.36, -w * 0.08, w * 0.04, w * 0.08, "#8a6131") +
      rect(-w * 0.04, y0 + sh, w * 0.08, w * 0.08, "#4a5568") + rect(-sw / 2, y0, sw, sh, "#1f2328", w * 0.02) + rect(-sw * 0.46, y0 + sh * 0.07, sw * 0.92, sh * 0.86, "#0f2a3f", w * 0.01);
    const press0 = since(p) != null && since(p) < 0.25;
    out += rect(-w * 0.3, -w * 0.16, w * 0.6, w * 0.05, "#c9ced6", w * 0.01) + rect(w * 0.05, -w * 0.155, w * 0.06, w * 0.035, press0 ? "#2fa35b" : "#8a8f98", w * 0.006);
    words += word(shown, 0, y0 + sh * 0.55, sw * 0.84, sh * 0.34, "#7ee08a", 800) + (S(p.label) ? plate(0, y0 - w * 0.07, sw * 0.8, w * 0.095, p.label, "#ffffff", INK, INK) : "");
    return out + words;
  }
  const stroke = run && t != null ? (1 - Math.cos(t * 5)) / 2 : 0, rate = N(p.rate, 2), base = I(p.notes, 3, 0, 60);
  const heap = Math.min(28, base + (run && t != null ? Math.floor(t * rate) : 0));
  out += rect(-w * 0.42, -w * 0.62, w * 0.06, w * 0.62, "#4a5568") + rect(-w * 0.02, -w * 0.62, w * 0.06, w * 0.62, "#4a5568") + rect(-w * 0.46, -w * 0.7, w * 0.54, w * 0.1, "#2d3748", w * 0.015) +
    rect(-w * 0.04 - w * 0.31, -w * 0.58 + stroke * w * 0.18, w * 0.32, w * 0.06, "#8a8f98", w * 0.01) + line(-w * 0.19, -w * 0.6, -w * 0.19, -w * 0.58 + stroke * w * 0.18, "#c9ced6", w * 0.025) +
    rect(-w * 0.4, -w * 0.3, w * 0.42, w * 0.06, "#c9ced6", w * 0.01) + rect(-w * 0.46, -w * 0.24, w * 0.54, w * 0.24, "#3a4250", w * 0.015);
  // notes sliding out to the heap
  if (run) for (let i = 0; i < 3; i++) { const ph = t == null ? i / 3 : ((t * rate * 0.5 + i / 3) % 1); out += rect(w * 0.04 + ph * w * 0.2, -w * 0.29 + ph * w * 0.2, w * 0.1, w * 0.045, "#6cbf7f", w * 0.006, "#2f7a45", w * 0.004); }
  let i = 0, row = 0;
  while (i < heap) { const kk = Math.max(1, 5 - row); for (let j = 0; j < kk && i < heap; j++, i++) out += bundle(w * 0.3 + (j - (kk - 1) / 2) * w * 0.1, -row * w * 0.04, w * 0.09); row++; }
  if (S(p.label)) words += plate(-w * 0.19, -w * 0.65, w * 0.52, w * 0.095, p.label, "#ffffff", INK, INK);
  if (S(p.amount)) words += plate(w * 0.3, -row * w * 0.04 - w * 0.15, w * 0.4, w * 0.095, p.amount, "#e6f6ea", "#1f6b35", "#2f7a45");
  return out + words;
}

// ---------------------------------------------------------------- chimney: a factory chimney with its emission level, a filter and a CO2 cloud
function chimney(p) {
  const w = N(p.w, 360), t = tNow(p), lv = clamp01(p.smoke ?? 0.6), filt = p.filter === true;
  const cx = w * 0.18, cw = w * 0.16, ch = w * 1.05, topY = -ch;
  let out = "", words = "";
  if (p.base !== false) out += rect(-w * 0.5, -w * 0.34, w * 0.62, w * 0.34, "#e4ded2", 0, "#9b8a78", w * 0.008) + [0, 1, 2].map((i) => path(`M${r1(-w * 0.5 + i * w * 0.2)} ${r1(-w * 0.34)} L${r1(-w * 0.4 + i * w * 0.2)} ${r1(-w * 0.44)} L${r1(-w * 0.3 + i * w * 0.2)} ${r1(-w * 0.34)} Z`, "#cfc6b8", "#9b8a78", w * 0.006)).join("") +
    [0, 1].map((i) => rect(-w * 0.42 + i * w * 0.2, -w * 0.25, w * 0.12, w * 0.09, WIN, w * 0.01)).join("");
  out += path(`M${r1(cx - cw * 0.6)} 0 L${r1(cx - cw * 0.45)} ${r1(topY)} L${r1(cx + cw * 0.45)} ${r1(topY)} L${r1(cx + cw * 0.6)} 0 Z`, "#9b4a3a", "#6e3226", w * 0.008) +
    rect(cx - cw * 0.55, topY - w * 0.02, cw * 1.1, w * 0.05, "#6e3226") + [0.25, 0.5].map((f) => rect(cx - cw * 0.5, topY + ch * f, cw, w * 0.02, "#f4f7fa", 0, "", 0)).join("");
  if (filt) out += rect(cx - cw * 0.85, topY + ch * 0.06, cw * 1.7, w * 0.16, "#2a9d8f", w * 0.02, "#1d6e60", w * 0.008) + [0, 1, 2, 3].map((i) => line(cx - cw * 0.65 + i * cw * 0.43, topY + ch * 0.08, cx - cw * 0.65 + i * cw * 0.43, topY + ch * 0.06 + w * 0.14, "#ffffff", w * 0.008, ' opacity="0.7"')).join("");
  out += puffs(cx, topY - w * 0.04, w * 1.2, filt ? lv * 0.35 : lv, t, !filt && lv > 0.5, 0.25);
  const cs = clamp01(p.cloudSize ?? 0.5);
  if (S(p.cloud)) { const r = w * (0.16 + 0.26 * cs), x = cx + w * 0.55, y = topY - w * 0.35 - r * 0.3, col = filt ? "#cdd5dd" : "#8a8f98";
    out += [[-0.55, 0.15, 0.6], [0.55, 0.15, 0.62], [0, -0.25, 0.75], [0, 0.25, 0.7]].map(([a, b, c]) => circ(x + a * r, y + b * r, r * c, col)).join("");
    words += word(p.cloud, x, y + r * 0.05, r * 1.7, r * 0.45, "#ffffff", 800); }
  if (S(p.label)) words += plate(-w * 0.19, -w * 0.17, w * 0.56, w * 0.16, p.label, "#ffffff", INK, "#9b8a78");
  return out + words;
}

// ---------------------------------------------------------------- food: Indian snacks, drinks, sweets and packets
function steam(x, y, s, t) {
  let o = "";
  for (let i = 0; i < 3; i++) { const ph = ((t == null ? 0 : t * 0.6) + i / 3) % 1;
    o += path(`M${r1(x + (i - 1) * s * 0.25)} ${r1(y - ph * s)} q${r1(s * 0.12)} ${r1(-s * 0.15)} 0 ${r1(-s * 0.3)} q${r1(-s * 0.12)} ${r1(-s * 0.15)} 0 ${r1(-s * 0.3)}`, "none", "#b9c1cb", s * 0.07, ` stroke-linecap="round" opacity="${r1((1 - ph) * 0.8 * 100) / 100}"`); }
  return o;
}
const FOOD_N = { samosa: 3, paniPuri: 6, jalebi: 3, laddoo: 9, momo: 6, iceCream: 2, thali: 4, toffeeJar: 10, biscuit: 1, sweetBox: 1, tiffin: 3 };
function food(p) {
  const kind = p.kind || "samosa", w = N(p.w, 300), t = tNow(p), n = N(p.n, -1) < 0 ? (FOOD_N[kind] ?? 1) : I(p.n, 1, 0, 30), lv = clamp01(p.level ?? 1), stack = N(p.stack, 0) < 1 ? (kind === "tiffin" ? 3 : 1) : I(p.stack, 1, 1, 8);
  let out = "", words = "";
  const plateE = (rx = w * 0.48) => `<ellipse cx="0" cy="${r1(-w * 0.05)}" rx="${r1(rx)}" ry="${r1(w * 0.1)}" fill="#e3e7ec" stroke="#9aa5b1" stroke-width="${r1(w * 0.012)}"/>` + `<ellipse cx="0" cy="${r1(-w * 0.06)}" rx="${r1(rx * 0.7)}" ry="${r1(w * 0.06)}" fill="#f4f7fa"/>`;
  const row = (k, fn, y, gap) => { let o = ""; for (let i = 0; i < k; i++) o += fn((i - (k - 1) / 2) * gap, y, i); return o; };
  const two = (k, cap, fn, gap) => { const a = Math.min(k, cap), b = Math.max(0, k - cap); return row(a, fn, -w * 0.1, gap) + row(Math.min(b, cap - 1), fn, -w * 0.2, gap); };
  switch (kind) {
    case "samosa": out = plateE() + two(n, 4, (x, y) => path(`M${r1(x - w * 0.1)} ${r1(y)} L${r1(x)} ${r1(y - w * 0.17)} L${r1(x + w * 0.1)} ${r1(y)} Q${r1(x)} ${r1(y + w * 0.03)} ${r1(x - w * 0.1)} ${r1(y)} Z`, "#e0a345", "#a8701f", w * 0.01) + line(x - w * 0.04, y - w * 0.04, x + w * 0.02, y - w * 0.12, "#c88a2e", w * 0.006), w * 0.21); break;
    case "paniPuri": out = plateE() + two(n, 5, (x, y) => circ(x, y - w * 0.05, w * 0.07, "#e9b45a", "#b47f2a", w * 0.008) + circ(x, y - w * 0.07, w * 0.025, "#8a5a2b"), w * 0.16); break;
    case "jalebi": out = plateE() + two(n, 4, (x, y) => path(`M${r1(x)} ${r1(y - w * 0.07)} m${r1(-w * 0.07)} 0 a${r1(w * 0.07)} ${r1(w * 0.055)} 0 1 1 ${r1(w * 0.14)} 0 a${r1(w * 0.05)} ${r1(w * 0.04)} 0 1 1 ${r1(-w * 0.1)} 0 a${r1(w * 0.03)} ${r1(w * 0.025)} 0 1 1 ${r1(w * 0.06)} 0`, "none", "#f08a1c", w * 0.025, ' stroke-linecap="round"'), w * 0.21); break;
    case "momo": out = plateE() + two(n, 4, (x, y) => path(`M${r1(x - w * 0.08)} ${r1(y)} Q${r1(x - w * 0.09)} ${r1(y - w * 0.12)} ${r1(x)} ${r1(y - w * 0.13)} Q${r1(x + w * 0.09)} ${r1(y - w * 0.12)} ${r1(x + w * 0.08)} ${r1(y)} Z`, "#f7f0e2", "#c9bfa8", w * 0.01) + path(`M${r1(x - w * 0.03)} ${r1(y - w * 0.12)} l${r1(w * 0.03)} ${r1(-w * 0.03)} l${r1(w * 0.03)} ${r1(w * 0.03)}`, "none", "#c9bfa8", w * 0.008), w * 0.19); break;
    case "laddoo": out = rect(-w * 0.48, -w * 0.08, w * 0.96, w * 0.08, "#c9ced6", w * 0.02, "#8a8f98", w * 0.008) + (() => { let o = ""; for (let i = 0; i < Math.min(n, 15); i++) o += circ(-w * 0.36 + (i % 5) * w * 0.18, -w * 0.15 - Math.floor(i / 5) * w * 0.1, w * 0.075, "#f2b33d", "#c08316", w * 0.008); return o; })(); break;
    case "thali": { out = `<ellipse cx="0" cy="${r1(-w * 0.06)}" rx="${r1(w * 0.5)}" ry="${r1(w * 0.14)}" fill="#d7dde4" stroke="#8d99a6" stroke-width="${r1(w * 0.012)}"/>`;
      const cols = ["#f2b33d", "#6fa83a", "#fbfbf8", "#c0563f", "#e5484d", "#2fa35b"];
      out += row(Math.min(n, 6), (x, y, i) => `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(w * 0.07)}" ry="${r1(w * 0.03)}" fill="${cols[i]}" stroke="#8d99a6" stroke-width="${r1(w * 0.008)}"/>` + path(`M${r1(x - w * 0.07)} ${r1(y)} Q${r1(x)} ${r1(y + w * 0.06)} ${r1(x + w * 0.07)} ${r1(y)}`, "#c9ced6"), -w * 0.1, w * 0.16) +
        circ(-w * 0.12, -w * 0.02, w * 0.08, "#e8c58a", "#b98a4a", w * 0.008) + mound(w * 0.02, w * 0.26, -w * 0.02, w * 0.06, "rice");
      break; }
    case "kulhad": out = path(`M${r1(-w * 0.2)} ${r1(-w * 0.4)} L${r1(w * 0.2)} ${r1(-w * 0.4)} L${r1(w * 0.14)} 0 L${r1(-w * 0.14)} 0 Z`, "#b5651d", "#7a3f12", w * 0.014) + `<ellipse cx="0" cy="${r1(-w * 0.4)}" rx="${r1(w * 0.2)}" ry="${r1(w * 0.04)}" fill="${lv > 0 ? "#b07a4a" : "#5a3010"}" stroke="#7a3f12" stroke-width="${r1(w * 0.01)}"/>` + (p.steam ? steam(0, -w * 0.46, w * 0.3, t) : ""); break;
    case "chaiGlass": case "lassi": {
      const tall = kind === "lassi", gh = tall ? w * 0.62 : w * 0.38, gw = tall ? w * 0.26 : w * 0.24, liq = kind === "lassi" ? "#fbf3df" : "#b07a4a";
      out = (lv > 0 ? path(`M${r1(-gw / 2 + gw * 0.08 * (1 - lv))} ${r1(-gh * lv * 0.92)} L${r1(gw / 2 - gw * 0.08 * (1 - lv))} ${r1(-gh * lv * 0.92)} L${r1(gw * 0.42)} 0 L${r1(-gw * 0.42)} 0 Z`, liq) : "") +
        path(`M${r1(-gw / 2)} ${r1(-gh)} L${r1(gw / 2)} ${r1(-gh)} L${r1(gw * 0.42)} 0 L${r1(-gw * 0.42)} 0 Z`, "#dfeaf3", "#9db3c7", w * 0.012, ' fill-opacity="0.35"') +
        (tall ? line(gw * 0.1, -gh * 1.15, gw * 0.25, -gh * 0.3, "#e5484d", w * 0.02) : "") + (p.steam ? steam(0, -gh - w * 0.04, w * 0.28, t) : "");
      break; }
    case "coffeeCup": out = `<ellipse cx="0" cy="${r1(-w * 0.03)}" rx="${r1(w * 0.3)}" ry="${r1(w * 0.05)}" fill="#e3e7ec" stroke="#9aa5b1" stroke-width="${r1(w * 0.01)}"/>` + path(`M${r1(-w * 0.18)} ${r1(-w * 0.36)} L${r1(w * 0.18)} ${r1(-w * 0.36)} L${r1(w * 0.14)} ${r1(-w * 0.05)} L${r1(-w * 0.14)} ${r1(-w * 0.05)} Z`, p.color || "#ffffff", "#9aa5b1", w * 0.012) +
      path(`M${r1(w * 0.17)} ${r1(-w * 0.3)} q${r1(w * 0.12)} ${r1(0)} ${r1(w * 0.08)} ${r1(w * 0.12)} q${r1(-w * 0.03)} ${r1(w * 0.06)} ${r1(-w * 0.1)} ${r1(w * 0.04)}`, "none", "#9aa5b1", w * 0.025) + `<ellipse cx="0" cy="${r1(-w * 0.36)}" rx="${r1(w * 0.18)}" ry="${r1(w * 0.03)}" fill="#6b4226"/>` + (p.steam ? steam(0, -w * 0.42, w * 0.3, t) : ""); break;
    case "chutney": out = bowlOf(w, "#3f8f3a"); break;
    case "bread": out = path(`M${r1(-w * 0.42)} 0 L${r1(-w * 0.42)} ${r1(-w * 0.22)} Q${r1(-w * 0.42)} ${r1(-w * 0.42)} ${r1(-w * 0.2)} ${r1(-w * 0.42)} L${r1(w * 0.2)} ${r1(-w * 0.42)} Q${r1(w * 0.42)} ${r1(-w * 0.42)} ${r1(w * 0.42)} ${r1(-w * 0.22)} L${r1(w * 0.42)} 0 Z`, "#d9a05b", "#9a6a2e", w * 0.012) + [-0.2, 0, 0.2].map((k) => line(w * k - w * 0.05, -w * 0.38, w * k + w * 0.05, -w * 0.3, "#f2d39e", w * 0.02)).join(""); break;
    case "iceCream": out = path(`M${r1(-w * 0.13)} ${r1(-w * 0.42)} L0 0 L${r1(w * 0.13)} ${r1(-w * 0.42)} Z`, "#e0a345", "#a8701f", w * 0.01) + (() => { let o = ""; for (let i = 0; i < Math.min(n, 4); i++) o += circ((i % 2 ? 1 : -1) * w * 0.02, -w * 0.48 - i * w * 0.15, w * 0.15, ["#f7c6d0", "#fbf3df", "#8a5a2b", "#a8e0c0"][i], shade(["#f7c6d0", "#fbf3df", "#8a5a2b", "#a8e0c0"][i], 0.85), w * 0.01); return o; })(); break;
    case "iceCup": out = path(`M${r1(-w * 0.2)} ${r1(-w * 0.32)} L${r1(w * 0.2)} ${r1(-w * 0.32)} L${r1(w * 0.15)} 0 L${r1(-w * 0.15)} 0 Z`, p.color || "#f7c6d0", "#c2447a", w * 0.012) + rect(-w * 0.22, -w * 0.37, w * 0.44, w * 0.05, "#ffffff", w * 0.02, "#c2447a", w * 0.008) + line(w * 0.05, -w * 0.37, w * 0.2, -w * 0.5, "#c9a46a", w * 0.025); break;
    case "paneer": out = rect(-w * 0.32, -w * 0.28, w * 0.64, w * 0.28, "#fbf7ee", w * 0.03, "#d6cdb8", w * 0.012) + [[-0.15, -0.15], [0.1, -0.1], [0.18, -0.2]].map(([a, b]) => circ(w * a, w * b, w * 0.015, "#e6dcc4")).join(""); break;
    case "tiffin": { for (let i = 0; i < stack; i++) out += rect(-w * 0.26, -w * 0.06 - (i + 1) * w * 0.16, w * 0.52, w * 0.15, "#d7dde4", w * 0.03, "#8d99a6", w * 0.012) + line(-w * 0.26, -w * 0.06 - (i + 1) * w * 0.16 + w * 0.03, w * 0.26, -w * 0.06 - (i + 1) * w * 0.16 + w * 0.03, "#a9b3bf", w * 0.008);
      const top = -w * 0.06 - stack * w * 0.16; out += rect(-w * 0.2, -w * 0.06, w * 0.4, w * 0.06, "#c9ced6", w * 0.02) + path(`M${r1(-w * 0.3)} ${r1(-w * 0.1)} L${r1(-w * 0.3)} ${r1(top - w * 0.06)} Q0 ${r1(top - w * 0.2)} ${r1(w * 0.3)} ${r1(top - w * 0.06)} L${r1(w * 0.3)} ${r1(-w * 0.1)}`, "none", "#6c7a8c", w * 0.02); break; }
    case "plate": { const po = clamp01(p.portion ?? 0.5); out = plateE() + (po > 0 ? mound(-w * 0.3 * po - w * 0.05, w * 0.3 * po + w * 0.05, -w * 0.07, w * 0.25 * po + w * 0.02, p.color ? "dal" : "rice") : ""); break; }
    case "ghee": case "toffeeJar": {
      const jar = kind === "toffeeJar", jh = w * 0.6, jw = w * 0.5;
      out = rect(-jw / 2, -jh, jw, jh, jar ? "#eef6fb" : "#f2c14e", w * 0.06, jar ? "#9db3c7" : "#b8860b", w * 0.012, ) + rect(-jw * 0.45, -jh - w * 0.07, jw * 0.9, w * 0.08, jar ? "#e5484d" : "#c0563f", w * 0.02);
      if (jar) { let o = ""; const k = Math.min(n, 18); for (let i = 0; i < k; i++) o += circ(-jw * 0.32 + (i % 4) * jw * 0.21, -w * 0.06 - Math.floor(i / 4) * w * 0.09, w * 0.04, ["#e5484d", "#f29f05", "#2fa35b", "#3a7bd5", "#7b5cd6"][i % 5]); out += o; }
      words += plate(0, -jh * 0.5, jw * 1.0, w * 0.19, p.label, "#ffffff", INK, "#9aa5b1"); break; }
    case "biscuit": case "milkPacket": case "sweetBox": {
      for (let i = 0; i < stack; i++) { const y = -i * w * (kind === "sweetBox" ? 0.2 : 0.14);
        if (kind === "biscuit") out += rect(-w * 0.45, y - w * 0.3, w * 0.9, w * 0.3, p.color || "#d9822b", w * 0.03, shade(p.color || "#d9822b"), w * 0.01) + circ(-w * 0.28, y - w * 0.15, w * 0.09, "#e8c58a", "#b98a4a", w * 0.008) + circ(-w * 0.22, y - w * 0.13, w * 0.09, "#e8c58a", "#b98a4a", w * 0.008);
        else if (kind === "milkPacket") out += path(`M${r1(-w * 0.3)} ${r1(y)} Q${r1(-w * 0.36)} ${r1(y - w * 0.25)} ${r1(-w * 0.28)} ${r1(y - w * 0.5)} L${r1(w * 0.28)} ${r1(y - w * 0.5)} Q${r1(w * 0.36)} ${r1(y - w * 0.25)} ${r1(w * 0.3)} ${r1(y)} Z`, "#f4f7fa", p.color || "#3a7bd5", w * 0.014) + rect(-w * 0.3, y - w * 0.18, w * 0.6, w * 0.06, p.color || "#3a7bd5");
        else out += rect(-w * 0.45, y - w * 0.2, w * 0.9, w * 0.2, p.color || "#e5484d", w * 0.02, shade(p.color || "#e5484d"), w * 0.01) + line(-w * 0.45, y - w * 0.1, w * 0.45, y - w * 0.1, "#f2c14e", w * 0.02); }
      const topY = -(stack - 1) * w * (kind === "sweetBox" ? 0.2 : 0.14);
      words += plate(kind === "biscuit" ? w * 0.08 : 0, topY - (kind === "milkPacket" ? w * 0.34 : kind === "sweetBox" ? w * 0.1 : w * 0.15), w * (kind === "biscuit" ? 0.62 : 0.6), w * (kind === "sweetBox" ? 0.15 : 0.2), p.label, "#ffffff", INK, "#9aa5b1"); break; }
    default: out = plateE();
  }
  if (S(p.price) || S(p.old)) words += tag(w * 0.42, -w * 0.5, w * 0.5, p.price, p.old);
  if (S(p.label) && !/ghee|toffeeJar|biscuit|milkPacket|sweetBox/.test(kind)) words += plate(0, w * 0.15, w * 0.74, w * 0.19, p.label, "#fffaf0", INK, "#c9c1a8");
  return out + words;
}
function bowlOf(w, fill) {
  return path(`M${r1(-w * 0.3)} ${r1(-w * 0.22)} Q${r1(-w * 0.28)} 0 0 0 Q${r1(w * 0.28)} 0 ${r1(w * 0.3)} ${r1(-w * 0.22)} Z`, "#d7dde4", "#8d99a6", w * 0.012) + `<ellipse cx="0" cy="${r1(-w * 0.22)}" rx="${r1(w * 0.3)}" ry="${r1(w * 0.06)}" fill="${fill}" stroke="#8d99a6" stroke-width="${r1(w * 0.01)}"/>`;
}

// ---------------------------------------------------------------- machine: appliances and work machines with screens and states
function screenOf(x, y, sw, sh, p, t) {
  const st = p.screen || "normal";
  if (st === "off") return rect(x - sw / 2, y - sh / 2, sw, sh, "#1f2328", sw * 0.03);
  let o = rect(x - sw / 2, y - sh / 2, sw, sh, st === "frozen" ? "#d9ecf7" : "#f4f7fa", sw * 0.03);
  if (st === "loading") { const a = t == null ? 0 : t * 6; o += circ(x, y, sh * 0.22, "none", "#d5dbe1", sh * 0.06) + path(`M${r1(x + Math.cos(a) * sh * 0.22)} ${r1(y + Math.sin(a) * sh * 0.22)} A${r1(sh * 0.22)} ${r1(sh * 0.22)} 0 0 1 ${r1(x + Math.cos(a + 1.6) * sh * 0.22)} ${r1(y + Math.sin(a + 1.6) * sh * 0.22)}`, "none", "#3a7bd5", sh * 0.06); return o; }
  if (st === "frozen") o += [0, 60, 120].map((d) => { const r = (d * Math.PI) / 180; return line(x - Math.cos(r) * sh * 0.25, y - Math.sin(r) * sh * 0.25, x + Math.cos(r) * sh * 0.25, y + Math.sin(r) * sh * 0.25, "#3a7bd5", sh * 0.04); }).join("");
  else {
    if (S(p.title)) o += rect(x - sw / 2, y - sh / 2, sw, sh * 0.3, p.color || "#2459a6", sw * 0.03) + word(p.title, x, y - sh / 2 + sh * 0.15, sw * 0.9, sh * 0.2, "#ffffff", 800);
    const ty = S(p.title) ? y + sh * 0.15 : y;
    if (S(p.old)) o += word(p.old, x, ty - sh * 0.16, sw * 0.8, sh * 0.16, "#8a8f98", 700) + line(x - sw * 0.25, ty - sh * 0.16, x + sw * 0.25, ty - sh * 0.16, "#e5484d", sh * 0.025);
    o += word(p.text, x, S(p.old) ? ty + sh * 0.1 : ty, sw * 0.88, sh * (S(p.title) ? 0.26 : 0.34), INK, 800);
  }
  if (st === "cracked") o += path(`M${r1(x + sw * 0.1)} ${r1(y - sh * 0.1)} l${r1(-sw * 0.25)} ${r1(-sh * 0.35)} M${r1(x + sw * 0.1)} ${r1(y - sh * 0.1)} l${r1(sw * 0.3)} ${r1(-sh * 0.2)} M${r1(x + sw * 0.1)} ${r1(y - sh * 0.1)} l${r1(-sw * 0.1)} ${r1(sh * 0.55)} M${r1(x + sw * 0.1)} ${r1(y - sh * 0.1)} l${r1(sw * 0.35)} ${r1(sh * 0.3)} M${r1(x + sw * 0.1)} ${r1(y - sh * 0.1)} l${r1(-sw * 0.4)} ${r1(sh * 0.15)}`, "none", "#4a5568", sw * 0.012);
  return o;
}
function shield(x, y, r) { return path(`M${r1(x)} ${r1(y - r)} L${r1(x + r * 0.85)} ${r1(y - r * 0.65)} Q${r1(x + r * 0.85)} ${r1(y + r * 0.5)} ${r1(x)} ${r1(y + r)} Q${r1(x - r * 0.85)} ${r1(y + r * 0.5)} ${r1(x - r * 0.85)} ${r1(y - r * 0.65)} Z`, "#2fa35b", "#ffffff", r * 0.12) + path(`M${r1(x - r * 0.35)} ${r1(y)} l${r1(r * 0.25)} ${r1(r * 0.28)} l${r1(r * 0.48)} ${r1(-r * 0.55)}`, "none", "#ffffff", r * 0.16); }
function machine(p) {
  const kind = p.kind || "laptop", w = N(p.w, 360), t = tNow(p), on = p.on === true, lv = clamp01(p.level ?? 1);
  let out = "", words = "";
  switch (kind) {
    case "cylinder": out = rect(-w * 0.22, -w * 0.72, w * 0.44, w * 0.66, p.color || "#e5484d", w * 0.16, "#a3273a", w * 0.012) + rect(-w * 0.16, -w * 0.06, w * 0.32, w * 0.06, "#8a8f98") +
      path(`M${r1(-w * 0.12)} ${r1(-w * 0.72)} L${r1(-w * 0.12)} ${r1(-w * 0.86)} L${r1(w * 0.12)} ${r1(-w * 0.86)} L${r1(w * 0.12)} ${r1(-w * 0.72)}`, "none", "#a3273a", w * 0.03) + rect(-w * 0.04, -w * 0.82, w * 0.08, w * 0.1, "#c9ced6") +
      rect(w * 0.12, -w * 0.62, w * 0.05, w * 0.46, "#ffffff", w * 0.02, "#a3273a", w * 0.006) + rect(w * 0.125, -w * 0.16 - w * 0.45 * lv, w * 0.04, w * 0.45 * lv, "#2fa35b", w * 0.015);
      words += plate(-w * 0.04, -w * 0.4, w * 0.3, w * 0.12, p.label, "#ffffff", INK, "#a3273a"); break;
    case "cooker": { const bob = on && t != null ? Math.abs(Math.sin(t * 9)) * w * 0.03 : 0;
      out = path(`M${r1(-w * 0.32)} ${r1(-w * 0.4)} L${r1(w * 0.32)} ${r1(-w * 0.4)} L${r1(w * 0.3)} 0 L${r1(-w * 0.3)} 0 Z`, "#c9ced6", "#6c7a8c", w * 0.012) + `<ellipse cx="0" cy="${r1(-w * 0.42)}" rx="${r1(w * 0.3)}" ry="${r1(w * 0.06)}" fill="#a9b3bf" stroke="#6c7a8c" stroke-width="${r1(w * 0.01)}"/>` +
        rect(w * 0.3, -w * 0.36, w * 0.3, w * 0.06, "#2b2b33", w * 0.03) + rect(-w * 0.04, -w * 0.52 - bob, w * 0.08, w * 0.1, "#2b2b33", w * 0.02) + (on ? puffs(0, -w * 0.58 - bob, w * 0.7, 0.6, t, false, 0.1) : ""); break; }
    case "fan": { const a = on && t != null ? t * 900 : 0;
      out = rect(-w * 0.2, -w * 0.05, w * 0.4, w * 0.05, "#4a5568", w * 0.02) + rect(-w * 0.03, -w * 0.5, w * 0.06, w * 0.45, "#6c7a8c") + circ(0, -w * 0.72, w * 0.3, "none", "#9aa5b1", w * 0.012) +
        `<g transform="translate(0,${r1(-w * 0.72)}) rotate(${r1(a % 360)})">` + [0, 120, 240].map((d) => `<ellipse cx="0" cy="${r1(-w * 0.15)}" rx="${r1(w * 0.07)}" ry="${r1(w * 0.14)}" transform="rotate(${d})" fill="${p.color || "#3a7bd5"}" opacity="${on ? 0.75 : 1}"/>`).join("") + `</g>` + circ(0, -w * 0.72, w * 0.05, "#2d3748"); break; }
    case "fridge": {
      const fh = w * 1.5, rows = listOf(p.rows).slice(0, 5), nr = Math.max(3, rows.length), ih = fh * 0.82, rh = ih / nr;
      out = rect(-w * 0.4, -fh, w * 0.8, fh, p.color || "#e9eef3", w * 0.04, "#9aa5b1", w * 0.012) + rect(-w * 0.35, -fh + w * 0.06, w * 0.7, ih, "#dff1fb", w * 0.02, "#9db3c7", w * 0.008);
      for (let r = 0; r < nr; r++) { const y = -fh + w * 0.06 + (r + 1) * rh, k = Math.round(lv * 4), col = ["#e5484d", "#3a7bd5", "#2fa35b", "#f29f05", "#7b5cd6"][r % 5];
        for (let i = 0; i < k; i++) out += rect(-w * 0.3 + i * w * 0.155, y - rh * 0.62, w * 0.12, rh * 0.5, col, w * 0.015, shade(col), w * 0.006);
        out += rect(-w * 0.35, y - w * 0.015, w * 0.7, w * 0.015, "#9db3c7");
        if (rows[r]) words += plate(0, y - rh * 0.3, w * 0.6, Math.min(rh * 0.4, w * 0.16), rows[r], "#ffffff", INK, col); }
      out += rect(w * 0.32, -fh * 0.6, w * 0.03, fh * 0.2, "#6c7a8c", w * 0.01); break; }
    case "washer": { const a = on && t != null ? t * 400 : 0;
      out = rect(-w * 0.4, -w * 0.9, w * 0.8, w * 0.9, "#f4f7fa", w * 0.04, "#9aa5b1", w * 0.012) + rect(-w * 0.4, -w * 0.9, w * 0.8, w * 0.14, "#e3e7ec", w * 0.04) + circ(w * 0.25, -w * 0.83, w * 0.035, "#6c7a8c") +
        circ(0, -w * 0.4, w * 0.27, "#c9ced6", "#8a8f98", w * 0.02) + circ(0, -w * 0.4, w * 0.21, "#7fb6e0") + `<g transform="translate(0,${r1(-w * 0.4)}) rotate(${r1(a % 360)})">` + circ(w * 0.08, w * 0.05, w * 0.07, "#e5484d") + circ(-w * 0.06, w * 0.08, w * 0.06, "#f2c14e") + `</g>`; break; }
    case "tv": out = rect(-w * 0.5, -w * 0.72, w, w * 0.6, "#1f2328", w * 0.03) + screenOf(0, -w * 0.42, w * 0.9, w * 0.5, p, t) + rect(-w * 0.05, -w * 0.12, w * 0.1, w * 0.08, "#4a5568") + rect(-w * 0.22, -w * 0.04, w * 0.44, w * 0.04, "#4a5568", w * 0.02); break;
    case "laptop": out = path(`M${r1(-w * 0.55)} 0 L${r1(w * 0.55)} 0 L${r1(w * 0.47)} ${r1(-w * 0.06)} L${r1(-w * 0.47)} ${r1(-w * 0.06)} Z`, "#9aa5b1", "#6c7a8c", w * 0.008) + rect(-w * 0.45, -w * 0.66, w * 0.9, w * 0.6, "#2d3748", w * 0.03) + screenOf(0, -w * 0.36, w * 0.82, w * 0.52, p, t); break;
    case "phone": out = rect(-w * 0.28, -w * 1.1, w * 0.56, w * 1.1, INK, w * 0.08) + screenOf(0, -w * 0.55, w * 0.48, w * 0.9, p, t); break;
    case "sewing": { const nd = on && t != null ? Math.abs(Math.sin(t * 10)) * w * 0.06 : 0, slide = on && t != null ? (t * w * 0.1) % (w * 0.3) : 0;
      out = rect(-w * 0.5, -w * 0.14, w, w * 0.04, "#a0703d") + rect(-w * 0.44, -w * 0.1, w * 0.04, w * 0.1, "#8a6131") + rect(w * 0.4, -w * 0.1, w * 0.04, w * 0.1, "#8a6131") +
        `<clipPath id="sw${Math.round(w)}"><rect x="${r1(-w * 0.45)}" y="${r1(-w * 0.2)}" width="${r1(w * 0.9)}" height="${r1(w * 0.06)}"/></clipPath><g clip-path="url(#sw${Math.round(w)})">` + [0, 1, 2, 3, 4].map((i) => rect(-w * 0.6 + i * w * 0.3 + slide, -w * 0.18, w * 0.28, w * 0.04, i % 2 ? "#e5484d" : "#f29f05")).join("") + `</g>` +
        path(`M${r1(-w * 0.36)} ${r1(-w * 0.18)} L${r1(-w * 0.36)} ${r1(-w * 0.5)} L${r1(w * 0.22)} ${r1(-w * 0.5)} L${r1(w * 0.22)} ${r1(-w * 0.36)} L${r1(-w * 0.2)} ${r1(-w * 0.36)} L${r1(-w * 0.2)} ${r1(-w * 0.18)} Z`, "#2b2b33", "#000000", w * 0.006) +
        circ(-w * 0.36, -w * 0.4, w * 0.08, "#4a5568", "#c9ced6", w * 0.01) + line(w * 0.16, -w * 0.36, w * 0.16, -w * 0.24 + nd, "#c9ced6", w * 0.012) + rect(-w * 0.1, -w * 0.48, w * 0.2, w * 0.05, "#c9a400", w * 0.01); break; }
    case "loom": { const sh = on && t != null ? Math.sin(t * 3) : 0, cloth = clamp01(p.level ?? 0.5);
      out = rect(-w * 0.48, -w * 0.8, w * 0.04, w * 0.8, "#8a6131") + rect(w * 0.44, -w * 0.8, w * 0.04, w * 0.8, "#8a6131") + rect(-w * 0.5, -w * 0.84, w, w * 0.05, "#a0703d", w * 0.01);
      for (let i = 0; i < 11; i++) out += line(-w * 0.38 + i * w * 0.076, -w * 0.78, -w * 0.38 + i * w * 0.076, -w * 0.2, "#d9cdb4", w * 0.006);
      out += rect(-w * 0.4, -w * 0.2 - w * 0.4 * cloth, w * 0.8, w * 0.4 * cloth, p.color || "#c2447a", 0) + [0.25, 0.5, 0.75].map((f) => line(-w * 0.4, -w * 0.2 - w * 0.4 * cloth * f, w * 0.4, -w * 0.2 - w * 0.4 * cloth * f, "#f2c14e", w * 0.01)).join("") +
        rect(-w * 0.44, -w * 0.22 - w * 0.4 * cloth - w * 0.04, w * 0.88, w * 0.03, "#8a6131") + path(`M${r1(sh * w * 0.3 - w * 0.08)} ${r1(-w * 0.24 - w * 0.4 * cloth - w * 0.05)} L${r1(sh * w * 0.3 + w * 0.08)} ${r1(-w * 0.24 - w * 0.4 * cloth - w * 0.05)} L${r1(sh * w * 0.3 + w * 0.05)} ${r1(-w * 0.24 - w * 0.4 * cloth - w * 0.09)} L${r1(sh * w * 0.3 - w * 0.05)} ${r1(-w * 0.24 - w * 0.4 * cloth - w * 0.09)} Z`, "#6b4a26") +
        rect(-w * 0.5, -w * 0.2, w, w * 0.05, "#a0703d", w * 0.01); break; }
    case "tandoor": case "bhatti": case "oven": {
      const fl = on ? (t == null ? 1 : 0.7 + 0.3 * Math.sin(t * 8)) : 0;
      if (kind === "tandoor") out = path(`M${r1(-w * 0.34)} 0 Q${r1(-w * 0.42)} ${r1(-w * 0.35)} ${r1(-w * 0.24)} ${r1(-w * 0.6)} L${r1(w * 0.24)} ${r1(-w * 0.6)} Q${r1(w * 0.42)} ${r1(-w * 0.35)} ${r1(w * 0.34)} 0 Z`, on ? "#b5651d" : "#a08a78", "#7a3f12", w * 0.012) + `<ellipse cx="0" cy="${r1(-w * 0.6)}" rx="${r1(w * 0.24)}" ry="${r1(w * 0.06)}" fill="${on ? "#f08a3c" : "#4a3b34"}" opacity="${on ? r1(0.6 + 0.4 * fl) : 1}"/>` + (on ? flames(0, -w * 0.6, w * 0.4, t, 3) : "");
      else if (kind === "bhatti") out = rect(-w * 0.42, -w * 0.42, w * 0.84, w * 0.42, on ? "#b5651d" : "#9a8a7c", w * 0.02, "#6e3226", w * 0.012) + [0, 1, 2].map((r) => line(-w * 0.42, -w * 0.14 * (r + 1), w * 0.42, -w * 0.14 * (r + 1), "#6e3226", w * 0.006)).join("") + rect(-w * 0.16, -w * 0.24, w * 0.32, w * 0.2, on ? "#f08a3c" : "#3b3b40", w * 0.08) + (on ? flames(0, -w * 0.42, w * 0.5, t, 3) : "");
      else out = rect(-w * 0.42, -w * 0.6, w * 0.84, w * 0.6, "#c9ced6", w * 0.03, "#6c7a8c", w * 0.012) + rect(-w * 0.32, -w * 0.46, w * 0.5, w * 0.34, on ? "#f2a03c" : "#3b3b40", w * 0.02, "#4a5568", w * 0.01) + [0, 1].map((i) => circ(w * 0.3, -w * 0.45 + i * w * 0.14, w * 0.04, "#4a5568")).join("") + (on ? rect(-w * 0.3, -w * 0.25, w * 0.46, w * 0.03, "#e5484d", w * 0.01, "", 0) : "");
      break; }
    case "kadhai": { const big = p.size === "big", kw = big ? w * 1.0 : w * 0.66;
      out = rect(-kw * 0.36, -w * 0.12, kw * 0.72, w * 0.12, "#4a5568", w * 0.02) + (on ? flames(0, -w * 0.12, kw * 0.5, t, 4) : "") +
        path(`M${r1(-kw / 2)} ${r1(-w * 0.32)} Q${r1(-kw * 0.45)} ${r1(-w * 0.1)} 0 ${r1(-w * 0.1)} Q${r1(kw * 0.45)} ${r1(-w * 0.1)} ${r1(kw / 2)} ${r1(-w * 0.32)} Z`, "#3b3b40", "#1c1c20", w * 0.012) +
        `<ellipse cx="0" cy="${r1(-w * 0.32)}" rx="${r1(kw / 2)}" ry="${r1(w * 0.05)}" fill="${lv > 0 ? "#e0b030" : "#2b2b33"}" stroke="#1c1c20" stroke-width="${r1(w * 0.01)}"/>` +
        circ(-kw / 2 - w * 0.03, -w * 0.32, w * 0.035, "none", "#1c1c20", w * 0.02) + circ(kw / 2 + w * 0.03, -w * 0.32, w * 0.035, "none", "#1c1c20", w * 0.02); break; }
    case "till": out = path(`M${r1(-w * 0.42)} ${r1(-w * 0.1)} L${r1(-w * 0.36)} ${r1(-w * 0.46)} L${r1(w * 0.36)} ${r1(-w * 0.46)} L${r1(w * 0.42)} ${r1(-w * 0.1)} Z`, "#4a5568", "#2d3748", w * 0.01) + rect(-w * 0.46, -w * 0.12, w * 0.92, w * 0.12, "#2d3748", w * 0.02) +
      (on ? rect(-w * 0.4, -w * 0.02, w * 0.8, w * 0.12, "#6b7280", w * 0.01) + [0, 1, 2].map((i) => rect(-w * 0.34 + i * w * 0.24, 0, w * 0.18, w * 0.07, "#6cbf7f", w * 0.01)).join("") : "") +
      rect(-w * 0.24, -w * 0.66, w * 0.48, w * 0.2, "#1f2328", w * 0.02); words += word(p.text, 0, -w * 0.56, w * 0.44, w * 0.13, "#7ee08a", 800);
      out = `<g transform="translate(0,${r1(-w * 0.12)})">${out}</g>`; words = `<g transform="translate(0,${r1(-w * 0.12)})">${words}</g>`; break;
    case "pos": { const st = p.state || "idle";
      out = rect(-w * 0.2, -w * 0.62, w * 0.4, w * 0.62, "#2d3748", w * 0.06) + rect(-w * 0.16, -w * 0.56, w * 0.32, w * 0.22, st === "approved" ? "#e6f6ea" : "#dfe8f3", w * 0.02) +
        [0, 1, 2].map((r) => [0, 1, 2].map((c) => rect(-w * 0.14 + c * w * 0.1, -w * 0.28 + r * w * 0.08, w * 0.07, w * 0.05, "#6c7a8c", w * 0.01)).join("")).join("");
      if (st === "approved") out += path(`M${r1(-w * 0.05)} ${r1(-w * 0.45)} l${r1(w * 0.04)} ${r1(w * 0.05)} l${r1(w * 0.08)} ${r1(-w * 0.09)}`, "none", "#2fa35b", w * 0.03);
      else words += word(p.text, 0, -w * 0.45, w * 0.3, w * 0.1, INK, 800);
      if (st === "tap") { const k = prog(p, 0.6); out += `<g transform="translate(${r1(w * 0.3 - k * w * 0.12)},${r1(-w * 0.78 + k * w * 0.1)}) rotate(-15)">` + rect(-w * 0.15, -w * 0.09, w * 0.3, w * 0.18, "#2459a6", w * 0.02) + rect(-w * 0.11, -w * 0.04, w * 0.06, w * 0.04, "#f2c14e") + `</g>` +
        [1, 2].map((i) => path(`M${r1(-w * 0.08 * i)} ${r1(-w * 0.66 - w * 0.03 * i)} Q0 ${r1(-w * 0.72 - w * 0.04 * i)} ${r1(w * 0.08 * i)} ${r1(-w * 0.66 - w * 0.03 * i)}`, "none", "#3a7bd5", w * 0.012)).join(""); }
      break; }
    case "meter": case "iu": { const iu = kind === "iu";
      out = rect(-w * 0.34, iu ? -w * 0.4 : -w * 0.8, w * 0.68, iu ? w * 0.4 : w * 0.8, iu ? "#2d3748" : "#e9eef3", w * 0.04, "#6c7a8c", w * 0.012) + rect(-w * 0.27, iu ? -w * 0.34 : -w * 0.7, w * 0.54, w * 0.18, "#1f2328", w * 0.02);
      words += word(p.text, 0, iu ? -w * 0.25 : -w * 0.61, w * 0.5, w * 0.12, "#7ee08a", 800);
      if (!iu) { out += rect(-w * 0.27, -w * 0.42, w * 0.54, w * 0.07, "#d5dbe1", w * 0.03) + rect(-w * 0.27, -w * 0.42, w * 0.54 * lv, w * 0.07, lv < 0.25 ? "#e5484d" : "#2fa35b", w * 0.03) + circ(0, -w * 0.2, w * 0.08, "#c9ced6", "#6c7a8c", w * 0.008);
        words += word(p.title, 0, -w * 0.88, w * 0.7, w * 0.11, INK, 800); }
      else out += rect(-w * 0.2, -w * 0.12, w * 0.4, w * 0.04, "#000000", w * 0.01);
      break; }
    case "printer": out = rect(-w * 0.42, -w * 0.4, w * 0.84, w * 0.34, "#e3e7ec", w * 0.04, "#8a8f98", w * 0.012) + rect(-w * 0.28, -w * 0.56, w * 0.56, w * 0.16, "#ffffff", 0, "#c9c6bd", w * 0.006) + rect(-w * 0.3, -w * 0.08, w * 0.6, w * 0.08, "#ffffff", 0, "#c9c6bd", w * 0.006) +
      ["#3a7bd5", "#e2558f", "#f2c14e", "#2b2b33"].map((c, i) => rect(w * 0.12 + i * w * 0.06, -w * 0.3, w * 0.04, w * 0.14, "#ffffff", w * 0.01, c, w * 0.006) + rect(w * 0.12 + i * w * 0.06, -w * 0.16 - w * 0.14 * lv, w * 0.04, w * 0.14 * lv, c, w * 0.01)).join(""); break;
    case "console": out = rect(-w * 0.4, -w * 0.18, w * 0.8, w * 0.18, "#2d3748", w * 0.03) + rect(-w * 0.36, -w * 0.14, w * 0.3, w * 0.03, "#3a7bd5", w * 0.01) +
      path(`M${r1(w * 0.0)} ${r1(-w * 0.32)} Q${r1(-w * 0.12)} ${r1(-w * 0.32)} ${r1(-w * 0.14)} ${r1(-w * 0.22)} L${r1(w * 0.36)} ${r1(-w * 0.22)} Q${r1(w * 0.34)} ${r1(-w * 0.32)} ${r1(w * 0.22)} ${r1(-w * 0.32)} Z`, "#4a5568") + circ(w * 0.02, -w * 0.27, w * 0.025, "#e5484d") + circ(w * 0.2, -w * 0.27, w * 0.025, "#2fa35b"); break;
    case "camera": { const fl = since(p) != null && since(p) < 0.3;
      out = rect(-w * 0.02, -w * 0.9, w * 0.04, w * 0.9, "#6c7a8c") + rect(-w * 0.02, -w * 0.9, w * 0.3, w * 0.03, "#6c7a8c") + rect(w * 0.16, -w * 0.88, w * 0.22, w * 0.12, "#2d3748", w * 0.02) + circ(w * 0.34, -w * 0.82, w * 0.04, fl ? "#fff3a0" : "#7fb6e0", "#1f2328", w * 0.008) +
        (fl ? path(`M${r1(w * 0.38)} ${r1(-w * 0.82)} L${r1(w * 0.7)} ${r1(-w * 0.5)} L${r1(w * 0.5)} ${r1(-w * 0.4)} Z`, "#fff3a0", "", 0, ' opacity="0.7"') : ""); break; }
    default: out = rect(-w * 0.3, -w * 0.4, w * 0.6, w * 0.4, "#c9ced6", w * 0.03);
  }
  if (p.shield) out += shield(w * 0.42, -w * 0.62, w * 0.12);
  if (S(p.price) || S(p.oldPrice)) words += tag(w * 0.76, -w * 0.3, w * 0.46, p.price, p.oldPrice);
  if (S(p.label) && kind !== "cylinder") words += plate(0, w * 0.1, w * 0.8, w * 0.16, p.label, "#fffaf0", INK, "#c9c1a8");
  return out + words;
}

// ---------------------------------------------------------------- goods: small everyday things (packs, tools, signs, toys)
function goods(p) {
  const kind = p.kind || "mug", w = N(p.w, 300), t = tNow(p), col = p.color, cnt = I(p.count, 1, 1, 8);
  let out = "", words = "";
  const lab = (y, ww, hh, bg = "#ffffff", fg = INK) => (words += plate(0, y, ww, hh, p.label, bg, fg, "#9aa5b1"));
  switch (kind) {
    case "mug": out = rect(-w * 0.26, -w * 0.5, w * 0.48, w * 0.5, col || "#3a7bd5", w * 0.06, shade(col || "#3a7bd5"), w * 0.012) + path(`M${r1(w * 0.22)} ${r1(-w * 0.4)} q${r1(w * 0.18)} 0 ${r1(w * 0.14)} ${r1(w * 0.16)} q${r1(-w * 0.04)} ${r1(w * 0.1)} ${r1(-w * 0.14)} ${r1(w * 0.08)}`, "none", shade(col || "#3a7bd5"), w * 0.05); lab(-w * 0.25, w * 0.46, w * 0.2); break;
    case "pen": out = `<g transform="rotate(-30)">` + rect(-w * 0.45, -w * 0.05, w * 0.8, w * 0.1, col || "#2459a6", w * 0.04) + path(`M${r1(w * 0.35)} ${r1(-w * 0.05)} L${r1(w * 0.48)} 0 L${r1(w * 0.35)} ${r1(w * 0.05)} Z`, "#e8c58a") + rect(-w * 0.3, -w * 0.08, w * 0.25, w * 0.03, "#c9ced6") + `</g>`; break;
    case "razor": out = rect(-w * 0.04, -w * 0.62, w * 0.08, w * 0.5, col || "#3a7bd5", w * 0.03) + rect(-w * 0.2, -w * 0.72, w * 0.4, w * 0.12, "#c9ced6", w * 0.02, "#6c7a8c", w * 0.008) + line(-w * 0.18, -w * 0.62, w * 0.18, -w * 0.62, "#8a8f98", w * 0.01); break;
    case "padlock": { const open = p.open === true;
      out = path(`M${r1(-w * 0.18)} ${r1(-w * 0.42)} L${r1(-w * 0.18)} ${r1(-w * 0.6 - (open ? w * 0.12 : 0))} A${r1(w * 0.18)} ${r1(w * 0.18)} 0 0 1 ${r1(w * 0.18)} ${r1(-w * 0.6 - (open ? w * 0.12 : 0))} L${r1(w * 0.18)} ${r1(open ? -w * 0.62 : -w * 0.42)}`, "none", "#8a8f98", w * 0.07) +
        rect(-w * 0.3, -w * 0.45, w * 0.6, w * 0.45, col || "#f2c14e", w * 0.06, "#b8860b", w * 0.012) + circ(0, -w * 0.26, w * 0.05, "#5a4632") + rect(-w * 0.02, -w * 0.26, w * 0.04, w * 0.1, "#5a4632"); lab(-w * 0.11, w * 0.5, w * 0.12); break; }
    case "matchbox": out = rect(-w * 0.35, -w * 0.25, w * 0.7, w * 0.25, col || "#e5484d", w * 0.02, "#a3273a", w * 0.01) + rect(-w * 0.35, -w * 0.25, w * 0.08, w * 0.25, "#5a4632") + line(w * 0.0, -w * 0.4, w * 0.2, -w * 0.25, "#e8c58a", w * 0.025) + circ(w * 0.0, -w * 0.4, w * 0.03, "#c0392b"); break;
    case "tissue": for (let i = 0; i < cnt; i++) out += rect(-w * 0.32, -(i + 1) * w * 0.07, w * 0.64, w * 0.065, "#ffffff", w * 0.02, "#c9ced6", w * 0.006); break;
    case "shirt": out = path(`M${r1(-w * 0.16)} ${r1(-w * 0.72)} L${r1(-w * 0.42)} ${r1(-w * 0.6)} L${r1(-w * 0.34)} ${r1(-w * 0.44)} L${r1(-w * 0.26)} ${r1(-w * 0.48)} L${r1(-w * 0.26)} 0 L${r1(w * 0.26)} 0 L${r1(w * 0.26)} ${r1(-w * 0.48)} L${r1(w * 0.34)} ${r1(-w * 0.44)} L${r1(w * 0.42)} ${r1(-w * 0.6)} L${r1(w * 0.16)} ${r1(-w * 0.72)} Q0 ${r1(-w * 0.6)} ${r1(-w * 0.16)} ${r1(-w * 0.72)} Z`, col || "#3a7bd5", shade(col || "#3a7bd5"), w * 0.012) + [0.5, 0.36, 0.22].map((y) => circ(0, -w * y, w * 0.015, "#ffffff")).join(""); lab(-w * 0.3, w * 0.4, w * 0.13); break;
    case "seedPacket": case "medicine": case "cigarettes": case "chip": {
      if (kind === "seedPacket") { out = rect(-w * 0.3, -w * 0.72, w * 0.6, w * 0.72, col || "#2fa35b", w * 0.03, "#1f6b35", w * 0.01) + circ(0, -w * 0.48, w * 0.14, "#fbf7ee") + piece("maize", 0, -w * 0.48, w * 0.1); lab(-w * 0.2, w * 0.54, w * 0.15); }
      if (kind === "medicine") { out = rect(-w * 0.45, -w * 0.3, w * 0.9, w * 0.3, "#dfe5ec", w * 0.04, "#9aa5b1", w * 0.01); for (let i = 0; i < 5; i++) out += `<ellipse cx="${r1(-w * 0.34 + i * w * 0.17)}" cy="${r1(-w * 0.15)}" rx="${r1(w * 0.06)}" ry="${r1(w * 0.09)}" fill="${col || "#e2558f"}" stroke="#ffffff" stroke-width="${r1(w * 0.01)}"/>`; }
      if (kind === "cigarettes") { const wr = clamp01(p.warning ?? 0.3), k = prog(p, 0.6), h = w * 0.7;
        out = rect(-w * 0.26, -h, w * 0.52, h, col || "#8a6d3b", w * 0.02, "#5a4632", w * 0.01) + rect(-w * 0.26, -h, w * 0.52, h * wr, "#2b2b33", w * 0.02) + (wr > 0.1 ? path(`M${r1(-w * 0.08)} ${r1(-h + h * wr * 0.25)} L${r1(w * 0.08)} ${r1(-h + h * wr * 0.75)} M${r1(w * 0.08)} ${r1(-h + h * wr * 0.25)} L${r1(-w * 0.08)} ${r1(-h + h * wr * 0.75)}`, "none", "#e5484d", w * 0.03) : "");
        if (S(p.label)) words += plate(0, -h * 0.25, w * 0.48, w * 0.13, p.label, "#ffffff", INK, "#5a4632"); void k; }
      if (kind === "chip") { for (let i = 0; i < cnt; i++) { const x = (i - (cnt - 1) / 2) * w * 0.5; out += rect(x - w * 0.2, -w * 0.4, w * 0.4, w * 0.4, "#2d3748", w * 0.03) + rect(x - w * 0.12, -w * 0.32, w * 0.24, w * 0.24, "#8a8f98", w * 0.02) +
          [0, 1, 2, 3].map((k) => line(x - w * 0.24, -w * 0.33 + k * w * 0.08, x - w * 0.2, -w * 0.33 + k * w * 0.08, "#c9a400", w * 0.02) + line(x + w * 0.2, -w * 0.33 + k * w * 0.08, x + w * 0.24, -w * 0.33 + k * w * 0.08, "#c9a400", w * 0.02)).join(""); }
        if (S(p.label)) lab(w * 0.1, w * 0.6, w * 0.14); }
      break; }
    case "bottle": case "can": {
      for (let i = 0; i < cnt; i++) { const x = (i - (cnt - 1) / 2) * w * 0.34, c = col || (kind === "can" ? "#c0392b" : "#2f6b3a");
        out += kind === "can" ? rect(x - w * 0.14, -w * 0.5, w * 0.28, w * 0.5, c, w * 0.04, shade(c), w * 0.01) + rect(x - w * 0.12, -w * 0.52, w * 0.24, w * 0.03, "#c9ced6", w * 0.01)
          : path(`M${r1(x - w * 0.06)} ${r1(-w * 0.92)} L${r1(x + w * 0.06)} ${r1(-w * 0.92)} L${r1(x + w * 0.06)} ${r1(-w * 0.7)} Q${r1(x + w * 0.15)} ${r1(-w * 0.62)} ${r1(x + w * 0.15)} ${r1(-w * 0.5)} L${r1(x + w * 0.15)} 0 L${r1(x - w * 0.15)} 0 L${r1(x - w * 0.15)} ${r1(-w * 0.5)} Q${r1(x - w * 0.15)} ${r1(-w * 0.62)} ${r1(x - w * 0.06)} ${r1(-w * 0.7)} Z`, c, shade(c), w * 0.01, ' fill-opacity="0.92"') + rect(x - w * 0.07, -w * 0.98, w * 0.14, w * 0.07, "#c9a400", w * 0.02); }
      if (S(p.label)) words += plate(0, -w * 0.27, Math.max(w * 0.5, cnt * w * 0.32), w * 0.14, p.label, "#fbf7ee", INK, "#9aa5b1"); break; }
    case "toolbox": { const tools = listOf(p.tools), upto = p.upto ? I(p.upto, 0, 0, 8) : tools.length;
      out = rect(-w * 0.45, -w * 0.4, w * 0.9, w * 0.4, col || "#e5484d", w * 0.03, "#a3273a", w * 0.012) + path(`M${r1(-w * 0.15)} ${r1(-w * 0.4)} L${r1(-w * 0.15)} ${r1(-w * 0.5)} L${r1(w * 0.15)} ${r1(-w * 0.5)} L${r1(w * 0.15)} ${r1(-w * 0.4)}`, "none", "#4a5568", w * 0.03);
      tools.slice(0, upto).forEach((tl, i) => { const k = i === upto - 1 ? ease(prog(p, 0.5)) : 1, x = (i - (Math.min(upto, tools.length) - 1) / 2) * w * 0.46, y = -w * 0.5 - w * 0.25 * k;
        words += plate(x, y, w * 0.4, w * 0.15, tl, "#fff3c4", INK, "#c9a400"); });
      if (S(p.label)) lab(-w * 0.2, w * 0.6, w * 0.15); break; }
    case "handcuffs": out = circ(-w * 0.18, -w * 0.25, w * 0.15, "none", "#8a8f98", w * 0.05) + circ(w * 0.18, -w * 0.25, w * 0.15, "none", "#8a8f98", w * 0.05) + line(-w * 0.04, -w * 0.32, w * 0.04, -w * 0.32, "#6c7a8c", w * 0.04); break;
    case "jail": { const k = ease(prog(p, 0.5)); out = rect(-w * 0.5, -w * 1.0, w, w * 0.06, "#4a5568") + rect(-w * 0.5, -w * 0.06, w, w * 0.06, "#4a5568");
      for (let i = 0; i < 6; i++) out += rect(-w * 0.45 + i * w * 0.18, -w * 0.94 - (1 - k) * w * 0.9, w * 0.05, w * 0.88, "#6c7a8c", w * 0.02);
      if (S(p.label)) words += plate(0, -w * 1.1, w * 0.6, w * 0.14, p.label, "#2d3748", "#ffffff", "#2d3748"); break; }
    case "tin": { const open = p.open === true; out = rect(-w * 0.22, -w * 0.48, w * 0.44, w * 0.48, "#c9ced6", w * 0.04, "#6c7a8c", w * 0.012) + rect(-w * 0.22, -w * 0.36, w * 0.44, w * 0.2, col || "#e5484d") +
        (open ? `<g transform="rotate(-35 ${r1(-w * 0.22)} ${r1(-w * 0.5)})">` + `<ellipse cx="0" cy="${r1(-w * 0.5)}" rx="${r1(w * 0.22)}" ry="${r1(w * 0.05)}" fill="#e3e7ec" stroke="#6c7a8c" stroke-width="${r1(w * 0.01)}"/></g>` : `<ellipse cx="0" cy="${r1(-w * 0.48)}" rx="${r1(w * 0.22)}" ry="${r1(w * 0.05)}" fill="#e3e7ec" stroke="#6c7a8c" stroke-width="${r1(w * 0.01)}"/>`) +
        (p.opener ? `<g transform="translate(${r1(w * 0.36)},${r1(-w * 0.3)}) rotate(20)">` + rect(-w * 0.03, 0, w * 0.06, w * 0.3, "#4a5568", w * 0.02) + path(`M${r1(-w * 0.03)} 0 L${r1(-w * 0.03)} ${r1(-w * 0.1)} L${r1(w * 0.06)} ${r1(-w * 0.06)} Z`, "#8a8f98") + `</g>` : ""); break; }
    case "stool": out = rect(-w * 0.3, -w * 0.5, w * 0.6, w * 0.06, col || "#a0703d", w * 0.02) + line(-w * 0.24, -w * 0.45, -w * 0.3, 0, "#8a6131", w * 0.04) + line(w * 0.24, -w * 0.45, w * 0.3, 0, "#8a6131", w * 0.04) + line(-w * 0.27, -w * 0.2, w * 0.27, -w * 0.2, "#8a6131", w * 0.025); break;
    case "noticeBoard": case "placard": { const pl = kind === "placard";
      out = pl ? rect(-w * 0.02, -w * 0.7, w * 0.04, w * 0.7, "#8a6131") + rect(-w * 0.45, -w * 1.05, w * 0.9, w * 0.42, col || "#fbf7ee", w * 0.02, "#8a6131", w * 0.012)
        : rect(-w * 0.45, -w * 0.9, w * 0.9, w * 0.6, "#c8955a", w * 0.02, "#8a6131", w * 0.012) + rect(-w * 0.4, -w * 0.85, w * 0.8, w * 0.5, "#fbf7ee", w * 0.01) + line(-w * 0.35, -w * 0.3, -w * 0.38, 0, "#8a6131", w * 0.03) + line(w * 0.35, -w * 0.3, w * 0.38, 0, "#8a6131", w * 0.03);
      words += pl ? word(p.label, 0, -w * 0.84, w * 0.82, w * 0.2, INK, 800) : word(p.label, 0, -w * 0.6, w * 0.74, w * 0.18, INK, 800); break; }
    case "magnifier": out = line(w * 0.12, -w * 0.38, w * 0.4, -w * 0.08, "#6b4a26", w * 0.08, ' stroke-linecap="round"') + circ(-w * 0.06, -w * 0.56, w * 0.24, "#dff1fb", "#4a5568", w * 0.05, ' fill-opacity="0.6"'); break;
    case "tree": out = rect(-w * 0.05, -w * 0.18, w * 0.1, w * 0.18, "#8a6131") + [0, 1, 2].map((i) => path(`M${r1(-w * (0.4 - i * 0.08))} ${r1(-w * (0.16 + i * 0.22))} L0 ${r1(-w * (0.52 + i * 0.22))} L${r1(w * (0.4 - i * 0.08))} ${r1(-w * (0.16 + i * 0.22))} Z`, "#2f8a3e", "#1f6b2c", w * 0.01)).join("") + [[-0.15, -0.3, "#e5484d"], [0.12, -0.45, "#f2c14e"], [-0.05, -0.62, "#3a7bd5"]].map(([a, b, c]) => circ(w * a, w * b, w * 0.035, c)).join("") + path(`M0 ${r1(-w * 1.02)} l${r1(w * 0.03)} ${r1(w * 0.06)} l${r1(w * 0.06)} 0 l${r1(-w * 0.05)} ${r1(w * 0.04)} l${r1(w * 0.02)} ${r1(w * 0.07)} l${r1(-w * 0.06)} ${r1(-w * 0.04)} l${r1(-w * 0.06)} ${r1(w * 0.04)} l${r1(w * 0.02)} ${r1(-w * 0.07)} l${r1(-w * 0.05)} ${r1(-w * 0.04)} l${r1(w * 0.06)} 0 Z`, "#f2c14e"); break;
    case "golfFlag": out = `<ellipse cx="0" cy="0" rx="${r1(w * 0.3)}" ry="${r1(w * 0.06)}" fill="#2fa35b"/>` + line(0, 0, 0, -w * 0.9, "#c9ced6", w * 0.02) + path(`M0 ${r1(-w * 0.9)} L${r1(w * 0.3)} ${r1(-w * 0.8)} L0 ${r1(-w * 0.7)} Z`, col || "#e5484d") + line(-w * 0.35, -w * 0.5, -w * 0.12, -w * 0.02, "#4a5568", w * 0.02) + rect(-w * 0.18, -w * 0.05, w * 0.1, w * 0.04, "#4a5568", w * 0.01) + circ(w * 0.12, -w * 0.03, w * 0.03, "#ffffff", "#c9ced6", w * 0.005); break;
    case "derrick": { const a = t == null ? 0 : Math.sin(t * 2) * 12;
      out = path(`M${r1(-w * 0.3)} 0 L${r1(-w * 0.08)} ${r1(-w * 0.6)} L${r1(w * 0.08)} ${r1(-w * 0.6)} L${r1(w * 0.3)} 0`, "none", "#4a5568", w * 0.03) + `<g transform="translate(0,${r1(-w * 0.62)}) rotate(${r1(a)})">` + rect(-w * 0.45, -w * 0.04, w * 0.8, w * 0.08, "#e07b24", w * 0.02) + path(`M${r1(w * 0.35)} ${r1(-w * 0.12)} Q${r1(w * 0.5)} 0 ${r1(w * 0.35)} ${r1(w * 0.12)} Z`, "#e07b24") + `</g>` + line(w * 0.38, -w * 0.62, w * 0.38, -w * 0.1, "#2b2b33", w * 0.012) + rect(-w * 0.45, -w * 0.06, w * 0.9, w * 0.06, "#6c7a8c"); break; }
    case "hammock": out = line(-w * 0.45, 0, -w * 0.42, -w * 0.5, "#8a6131", w * 0.05) + line(w * 0.45, 0, w * 0.42, -w * 0.5, "#8a6131", w * 0.05) + path(`M${r1(-w * 0.42)} ${r1(-w * 0.45)} Q0 ${r1(-w * 0.05)} ${r1(w * 0.42)} ${r1(-w * 0.45)} Q0 ${r1(-w * 0.18)} ${r1(-w * 0.42)} ${r1(-w * 0.45)} Z`, col || "#f29f05", "#c76a00", w * 0.01); break;
    case "bricks": { let k = 0; for (let r = 0; r < 4; r++) for (let c = 0; c < 4 - r; c++, k++) out += rect(-w * 0.4 + c * w * 0.2 + r * w * 0.1, -(r + 1) * w * 0.12, w * 0.19, w * 0.11, ["#e5484d", "#3a7bd5", "#f2c14e", "#2fa35b"][k % 4], w * 0.02, "#2b2b33", w * 0.006); break; }
    case "bulb": { const on = p.on === true; out = (on ? circ(0, -w * 0.55, w * 0.36, "#fff3a0", "", 0, ' opacity="0.5"') : "") + circ(0, -w * 0.55, w * 0.22, on ? "#ffe066" : "#e3e7ec", "#b8860b", w * 0.012) + rect(-w * 0.1, -w * 0.35, w * 0.2, w * 0.14, "#8a8f98", w * 0.02); break; }
    case "container": out = rect(-w * 0.5, -w * 0.4, w, w * 0.4, col || "#2a9d8f", w * 0.01, shade(col || "#2a9d8f"), w * 0.01) + [0, 1, 2, 3, 4, 5, 6, 7].map((i) => line(-w * 0.45 + i * w * 0.128, -w * 0.37, -w * 0.45 + i * w * 0.128, -w * 0.03, shade(col || "#2a9d8f", 0.85), w * 0.015)).join(""); lab(-w * 0.2, w * 0.6, w * 0.14); break;
    case "box": for (let i = 0; i < cnt; i++) out += rect(-w * 0.32, -(i + 1) * w * 0.34, w * 0.64, w * 0.33, col || "#c8955a", w * 0.02, "#8a6131", w * 0.01) + line(-w * 0.32, -(i + 1) * w * 0.34 + w * 0.08, w * 0.32, -(i + 1) * w * 0.34 + w * 0.08, "#8a6131", w * 0.01) + (p.band ? rect(-w * 0.32, -(i + 1) * w * 0.34 + w * 0.16, w * 0.64, w * 0.04, p.band) : ""); lab(-w * 0.17, w * 0.56, w * 0.14); break;
    case "signal": { const lit = p.lit || "red";
      out = rect(-w * 0.03, -w * 0.5, w * 0.06, w * 0.5, "#4a5568") + rect(-w * 0.16, -w * 1.1, w * 0.32, w * 0.62, "#2d3748", w * 0.05) +
        [["red", "#e5484d"], ["amber", "#f29f05"], ["green", "#2fa35b"]].map(([n2, c], i) => circ(0, -w * 1.0 + i * w * 0.2, w * 0.08, lit === n2 ? c : shade(c, 0.4))).join("");
      if (S(p.label)) words += plate(w * 0.42, -w * (lit === "red" ? 1.0 : lit === "amber" ? 0.8 : 0.6), w * 0.5, w * 0.14, p.label, "#ffffff", INK, "#2d3748"); break; }
    case "wheel": { const a = (N(p.angle, 0) + (p.on && t != null ? t * 20 : 0)) % 360, r = w * 0.42, n = 8, at = I(p.at, 0, 0, 8);
      out = line(-w * 0.3, 0, 0, -w * 0.5, "#6c7a8c", w * 0.03) + line(w * 0.3, 0, 0, -w * 0.5, "#6c7a8c", w * 0.03) + circ(0, -w * 0.5, r, "none", "#7b5cd6", w * 0.025);
      for (let i = 0; i < n; i++) { const ang = ((a + (i * 360) / n) * Math.PI) / 180, x = Math.cos(ang) * r, y = -w * 0.5 + Math.sin(ang) * r;
        out += line(0, -w * 0.5, x, y, "#9b86e0", w * 0.01) + rect(x - w * 0.05, y, w * 0.1, w * 0.08, at === i + 1 ? "#e5484d" : ["#f2c14e", "#3a7bd5", "#2fa35b", "#e2558f"][i % 4], w * 0.02, "#2d3748", w * 0.006); }
      out += circ(0, -w * 0.5, w * 0.04, "#2d3748"); break; }
    default: out = rect(-w * 0.3, -w * 0.4, w * 0.6, w * 0.4, col || "#c9ced6", w * 0.03);
  }
  if (S(p.price) || S(p.old)) words += tag(w * 0.5, -w * 0.6, w * 0.5, p.price, p.old);
  return out + words;
}

// ---------------------------------------------------------------- stall: tea stall, samosa stall, sweet shop, dhaba, ice-cream cart, kiln, with a menu board
function menuBoard(x, y, bw, p) {
  const items = listOf(p.items).slice(0, 6), strike = I(p.strike, 0, 0, 6), n = Math.max(1, items.length), rh = bw * 0.24, bh = n * rh + bw * 0.12;
  let o = rect(x - bw * 0.02, y, bw * 0.04, -y, "#8a6131") + rect(x - bw / 2, y - bh, bw, bh, "#2f4f3a", bw * 0.04, "#8a6131", bw * 0.03), wds = "";
  items.forEach((it, i) => {
    const j = it.lastIndexOf(":"), name = j < 0 ? it : it.slice(0, j).trim(), price = j < 0 ? "" : it.slice(j + 1).trim(), cy = y - bh + bw * 0.06 + (i + 0.5) * rh;
    const hit = strike === i + 1, fresh = hit && S(p.new);
    wds += word(name, x - bw * 0.2, cy, bw * 0.48, rh * 0.55, "#ffffff", 700) + word(price, x + (fresh ? bw * 0.13 : bw * 0.28), cy, bw * (fresh ? 0.2 : 0.34), rh * (fresh ? 0.42 : 0.6), "#f2c14e", 800);
    if (hit) wds += line(x + (fresh ? bw * 0.03 : bw * 0.12), cy, x + (fresh ? bw * 0.23 : bw * 0.44), cy, "#e5484d", rh * 0.08);
    if (fresh) { const k = ease(prog(p, 0.7)); wds += `<g transform="translate(${r1(x + bw * 0.35)},${r1(cy)}) scale(${r1(0.3 + 0.7 * k)})">` + rect(-bw * 0.12, -rh * 0.38, bw * 0.24, rh * 0.76, "#fff3c4", rh * 0.15, "#e5484d", bw * 0.01) + word(p.new, 0, 0, bw * 0.22, rh * 0.56, "#e5484d", 800) + `</g>`; }
  });
  if (S(p.cost)) { const k = ease(prog(p, 0.5)); wds += `<g transform="translate(${r1(x)},${r1(y - bh - bw * 0.16)}) scale(${r1(0.4 + 0.6 * k)})">` + tag(0, 0, bw * 0.7, p.cost, "", "#f29f05") + `</g>`; }
  return { svg: o, words: wds, top: y - bh };
}
function stall(p) {
  const kind = p.kind || "tea", w = N(p.w, 800), t = tNow(p), cnt = I(p.count, 3, 0, 12), open = p.open !== false;
  const col = p.color || { tea: "#2a9d8f", samosa: "#e07b24", sweets: "#c2447a", dhaba: "#8a6d3b", icecream: "#3a7bd5", momo: "#7b5cd6", kiln: "#9b4a3a" }[kind] || "#2a9d8f";
  let out = "", words = "";
  if (kind === "kiln") {
    out = path(`M${r1(-w * 0.06)} 0 L${r1(-w * 0.04)} ${r1(-w * 0.8)} L${r1(w * 0.04)} ${r1(-w * 0.8)} L${r1(w * 0.06)} 0 Z`, col, shade(col), w * 0.008) + (p.smoke !== false ? puffs(0, -w * 0.82, w, 0.7, t, true, 0.3) : "");
    for (let s = 0; s < 2; s++) for (let r = 0; r < 4; r++) for (let c = 0; c < 4 - (r % 2); c++) out += rect((s ? w * 0.12 : -w * 0.48) + c * w * 0.09 + (r % 2) * w * 0.045, -(r + 1) * w * 0.05, w * 0.085, w * 0.045, "#c0563f", w * 0.005, "#8e3a26", w * 0.003);
    if (S(p.label)) words += plate(0, w * 0.08, w * 0.5, w * 0.1, p.label, "#ffffff", INK, col);
    return out + words;
  }
  const cx0 = -w * 0.1, cw = w * 0.56, ch = w * 0.3, roof = -w * 0.62;
  // the stall: posts, a striped awning, a counter with its wares
  out += rect(cx0 + w * 0.01, roof, w * 0.025, -roof, "#8a6131") + rect(cx0 + cw - w * 0.035, roof, w * 0.025, -roof, "#8a6131");
  for (let i = 0; i < 6; i++) out += path(`M${r1(cx0 - w * 0.02 + (i * (cw + w * 0.04)) / 6)} ${r1(roof)} L${r1(cx0 - w * 0.02 + ((i + 1) * (cw + w * 0.04)) / 6)} ${r1(roof)} L${r1(cx0 - w * 0.02 + ((i + 1) * (cw + w * 0.04)) / 6)} ${r1(roof + w * 0.07)} Q${r1(cx0 - w * 0.02 + ((i + 0.5) * (cw + w * 0.04)) / 6)} ${r1(roof + w * 0.1)} ${r1(cx0 - w * 0.02 + (i * (cw + w * 0.04)) / 6)} ${r1(roof + w * 0.07)} Z`, i % 2 ? "#ffffff" : col);
  out += rect(cx0 - w * 0.03, roof - w * 0.1, cw + w * 0.06, w * 0.1, col, w * 0.015, shade(col), w * 0.006);
  out += rect(cx0, -ch, cw, ch, "#c8955a", w * 0.01, "#8a6131", w * 0.008) + rect(cx0 - w * 0.01, -ch - w * 0.02, cw + w * 0.02, w * 0.025, "#8a6131");
  const top = -ch - w * 0.02, mid = cx0 + cw / 2;
  if (kind === "tea") { out += rect(cx0 + w * 0.04, top - w * 0.14, w * 0.12, w * 0.14, "#c9ced6", w * 0.02, "#6c7a8c", w * 0.008) + steam(cx0 + w * 0.1, top - w * 0.15, w * 0.12, t);
    for (let i = 0; i < cnt; i++) out += `<g transform="translate(${r1(cx0 + w * 0.22 + i * w * 0.055)},${r1(top)})">` + food({ kind: "chaiGlass", w: w * 0.12 }) + `</g>`; }
  else if (kind === "samosa" || kind === "momo") { const big = p.size === "big";
    out += `<g transform="translate(${r1(cx0 + w * 0.12)},${r1(top)})">` + machine({ kind: "kadhai", w: w * (big ? 0.2 : 0.14), size: big ? "big" : "small", on: true, _t: p._t }) + `</g>`;
    for (let i = 0; i < Math.min(cnt, 4); i++) out += `<g transform="translate(${r1(cx0 + w * 0.32 + (i % 2) * w * 0.12)},${r1(top - Math.floor(i / 2) * w * 0.05)})">` + food({ kind, w: w * 0.12, n: 3 }) + `</g>`; }
  else if (kind === "sweets") for (let i = 0; i < Math.min(cnt, 4); i++) out += `<g transform="translate(${r1(cx0 + w * 0.1 + i * w * 0.12)},${r1(top)})">` + food({ kind: i % 2 ? "jalebi" : "laddoo", w: w * 0.12, n: i % 2 ? 3 : 9 }) + `</g>`;
  else if (kind === "dhaba") for (let i = 0; i < Math.min(cnt, 6); i++) out += `<g transform="translate(${r1(cx0 + w * 0.12 + (i % 3) * w * 0.15)},${r1(top - Math.floor(i / 3) * w * 0.03)})">` + food({ kind: "thali", w: w * 0.13, n: 3 }) + `</g>`;
  else if (kind === "icecream") { if (!open) { out += rect(cx0, roof + w * 0.1, cw, -roof - w * 0.1 - ch, "#9aa5b1"); for (let i = 1; i < 6; i++) out += line(cx0, roof + w * 0.1 + i * (-roof - w * 0.1 - ch) / 6, cx0 + cw, roof + w * 0.1 + i * (-roof - w * 0.1 - ch) / 6, "#6c7a8c", w * 0.004); }
    else for (let i = 0; i < Math.min(cnt, 5); i++) out += `<g transform="translate(${r1(cx0 + w * 0.08 + i * w * 0.1)},${r1(top)})">` + food({ kind: "iceCream", w: w * 0.1, n: 2 }) + `</g>`;
    out += circ(cx0 + w * 0.1, -w * 0.05, w * 0.05, "#2b2b33") + circ(cx0 + cw - w * 0.1, -w * 0.05, w * 0.05, "#2b2b33"); }
  const q = I(p.queue, 0, 0, 10);
  for (let i = 0; i < q; i++) out += miniPerson(cx0 + cw + w * 0.08 + i * w * 0.08, w * 0.24, i, -1);
  if (S(p.items)) { const mb = menuBoard(-w * 0.34, -w * 0.08, w * 0.34, p); out = mb.svg + out; words += mb.words; }
  if (S(p.label)) words += plate(mid, roof - w * 0.05, cw * 0.86, w * 0.085, p.label, "#ffffff", INK, shade(col));
  return out + words;
}

// ---------------------------------------------------------------- natureSign: weather and farm signs, and shock bolts that strike
function natureSign(p) {
  const kind = p.kind || "sun", w = N(p.w, 300), t = tNow(p), on = p.on !== false;
  let out = "", words = "";
  const cloud = (x, y, s, c) => [[-0.35, 0.1, 0.35], [0.3, 0.1, 0.38], [0, -0.15, 0.45], [0, 0.18, 0.38]].map(([a, b, r]) => circ(x + a * s, y + b * s, r * s, c)).join("");
  switch (kind) {
    case "sun": { const a = t == null ? 0 : t * 20; out = `<g transform="rotate(${r1(a % 360)})">` + Array.from({ length: 10 }, (_, i) => { const r = (i * 36 * Math.PI) / 180; return line(Math.cos(r) * w * 0.28, Math.sin(r) * w * 0.28, Math.cos(r) * w * 0.42, Math.sin(r) * w * 0.42, "#f29f05", w * 0.04, ' stroke-linecap="round"'); }).join("") + `</g>` + circ(0, 0, w * 0.22, "#f2c14e", "#f29f05", w * 0.02); break; }
    case "rain": case "cloud": case "storm": {
      out = cloud(0, -w * 0.12, w * 0.4, kind === "storm" ? "#6b7280" : "#b9c1cb");
      if (kind !== "cloud" && on) for (let i = 0; i < 6; i++) { const ph = ((t == null ? 0.5 : t * 1.6) + i / 6) % 1, x = -w * 0.25 + (i % 3) * w * 0.25 + (i > 2 ? w * 0.12 : 0);
        out += line(x, w * 0.08 + ph * w * 0.3, x - w * 0.03, w * 0.14 + ph * w * 0.3, "#3a7bd5", w * 0.02, ` stroke-linecap="round" opacity="${r1(1 - ph * 0.6)}"`); }
      if (kind === "storm") out += path(`M${r1(w * 0.02)} ${r1(w * 0.02)} L${r1(-w * 0.08)} ${r1(w * 0.22)} L${r1(w * 0.0)} ${r1(w * 0.22)} L${r1(-w * 0.06)} ${r1(w * 0.42)} L${r1(w * 0.1)} ${r1(w * 0.16)} L${r1(w * 0.02)} ${r1(w * 0.16)} L${r1(w * 0.08)} ${r1(w * 0.02)} Z`, "#f2c14e", "#c99a00", w * 0.008);
      break; }
    case "frost": out = [0, 60, 120].map((d) => `<g transform="rotate(${d})">` + line(0, -w * 0.38, 0, w * 0.38, "#7fb6e0", w * 0.04) + path(`M${r1(-w * 0.08)} ${r1(-w * 0.3)} L0 ${r1(-w * 0.22)} L${r1(w * 0.08)} ${r1(-w * 0.3)} M${r1(-w * 0.08)} ${r1(w * 0.3)} L0 ${r1(w * 0.22)} L${r1(w * 0.08)} ${r1(w * 0.3)}`, "none", "#7fb6e0", w * 0.03) + `</g>`).join("") + circ(0, 0, w * 0.06, "#dff1fb", "#7fb6e0", w * 0.02); break;
    case "drought": case "crop": { const dry = kind === "drought";
      out = rect(-w * 0.42, w * 0.18, w * 0.84, w * 0.12, dry ? "#c8a46a" : "#8a6131", w * 0.02) + (dry ? path(`M${r1(-w * 0.3)} ${r1(w * 0.2)} l${r1(w * 0.05)} ${r1(w * 0.05)} l${r1(-w * 0.03)} ${r1(w * 0.04)} M${r1(w * 0.1)} ${r1(w * 0.2)} l${r1(-w * 0.04)} ${r1(w * 0.05)} l${r1(w * 0.05)} ${r1(w * 0.04)}`, "none", "#8a6131", w * 0.012) : "");
      for (let i = 0; i < 4; i++) { const x = -w * 0.3 + i * w * 0.2; out += dry ? path(`M${r1(x)} ${r1(w * 0.18)} Q${r1(x + w * 0.02)} ${r1(-w * 0.05)} ${r1(x + w * 0.1)} ${r1(w * 0.02)}`, "none", "#a68a4a", w * 0.025) + path(`M${r1(x)} ${r1(w * 0.1)} Q${r1(x - w * 0.08)} ${r1(w * 0.08)} ${r1(x - w * 0.1)} ${r1(w * 0.16)}`, "none", "#a68a4a", w * 0.02)
        : line(x, w * 0.18, x, -w * 0.2, "#4f8a2a", w * 0.025) + `<ellipse cx="${r1(x)}" cy="${r1(-w * 0.24)}" rx="${r1(w * 0.03)}" ry="${r1(w * 0.07)}" fill="#e0b55a"/>` + path(`M${r1(x)} ${r1(0)} Q${r1(x + w * 0.08)} ${r1(-w * 0.05)} ${r1(x + w * 0.1)} ${r1(-w * 0.12)}`, "none", "#6fa83a", w * 0.02); }
      if (dry) out += circ(w * 0.32, -w * 0.28, w * 0.1, "#f2c14e", "#f29f05", w * 0.01);
      break; }
    case "flood": { const ph = t == null ? 0 : t * 2; let d = `M${r1(-w * 0.45)} ${r1(w * 0.3)} L${r1(-w * 0.45)} 0`; for (let x = -w * 0.45; x <= w * 0.45 + 1; x += w * 0.09) d += ` L${r1(x)} ${r1(Math.sin(x / (w * 0.09) + ph) * w * 0.03)}`;
      out = homeOf("small", 0, w * 0.5, false).svg.replace(/^/, "") + path(d + ` L${r1(w * 0.45)} ${r1(w * 0.3)} Z`, "#4a90c8", "#2f6fa3", w * 0.01, ' opacity="0.8"'); break; }
    case "fire": out = flames(0, w * 0.3, w * 0.9, t, 3); break;
    case "bolt": { const st = since(p), flash = st != null && st < 0.4, sign = S(p.sign), c = sign === "+" ? "#2fa35b" : sign === "−" || sign === "-" ? "#e5484d" : "#f2c14e";
      out = (flash ? circ(0, 0, w * 0.45, "#fff3a0", "", 0, ' opacity="0.6"') : "") + path(`M${r1(w * 0.06)} ${r1(-w * 0.42)} L${r1(-w * 0.16)} ${r1(w * 0.04)} L${r1(0)} ${r1(w * 0.04)} L${r1(-w * 0.1)} ${r1(w * 0.42)} L${r1(w * 0.18)} ${r1(-w * 0.08)} L${r1(w * 0.02)} ${r1(-w * 0.08)} L${r1(w * 0.14)} ${r1(-w * 0.42)} Z`, c, shade(c), w * 0.015);
      if (sign) out += circ(w * 0.26, -w * 0.3, w * 0.1, "#ffffff", c, w * 0.015) + tx(sign === "-" ? "−" : sign, w * 0.26, -w * 0.3, w * 0.16, c, 800);
      break; }
    case "sheep": out = [[-0.15, 0], [0.12, 0], [0, -0.1], [-0.05, 0.08], [0.15, -0.08]].map(([a, b]) => circ(w * a, w * b, w * 0.15, "#fbfbf8", "#c9c6bd", w * 0.01)).join("") + `<ellipse cx="${r1(w * 0.3)}" cy="${r1(-w * 0.06)}" rx="${r1(w * 0.09)}" ry="${r1(w * 0.07)}" fill="#3b3b40"/>` + [-0.15, 0.15].map((a) => line(w * a, w * 0.12, w * a, w * 0.28, "#3b3b40", w * 0.03)).join(""); break;
    case "buffalo": out = `<ellipse cx="0" cy="0" rx="${r1(w * 0.3)}" ry="${r1(w * 0.16)}" fill="#3b3b40"/>` + `<ellipse cx="${r1(w * 0.32)}" cy="${r1(-w * 0.08)}" rx="${r1(w * 0.1)}" ry="${r1(w * 0.08)}" fill="#3b3b40"/>` + path(`M${r1(w * 0.26)} ${r1(-w * 0.14)} Q${r1(w * 0.18)} ${r1(-w * 0.26)} ${r1(w * 0.3)} ${r1(-w * 0.24)} M${r1(w * 0.38)} ${r1(-w * 0.14)} Q${r1(w * 0.46)} ${r1(-w * 0.26)} ${r1(w * 0.34)} ${r1(-w * 0.24)}`, "none", "#8a8f98", w * 0.02) + [-0.2, -0.08, 0.1, 0.2].map((a) => line(w * a, w * 0.12, w * a, w * 0.3, "#3b3b40", w * 0.04)).join(""); break;
    case "heart": out = path(`M0 ${r1(w * 0.3)} C${r1(-w * 0.5)} ${r1(-w * 0.05)} ${r1(-w * 0.25)} ${r1(-w * 0.42)} 0 ${r1(-w * 0.18)} C${r1(w * 0.25)} ${r1(-w * 0.42)} ${r1(w * 0.5)} ${r1(-w * 0.05)} 0 ${r1(w * 0.3)} Z`, p.color || "#e5484d", shade(p.color || "#e5484d"), w * 0.015) + path(`M${r1(-w * 0.3)} 0 L${r1(-w * 0.1)} 0 L${r1(-w * 0.04)} ${r1(-w * 0.1)} L${r1(w * 0.04)} ${r1(w * 0.1)} L${r1(w * 0.1)} 0 L${r1(w * 0.3)} 0`, "none", "#ffffff", w * 0.025); break;
    case "ozone": { const th = clamp01(p.level ?? 1); out = path(`M${r1(-w * 0.48)} ${r1(w * 0.1)} A${r1(w * 0.5)} ${r1(w * 0.42)} 0 0 1 ${r1(w * 0.48)} ${r1(w * 0.1)}`, "none", "#7fb6e0", w * (0.02 + 0.08 * th), ` opacity="${r1(0.4 + 0.6 * th)}"`) + circ(0, w * 0.3, w * 0.25, "#4a90c8") + path(`M${r1(-w * 0.12)} ${r1(w * 0.2)} q${r1(w * 0.08)} ${r1(-w * 0.05)} ${r1(w * 0.14)} ${r1(w * 0.04)} t${r1(w * 0.1)} ${r1(w * 0.04)}`, "none", "#2fa35b", w * 0.04); break; }
    default: out = circ(0, 0, w * 0.3, "#c9ced6");
  }
  if (S(p.label)) words += plate(0, w * 0.52, w * 0.9, w * 0.2, p.label, "#ffffff", INK, "#9aa5b1");
  return out + words;
}

// ---------------------------------------------------------------- cityMap: one city as a detailed street map that fades into a simple metro map
function cityMap(p) {
  const w = N(p.w, 760), h = w * 0.66, d = clamp01(p.detail ?? 1), x0 = -w / 2, y0 = -h / 2, names = parts(p.stations);
  let out = rect(x0, y0, w, h, "#f4efe3", w * 0.02, "#b9b1a0", w * 0.006), streets = "";
  let sd = 5;
  const rn = () => ((sd = (sd * 9301 + 49297) % 233280), sd / 233280);
  for (let i = 1; i < 9; i++) streets += line(x0 + (w * i) / 9 + (rn() - 0.5) * w * 0.02, y0 + w * 0.01, x0 + (w * i) / 9 + (rn() - 0.5) * w * 0.02, y0 + h - w * 0.01, "#ffffff", w * 0.012);
  for (let i = 1; i < 6; i++) streets += line(x0 + w * 0.01, y0 + (h * i) / 6 + (rn() - 0.5) * w * 0.02, x0 + w - w * 0.01, y0 + (h * i) / 6 + (rn() - 0.5) * w * 0.02, "#ffffff", w * 0.012);
  for (let i = 0; i < 26; i++) streets += rect(x0 + w * 0.03 + rn() * w * 0.9, y0 + w * 0.03 + rn() * (h - w * 0.1), w * (0.02 + rn() * 0.03), w * (0.02 + rn() * 0.02), i % 5 ? "#d9d2c2" : "#bfe0b5", w * 0.004);
  streets += path(`M${r1(x0)} ${r1(y0 + h * 0.75)} Q${r1(-w * 0.2)} ${r1(y0 + h * 0.5)} 0 ${r1(y0 + h * 0.7)} T${r1(x0 + w)} ${r1(y0 + h * 0.55)}`, "none", "#a9d0ec", w * 0.035);
  out += `<g opacity="${r1(d * 100) / 100}">${streets}</g>`;
  const lines = [["#e5484d", [[0.08, 0.3], [0.3, 0.3], [0.5, 0.5], [0.72, 0.5], [0.93, 0.28]]], ["#2459a6", [[0.18, 0.9], [0.3, 0.6], [0.5, 0.5], [0.62, 0.22], [0.8, 0.1]]], ["#2fa35b", [[0.06, 0.62], [0.3, 0.6], [0.55, 0.78], [0.9, 0.78]]]];
  let k = 0, words = "";
  for (const [c, pts] of lines) {
    out += path(pts.map(([a, b], i) => `${i ? "L" : "M"}${r1(x0 + a * w)} ${r1(y0 + b * h)}`).join(" "), "none", c, w * (0.008 + 0.012 * (1 - d)), ' stroke-linejoin="round" stroke-linecap="round"');
    for (const [a, b] of pts) { out += circ(x0 + a * w, y0 + b * h, w * (0.009 + 0.008 * (1 - d)), "#ffffff", c, w * 0.005);
      if (S(names[k])) words += word(names[k], x0 + a * w, y0 + b * h - w * 0.045, w * 0.2, w * 0.05, INK, 800); k++; }
  }
  return out + words + (S(p.label) ? plate(0, y0 - w * 0.07, w * 0.5, w * 0.09, p.label, "#ffffff", INK, "#b9b1a0") : "");
}

export const DRAWS = {
  produce: { fn: produce, anchor: "bottom" },
  vehicle: { fn: vehicle, anchor: "bottom" },
  houses: { fn: houses, anchor: "bottom" },
  campus: { fn: campus, anchor: "bottom" },
  pump: { fn: pump, anchor: "bottom" },
  godown: { fn: godown, anchor: "bottom" },
  headlines: { fn: headlines, anchor: "center" },
  slip: { fn: slip, anchor: "center" },
  clock: { fn: clock, anchor: "center" },
  chance: { fn: chance, anchor: "center" },
  press: { fn: press, anchor: "bottom" },
  chimney: { fn: chimney, anchor: "bottom" },
  food: { fn: food, anchor: "bottom" },
  machine: { fn: machine, anchor: "bottom" },
  goods: { fn: goods, anchor: "bottom" },
  stall: { fn: stall, anchor: "bottom" },
  natureSign: { fn: natureSign, anchor: "center" },
  cityMap: { fn: cityMap, anchor: "center" },
};
