// Family "econ_tools" (Sloman economics book, 5 November 2026): the teaching tools the chapter workers asked for most,
// each one parametric drawing that a scene plan changes through its steps on the cue word.
//   formula       an equation built term by term: fractions, Δ, powers and subscripts; letters take numbers in place
//                 (or under the terms), working lines, a result that computes itself; beam mode: both sides of an
//                 identity on a balance that levels when they are equal (MV = PY)
//   scaleBalance  a tarazu or a seesaw: things and values in two pans (or on two ends) and a beam that tips by their
//                 weights; a burden weight that slides along a seesaw (who bears a tax); a fixed coupon on the pivot
//   causeChain    a mechanism told as chips that light in order with up/down badges, arrows that draw themselves, an
//                 optional loop back (spirals) and an "until X = Y" stamp at the end; a second row for a second market
//   sorter        cards fly into labelled bins and get a tick, or a cross and then the right bin (any classification)
//   spectrum      a line between two poles with many pins that drop in and slide between two dated states; as a
//                 pendulum, a bob that swings between the poles (the swing of ideas over time)
//   padlocks      ceteris paribus: labelled tags held by padlocks; the one being told springs open (or snaps shut)
//   tugOfWar      two teams pull over a share; each pull moves the share a little and lifts a price tag a notch
//   oneVsAll      fallacy of composition: one actor acts and gains, then everyone does it and the total turns over
//   tAccount      a balance sheet as an open ledger: rows enter on cue, amounts are struck and rewritten, totals match,
//                 a capital cushion takes a loss, net worth balances a household's sheet
//   choicePaths   opportunity cost: paths from one start to 2-4 options; the chosen one lights, the best forgone one
//                 keeps a glow and a tag
//   incomeLine    a threshold over a population: people stand at their incomes, a line counts and shades those below;
//                 relative mode follows the average as everyone gets richer
//   doorway       a threshold concept as a door with a step that opens on the word; the view beyond grows clear
// Every drawing is a pure function of its parameters, _t (seconds since it appeared) and _s (seconds since its last
// step): no state and no unseeded randomness, so frames can be drawn out of order. Words come only from parameters.
// Conventions: a count (upto, at) shows parts 1..n and the newest one arrives with a short animation after the step;
// a value that glides (tilt, share, at, open, rise) has a *From partner the step sets to the value before it.

import { shade, INK, FONT, esc, clamp01, parts, idxSet, isNum, easeIO, markSvg, drawSaancha, boxOf, inr, READ_PX } from "../draw.mjs";
import { textWidth } from "../boxes.mjs";

// ---------------------------------------------------------------- shared helpers
const N = (v, d) => (isNum(v) ? Number(v) : d);
const f1 = (v) => (Number.isFinite(v) ? Math.round(v * 10) / 10 : 0);
// letter widths: the box rule's table, wider for the maths signs (×, −, %, Δ are wider than a plain letter)
const SYMW = { "%": 0.9, "×": 0.6, "−": 0.6, "+": 0.6, "=": 0.6, "÷": 0.6, "Δ": 0.7, "∆": 0.7, "Σ": 0.64, "<": 0.6, ">": 0.6, "≤": 0.6,
  "≥": 0.6, "≠": 0.6, "≈": 0.6, "≡": 0.6, "·": 0.3, "→": 1.0, "⇒": 1.0, "(": 0.34, ")": 0.34, "/": 0.3, ",": 0.28, ".": 0.28, "?": 0.62, "I": 0.32, "J": 0.56, "M": 0.86, "W": 0.98, "m": 0.9, "w": 0.8 };
const tw = (t, px) => { let u = 0; for (const ch of String(t ?? "")) u += SYMW[ch] ?? textWidth(ch, 1); return u * px; };
const fitT = (t, maxW, cap) => { const u = tw(t, 1); return u > 0 ? Math.min(cap, maxW / u) : cap; };
const ph = (s, a, d) => clamp01((s - a) / (d || 1e-6));
const ease = (x) => easeIO(clamp01(x));
const backOut = (x) => { const u = clamp01(x) - 1, c = 1.6; return 1 + (c + 1) * u * u * u + c * u * u; };
const stepS = (p) => (isNum(p._s) ? Math.max(0, +p._s) : isNum(p._t) ? Math.max(0, +p._t) : 1e4);
const timeT = (p) => (isNum(p._t) ? Math.max(0, +p._t) : 0);
const lerp = (a, b, u) => a + (b - a) * u;
// a value that settles on its new place with a small damped overshoot (a beam, a pendulum, a share)
function settle(from, to, s, glide) {
  const u = s / Math.max(0.05, glide);
  if (!Number.isFinite(u) || u >= 1.8) return to;
  return to + (from - to) * Math.exp(-3.1 * u) * Math.cos(u * 3.4);
}
const clampN = (v, a, b) => Math.max(a, Math.min(b, v));
// a tick or cross that has started (a mark at 0 would leave the dot of its round line cap)
const mark = (kind, size, color, k) => (k > 0 ? markSvg(kind, size, color, Math.min(1, k)) : "");
// a light fill of a colour (mixed with white), for chips and backs
const tint = (c, u = 0.86) => mixHex(c, "#ffffff", u);

// a text centred (or anchored) on its middle line, like draw.mjs's tx but with any anchor
function T(text, x, cy, size, fill = INK, weight = 800, anchor = "middle", extra = "") {
  if (text === "" || text == null) return "";
  return `<text x="${f1(x)}" y="${f1(cy + size * 0.35)}" font-family=${JSON.stringify(FONT)} font-size="${f1(size)}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}"${extra}>${esc(text)}</text>`;
}

// one or two lines that fit maxW, as large as cap; two lines only when one line would fall under min px
function wrap2(text, maxW, cap, min = 36) {
  const s = String(text ?? "");
  const one = fitT(s, maxW, cap);
  if (one >= min || !s.trim().includes(" ")) return { lines: [s], fs: one };
  const words = s.trim().split(/\s+/);
  let best = null;
  for (let i = 1; i < words.length; i++) {
    const a = words.slice(0, i).join(" "), b = words.slice(i).join(" ");
    const f = Math.min(fitT(a, maxW, cap), fitT(b, maxW, cap));
    if (!best || f > best.fs) best = { lines: [a, b], fs: f };
  }
  return best && best.fs > one * 1.05 ? best : { lines: [s], fs: one };
}
function linesSvg(wr, x, cy, fill = INK, weight = 800, anchor = "middle") {
  const lh = wr.fs * 1.18, y0 = cy - ((wr.lines.length - 1) * lh) / 2;
  return wr.lines.map((l, i) => T(l, x, y0 + i * lh, wr.fs, fill, weight, anchor)).join("");
}

function arrowHead(x, y, ang, size, color) {
  const a1 = ang - 0.5, a2 = ang + 0.5;
  return `<path d="M${f1(x - size * Math.cos(a1))} ${f1(y - size * Math.sin(a1))} L${f1(x)} ${f1(y)} L${f1(x - size * Math.cos(a2))} ${f1(y - size * Math.sin(a2))}" fill="none" stroke="${color}" stroke-width="${f1(size * 0.32)}" stroke-linecap="round" stroke-linejoin="round"/>`;
}
// a straight arrow that draws itself (k 0..1)
function arrowLine(x1, y1, x2, y2, color, sw, k = 1, dashed = false) {
  if (k <= 0) return "";
  const ex = lerp(x1, x2, k), ey = lerp(y1, y2, k), ang = Math.atan2(y2 - y1, x2 - x1);
  return `<path d="M${f1(x1)} ${f1(y1)} L${f1(ex)} ${f1(ey)}" stroke="${color}" stroke-width="${f1(sw)}" stroke-linecap="round"${dashed ? ` stroke-dasharray="${f1(sw * 2)} ${f1(sw * 1.6)}"` : ""}/>` +
    (k > 0.6 ? arrowHead(ex, ey, ang, sw * 3.2, color) : "");
}
function chipBox(x, y, w, h, fill, stroke, sw, r) {
  return `<rect x="${f1(x - w / 2)}" y="${f1(y - h / 2)}" width="${f1(w)}" height="${f1(h)}" rx="${f1(r ?? h * 0.22)}" fill="${fill}" stroke="${stroke}" stroke-width="${f1(sw)}"/>`;
}
// a simple person sign (head and shoulders) in BIE's flat style; h is its height, standing on y = 0
function figure(h, col, extra = "") {
  const r = h * 0.2;
  return `<g${extra}><path d="M${f1(-h * 0.3)} 0 L${f1(-h * 0.3)} ${f1(-h * 0.36)} Q${f1(-h * 0.3)} ${f1(-h * 0.56)} ${f1(-h * 0.1)} ${f1(-h * 0.58)} L${f1(h * 0.1)} ${f1(-h * 0.58)} Q${f1(h * 0.3)} ${f1(-h * 0.56)} ${f1(h * 0.3)} ${f1(-h * 0.36)} L${f1(h * 0.3)} 0 Z" fill="${col}"/>` +
    `<circle cx="0" cy="${f1(-h * 0.78)}" r="${f1(r)}" fill="${shade(col, 1.25)}" stroke="${col}" stroke-width="${f1(h * 0.03)}"/></g>`;
}
function upDownBadge(dir, r, x, y, k = 1) {
  if (!dir || k <= 0) return "";
  const sc = backOut(k);
  const col = dir === "up" ? "#2fa35b" : dir === "down" ? "#e5484d" : "#7a8594";
  const glyph = dir === "up" ? `<path d="M0 ${f1(r * 0.5)} L0 ${f1(-r * 0.45)} M${f1(-r * 0.38)} ${f1(-r * 0.08)} L0 ${f1(-r * 0.5)} L${f1(r * 0.38)} ${f1(-r * 0.08)}" fill="none" stroke="#ffffff" stroke-width="${f1(r * 0.24)}" stroke-linecap="round" stroke-linejoin="round"/>`
    : dir === "down" ? `<path d="M0 ${f1(-r * 0.5)} L0 ${f1(r * 0.45)} M${f1(-r * 0.38)} ${f1(r * 0.08)} L0 ${f1(r * 0.5)} L${f1(r * 0.38)} ${f1(r * 0.08)}" fill="none" stroke="#ffffff" stroke-width="${f1(r * 0.24)}" stroke-linecap="round" stroke-linejoin="round"/>`
    : `<path d="M${f1(-r * 0.42)} ${f1(-r * 0.18)} L${f1(r * 0.42)} ${f1(-r * 0.18)} M${f1(-r * 0.42)} ${f1(r * 0.18)} L${f1(r * 0.42)} ${f1(r * 0.18)}" stroke="#ffffff" stroke-width="${f1(r * 0.22)}" stroke-linecap="round"/>`;
  return `<g transform="translate(${f1(x)},${f1(y)}) scale(${sc.toFixed(3)})"><circle r="${f1(r)}" fill="${col}" stroke="#ffffff" stroke-width="${f1(r * 0.14)}"/>${glyph}</g>`;
}
const dirOf = (s) => { const v = String(s || "").trim().toLowerCase();
  return ["up", "↑", "+", "rise", "badh"].includes(v) ? "up" : ["down", "↓", "-", "−", "fall", "ghat"].includes(v) ? "down" : ["eq", "=", "same", "stay"].includes(v) ? "eq" : ""; };
const firstNum = (s) => { const m = String(s ?? "").replace(/(\d),(?=\d{2,3}\b)/g, "$1").match(/[-−]?\d+(?:\.\d+)?/); return m ? Number(m[0].replace("−", "-")) : null; };
function fmtNum(v, group = "") {
  if (!Number.isFinite(v)) return "";
  const neg = v < 0, a = Math.abs(v);
  let s = Math.abs(a - Math.round(a)) < 1e-9 ? String(Math.round(a)) : a >= 0.01 ? a.toFixed(2).replace(/\.?0+$/, "") : a.toPrecision(2);
  const [ip, dp] = s.split(".");
  let g = ip;
  if (group === "in" && ip.length > 3) g = ip.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + ip.slice(-3);
  else if (group === "w" || (!group && ip.length >= 5)) g = ip.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return (neg ? "−" : "") + g + (dp ? "." + dp : "");
}
// the digit grouping the writer used (1,00,000 Indian or 100,000 western), so totals look like their rows; rupees are
// always Indian (₹1,00,000)
const groupOf = (texts) => (texts.some((t) => /\d,\d{2},\d{3}/.test(t) || /₹\s?[−-]?\d/.test(t)) ? "in" : texts.some((t) => /\d,\d{3}/.test(t)) ? "w" : "");

// ---------------------------------------------------------------- math rows: fractions, powers, subscripts, accents
// Markup: {num}//{den} (or a whole token a − c//d + b) is a fraction; x^2, d^{t-1} a power; U_t, D_{g} a subscript;
// * becomes ×, - becomes −, <= ≤, >= ≥, != ≠, -> →. Text between \u0001 and \u0002 is drawn in the accent colour.
function normMath(s) {
  return String(s ?? "").replace(/<=/g, "≤").replace(/>=/g, "≥").replace(/!=/g, "≠").replace(/->/g, "→").replace(/\*/g, "×")
    .replace(/(^|[^\u0900-\u097f])-(?=[^\u0900-\u097f]|$)/g, "$1−");
}
function matchBrace(s, i) {
  let d = 0;
  for (let j = i; j < s.length; j++) { if (s[j] === "{") d++; else if (s[j] === "}") { d--; if (!d) return j; } }
  return s.length - 1;
}
function topLevelFrac(s) {
  let d = 0;
  for (let i = 0; i < s.length - 1; i++) {
    if (s[i] === "{") d++; else if (s[i] === "}") d--;
    else if (!d && s[i] === "/" && s[i + 1] === "/" && !(s[i - 1] === "}" && s[i + 2] === "{")) return i;   // {a}//{b} is inline
  }
  return -1;
}
function parseRow(src, accent = false) {
  const s = String(src ?? "");
  const cut = topLevelFrac(s);
  if (cut >= 0) return [{ k: "frac", num: parseRow(s.slice(0, cut).trim(), accent), den: parseRow(s.slice(cut + 2).trim(), accent) }];
  const out = [];
  let buf = "", acc = accent;
  const flush = () => { if (buf) out.push({ k: "t", s: buf, a: acc }); buf = ""; };
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === "\u0001") { flush(); acc = true; continue; }
    if (c === "\u0002") { flush(); acc = accent; continue; }
    if (c === "{") {
      const j = matchBrace(s, i), g = s.slice(i + 1, j);
      if (s.slice(j + 1, j + 4) === "//{") {
        const k2 = matchBrace(s, j + 3);
        flush(); out.push({ k: "frac", num: parseRow(g, acc), den: parseRow(s.slice(j + 4, k2), acc) }); i = k2; continue;
      }
      flush(); out.push(...parseRow(g, acc)); i = j; continue;
    }
    if ((c === "^" || c === "_") && i + 1 < s.length) {
      flush();
      let g, j;
      if (s[i + 1] === "{") { j = matchBrace(s, i + 1); g = s.slice(i + 2, j); }
      else { const m = s.slice(i + 1).match(/^(\u0001[^\u0002]*\u0002|[A-Za-z0-9.+−ΔΣ∆α-ωΑ-Ω']+)/); g = m ? m[0] : s[i + 1]; j = i + g.length; }
      out.push({ k: c === "^" ? "sup" : "sub", row: parseRow(g, acc) }); i = j; continue;
    }
    buf += c;
  }
  flush();
  return out;
}
// a script or a fraction's line is smaller than its row, but never under the readable floor while the row itself is
// over it (Sloman workers, Nov 2026: the g of D_g came out at 29.8 px in a 48 px chip)
const smallFs = (fs, k) => Math.max(fs * k, Math.min(fs, READ_PX));
function measureRow(row, fs) {
  let w = 0, asc = fs * 0.78, desc = fs * 0.24;
  for (const n of row) {
    if (n.k === "t") { w += tw(n.s, fs); }
    else if (n.k === "sup") { const m = measureRow(n.row, smallFs(fs, 0.62)); w += m.w + fs * 0.1; asc = Math.max(asc, fs * 0.42 + m.asc); }
    else if (n.k === "sub") { const m = measureRow(n.row, smallFs(fs, 0.62)); w += m.w + fs * 0.1; desc = Math.max(desc, fs * 0.24 + m.desc); }
    else if (n.k === "frac") {
      const a = measureRow(n.num, smallFs(fs, 0.88)), b = measureRow(n.den, smallFs(fs, 0.88)), axis = fs * 0.3, gap = fs * 0.14;
      w += Math.max(a.w, b.w) + fs * 0.3;
      asc = Math.max(asc, axis + gap + a.desc + a.asc);
      desc = Math.max(desc, gap + b.asc + b.desc - axis);
    }
  }
  return { w, asc, desc };
}
function renderRow(row, x, base, fs, col, acc, weight = 800) {
  let out = "", cx = x;
  for (const n of row) {
    if (n.k === "t") {
      // each word sits on the middle of its own measured slot, so a font wider or narrower than the estimate
      // shares its error on both sides instead of pushing into the next term
      let x = cx;
      for (const piece of n.s.split(/( +)/)) {
        const pw = tw(piece, fs);
        if (piece.trim()) out += `<text x="${f1(x + pw / 2)}" y="${f1(base)}" font-family=${JSON.stringify(FONT)} font-size="${f1(fs)}" font-weight="${weight}" fill="${n.a ? acc : col}" text-anchor="middle">${esc(piece)}</text>`;
        x += pw;
      }
      cx += tw(n.s, fs);
    } else if (n.k === "sup" || n.k === "sub") {
      const f = smallFs(fs, 0.62), m = measureRow(n.row, f);
      out += renderRow(n.row, cx + fs * 0.07, base + (n.k === "sup" ? -fs * 0.42 : fs * 0.24), f, col, acc, weight);
      cx += m.w + fs * 0.1;
    } else if (n.k === "frac") {
      const f = smallFs(fs, 0.88), a = measureRow(n.num, f), b = measureRow(n.den, f), W = Math.max(a.w, b.w) + fs * 0.3, axis = base - fs * 0.3, gap = fs * 0.14;
      out += renderRow(n.num, cx + (W - a.w) / 2, axis - gap - a.desc, f, col, acc, weight) +
        `<path d="M${f1(cx + fs * 0.05)} ${f1(axis)} L${f1(cx + W - fs * 0.05)} ${f1(axis)}" stroke="${col}" stroke-width="${f1(fs * 0.065)}" stroke-linecap="round"/>` +
        renderRow(n.den, cx + (W - b.w) / 2, axis + gap + b.asc, f, col, acc, weight);
      cx += W;
    }
  }
  return out;
}
const plainOf = (s) => String(s ?? "").replace(/[\u0001\u0002{}]/g, "").replace(/\/\//g, "/").replace(/[\^_]/g, "");

// a safe evaluator for + − × ÷ / ^ ( ) with percent and implied multiplication; NaN when a letter is left
function evaluate(src) {
  let s = normMath(String(src ?? "")).replace(/[\u0001\u0002]/g, "");
  s = s.replace(/\{([^{}]*)\}\/\/\{([^{}]*)\}/g, "($1)/($2)");
  for (let k = 0; k < 4 && s.includes("{"); k++) s = s.replace(/\{([^{}]*)\}\/\/\{([^{}]*)\}/g, "($1)/($2)").replace(/\{([^{}]*)\}/g, "($1)");
  const cut = s.indexOf("//");
  if (cut >= 0) s = `(${s.slice(0, cut)})/(${s.slice(cut + 2)})`;
  s = s.replace(/(\d),(?=\d{3}\b)/g, "$1").replace(/[₹$£€¥\s]/g, "").replace(/_/g, "");
  const toks = s.match(/\d+(?:\.\d+)?|\.\d+|[+−\-×÷/^()%·]|[^\d.+−\-×÷/^()%·]+/g) || [];
  let i = 0;
  const peek = () => toks[i], next = () => toks[i++];
  function primary() {
    const t = next();
    if (t === "(") { const v = expr(); if (peek() === ")") next(); return v; }
    if (t !== undefined && /^[\d.]/.test(t)) { let v = Number(t); if (peek() === "%") { next(); v /= 100; } return v; }
    return NaN;
  }
  function unary() { if (peek() === "−" || peek() === "-") { next(); return -unary(); } if (peek() === "+") { next(); return unary(); } return power(); }
  function power() { const b = primary(); if (peek() === "^") { next(); return Math.pow(b, unary()); } return b; }
  function term() {
    let v = unary();
    for (;;) {
      const t = peek();
      if (t === "×" || t === "·") { next(); v *= unary(); }
      else if (t === "/" || t === "÷") { next(); v /= unary(); }
      else if (t === "(" || (t !== undefined && /^[\d.]/.test(t))) v *= unary();
      else return v;
    }
  }
  function expr() {
    let v = term();
    for (;;) { const t = peek(); if (t === "+") { next(); v += term(); } else if (t === "−" || t === "-") { next(); v -= term(); } else return v; }
  }
  if (!toks.length) return NaN;
  const v = expr();
  return i === toks.length ? v : NaN;
}

// values "P=10;a=120;3:2×10": symbol substitutions and whole-term replacements by term number
function parseValues(s) {
  const sym = {}, idx = {};
  for (const e of parts(s)) {
    if (!e) continue;
    let m = e.match(/^(\d+)\s*:\s*(.*)$/);
    if (m) { idx[+m[1]] = m[2].trim(); continue; }
    m = e.match(/^([^=]+?)\s*=\s*(.*)$/);
    if (m) sym[m[1].trim()] = m[2].trim();
  }
  return { sym, idx };
}
const IDENT = /%?[ΔΣ∆]?[A-Za-zα-ωΑ-Ω]+(?:_\{[^}]*\}|_[A-Za-z0-9]+)?'?/g;
function substitute(text, sym) {
  const s = String(text ?? "");
  if (!Object.keys(sym).length) return s;
  let out = "", last = 0;
  for (const m of s.matchAll(IDENT)) {
    const id = m[0], at = m.index;
    let rep = null;
    if (sym[id] !== undefined) rep = sym[id];
    else if (/^[A-Za-z]{2,4}$/.test(id) && [...id].every((ch) => sym[ch] !== undefined)) rep = [...id].map((ch) => sym[ch]).join("×");
    if (rep === null) continue;
    const before = s.slice(0, at), after = s.slice(at + id.length);
    const pre = /[0-9A-Za-z)}\u0002]$/.test(before) ? "×" : "", post = /^[0-9A-Za-z(\u0001]/.test(after) ? "×" : "";
    const wrapUp = /[\^_]$/.test(before);
    out += s.slice(last, at) + (wrapUp ? "{" : pre) + "\u0001" + rep + "\u0002" + (wrapUp ? "}" : post);
    last = at + id.length;
  }
  return out + s.slice(last);
}

const OPS = /^(=|\+|−|-|×|\*|÷|\/|<|>|≤|≥|<=|>=|≡|≈|·|⇒|→|->|≠|!=|:|,)$/;

function formula(p) {
  const w = N(p.w, 1200), acc = p.color || "#e07b24", s = stepS(p);
  const toks = String(p.terms ?? "Q|=|a|−|bP").split("|").map((t) => normMath(t.trim())).filter((t) => t !== "");
  if (!toks.length) return `<path d="M${-w * 0.3} 0 L${w * 0.3} 0" stroke="#c9ced6" stroke-width="${f1(w * 0.004)}" stroke-dasharray="${f1(w * 0.01)} ${f1(w * 0.01)}"/>`;
  // term numbers: an operator arrives with the term after it
  const isOp = toks.map((t) => OPS.test(t)), termOf = new Array(toks.length);
  let k = 0;
  toks.forEach((t, i) => { if (!isOp[i]) termOf[i] = ++k; });
  const nT = Math.max(1, k);
  for (let i = 0; i < toks.length; i++) if (isOp[i]) { let j = i + 1; while (j < toks.length && isOp[j]) j++; termOf[i] = j < toks.length ? termOf[j] : (i > 0 ? termOf[i - 1] || 1 : 1); }
  const upto = Math.max(0, Math.round(N(p.upto, 0))), shownT = upto ? Math.min(upto, nT) : nT, allIn = shownT >= nT;
  const { sym, idx } = parseValues(p.values);
  const mode = ["in", "under"].includes(p.sub) ? p.sub : "";
  const glow = idxSet(p.glow);
  const labels = {};
  for (const e of parts(p.labels)) { const m = e.match(/^(\d+)\s*:\s*(.+)$/); if (m) labels[+m[1]] = m[2].trim(); }
  const lines = parts(p.lines).filter(Boolean).map(normMath), lUp = Math.round(N(p.linesUpto, 0)), shownL = lUp ? Math.min(lUp, lines.length) : lines.length;
  const beam = p.beam === true;
  // the text of each token as drawn (substituted in place when sub = in)
  const drawn = toks.map((t, i) => {
    if (mode !== "in" || isOp[i]) return t;
    if (idx[termOf[i]] !== undefined) return "\u0001" + normMath(idx[termOf[i]]) + "\u0002";
    return substitute(t, sym);
  });
  const evalSide = (a, b) => evaluate(toks.slice(a, b).map((t, i) => (isOp[a + i] ? t : idx[termOf[a + i]] !== undefined ? idx[termOf[a + i]] : substitute(t, sym))).join(" "));
  const eqAt = toks.findIndex((t) => t === "=" || t === "≡");
  // the result: "auto" computes the right-hand side (after =) with the values
  let result = String(p.result ?? "").trim();
  if (result.toLowerCase() === "auto") {
    const v = eqAt >= 0 ? evalSide(eqAt + 1, toks.length) : evalSide(0, toks.length);
    result = Number.isFinite(v) ? fmtNum(v) : "";
  }
  if (result && p.unit) result = /^[₹$£€¥]/.test(String(p.unit)) ? inr(`${p.unit}${result.replace(/,/g, "")}`) : `${result}${p.unit}`;
  const showResult = !!result && allIn && (!lines.length || shownL >= lines.length);
  // the phase the latest step brought (it is the one that animates)
  const phase = showResult ? "result" : lines.length && shownL > 0 && allIn ? "lines" : mode && allIn ? "sub" : "terms";
  const rows = drawn.map((t) => parseRow(t)), rowsOld = toks.map((t) => parseRow(t));
  let fs = Math.min(w * 0.07, 96);
  const gapF = 0.3;
  const widthAt = (f) => rows.reduce((a, r) => a + measureRow(r, f).w, 0) + gapF * f * (rows.length - 1) +
    (showResult && !lines.length ? tw("= " + plainOf(result), f) + f * 1.1 : 0);
  const W0 = widthAt(fs);
  if (W0 > w * 0.92) fs *= (w * 0.92) / W0;
  const ms = rows.map((r) => measureRow(r, fs));
  const asc = Math.max(...ms.map((m) => m.asc)), desc = Math.max(...ms.map((m) => m.desc));
  const gap = gapF * fs;
  // positions: centred, or around the = at the pivot in beam mode
  const xs = [];
  if (beam && eqAt > 0) {
    xs[eqAt] = -ms[eqAt].w / 2;
    for (let i = eqAt - 1; i >= 0; i--) xs[i] = xs[i + 1] - gap - ms[i].w;
    for (let i = eqAt + 1; i < toks.length; i++) xs[i] = xs[i - 1] + ms[i - 1].w + gap;
  } else {
    const total = ms.reduce((a, m) => a + m.w, 0) + gap * (toks.length - 1) + (showResult && !lines.length ? tw("= " + plainOf(result), fs) + fs * 1.1 : 0);
    let x = -total / 2;
    toks.forEach((t, i) => { xs[i] = x; x += ms[i].w + gap; });
  }
  const underVals = {};
  if (mode === "under") toks.forEach((t, i) => {
    if (isOp[i]) return;
    const v = idx[termOf[i]] !== undefined ? idx[termOf[i]] : sym[plainOf(t).trim()];
    if (v !== undefined && v !== "") underVals[i] = normMath(v);
  });
  const chipH = fs * 0.78, chipFs = Math.max(36, fs * 0.5);
  const valBand = Object.keys(underVals).length ? chipH + fs * 0.25 : 0;
  // label tiers under the terms (two rows when they would touch)
  const labFs = Math.max(36, Math.min(fs * 0.42, w * 0.032));
  const labItems = [];
  toks.forEach((t, i) => { if (!isOp[i] && labels[termOf[i]] && termOf[i] <= shownT && !labItems.some((l) => l.term === termOf[i])) {
    const cx = xs[i] + ms[i].w / 2, lw = Math.min(w * 0.4, tw(labels[termOf[i]], labFs));
    labItems.push({ term: termOf[i], cx, lw, text: labels[termOf[i]] });
  } });
  const tierEnd = [-Infinity, -Infinity];
  labItems.forEach((l) => { const a = l.cx - l.lw / 2 - labFs * 0.6; l.tier = a > tierEnd[0] ? 0 : 1; tierEnd[l.tier] = l.cx + l.lw / 2 + labFs * 0.6; });
  const labBand = labItems.length ? labFs * (labItems.some((l) => l.tier) ? 3.7 : 2.4) : 0;
  const lineH = (asc + desc) * 1.35;
  const linesBlock = lines.length ? lines.length * lineH : 0;
  const beamBand = beam ? fs * 1.5 : 0;
  const totalH = asc + desc + valBand + labBand + linesBlock + beamBand;
  const base = -totalH / 2 + asc + (p.title ? fs * 0.35 : 0);
  let out = "";
  const termScale = (i) => {
    if (phase !== "terms" || !upto || termOf[i] !== shownT) return 1;
    return 0.35 + 0.65 * backOut(ph(s, 0, 0.45));
  };
  // glow behind terms
  toks.forEach((t, i) => {
    if (isOp[i] || !glow.has(termOf[i]) || termOf[i] > shownT) return;
    out += `<rect x="${f1(xs[i] - fs * 0.14)}" y="${f1(base - asc - fs * 0.1)}" width="${f1(ms[i].w + fs * 0.28)}" height="${f1(asc + desc + fs * 0.2)}" rx="${f1(fs * 0.16)}" fill="#fff1b8" stroke="#f2c14e" stroke-width="${f1(fs * 0.05)}"/>`;
  });
  // the main line (in beam mode it rides on the beam and tips with it)
  let main = "";
  const flipK = phase === "sub" && mode === "in" ? ph(s, 0, 0.7) : 1;
  toks.forEach((t, i) => {
    if (termOf[i] > shownT) return;
    let row = rows[i], col = INK;
    if (beam && i === eqAt) {
      const L = evalSide(0, eqAt), R = evalSide(eqAt + 1, toks.length), known = mode && Number.isFinite(L) && Number.isFinite(R);
      const bal = known && Math.abs(L - R) <= 1e-6 * Math.max(1, Math.abs(L), Math.abs(R));
      if (known && !bal) { row = parseRow("≠"); col = "#e5484d"; } else if (bal) col = "#2fa35b";
    }
    const sc = termScale(i), cx = xs[i] + ms[i].w / 2;
    const body = renderRow(row, xs[i], base, fs, col, acc);
    main += sc < 1 ? `<g transform="translate(${f1(cx)},${f1(base - fs * 0.3)}) scale(${sc.toFixed(3)}) translate(${f1(-cx)},${f1(-(base - fs * 0.3))})" opacity="${clamp01(sc * 1.4 - 0.4).toFixed(3)}">${body}</g>` : body;
    // strike-and-write: the old letters rise and fade with a stroke through them while the numbers pop in
    if (mode === "in" && !isOp[i] && drawn[i] !== toks[i] && flipK < 1) {
      const mo = measureRow(rowsOld[i], fs * 0.7), ox = cx - mo.w / 2, oy = base - asc - fs * 0.15 - fs * 0.5 * flipK;
      main += `<g opacity="${(1 - flipK).toFixed(3)}">${renderRow(rowsOld[i], ox, oy, fs * 0.7, "#8a94a3", acc)}` +
        `<path d="M${f1(ox - fs * 0.05)} ${f1(oy - fs * 0.22)} L${f1(ox + mo.w * Math.min(1, flipK * 3) + fs * 0.05)} ${f1(oy - fs * 0.22)}" stroke="#e5484d" stroke-width="${f1(fs * 0.06)}" stroke-linecap="round"/></g>`;
    }
    if (underVals[i] !== undefined) {
      const k2 = phase === "sub" ? backOut(ph(s, 0.1 * (termOf[i] - 1), 0.45)) : 1;
      if (k2 > 0.01) {
        const vr = parseRow(underVals[i]), vm = measureRow(vr, chipFs), cw = Math.max(vm.w + chipFs * 0.8, chipH * 1.3), cy = base + desc + fs * 0.2 + chipH / 2;
        main += `<g transform="translate(${f1(cx)},${f1(cy)}) scale(${k2.toFixed(3)})">` + chipBox(0, 0, cw, chipH, acc, shade(acc, 0.8), fs * 0.03) +
          renderRow(vr, -vm.w / 2, chipFs * 0.35, chipFs, "#ffffff", "#ffffff") + `</g>` +
          `<path d="M${f1(cx)} ${f1(base + desc + fs * 0.02)} L${f1(cx)} ${f1(cy - chipH / 2)}" stroke="${acc}" stroke-width="${f1(fs * 0.03)}" opacity="${clamp01(k2).toFixed(3)}"/>`;
      }
    }
  });
  if (beam && eqAt > 0) {
    const L = evalSide(0, eqAt), R = evalSide(eqAt + 1, toks.length), known = mode && Number.isFinite(L) && Number.isFinite(R);
    const target = known ? clampN((2 * (R - L)) / Math.max(1e-9, Math.abs(L), Math.abs(R)), -1, 1) : 0;
    const tilt = settle(clampN(N(p.tiltFrom, 0), -1, 1), target, s, N(p.glide, 1));
    const by = base + desc + valBand + fs * 0.2, x0 = Math.min(...xs) - fs * 0.4, x1 = Math.max(...xs.map((x, i) => x + ms[i].w)) + fs * 0.4;
    const ang = tilt * 8, piv = by + fs * 0.12;
    out += `<path d="M0 ${f1(piv)} L${f1(-fs * 0.55)} ${f1(piv + fs * 1.15)} L${f1(fs * 0.55)} ${f1(piv + fs * 1.15)} Z" fill="#8a94a3" stroke="#5c677d" stroke-width="${f1(fs * 0.04)}" stroke-linejoin="round"/>` +
      `<rect x="${f1(-fs * 1.1)}" y="${f1(piv + fs * 1.12)}" width="${f1(fs * 2.2)}" height="${f1(fs * 0.16)}" rx="${f1(fs * 0.06)}" fill="#5c677d"/>`;
    main = `<g transform="rotate(${ang.toFixed(2)} 0 ${f1(piv)})">` + main +
      `<rect x="${f1(x0)}" y="${f1(by)}" width="${f1(x1 - x0)}" height="${f1(fs * 0.24)}" rx="${f1(fs * 0.1)}" fill="#a8763f" stroke="${shade("#a8763f", 0.7)}" stroke-width="${f1(fs * 0.03)}"/>` +
      `<circle cx="0" cy="${f1(piv)}" r="${f1(fs * 0.1)}" fill="#5c677d"/></g>`;
    const bal = known && Math.abs(L - R) <= 1e-6 * Math.max(1, Math.abs(L), Math.abs(R));
    if (bal && Math.abs(tilt) < 0.03) out += `<g transform="translate(0,${f1(base - asc - fs * 0.55)})">${mark("tick", fs * 0.6, "#2fa35b", ph(s, 0.9, 0.4) || (s > 5 ? 1 : 0))}</g>`;
  }
  out += main;
  // labels under the terms, with a short leader
  labItems.forEach((l) => {
    const y = base + desc + valBand + (beam ? beamBand : 0) + labFs * (1.45 + l.tier * 1.3);
    const fsl = Math.min(labFs, fitT(l.text, w * 0.4, labFs));
    out += `<path d="M${f1(l.cx)} ${f1(base + desc + valBand + fs * 0.05)} L${f1(l.cx)} ${f1(y - fsl * 0.55)}" stroke="#7a8594" stroke-width="${f1(Math.max(3, fs * 0.03))}"/>` +
      T(l.text, l.cx, y, fsl, "#4a5568", 700);
  });
  // working lines, the = signs under the first =
  const eqX = eqAt >= 0 && !beam ? xs[eqAt] : null;
  let lastEnd = Math.max(...xs.map((x, i) => (termOf[i] <= shownT ? x + ms[i].w : -Infinity))), lastBase = base;
  lines.forEach((ln, j) => {
    if (j >= shownL) return;
    const row = parseRow(mode === "in" ? substitute(ln, {}) : ln), m = measureRow(row, fs), y = base + desc + valBand + labBand + (j + 1) * lineH - desc * 0.3;
    const x = eqX !== null && /^\s*[=≡≈]/.test(ln) ? eqX : -m.w / 2;
    const k3 = phase === "lines" && j === shownL - 1 ? ease(ph(s, 0, 0.45)) : 1;
    out += `<g opacity="${k3.toFixed(3)}" transform="translate(0,${f1((1 - k3) * fs * 0.4)})">${renderRow(row, x, y, fs, INK, acc)}</g>`;
    lastEnd = x + m.w; lastBase = y;
  });
  if (showResult) {
    const rr = parseRow((/^[=≡≈]/.test(result) ? "" : "= ") + result), rm = measureRow(rr, fs);
    const x = lastEnd + gap * 1.4, k4 = phase === "result" ? backOut(ph(s, 0, 0.5)) : 1;
    const bx = x - fs * 0.25, bw = rm.w + fs * 0.5, cyR = lastBase - fs * 0.3;
    const fitsRight = x + rm.w + fs * 0.3 <= w * 0.5;
    const rx = fitsRight ? bx : -bw / 2, ry = fitsRight ? cyR : lastBase + lineH * 0.7;
    out += `<g transform="translate(${f1(rx + bw / 2)},${f1(ry)}) scale(${k4.toFixed(3)})">` +
      `<rect x="${f1(-bw / 2)}" y="${f1(-(rm.asc + rm.desc) / 2 - fs * 0.2)}" width="${f1(bw)}" height="${f1(rm.asc + rm.desc + fs * 0.4)}" rx="${f1(fs * 0.18)}" fill="${tint(acc)}" stroke="${acc}" stroke-width="${f1(fs * 0.06)}"/>` +
      renderRow(rr, -rm.w / 2, (rm.asc - rm.desc) / 2, fs, shade(acc, 0.7), shade(acc, 0.7)) + `</g>`;
  }
  if (p.title) out = T(p.title, 0, base - asc - fs * 1.0, fitT(p.title, w * 0.9, Math.max(36, fs * 0.55)), "#4a5568", 800) + out;
  return out;
}

// ---------------------------------------------------------------- scaleBalance: a tarazu or a seesaw
const MINE = new Set(["formula", "scaleBalance", "causeChain", "sorter", "spectrum", "padlocks", "tugOfWar", "oneVsAll", "tAccount",
  "choicePaths", "incomeLine", "doorway"]);
function panItems(spec) {
  return parts(spec).filter(Boolean).slice(0, 8).map((it) => {
    let m = it.match(/^@([A-Za-z]\w*)(?::(.*?))?(?:=(-?\d+(?:\.\d+)?))?$/);
    if (m) return { thing: m[1], text: (m[2] || "").trim(), wt: m[3] != null ? +m[3] : 1 };
    m = it.match(/^(.*\S)=(-?\d+(?:\.\d+)?)$/);
    return m ? { text: m[1].trim(), wt: +m[2] } : { text: it, wt: 1 };
  });
}
// a drawing of the library, fitted into a size x size box standing on (0, 0)
function thingSvg(name, size) {
  if (MINE.has(name)) return null;
  const svg = drawSaancha(name, {});
  if (/stroke="#e5484d" stroke-width="4"\/><text y="8"/.test(svg)) return null;          // not a saancha of the library
  const b = boxOf(name, {}).box;
  if (!b) return null;
  const bw = b[2] - b[0], bh = b[3] - b[1], sc = size / Math.max(1, bw, bh);
  return { svg: `<g transform="translate(${f1(-(b[0] + b[2]) / 2 * sc)},${f1(-b[3] * sc)}) scale(${sc.toFixed(4)})">${svg}</g>`, h: bh * sc };
}
// a stack of items standing on (0, 0), inside a width; k: drop progress of the newest one
function stackSvg(items, width, w, color, newest, k) {
  const cols = items.length > 3 ? 2 : 1, cw = width / cols, ch = w * 0.066, gap = w * 0.012;
  const hs = [0, 0];
  let out = "";
  items.forEach((it, i) => {
    const c = cols === 2 ? i % 2 : 0, x = cols === 2 ? (c - 0.5) * cw : 0;
    let body = "", h;
    const th = it.thing ? thingSvg(it.thing, w * 0.12) : null;
    if (th) {
      const lab = it.text ? wrap2(it.text, cw * 0.92, w * 0.03) : null, lh = lab ? lab.fs * 1.3 : 0;
      h = th.h + lh;
      body = `<g transform="translate(0,${f1(-lh)})">${th.svg}</g>` + (lab ? linesSvg(lab, 0, -lh / 2, INK, 800) : "");
    } else {
      const text = it.text || it.thing || "", wr = wrap2(text, cw * 0.86, w * 0.038, 36);
      h = wr.lines.length > 1 ? ch * 1.45 : ch;
      const fill = i % 2 ? shade(color, 1.18) : color;
      body = chipBox(0, -h / 2, cw * 0.94, h, fill, shade(color, 0.75), w * 0.003, h * 0.24) + linesSvg(wr, 0, -h / 2, "#ffffff", 800);
    }
    const y0 = -hs[c];
    hs[c] += h + gap;
    const dy = i === newest ? -(1 - k) * w * 0.28 : 0, op = i === newest ? clamp01(k * 3) : 1;
    out += `<g transform="translate(${f1(x)},${f1(y0 + dy)})" opacity="${op.toFixed(3)}">${body}</g>`;
  });
  return { svg: out, h: Math.max(hs[0], hs[1]) };
}
function scaleBalance(p) {
  const w = N(p.w, 1000), s = stepS(p), seesaw = p.mode === "seesaw";
  const lc = p.leftColor || "#e07b24", rc = p.rightColor || "#2459a6";
  const L = panItems(p.left), R = panItems(p.right);
  // the order things arrive in (L1,R1,...), and how many have arrived
  let order = String(p.order ?? "").split(",").map((q) => q.trim().toUpperCase()).filter((q) => /^[LR]\d+$/.test(q));
  if (!order.length) order = [...L.map((_, i) => `L${i + 1}`), ...R.map((_, i) => `R${i + 1}`)];
  const upto = Math.max(0, Math.round(N(p.upto, 0))), shown = upto ? order.slice(0, upto) : order;
  const vis = (side, arr, list) => arr.filter((_, i) => list.includes(`${side}${i + 1}`));
  const newestKey = upto && upto <= order.length ? order[upto - 1] : "";
  const k = ph(s, 0, 0.55);
  const lv = vis("L", L, shown), rv = vis("R", R, shown);
  const sideW = (items, val) => { const v = firstNum(val); return v !== null ? v : items.reduce((a, it) => a + it.wt, 0); };
  const autoTilt = (li, ri) => { const a = sideW(li, p.leftValue), b = sideW(ri, p.rightValue), m = Math.max(Math.abs(a), Math.abs(b));
    return m > 0 ? clampN((b - a) / m * 1.6, -1, 1) : 0; };
  const hasW = String(p.weight ?? "") !== "" && seesaw, share = clamp01(N(p.share, 0.5));
  let target, from;
  if (hasW) { target = -(share - 0.5) * 2; from = isNum(p.shareFrom) ? -(clamp01(+p.shareFrom) - 0.5) * 2 : target; }
  else if (p.auto === true) {
    target = autoTilt(lv, rv);
    const prev = upto > 1 ? order.slice(0, upto - 1) : [];
    from = isNum(p.tiltFrom) ? clampN(+p.tiltFrom, -1, 1) : upto > 1 ? autoTilt(vis("L", L, prev), vis("R", R, prev)) : 0;
  } else { target = clampN(N(p.tilt, 0), -1, 1); from = isNum(p.tiltFrom) ? clampN(+p.tiltFrom, -1, 1) : 0; }
  const glide = N(p.glide, 1);
  const tilt = settle(from, target, s, glide), level = Math.abs(target) < 0.02 && Math.abs(tilt) < 0.03;
  const ang = tilt * (seesaw ? 12 : 14), th = (ang * Math.PI) / 180;
  const fsL = w * 0.042;
  let out = "", pivY, ends;
  if (!seesaw) {
    pivY = -w * 0.62;
    const A = w * 0.33, Lh = w * 0.28, P = w * 0.34;
    out += `<path d="M${f1(-w * 0.12)} 0 L${f1(-w * 0.09)} ${f1(-w * 0.035)} L${f1(w * 0.09)} ${f1(-w * 0.035)} L${f1(w * 0.12)} 0 Z" fill="#7a5a3a" stroke="#5a4028" stroke-width="${f1(w * 0.004)}"/>` +
      `<rect x="${f1(-w * 0.018)}" y="${f1(pivY)}" width="${f1(w * 0.036)}" height="${f1(-pivY - w * 0.03)}" rx="${f1(w * 0.008)}" fill="#a8763f" stroke="#7a5a3a" stroke-width="${f1(w * 0.004)}"/>` +
      `<path d="M${f1(-w * 0.05)} ${f1(pivY + w * 0.16)} A${f1(w * 0.12)} ${f1(w * 0.12)} 0 0 0 ${f1(w * 0.05)} ${f1(pivY + w * 0.16)}" fill="none" stroke="#5a4028" stroke-width="${f1(w * 0.004)}"/>` +
      `<path d="M0 ${f1(pivY)} L${f1(-Math.sin(th) * w * 0.15)} ${f1(pivY + Math.cos(th) * w * 0.15)}" stroke="${level ? "#2fa35b" : "#c0392b"}" stroke-width="${f1(w * 0.008)}" stroke-linecap="round"/>`;
    ends = [-1, 1].map((d) => ({ d, x: d * A * Math.cos(th), y: pivY + d * A * Math.sin(th) }));
    let pans = "";
    ends.forEach((e) => {
      const items = e.d < 0 ? lv : rv, col = e.d < 0 ? lc : rc, rim = e.y + Lh, nk = newestKey.startsWith(e.d < 0 ? "L" : "R") ? items.length - 1 : -1;
      const st = stackSvg(items, P * 0.9, w, col, nk, k);
      const val = e.d < 0 ? p.leftValue : p.rightValue, lab = e.d < 0 ? p.leftLabel : p.rightLabel;
      pans += `<path d="M${f1(e.x)} ${f1(e.y)} L${f1(e.x - P * 0.47)} ${f1(rim)} M${f1(e.x)} ${f1(e.y)} L${f1(e.x + P * 0.47)} ${f1(rim)}" stroke="#7a838f" stroke-width="${f1(w * 0.004)}"/>` +
        `<g transform="translate(${f1(e.x)},${f1(rim - w * 0.004)})">${st.svg}</g>` +
        `<path d="M${f1(e.x - P / 2)} ${f1(rim)} L${f1(e.x + P / 2)} ${f1(rim)} Q${f1(e.x + P * 0.42)} ${f1(rim + w * 0.064)} ${f1(e.x)} ${f1(rim + w * 0.064)} Q${f1(e.x - P * 0.42)} ${f1(rim + w * 0.064)} ${f1(e.x - P / 2)} ${f1(rim)} Z" fill="${shade(col, 0.95)}" stroke="${shade(col, 0.7)}" stroke-width="${f1(w * 0.004)}"/>` +
        (val !== undefined && val !== "" ? T(val, e.x, rim + w * 0.028, fitT(val, P * 0.6, w * 0.036), "#ffffff", 800) : "") +
        (lab ? linesSvg(wrap2(lab, P * 1.05, fsL), e.x, rim + w * 0.064 + fsL * 1.05, INK, 800) : "") +
        (p.crack === (e.d < 0 ? "left" : "right") ? `<path d="M${f1(e.x - P * 0.3)} ${f1(rim + w * 0.03)} l${f1(P * 0.12)} ${f1(w * 0.02)} l${f1(P * 0.08)} ${f1(-w * 0.025)} l${f1(P * 0.12)} ${f1(w * 0.028)} l${f1(P * 0.1)} ${f1(-w * 0.02)} l${f1(P * 0.12)} ${f1(w * 0.02)}" fill="none" stroke="#3b2a1a" stroke-width="${f1(w * 0.006)}" stroke-linejoin="round"/>` : "");
      e.top = rim - st.h;
    });
    out += `<g transform="rotate(${ang.toFixed(2)} 0 ${f1(pivY)})"><rect x="${f1(-A - w * 0.02)}" y="${f1(pivY - w * 0.011)}" width="${f1(2 * A + w * 0.04)}" height="${f1(w * 0.022)}" rx="${f1(w * 0.011)}" fill="#c08a3e" stroke="#7a5a3a" stroke-width="${f1(w * 0.004)}"/></g>` +
      pans + `<circle cx="0" cy="${f1(pivY)}" r="${f1(w * 0.024)}" fill="#7a5a3a"/><circle cx="0" cy="${f1(pivY)}" r="${f1(w * 0.01)}" fill="#e9d3a9"/>`;
  } else {
    pivY = -w * 0.17;
    const A = w * 0.36, Pk = w * 0.46, top = pivY - w * 0.03;
    ends = [-1, 1].map((d) => ({ d, x: d * A * Math.cos(th), y: top + d * A * Math.sin(th) }));
    out += `<path d="M0 ${f1(pivY)} L${f1(-w * 0.09)} 0 L${f1(w * 0.09)} 0 Z" fill="#8a94a3" stroke="#5c677d" stroke-width="${f1(w * 0.004)}" stroke-linejoin="round"/>`;
    let plank = `<rect x="${f1(-Pk)}" y="${f1(top)}" width="${f1(2 * Pk)}" height="${f1(w * 0.03)}" rx="${f1(w * 0.01)}" fill="#c08a3e" stroke="#7a5a3a" stroke-width="${f1(w * 0.004)}"/>`;
    if (hasW) {
      const sh = settle(isNum(p.shareFrom) ? clamp01(+p.shareFrom) : share, share, s, glide), xw = -(sh - 0.5) * 2 * A, ww = Math.min(w * 0.3, Math.max(w * 0.16, tw(p.weight, w * 0.038) / 0.72)), wh = w * 0.075;
      plank += `<g transform="translate(${f1(xw)},${f1(top)})"><path d="M${f1(-ww / 2)} 0 L${f1(-ww * 0.38)} ${f1(-wh)} L${f1(ww * 0.38)} ${f1(-wh)} L${f1(ww / 2)} 0 Z" fill="#4a5568" stroke="#2d3748" stroke-width="${f1(w * 0.004)}"/>` +
        `<path d="M${f1(-ww * 0.14)} ${f1(-wh)} Q0 ${f1(-wh * 1.5)} ${f1(ww * 0.14)} ${f1(-wh)}" fill="none" stroke="#2d3748" stroke-width="${f1(w * 0.008)}"/>` +
        T(p.weight, 0, -wh * 0.48, fitT(p.weight, ww * 0.72, w * 0.038), "#ffffff", 800) + `</g>`;
    }
    out += `<g transform="rotate(${ang.toFixed(2)} 0 ${f1(pivY)})">${plank}</g><circle cx="0" cy="${f1(pivY)}" r="${f1(w * 0.014)}" fill="#5c677d"/>`;
    if (p.pivotLabel) { const f = fitT(p.pivotLabel, w * 0.26, w * 0.034), cw = tw(p.pivotLabel, f) + f;
      out += chipBox(0, -w * 0.065, cw, f * 1.5, "#ffffff", "#5c677d", w * 0.003) + T(p.pivotLabel, 0, -w * 0.065, f, INK, 800); }
    const amt = (part) => { const m = String(p.weight ?? "").match(/^([^\d−-]*)(\d+(?:\.\d+)?)/); return m ? `${m[1]}${fmtNum(+m[2] * part)}` : `${Math.round(part * 100)}%`; };
    ends.forEach((e) => {
      const items = e.d < 0 ? lv : rv, col = e.d < 0 ? lc : rc, nk = newestKey.startsWith(e.d < 0 ? "L" : "R") ? items.length - 1 : -1;
      const val = e.d < 0 ? p.leftValue : p.rightValue, lab = e.d < 0 ? p.leftLabel : p.rightLabel;
      let y = e.y - w * 0.004, g = "";
      if (val !== undefined && val !== "") { const f = fitT(val, w * 0.24, w * 0.04), h = f * 1.5;
        g += chipBox(e.x, y - h / 2, Math.max(h * 1.6, tw(val, f) + f), h, "#ffffff", col, w * 0.005) + T(val, e.x, y - h / 2, f, shade(col, 0.7), 800); y -= h + w * 0.01; }
      const st = stackSvg(items, w * 0.26, w, col, nk, k);
      g += `<g transform="translate(${f1(e.x)},${f1(y)})">${st.svg}</g>`; y -= st.h;
      if (hasW && p.split === true) { const part = e.d < 0 ? share : 1 - share, sp = amt(part), f = w * 0.036, h = f * 1.45;
        g += chipBox(e.x, y - h / 2 - w * 0.005, tw(sp, f) + f, h, "#4a5568", "#2d3748", w * 0.003) + T(sp, e.x, y - h / 2 - w * 0.005, f, "#ffffff", 800); y -= h + w * 0.015; }
      if (lab) { const wr = wrap2(lab, w * 0.27, fsL); y -= wr.lines.length * wr.fs * 1.18 * 0.5 + w * 0.01; g += linesSvg(wr, e.x, y, shade(col, 0.6), 800); y -= wr.lines.length * wr.fs * 0.6; }
      if (p.crack === (e.d < 0 ? "left" : "right")) g += `<path d="M${f1(e.x - w * 0.08)} ${f1(e.y + w * 0.04)} l${f1(w * 0.04)} ${f1(w * 0.02)} l${f1(w * 0.03)} ${f1(-w * 0.025)} l${f1(w * 0.04)} ${f1(w * 0.025)} l${f1(w * 0.03)} ${f1(-w * 0.02)}" fill="none" stroke="#3b2a1a" stroke-width="${f1(w * 0.006)}"/>`;
      out += g; e.top = y;
    });
  }
  // a tick on the winner, the level tag, the gap block, the title
  const mk = p.mark === "auto" ? (target < -0.02 ? "left" : target > 0.02 ? "right" : "") : p.mark;
  ends.forEach((e) => { if (mk === (e.d < 0 ? "left" : "right")) out += `<g transform="translate(${f1(e.x)},${f1(e.top - w * 0.05)})">${mark("tick", w * 0.07, "#2fa35b", ph(s, glide * 0.6, 0.4) || (s > 50 ? 1 : 0))}</g>`; });
  let tagY = (seesaw ? Math.min(...ends.map((e) => e.top)) - w * 0.06 : pivY - w * 0.085);
  // the chips and the title keep the readable floor (36 px); the title sits just above the highest thing, not a band
  // higher, so it no longer runs into a pill placed over the scale (ch12)
  let chipTop = Infinity;
  if (p.levelTag && level) { const f = fitT(p.levelTag, w * 0.5, Math.max(36, w * 0.04)), cw = tw(p.levelTag, f) + f * 1.2, kk = backOut(ph(s, glide * 0.8, 0.4));
    out += `<g transform="translate(0,${f1(tagY)}) scale(${kk.toFixed(3)})">${chipBox(0, 0, cw, f * 1.55, "#e6f6ea", "#2fa35b", w * 0.004)}${T(p.levelTag, 0, 0, f, "#1f7a43", 800)}</g>`; chipTop = tagY - f * 0.78; tagY -= f * 2; }
  if (p.gapLabel) { const f = fitT(p.gapLabel, w * 0.5, Math.max(36, w * 0.04)), cw = tw(p.gapLabel, f) + f * 1.2, kk = backOut(ph(s, glide * 0.7, 0.45));
    out += `<g transform="translate(0,${f1(tagY)}) scale(${kk.toFixed(3)})">${chipBox(0, 0, cw, f * 1.55, "#e5484d", "#a3273a", w * 0.004)}${T(p.gapLabel, 0, 0, f, "#ffffff", 800)}</g>`; chipTop = tagY - f * 0.78; tagY -= f * 2; }
  const highest = Math.min(chipTop, ...ends.map((e) => e.top - (mk ? w * 0.1 : 0)), seesaw ? 0 : pivY - w * 0.05);
  if (p.title) { const f = fitT(p.title, w * 0.9, Math.max(36, w * 0.046)); out += T(p.title, 0, highest - w * 0.015 - f * 0.5, f, INK, 800); }
  return out;
}

// ---------------------------------------------------------------- causeChain: a mechanism as chips that light in order
function chainChips(spec) {
  return parts(spec).filter(Boolean).slice(0, 10).map((c) => {
    const i = c.lastIndexOf("|");
    return i >= 0 ? { text: c.slice(0, i).trim(), dir: dirOf(c.slice(i + 1)) } : { text: c, dir: "" };
  });
}
function chipText(text, cw, ch, cap, fill) {
  if (/[_^{}]|\/\//.test(text)) {
    const row = parseRow(normMath(text)), u = measureRow(row, 1), f = Math.min(cap, (cw * 0.86) / Math.max(0.01, u.w));
    const m = measureRow(row, f);
    return renderRow(row, -m.w / 2, f * 0.35, f, fill, fill);
  }
  return linesSvg(wrap2(normMath(text), cw * 0.86, cap, 36), 0, 0, fill, 800);
}
function causeChain(p) {
  const w = N(p.w, 1600), col = p.color || "#2459a6", s = stepS(p), t = timeT(p);
  const r1 = chainChips(p.links ?? "A|up;B|up;C|down;D|down"), r2 = chainChips(p.links2);
  if (!r1.length) r1.push({ text: "", dir: "" });
  const n1 = r1.length, n = n1 + r2.length;
  let layout = ["row", "snake", "ring"].includes(p.layout) ? p.layout : n1 <= 5 || r2.length ? "row" : "snake";
  if (r2.length && layout !== "row") layout = "row";
  const pos = [], joinAt = Math.round(N(p.join, 0)) >= 1 ? Math.min(n1, Math.round(N(p.join, 0))) : n1;   // 0: the last chip
  let cw, ch;
  if (layout === "ring") {
    cw = Math.min(w * 0.24, (w * 2.2) / Math.max(3, n1)); ch = Math.min(w * 0.085, cw * 0.55);
    r1.forEach((_, i) => { const a = -Math.PI / 2 + (2 * Math.PI * i) / n1; pos.push([Math.cos(a) * w * 0.36, Math.sin(a) * w * 0.2]); });
  } else if (layout === "snake") {
    const m = Math.ceil(n1 / 2), slot = (w * 0.96) / m;
    cw = Math.min(slot * 0.72, w * 0.26); ch = Math.min(w * 0.085, cw * 0.62);
    const gapY = ch * 2.2;
    r1.forEach((_, i) => pos.push(i < m ? [-w * 0.48 + slot * (i + 0.5), -gapY / 2] : [-w * 0.48 + slot * (m - 1 - (i - m) + 0.5), gapY / 2]));
  } else {
    const slot = (w * 0.96) / n1;
    cw = Math.min(slot * 0.72, w * 0.26); ch = Math.min(w * 0.085, cw * 0.62);
    r1.forEach((_, i) => pos.push([-w * 0.48 + slot * (i + 0.5), r2.length ? -ch * 1.15 : 0]));
    if (r2.length) {
      const j = joinAt - 1, sx = Math.min(pos[j][0], w * 0.48 - slot * (r2.length - 0.5));
      r2.forEach((_, i) => pos.push([Math.max(-w * 0.48 + slot * 0.5, sx) + slot * i, ch * 1.15]));
    }
  }
  const chips = [...r1, ...r2], at = Math.max(0, Math.round(N(p.at, 0))), lit = at ? Math.min(at, n) : n, newest = at ? lit - 1 : -1;
  const ghost = p.ghost !== false, sw = Math.max(4, w * 0.005), pad = w * 0.008;
  const edgePt = (c, o, pd) => { const dx = o[0] - c[0], dy = o[1] - c[1];
    const sc = Math.min(Math.abs(dx) > 1e-6 ? (cw / 2 + pd) / Math.abs(dx) : Infinity, Math.abs(dy) > 1e-6 ? (ch / 2 + pd) / Math.abs(dy) : Infinity);
    return [c[0] + dx * sc, c[1] + dy * sc]; };
  const edges = [];
  for (let i = 0; i + 1 < n1; i++) edges.push([i, i + 1]);
  if (r2.length) { edges.push([joinAt - 1, n1]); for (let i = n1; i + 1 < n; i++) edges.push([i, i + 1]); }
  let out = "", toks = "";
  edges.forEach(([a, b]) => {
    const on = b < lit, show = on || ghost;
    if (!show) return;
    const A0 = edgePt(pos[a], pos[b], pad), B0 = edgePt(pos[b], pos[a], pad * 2.2);
    const k = on ? (b === newest ? ph(s, 0, 0.35) : 1) : 1, c = on ? "#5c677d" : "#c3cad3";
    if (layout === "ring") {
      const mx = (A0[0] + B0[0]) / 2, my = (A0[1] + B0[1]) / 2, len = Math.hypot(mx, my) || 1, cx = mx + (mx / len) * w * 0.04, cy = my + (my / len) * w * 0.04;
      const ang = Math.atan2(B0[1] - cy, B0[0] - cx);
      out += `<path d="M${f1(A0[0])} ${f1(A0[1])} Q${f1(cx)} ${f1(cy)} ${f1(B0[0])} ${f1(B0[1])}" fill="none" stroke="${c}" stroke-width="${f1(sw)}" stroke-linecap="round" pathLength="1" stroke-dasharray="${on ? `${k.toFixed(3)} 1` : "0.04 0.03"}"/>` +
        (k > 0.9 ? arrowHead(B0[0], B0[1], ang, sw * 3.2, c) : "");
    } else out += arrowLine(A0[0], A0[1], B0[0], B0[1], c, sw, k, !on);
    if (on && p.run === true) { const u = ((t * 0.7 + a * 0.37) % 1 + 1) % 1; toks += `<circle cx="${f1(lerp(A0[0], B0[0], u))}" cy="${f1(lerp(A0[1], B0[1], u))}" r="${f1(sw * 1.6)}" fill="#f29f05" stroke="#ffffff" stroke-width="${f1(sw * 0.4)}"/>`; }
  });
  // the loop back from the last chip to the first (spirals, self-fulfilling expectations)
  let below = Math.max(...pos.map((q) => q[1])) + ch / 2;
  const allLit = lit >= n;
  if (p.loop === true && n > 1) {
    const on = allLit, c = on ? "#7b2cbf" : "#c3cad3", kL = on ? (at ? ph(s, 0.45, 0.6) : 1) : 1, last = pos[n - 1], first = pos[0];
    let d, labX, labY;
    if (layout === "ring") {
      const A0 = edgePt(last, first, pad), B0 = edgePt(first, last, pad * 2.2), mx = (A0[0] + B0[0]) / 2, my = (A0[1] + B0[1]) / 2, len = Math.hypot(mx, my) || 1;
      const cx = mx + (mx / len) * w * 0.04, cy = my + (my / len) * w * 0.04;
      d = `M${f1(A0[0])} ${f1(A0[1])} Q${f1(cx)} ${f1(cy)} ${f1(B0[0])} ${f1(B0[1])}`; labX = cx; labY = cy - ch * 0.5;
      if (on || ghost) out += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${f1(sw)}" pathLength="1" stroke-dasharray="${on ? `${kL.toFixed(3)} 1` : "0.04 0.03"}"/>` + (kL > 0.9 ? arrowHead(B0[0], B0[1], Math.atan2(B0[1] - cy, B0[0] - cx), sw * 3.2, c) : "");
    } else if (layout === "snake") {
      const xl = -w * 0.495, y1 = first[1], y2 = last[1], x2 = last[0] - cw / 2 - pad, x1 = first[0] - cw / 2 - pad * 2.2;
      d = `M${f1(x2)} ${f1(y2)} L${f1(xl)} ${f1(y2)} L${f1(xl)} ${f1(y1)} L${f1(x1)} ${f1(y1)}`; labX = null;
      if (on || ghost) out += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${f1(sw)}" stroke-linejoin="round" pathLength="1" stroke-dasharray="${on ? `${kL.toFixed(3)} 1` : "0.04 0.03"}"/>` + (kL > 0.9 ? arrowHead(x1, y1, 0, sw * 3.2, c) : "");
    } else {
      const yb = below + ch * 0.75, xa = last[0], xb = first[0], y0a = last[1] + ch / 2 + pad, y0b = first[1] + ch / 2 + pad * 2.2, rr = ch * 0.35;
      d = `M${f1(xa)} ${f1(y0a)} L${f1(xa)} ${f1(yb - rr)} Q${f1(xa)} ${f1(yb)} ${f1(xa - rr)} ${f1(yb)} L${f1(xb + rr)} ${f1(yb)} Q${f1(xb)} ${f1(yb)} ${f1(xb)} ${f1(yb - rr)} L${f1(xb)} ${f1(y0b)}`;
      labX = (xa + xb) / 2; labY = yb;
      if (on || ghost) out += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${f1(sw)}" stroke-linejoin="round" pathLength="1" stroke-dasharray="${on ? `${kL.toFixed(3)} 1` : "0.04 0.03"}"/>` + (kL > 0.9 ? arrowHead(xb, y0b, -Math.PI / 2, sw * 3.2, c) : "");
      below = yb + sw;
    }
    if (p.loopLabel && labX !== null && (on || ghost)) {
      const f = Math.max(36, Math.min(w * 0.026, fitT(p.loopLabel, w * 0.3, w * 0.026))), bw2 = tw(p.loopLabel, f) + f;
      out += chipBox(labX, labY, bw2, f * 1.45, "#ffffff", c, sw * 0.6) + T(p.loopLabel, labX, labY, f, on ? "#5a1f99" : "#9aa5b1", 800);
      if (layout === "row") below = labY + f * 0.8;
    }
  }
  // the chips
  chips.forEach((c, i) => {
    const on = i < lit;
    if (!on && !ghost) return;
    const [x, y] = pos[i], isNew = i === newest, kk = isNew ? ph(s, 0.2, 0.35) : 1;
    const tone = c.dir === "up" ? ["#e6f6ea", "#2fa35b"] : c.dir === "down" ? ["#fdeaea", "#e5484d"] : [tint(col), col];
    const sc = isNew ? 0.85 + 0.15 * backOut(kk) : 1;
    let g = on ? chipBox(0, 0, cw, ch, tone[0], tone[1], sw * 0.9) : chipBox(0, 0, cw, ch, "#ffffff", "#c3cad3", sw * 0.6);
    if (!on) g = g.replace("/>", ` stroke-dasharray="${f1(sw * 2)} ${f1(sw * 1.4)}"/>`);
    g += chipText(c.text, cw, ch, Math.min(w * 0.03, ch * 0.42), on ? INK : "#9aa5b1");
    if (c.dir) g += on ? upDownBadge(c.dir, ch * 0.27, cw / 2 - ch * 0.05, -ch / 2 + ch * 0.05, isNew ? ph(s, 0.45, 0.35) : 1)
      : `<circle cx="${f1(cw / 2 - ch * 0.05)}" cy="${f1(-ch / 2 + ch * 0.05)}" r="${f1(ch * 0.2)}" fill="#ffffff" stroke="#c3cad3" stroke-width="${f1(sw * 0.5)}"/>`;
    out += `<g transform="translate(${f1(x)},${f1(y)}) scale(${sc.toFixed(3)})"${on ? "" : ` opacity="0.75"`}>${g}</g>`;
  });
  out += toks;
  // the end condition, stamped once every chip is lit
  if (p.until) {
    const kU = allLit ? (at ? ph(s, 0.6, 0.45) : 1) : 0;
    if (kU > 0 || ghost) {
      const row = parseRow(normMath(p.until)), f = Math.max(36, Math.min(w * 0.032, (w * 0.5) / Math.max(0.01, measureRow(row, 1).w))), m = measureRow(row, f);
      const bw2 = m.w + f * 1.4, bh = f * 1.7, cy = layout === "ring" ? 0 : below + bh * 0.85, sc = kU > 0 ? 1 + 0.5 * (1 - backOut(kU)) : 1;
      out += `<g transform="translate(0,${f1(cy)}) rotate(-3) scale(${sc.toFixed(3)})" opacity="${(kU > 0 ? clamp01(kU * 2) : 0.35).toFixed(3)}">` +
        `<rect x="${f1(-bw2 / 2)}" y="${f1(-bh / 2)}" width="${f1(bw2)}" height="${f1(bh)}" rx="${f1(bh * 0.2)}" fill="#fff8e1" stroke="#c77700" stroke-width="${f1(sw)}" stroke-dasharray="${f1(sw * 2.5)} ${f1(sw * 1.2)}"/>` +
        renderRow(row, -m.w / 2, f * 0.35, f, "#8a4b00", "#8a4b00") + `</g>`;
    }
  }
  if (p.title) out = T(p.title, 0, Math.min(...pos.map((q) => q[1])) - ch / 2 - w * 0.04, fitT(p.title, w * 0.8, w * 0.034), INK, 800) + out;
  return out;
}

// ---------------------------------------------------------------- sorter: cards fly into labelled bins
function sorter(p) {
  const w = N(p.w, 1500), H = w * 0.6, s = stepS(p), col = p.color || "#2459a6";
  const bins = parts(p.bins ?? "A;B").filter(Boolean).slice(0, 4);
  if (!bins.length) bins.push("", "");
  const cards = parts(p.cards).filter(Boolean).slice(0, 16).map((c) => { const i = c.indexOf("|"); return i > 0 ? { short: c.slice(0, i).trim(), long: c.slice(i + 1).trim() } : { short: c, long: c }; });
  const ans = String(p.answers ?? "").split(",").map((v) => clampN(parseInt(v, 10) || 1, 1, bins.length));
  const wrong = {};
  for (const e of parts(String(p.wrong ?? "").replace(/,/g, ";"))) { const m = e.match(/^(\d+)\s*:\s*(\d+)$/); if (m) wrong[+m[1]] = clampN(+m[2], 1, bins.length); }
  const nb = bins.length, n = cards.length, at = clampN(Math.round(N(p.at, 0)), 0, n), marks = p.marks !== false;
  const bw = Math.min((w / nb) * 0.86, w * 0.42), binTop = H * 0.08, binBot = H * 0.46, band = H * 0.11;
  const bx = (b) => -w / 2 + (w / nb) * (b - 0.5);
  const per = bins.map(() => []);
  for (let i = 0; i < at; i++) per[(ans[i] || 1) - 1].push(i);
  const colsOf = (b) => (per[b].length > 3 ? 2 : 1), chH = H * 0.075;
  const slot = (b, j) => { const cols = colsOf(b), cwd = (bw * 0.9) / cols, c = cols === 2 ? j % 2 : 0, r = cols === 2 ? Math.floor(j / 2) : j;
    return { x: bx(b + 1) + (cols === 2 ? (c - 0.5) * cwd : 0), y: binBot - band - H * 0.02 - chH / 2 - r * (chH + H * 0.012), w: cwd * 0.94 }; };
  let out = "";
  // the bins (back walls first, their fronts with the label after the cards)
  bins.forEach((b, i) => { const x = bx(i + 1);
    out += `<path d="M${f1(x - bw / 2)} ${f1(binTop)} L${f1(x - bw / 2 + bw * 0.04)} ${f1(binBot)} L${f1(x + bw / 2 - bw * 0.04)} ${f1(binBot)} L${f1(x + bw / 2)} ${f1(binTop)} Z" fill="${tint(DIAGC[i % DIAGC.length])}" stroke="${shade(DIAGC[i % DIAGC.length], 0.8)}" stroke-width="${f1(w * 0.003)}"/>`; });
  const chip = (i, x, y, cwd, mk) => {
    const f = Math.min(H * 0.044, fitT(cards[i].short, cwd * (mk ? 0.72 : 0.88), H * 0.044));
    return chipBox(x, y, cwd, chH, "#ffffff", "#9aa5b1", w * 0.0025) + T(cards[i].short, x - (mk ? cwd * 0.08 : 0), y, f, INK, 800) +
      (mk ? `<g transform="translate(${f1(x + cwd / 2 - chH * 0.42)},${f1(y)})">${mark(mk, chH * 0.52, mk === "tick" ? "#2fa35b" : "#e5484d", 1)}</g>` : "");
  };
  // sorted cards (the newest one is in flight)
  const bigW = Math.min(w * 0.62, w * 0.9), bigH = H * 0.24, trayY = -H / 2 + H * 0.16;
  let flying = "";
  per.forEach((list, b) => list.forEach((i, j) => {
    const sl = slot(b, j);
    if (i !== at - 1 || s > 10) { out += chip(i, sl.x, sl.y, sl.w, marks ? "tick" : ""); return; }
    const wb = wrong[i + 1] && wrong[i + 1] !== b + 1 ? wrong[i + 1] - 1 : -1;
    const wsl = wb >= 0 ? slot(wb, per[wb].length) : null;
    const fly = (from, to, u) => { const e = ease(u), x = lerp(from.x, to.x, e), y = lerp(from.y, to.y, e) - Math.sin(Math.PI * e) * H * 0.12;
      const sc = lerp(from.w / bigW, to.w / bigW, e);
      return `<g transform="translate(${f1(x)},${f1(y)}) scale(${sc.toFixed(3)})">${bigCard(i)}</g>`; };
    const tray = { x: 0, y: trayY, w: bigW };
    if (wsl) {
      if (s < 0.7) flying = fly(tray, wsl, s / 0.7);
      else if (s < 1.3) flying = chip(i, wsl.x, wsl.y, wsl.w, "") + `<g transform="translate(${f1(wsl.x + wsl.w / 2 - chH * 0.42)},${f1(wsl.y)})">${mark("cross", chH * 0.5, "#e5484d", ph(s, 0.7, 0.3))}</g>`;
      else if (s < 2.0) flying = fly(wsl, sl, (s - 1.3) / 0.7);
      else out += chip(i, sl.x, sl.y, sl.w, "") + (marks ? `<g transform="translate(${f1(sl.x + sl.w / 2 - chH * 0.42)},${f1(sl.y)})">${mark("tick", chH * 0.52, "#2fa35b", ph(s, 2.0, 0.3))}</g>` : "");
    } else if (s < 0.7) flying = fly(tray, sl, s / 0.7);
    else out += chip(i, sl.x, sl.y, sl.w, "") + (marks ? `<g transform="translate(${f1(sl.x + sl.w / 2 - chH * 0.42)},${f1(sl.y)})">${mark("tick", chH * 0.52, "#2fa35b", ph(s, 0.7, 0.3))}</g>` : "");
  }));
  function bigCard(i) {
    const wr = wrap2(cards[i].long, bigW * 0.88, H * 0.06, 36);
    return chipBox(0, 0, bigW, bigH, "#ffffff", col, w * 0.004, bigH * 0.12) + `<rect x="${f1(-bigW / 2)}" y="${f1(-bigH / 2)}" width="${f1(w * 0.012)}" height="${f1(bigH)}" rx="${f1(w * 0.006)}" fill="${col}"/>` + linesSvg(wr, 0, 0, INK, 800);
  }
  // the bin fronts and their labels
  bins.forEach((b, i) => { const x = bx(i + 1), c = DIAGC[i % DIAGC.length];
    out += `<rect x="${f1(x - bw / 2 + bw * 0.035)}" y="${f1(binBot - band)}" width="${f1(bw * 0.93)}" height="${f1(band)}" rx="${f1(band * 0.18)}" fill="${c}"/>` +
      T(b, x, binBot - band / 2, fitT(b, bw * 0.86, H * 0.065), "#ffffff", 800); });
  // the waiting card (the next to sort) with the rest of the deck behind it
  if (at < n) {
    const left = n - at - 1, kN = at > 0 ? ph(s, 0.25, 0.4) : 1;
    for (let d = Math.min(2, left); d >= 1; d--) out += `<rect x="${f1(-bigW / 2 + d * w * 0.008)}" y="${f1(trayY - bigH / 2 - d * w * 0.008)}" width="${f1(bigW)}" height="${f1(bigH)}" rx="${f1(bigH * 0.12)}" fill="#f1f4f8" stroke="#c3cad3" stroke-width="${f1(w * 0.0025)}"/>`;
    out += `<g transform="translate(0,${f1(trayY)})" opacity="${kN.toFixed(3)}">${bigCard(at)}</g>`;
  }
  out += flying;
  if (p.title) out = T(p.title, 0, -H / 2 - H * 0.04, fitT(p.title, w * 0.8, H * 0.06), INK, 800) + out;
  return out;
}
const DIAGC = ["#2459a6", "#e07b24", "#2fa35b", "#7b61ff"];

// ---------------------------------------------------------------- spectrum: pins between two poles, or a pendulum
function mixHex(a, b, u) {
  const pa = parseInt(String(a).slice(1), 16), pb = parseInt(String(b).slice(1), 16);
  if (!Number.isFinite(pa) || !Number.isFinite(pb)) return a;
  const c = (sh) => Math.round(((pa >> sh) & 255) * (1 - u) + ((pb >> sh) & 255) * u);
  return `#${((c(16) << 16) | (c(8) << 8) | c(0)).toString(16).padStart(6, "0")}`;
}
function pinList(spec) {
  return parts(spec).filter(Boolean).slice(0, 14).map((e) => { const i = e.lastIndexOf(":");
    return i > 0 ? { name: e.slice(0, i).trim(), v: N(e.slice(i + 1).trim(), NaN) } : { name: e.trim(), v: NaN }; });
}
function tiers(items, gap, max) {
  const ends = [];
  [...items].sort((a, b) => a.a - b.a).forEach((it) => {
    let t = 0;
    while (t < ends.length && it.a < ends[t] + gap) t++;
    it.tier = Math.min(t, max - 1);
    ends[it.tier] = Math.max(ends[it.tier] ?? -Infinity, it.b);
  });
  return Math.max(1, ends.length);
}
function spectrum(p) {
  const w = N(p.w, 1600), s = stepS(p), t = timeT(p);
  const lcol = p.leftColor || "#e07b24", rcol = p.rightColor || "#2459a6";
  if (p.look === "pendulum") return pendulum(p, w, s, t, lcol, rcol);
  const lo = N(p.min, 0), hi = N(p.max, 1) > lo ? N(p.max, 1) : lo + 1;
  const x0 = -w * 0.44, x1 = w * 0.44, X = (v) => x0 + clamp01((v - lo) / (hi - lo)) * (x1 - x0), bh = w * 0.032;
  let out = "";
  for (let i = 0; i < 16; i++) { const a = x0 + ((x1 - x0) * i) / 16;
    out += `<rect x="${f1(a - 0.5)}" y="${f1(-bh / 2)}" width="${f1((x1 - x0) / 16 + 1)}" height="${f1(bh)}" fill="${mixHex(lcol, rcol, (i + 0.5) / 16)}"/>`; }
  out += `<rect x="${f1(x0)}" y="${f1(-bh / 2)}" width="${f1(x1 - x0)}" height="${f1(bh)}" rx="${f1(bh * 0.3)}" fill="none" stroke="${INK}" stroke-width="${f1(w * 0.002)}" opacity="0.35"/>`;
  const fe = w * 0.03;
  if (p.left) out += T(p.left, x0, bh / 2 + fe * 0.95, fitT(p.left, w * 0.42, fe), shade(lcol, 0.7), 800, "start");
  if (p.right) out += T(p.right, x1, bh / 2 + fe * 0.95, fitT(p.right, w * 0.42, fe), shade(rcol, 0.7), 800, "end");
  const P1 = pinList(p.pins), P2 = {};
  pinList(p.pins2).forEach((q) => { if (Number.isFinite(q.v)) P2[q.name] = q.v; });
  const two = String(p.state) === "2", u = two ? ease(s / N(p.glide, 1.4)) : 0, has2 = Object.keys(P2).length > 0;
  const upto = Math.max(0, Math.round(N(p.upto, 0))), shown = upto ? Math.min(upto, P1.length) : P1.length, glow = idxSet(p.glow);
  const fs = w * 0.026, chH = fs * 1.5;
  const items = P1.slice(0, shown).map((q, i) => {
    const xa = Number.isFinite(q.v) ? X(q.v) : 0, xb = has2 && P2[q.name] !== undefined ? X(P2[q.name]) : xa;
    const f = Math.min(fs, fitT(q.name, w * 0.2, fs)), cw = tw(q.name, f) + f * 0.9;
    return { i, name: q.name, f, cw, x: lerp(xa, xb, u), a: Math.min(xa, xb) - cw / 2, b: Math.max(xa, xb) + cw / 2 };
  });
  const nt = tiers(items, w * 0.01, 5);
  let top = -bh / 2 - w * 0.08;
  items.forEach((it) => {
    const ty = -bh / 2 - w * 0.075 - it.tier * chH * 1.3, hot = glow.has(it.i + 1), isNew = upto && it.i === shown - 1;
    const k = isNew ? ph(s, 0, 0.45) : 1, dy = -(1 - backOut(k)) * w * 0.05, pinY = -bh / 2 - w * 0.016, c = hot ? "#e5484d" : INK;
    const cx = clampN(it.x, x0 + it.cw / 2 - w * 0.04, x1 - it.cw / 2 + w * 0.04);
    out += `<g transform="translate(0,${f1(dy)})" opacity="${clamp01(k * 2).toFixed(3)}">` +
      `<path d="M${f1(it.x)} ${f1(ty + chH / 2)} L${f1(it.x)} ${f1(pinY - w * 0.012)}" stroke="#7a8594" stroke-width="${f1(w * 0.0025)}"/>` +
      `<path d="M${f1(it.x)} ${f1(-bh / 2 + w * 0.002)} L${f1(it.x - w * 0.009)} ${f1(pinY - w * 0.004)} A${f1(w * 0.012)} ${f1(w * 0.012)} 0 1 1 ${f1(it.x + w * 0.009)} ${f1(pinY - w * 0.004)} Z" fill="${c}"/>` +
      `<circle cx="${f1(it.x)}" cy="${f1(pinY - w * 0.012)}" r="${f1(w * 0.0045)}" fill="#ffffff"/>` +
      chipBox(cx, ty, it.cw, chH, hot ? "#fff1b8" : "#ffffff", hot ? "#f2c14e" : "#9aa5b1", w * (hot ? 0.004 : 0.0022)) + T(it.name, cx, ty, it.f, INK, 800) + `</g>`;
    top = Math.min(top, ty - chH / 2);
  });
  const date = two ? (ph(s, 0, 0.5) < 0.5 ? p.date : p.date2) : p.date;
  let ttl = top - w * 0.045;
  if (date) {
    const f = Math.min(w * 0.034, fitT(date, w * 0.26, w * 0.034)), cw = tw(date, f) + f * 1.1, sq = two ? Math.abs(Math.cos(Math.PI * ph(s, 0, 0.5))) : 1;
    out += `<g transform="translate(${f1(x1 - cw / 2)},${f1(ttl)}) scale(1,${Math.max(0.02, sq).toFixed(3)})">${chipBox(0, 0, cw, f * 1.5, INK, INK, 1)}${T(date, 0, 0, f, "#ffffff", 800)}</g>`;
  }
  if (p.title) out += T(p.title, date ? -w * 0.12 : 0, ttl, fitT(p.title, w * (date ? 0.6 : 0.88), w * 0.036), INK, 800);
  return out;
}
function pendulum(p, w, s, t, lcol, rcol) {
  const pivY = -w * 0.17, R = w * 0.3, maxA = (36 * Math.PI) / 180, br = w * 0.04;
  const at = clampN(N(p.at, 0), -1, 1), pos = settle(isNum(p.atFrom) ? clampN(+p.atFrom, -1, 1) : at, at, s, N(p.glide, 1.4));
  const a = pos * maxA, bx = R * Math.sin(a), by = pivY + R * Math.cos(a);
  const arc = Array.from({ length: 25 }, (_, k) => { const aa = -(maxA + 0.07) + ((2 * (maxA + 0.07)) * k) / 24, rr = R + w * 0.03;
    return `${k ? "L" : "M"}${f1(rr * Math.sin(aa))} ${f1(pivY + rr * Math.cos(aa))}`; }).join(" ");      // points, so the box is the arc's own
  let out = `<path d="${arc}" fill="none" stroke="#c3cad3" stroke-width="${f1(w * 0.004)}" stroke-dasharray="${f1(w * 0.01)} ${f1(w * 0.008)}"/>`;
  pinList(p.pins).forEach((q) => { if (!Number.isFinite(q.v)) return; const aa = clampN(q.v, -1, 1) * maxA, rr = R + w * 0.03;
    const mx = rr * Math.sin(aa), my = pivY + rr * Math.cos(aa), f = Math.min(w * 0.022, fitT(q.name, w * 0.14, w * 0.022));
    out += `<circle cx="${f1(mx)}" cy="${f1(my)}" r="${f1(w * 0.007)}" fill="#7a8594"/>` + T(q.name, mx + Math.sin(aa) * w * 0.02, my + w * 0.03, f, "#4a5568", 700); });
  // the clock face the pendulum hangs from
  out += `<circle cx="0" cy="${f1(pivY - w * 0.02)}" r="${f1(w * 0.06)}" fill="#fffaf0" stroke="#a8763f" stroke-width="${f1(w * 0.008)}"/>`;
  for (let k = 0; k < 12; k++) { const aa = (k * Math.PI) / 6, r0 = w * 0.047, r1 = w * (k % 3 ? 0.052 : 0.056);
    out += `<path d="M${f1(Math.sin(aa) * r0)} ${f1(pivY - w * 0.02 - Math.cos(aa) * r0)} L${f1(Math.sin(aa) * r1)} ${f1(pivY - w * 0.02 - Math.cos(aa) * r1)}" stroke="#5a4028" stroke-width="${f1(w * 0.003)}"/>`; }
  out += `<path d="M0 ${f1(pivY - w * 0.02)} L0 ${f1(pivY - w * 0.055)} M0 ${f1(pivY - w * 0.02)} L${f1(w * 0.026)} ${f1(pivY - w * 0.02)}" stroke="#2d3748" stroke-width="${f1(w * 0.005)}" stroke-linecap="round"/>` +
    `<path d="M0 ${f1(pivY)} L${f1(bx)} ${f1(by)}" stroke="#7a5a3a" stroke-width="${f1(w * 0.008)}" stroke-linecap="round"/>` +
    `<circle cx="${f1(bx)}" cy="${f1(by)}" r="${f1(br)}" fill="${mixHex(lcol, rcol, (pos + 1) / 2)}" stroke="${shade(mixHex(lcol, rcol, (pos + 1) / 2), 0.7)}" stroke-width="${f1(w * 0.005)}"/>` +
    `<circle cx="${f1(bx - br * 0.35)}" cy="${f1(by - br * 0.35)}" r="${f1(br * 0.22)}" fill="#ffffff" opacity="0.6"/><circle cx="0" cy="${f1(pivY)}" r="${f1(w * 0.01)}" fill="#2d3748"/>`;
  const ey = pivY + R + br + w * 0.045, fe = w * 0.028;
  [[-1, p.left, lcol, p.leftNote], [1, p.right, rcol, p.rightNote]].forEach(([d, lab, c, note]) => {
    const ex = d * R * Math.sin(maxA);
    if (lab) { const wr = wrap2(lab, w * 0.26, fe), hh = wr.lines.length * wr.fs * 1.18 + wr.fs * 0.5, cw = Math.max(...wr.lines.map((l) => tw(l, wr.fs))) + wr.fs;
      out += chipBox(ex, ey, cw, hh, tint(c), c, w * 0.004) + linesSvg(wr, ex, ey, shade(c, 0.6), 800); }
    if (note && d * pos > 0.6) { const f = Math.min(w * 0.024, fitT(note, w * 0.2, w * 0.024)), nx = d * w * 0.36, ny = pivY + R * 0.35, fl = 0.6 + 0.4 * Math.abs(Math.sin(t * 4));
      let star = "";
      for (let k = 0; k < 16; k++) { const aa = (k * Math.PI) / 8, rr = k % 2 ? w * 0.05 : w * 0.085; star += `${k ? "L" : "M"}${f1(nx + Math.cos(aa) * rr * 1.35)} ${f1(ny + Math.sin(aa) * rr * 0.7)} `; }
      out += `<g opacity="${fl.toFixed(3)}"><path d="${star}Z" fill="#f2c14e" stroke="#c77700" stroke-width="${f1(w * 0.003)}"/></g>` + T(note, nx, ny, f, "#5a3200", 800); }
  });
  if (p.era) { const f = Math.min(w * 0.032, fitT(p.era, w * 0.4, w * 0.032)), cw = tw(p.era, f) + f * 1.1;
    out += chipBox(0, pivY - w * 0.115, cw, f * 1.5, INK, INK, 1) + T(p.era, 0, pivY - w * 0.115, f, "#ffffff", 800); }
  if (p.title) out += T(p.title, 0, pivY - w * (p.era ? 0.18 : 0.115), fitT(p.title, w * 0.8, w * 0.034), INK, 800);
  return out;
}

// ---------------------------------------------------------------- padlocks: ceteris paribus tags
function lockSvg(L, lift, rot, open) {
  const shk = `<path d="M${f1(-L * 0.24)} ${f1(-L * 0.1)} L${f1(-L * 0.24)} ${f1(-L * 0.36)} A${f1(L * 0.24)} ${f1(L * 0.24)} 0 0 1 ${f1(L * 0.24)} ${f1(-L * 0.36)} L${f1(L * 0.24)} ${f1(-L * 0.1)}" fill="none" stroke="#8d99a6" stroke-width="${f1(L * 0.11)}" stroke-linecap="round"/>`;
  return `<g transform="translate(0,${f1(-lift)}) rotate(${rot.toFixed(1)} ${f1(L * 0.24)} ${f1(-L * 0.1)})">${shk}</g>` +
    `<rect x="${f1(-L * 0.4)}" y="${f1(-L * 0.16)}" width="${f1(L * 0.8)}" height="${f1(L * 0.62)}" rx="${f1(L * 0.12)}" fill="${open ? "#f6d77a" : "#e6b422"}" stroke="#a7862d" stroke-width="${f1(L * 0.05)}"/>` +
    `<circle cx="0" cy="${f1(L * 0.1)}" r="${f1(L * 0.08)}" fill="#5a4636"/><rect x="${f1(-L * 0.035)}" y="${f1(L * 0.12)}" width="${f1(L * 0.07)}" height="${f1(L * 0.16)}" fill="#5a4636"/>`;
}
function padlocks(p) {
  const w = N(p.w, 1500), s = stepS(p), col = p.color || "#2459a6";
  const labels = parts(p.labels ?? "A;B;C").filter(Boolean).slice(0, 9);
  if (!labels.length) labels.push("");
  const n = labels.length, cols = Math.max(1, Math.min(n, Math.round(N(p.cols, 0)) || (n <= 3 ? n : n === 4 ? 2 : 3))), rows = Math.ceil(n / cols);
  const cellW = w / cols, tagW = cellW * 0.82, tagH = Math.min(tagW * 0.34, w * 0.1), rowH = tagH * 1.7, Ls = tagH * 0.78;
  const open = idxSet(p.open), glow = idxSet(p.glow);
  let out = "";
  labels.forEach((lab, i) => {
    const r = Math.floor(i / cols), c = i % cols, inRow = Math.min(cols, n - r * cols);
    const cx = -((inRow - 1) / 2) * cellW + c * cellW, cy = (r - (rows - 1) / 2) * rowH;
    const isOpen = open.has(i + 1), hot = glow.has(i + 1), u = hot ? s / 0.9 : 99;
    const lockX = cx - tagW / 2 + Ls * 0.42, xa = cx - tagW / 2 + Ls * 0.95, xb = cx + tagW / 2, hole = xa + tagH * 0.28;
    const lift = isOpen ? Ls * 0.32 * (hot ? backOut(ph(s, 0, 0.35)) : 1) : hot ? Ls * 0.32 * (1 - ease(ph(s, 0, 0.25))) * (s < 0.25 ? 1 : 0) : 0;
    const rotS = isOpen ? -28 * (hot ? ease(ph(s, 0.1, 0.35)) : 1) : 0;
    const swing = isOpen ? 5 + (hot ? 9 * Math.exp(-3 * u) * Math.sin(u * 9) : 0) : 0;
    const fill = isOpen ? tint(col) : "#eef1f5", stroke = isOpen ? col : "#9aa5b1";
    const tag = `<path d="M${f1(xa)} ${f1(cy - tagH * 0.2)} L${f1(xa + tagH * 0.3)} ${f1(cy - tagH / 2)} L${f1(xb - tagH * 0.12)} ${f1(cy - tagH / 2)} Q${f1(xb)} ${f1(cy - tagH / 2)} ${f1(xb)} ${f1(cy - tagH * 0.38)} L${f1(xb)} ${f1(cy + tagH * 0.38)} Q${f1(xb)} ${f1(cy + tagH / 2)} ${f1(xb - tagH * 0.12)} ${f1(cy + tagH / 2)} L${f1(xa + tagH * 0.3)} ${f1(cy + tagH / 2)} L${f1(xa)} ${f1(cy + tagH * 0.2)} Z" fill="${fill}" stroke="${stroke}" stroke-width="${f1(w * 0.003)}"/>` +
      `<circle cx="${f1(hole)}" cy="${f1(cy)}" r="${f1(tagH * 0.09)}" fill="#ffffff" stroke="${stroke}" stroke-width="${f1(w * 0.002)}"/>` +
      linesSvg(wrap2(lab, (xb - tagH * 0.15) - (hole + tagH * 0.18), tagH * 0.38, 36), (hole + tagH * 0.18 + xb - tagH * 0.15) / 2, cy, isOpen ? INK : "#4a5568", 800);
    out += (hot ? `<rect x="${f1(xa - tagH * 0.12)}" y="${f1(cy - tagH * 0.66)}" width="${f1(xb - xa + tagH * 0.24)}" height="${f1(tagH * 1.32)}" rx="${f1(tagH * 0.2)}" fill="#fff1b8" stroke="#f2c14e" stroke-width="${f1(w * 0.004)}"/>` : "") +
      `<path d="M${f1(lockX + Ls * 0.24)} ${f1(cy - Ls * 0.1)} Q${f1((lockX + hole) / 2)} ${f1(cy - tagH * 0.05)} ${f1(hole)} ${f1(cy)}" fill="none" stroke="#7a838f" stroke-width="${f1(w * 0.003)}"/>` +
      `<g transform="rotate(${swing.toFixed(2)} ${f1(hole)} ${f1(cy)})">${tag}</g>` +
      `<g transform="translate(${f1(lockX)},${f1(cy)})">${lockSvg(Ls, lift, rotS, isOpen)}</g>`;
  });
  if (p.title) out = T(p.title, 0, -((rows - 1) / 2) * rowH - tagH * 1.05, fitT(p.title, w * 0.8, w * 0.034), INK, 800) + out;
  return out;
}

// ---------------------------------------------------------------- tugOfWar: two teams over a share
function tugOfWar(p) {
  const w = N(p.w, 1500), s = stepS(p), t = timeT(p), lc = p.leftColor || "#e07b24", rc = p.rightColor || "#2459a6";
  const share = clamp01(N(p.share, 0.5)), sh = settle(isNum(p.shareFrom) ? clamp01(+p.shareFrom) : share, share, s, N(p.glide, 1));
  const dx = -(sh - 0.5) * w * 0.8, pull = ["left", "right", "both"].includes(p.pull) ? p.pull : "";
  const jerk = pull ? Math.sin(Math.PI * ph(s, 0, 0.9)) : 0, ropeY = -w * 0.15;
  let out = `<path d="M0 ${f1(-w * 0.012)} L0 ${f1(w * 0.012)}" stroke="#7a8594" stroke-width="${f1(w * 0.004)}"/><path d="M${f1(-w * 0.48)} 0 L${f1(w * 0.48)} 0" stroke="#c9b892" stroke-width="${f1(w * 0.004)}"/>`;
  out += `<path d="M0 ${f1(-w * 0.03)} L0 ${f1(-w * 0.11)}" stroke="#7a8594" stroke-width="${f1(w * 0.003)}" stroke-dasharray="${f1(w * 0.008)} ${f1(w * 0.006)}"/>`;
  out += `<path d="M${f1(dx - w * 0.43)} ${f1(ropeY)} L${f1(dx + w * 0.43)} ${f1(ropeY)}" stroke="#8a5a2b" stroke-width="${f1(w * 0.012)}" stroke-linecap="round"/>` +
    `<path d="M${f1(dx - w * 0.43)} ${f1(ropeY)} L${f1(dx + w * 0.43)} ${f1(ropeY)}" stroke="#c9965a" stroke-width="${f1(w * 0.004)}" stroke-dasharray="${f1(w * 0.012)} ${f1(w * 0.01)}"/>` +
    `<path d="M${f1(dx)} ${f1(ropeY)} L${f1(dx - w * 0.012)} ${f1(ropeY + w * 0.05)} L${f1(dx + w * 0.012)} ${f1(ropeY + w * 0.05)} Z" fill="#e5484d"/>`;
  [[-1, lc, p.left, "left"], [1, rc, p.right, "right"]].forEach(([d, c, name, side]) => {
    for (let j = 2; j >= 0; j--) {
      const fx = dx + d * w * (0.15 + 0.1 * j), lean = (16 + (pull === side || pull === "both" ? 13 * jerk : 0) + 1.5 * Math.sin(t * 2.2 + j * 1.3)) * d;
      const r = (lean * Math.PI) / 180, sx = fx + Math.sin(r) * w * 0.15, sy = -Math.cos(r) * w * 0.15;
      out += `<path d="M${f1(sx)} ${f1(sy)} L${f1(fx - d * w * 0.055)} ${f1(ropeY)}" stroke="${shade(c, 0.8)}" stroke-width="${f1(w * 0.014)}" stroke-linecap="round"/>` +
        `<g transform="rotate(${lean.toFixed(2)} ${f1(fx)} 0)">` +
        `<path d="M${f1(fx - w * 0.014)} 0 L${f1(fx)} ${f1(-w * 0.075)} L${f1(fx + w * 0.02)} 0" fill="none" stroke="${shade(c, 0.6)}" stroke-width="${f1(w * 0.013)}" stroke-linecap="round" stroke-linejoin="round"/>` +
        `<rect x="${f1(fx - w * 0.022)}" y="${f1(-w * 0.165)}" width="${f1(w * 0.044)}" height="${f1(w * 0.095)}" rx="${f1(w * 0.02)}" fill="${c}"/>` +
        `<circle cx="${f1(fx)}" cy="${f1(-w * 0.19)}" r="${f1(w * 0.022)}" fill="#f1c9a5" stroke="${shade(c, 0.7)}" stroke-width="${f1(w * 0.003)}"/></g>`;
    }
    if (name) out += T(name, dx + d * w * 0.25, w * 0.035, fitT(name, w * 0.3, w * 0.032), shade(c, 0.65), 800);
  });
  // the share bar above
  const by = -w * 0.44, bw = w * 0.8, bh = w * 0.05, cut = -bw / 2 + bw * sh;
  out += `<rect x="${f1(-bw / 2)}" y="${f1(by - bh / 2)}" width="${f1(cut + bw / 2)}" height="${f1(bh)}" fill="${lc}"/><rect x="${f1(cut)}" y="${f1(by - bh / 2)}" width="${f1(bw / 2 - cut)}" height="${f1(bh)}" fill="${rc}"/>` +
    `<rect x="${f1(-bw / 2)}" y="${f1(by - bh / 2)}" width="${f1(bw)}" height="${f1(bh)}" rx="${f1(bh * 0.2)}" fill="none" stroke="${INK}" stroke-width="${f1(w * 0.002)}"/>` +
    `<path d="M0 ${f1(by - bh * 0.75)} L0 ${f1(by + bh * 0.75)}" stroke="${INK}" stroke-width="${f1(w * 0.003)}" stroke-dasharray="${f1(w * 0.006)} ${f1(w * 0.004)}"/>`;
  const pl = `${Math.round(sh * 100)}%`, pr = `${100 - Math.round(sh * 100)}%`, fb = bh * 0.62;
  // shareNumbers: false hides the two % numbers (a story where the split is not a number, Sloman workers Nov 2026)
  const nums = p.shareNumbers !== false && p.shareNumbers !== "false";
  if (nums && cut + bw / 2 > tw(pl, fb) + fb) out += T(pl, (-bw / 2 + cut) / 2, by, fb, "#ffffff", 800);
  if (nums && bw / 2 - cut > tw(pr, fb) + fb) out += T(pr, (cut + bw / 2) / 2, by, fb, "#ffffff", 800);
  if (p.shareLabel) out += T(p.shareLabel, 0, by - bh * 1.15, fitT(p.shareLabel, w * 0.7, w * 0.03), INK, 800);
  // the price tag that climbs one notch a round
  const prices = parts(p.prices).filter(Boolean), rounds = Math.max(0, Math.round(N(p.rounds, 0)));
  if (rounds > 0 || prices.length) {
    const nN = Math.max(3, rounds, prices.length), y0 = ropeY - w * 0.07, y1 = -w * 0.37, step = (y0 - y1) / nN;
    const rv = settle(Math.max(0, rounds - 1), rounds, s, 0.8), ty = y0 - rv * step;
    out += `<path d="M${f1(-w * 0.13)} ${f1(y0 + w * 0.01)} L${f1(-w * 0.13)} ${f1(y1)}" stroke="#7a8594" stroke-width="${f1(w * 0.005)}"/>`;
    for (let k = 0; k <= nN; k++) out += `<path d="M${f1(-w * 0.14)} ${f1(y0 - k * step)} L${f1(-w * 0.12)} ${f1(y0 - k * step)}" stroke="#7a8594" stroke-width="${f1(w * 0.004)}"/>`;
    const txt = rounds > 0 ? prices[Math.min(rounds, prices.length) - 1] || p.tag || "" : p.tag || "";
    if (txt) { const f = Math.min(w * 0.03, fitT(txt, w * 0.2, w * 0.03)), tw2 = tw(txt, f) + f * 1.4, th2 = f * 1.5, x = -w * 0.115;
      out += `<path d="M${f1(x)} ${f1(ty)} L${f1(x + th2 * 0.45)} ${f1(ty - th2 / 2)} L${f1(x + tw2)} ${f1(ty - th2 / 2)} L${f1(x + tw2)} ${f1(ty + th2 / 2)} L${f1(x + th2 * 0.45)} ${f1(ty + th2 / 2)} Z" fill="#fff3c4" stroke="#c77700" stroke-width="${f1(w * 0.003)}"/>` +
        `<circle cx="${f1(x + th2 * 0.42)}" cy="${f1(ty)}" r="${f1(th2 * 0.1)}" fill="#c77700"/>` + T(txt, x + th2 * 0.45 + (tw2 - th2 * 0.45) / 2, ty, f, "#5a3200", 800); }
    if (p.tag && rounds > 0 && prices.length) out += T(p.tag, -w * 0.13, y1 - w * 0.025, fitT(p.tag, w * 0.2, w * 0.028), "#5a3200", 800);
  }
  return out;
}

// ---------------------------------------------------------------- oneVsAll: one actor against everyone doing it
function resultTag(text, dir, x, y, width, fs) {
  const wr = wrap2(text, width * 0.72, fs), r = fs * 0.75, cw = Math.max(...wr.lines.map((l) => tw(l, wr.fs))) + wr.fs * 1.1, hh = wr.lines.length * wr.fs * 1.2 + wr.fs * 0.5;
  const c = dir === "up" ? "#2fa35b" : dir === "down" ? "#e5484d" : "#7a8594";
  return chipBox(x + r * 0.6 + cw / 2, y, cw, hh, tint(c), c, fs * 0.08) + linesSvg(wr, x + r * 0.6 + cw / 2, y, shade(c, 0.6), 800) + upDownBadge(dir || "eq", r, x, y, 1);
}
function oneVsAll(p) {
  const w = N(p.w, 1600), s = stepS(p), stage = clampN(Math.round(N(p.stage, 2)), 0, 2), col = p.color || "#2459a6", ac = "#e07b24";
  const PW = w * 0.47, PH = w * 0.44, fs = w * 0.028, floor = PH * 0.3;
  let out = "";
  [[-1, p.leftTitle], [1, p.rightTitle]].forEach(([d, title]) => {
    const cx = d * w * 0.25;
    out += `<rect x="${f1(cx - PW / 2)}" y="${f1(-PH / 2)}" width="${f1(PW)}" height="${f1(PH)}" rx="${f1(w * 0.02)}" fill="${d < 0 ? "#f7f9fc" : "#fbf8f3"}" stroke="#c3cad3" stroke-width="${f1(w * 0.003)}"/>` +
      `<path d="M${f1(cx - PW * 0.46)} ${f1(floor)} L${f1(cx + PW * 0.46)} ${f1(floor)}" stroke="#d5dbe1" stroke-width="${f1(w * 0.003)}"/>`;
    if (title) out += T(title, cx, -PH / 2 + fs * 1.1, fitT(title, PW * 0.9, fs * 1.15), INK, 800);
  });
  const oneDir = dirOf(p.oneDir), allDir = dirOf(p.allDir);
  // left: the one
  const lx = -w * 0.25 - PW * 0.2, fh = PH * 0.4;
  out += `<g transform="translate(${f1(lx)},${f1(floor)})">${figure(fh, stage >= 1 ? ac : col)}</g>`;
  if (p.actor) out += T(p.actor, lx, floor + fs * 1.0, fitT(p.actor, PW * 0.4, fs), INK, 800);
  const actChip = (x, y, k) => { if (!p.action || k <= 0) return ""; const wr = wrap2(p.action, PW * 0.42, fs), cw = Math.max(...wr.lines.map((l) => tw(l, wr.fs))) + wr.fs, hh = wr.lines.length * wr.fs * 1.2 + wr.fs * 0.5;
    return `<g transform="translate(${f1(x)},${f1(y)}) scale(${backOut(k).toFixed(3)})">${chipBox(0, 0, cw, hh, "#fff3e0", ac, w * 0.003)}${linesSvg(wr, 0, 0, "#7a3d00", 800)}</g>`; };
  if (stage >= 1) {
    out += actChip(lx, floor - fh - fs * 1.4, stage === 1 ? ph(s, 0, 0.4) : 1);
    const k = stage === 1 ? ease(ph(s, 0.5, 0.4)) : 1;
    if (p.oneResult && k > 0) out += `<g opacity="${k.toFixed(3)}" transform="translate(${f1((1 - k) * w * 0.03)},0)">${resultTag(p.oneResult, oneDir, -w * 0.25 + PW * 0.02, -PH * 0.02, PW * 0.46, fs)}</g>`;
  }
  // right: the crowd
  const n = clampN(Math.round(N(p.n, 12)), 2, 30), cols = Math.min(6, Math.ceil(Math.sqrt(n * 1.6))), rows = Math.ceil(n / cols);
  const areaW = PW * 0.46, cxR = w * 0.25 - PW * 0.24, gh = Math.min(PH * 0.3, (areaW / cols) * 1.5), dxp = areaW / cols;
  for (let i = n - 1; i >= 0; i--) {
    const r = Math.floor(i / cols), c = i % cols, x = cxR - areaW / 2 + dxp * (c + 0.5) + (r % 2 ? dxp * 0.25 : 0), y = floor - r * gh * 0.5;
    const on = stage >= 2 ? ph(s, 0.06 * i, 0.3) : 0;
    out += `<g transform="translate(${f1(x)},${f1(y)})">${figure(gh * (1 - r * 0.06), mixHex(col, ac, on))}</g>`;
  }
  if (p.total) out += T(p.total, w * 0.25 + PW * 0.2, -PH * 0.2, fitT(p.total, PW * 0.42, fs), "#4a5568", 800);
  if (stage >= 2) {
    out += actChip(cxR, floor - gh * (0.5 * (rows - 1) + 1) - fs * 1.3, ph(s, 0.2, 0.4));
    const k = ph(s, 0.8, 0.4), flips = oneDir && allDir && oneDir !== allDir && !!p.oneResult;
    if (k > 0 && (p.allResult || flips)) {
      const fk = flips ? ph(s, 1.4, 0.5) : 1, sx = flips ? Math.max(0.02, Math.abs(Math.cos(Math.PI * fk))) : 1;
      const [txt, dd] = flips && fk < 0.5 ? [p.oneResult, oneDir] : [p.allResult || "", allDir];
      const x0 = w * 0.25 + PW * 0.02;
      out += `<g opacity="${clamp01(k * 2).toFixed(3)}" transform="translate(${f1(x0 + PW * 0.2)},${f1(-PH * 0.02)}) scale(${sx.toFixed(3)},1) translate(${f1(-(x0 + PW * 0.2))},${f1(PH * 0.02)})">${resultTag(txt, dd, x0, -PH * 0.02, PW * 0.46, fs)}</g>`;
    }
  }
  if (p.title) out = T(p.title, 0, -PH / 2 - fs * 1.2, fitT(p.title, w * 0.9, fs * 1.25), INK, 800) + out;
  return out;
}

// ---------------------------------------------------------------- tAccount: a balance sheet that stays balanced
function ledgerRows(spec) {
  return parts(spec).filter(Boolean).slice(0, 10).map((e) => { const i = e.lastIndexOf(":");
    return i > 0 ? { label: e.slice(0, i).trim(), amt: e.slice(i + 1).trim() } : { label: e.trim(), amt: "" }; });
}
function tAccount(p) {
  const w = N(p.w, 1400), s = stepS(p), acc = p.color || "#e07b24";
  const L = ledgerRows(p.left), R = ledgerRows(p.right);
  let order = String(p.order ?? "").split(",").map((q) => q.trim().toUpperCase()).filter((q) => /^[LR]\d+$/.test(q));
  if (!order.length) for (let i = 0; i < Math.max(L.length, R.length); i++) { if (i < L.length) order.push(`L${i + 1}`); if (i < R.length) order.push(`R${i + 1}`); }
  const upto = Math.max(0, Math.round(N(p.upto, 0))), shown = new Set(upto ? order.slice(0, upto) : [...order, ...L.map((_, i) => `L${i + 1}`), ...R.map((_, i) => `R${i + 1}`)]);
  const newest = upto && upto <= order.length ? order[upto - 1] : "", kNew = ph(s, 0, 0.5);
  const glow = new Set(String(p.glow ?? "").split(",").map((q) => q.trim().toUpperCase()).filter(Boolean));
  const was = {};
  for (const e of parts(p.was)) { const m = e.match(/^([LR]\d+)\s*:\s*(.+)$/i); if (m) was[m[1].toUpperCase()] = m[2].trim(); }
  const sum = (rows, side) => rows.reduce((a, r, i) => a + (shown.has(`${side}${i + 1}`) ? firstNum(r.amt) || 0 : 0), 0);
  const left = L.map((r, i) => ({ ...r, key: `L${i + 1}` }));
  if (p.net === true) { const v = sum(R, "R") - sum(L, "L"); left.push({ label: p.netLabel || "", amt: fmtNum(v, groupOf([...L, ...R].map((r) => r.amt))), key: "NET", net: v }); }
  const right = R.map((r, i) => ({ ...r, key: `R${i + 1}` }));
  const grp = groupOf([...L, ...R].map((r) => r.amt));
  const pageW = w * 0.47, rowH = w * 0.062, fs = w * 0.028, headH = rowH * 1.1, nRows = Math.max(1, left.length, right.length), totals = p.totals !== false;
  const pageH = headH + nRows * rowH + (totals ? rowH * 1.25 : 0) + rowH * 0.25;
  const y0 = -pageH / 2, pad = w * 0.016;
  let out = "";
  [[-1, p.leftHead, left, "L"], [1, p.rightHead, right, "R"]].forEach(([d, head, rows, side]) => {
    const px = d < 0 ? -w * 0.49 : w * 0.02, hc = d < 0 ? "#c0563f" : "#2459a6";
    out += `<rect x="${f1(px)}" y="${f1(y0)}" width="${f1(pageW)}" height="${f1(pageH)}" rx="${f1(w * 0.01)}" fill="#fffdf7" stroke="#c9bfa8" stroke-width="${f1(w * 0.003)}"/>` +
      `<rect x="${f1(px)}" y="${f1(y0)}" width="${f1(pageW)}" height="${f1(headH)}" rx="${f1(w * 0.01)}" fill="${hc}"/>` +
      (head ? T(head, px + pageW / 2, y0 + headH / 2, fitT(head, pageW * 0.9, fs * 1.1), "#ffffff", 800) : "");
    for (let i = 1; i < nRows; i++) out += `<path d="M${f1(px + pad)} ${f1(y0 + headH + i * rowH)} L${f1(px + pageW - pad)} ${f1(y0 + headH + i * rowH)}" stroke="#ece4d2" stroke-width="${f1(w * 0.0018)}"/>`;
    rows.forEach((r, i) => {
      const vis = r.key === "NET" || shown.has(r.key);
      if (!vis) return;
      const cy = y0 + headH + (i + 0.5) * rowH, isNew = r.key === newest, k = isNew ? kNew : 1, dx = d * (1 - ease(k)) * w * 0.06;
      let g = glow.has(r.key) ? `<rect x="${f1(px + w * 0.004)}" y="${f1(cy - rowH / 2 + w * 0.003)}" width="${f1(pageW - w * 0.008)}" height="${f1(rowH - w * 0.006)}" fill="#fff1b8"/>` : "";
      const amtCol = r.net !== undefined ? (r.net < 0 ? "#c0392b" : "#1f7a43") : was[r.key] ? acc : INK;
      const af = Math.min(fs, fitT(r.amt, pageW * 0.3, fs));
      g += T(r.label, px + pad, cy, Math.min(fs, fitT(r.label, pageW * (was[r.key] ? 0.42 : 0.6), fs)), r.net !== undefined ? amtCol : INK, 700, "start") + T(r.amt, px + pageW - pad, cy, af, amtCol, 800, "end");
      if (was[r.key]) { const of = af * 0.72, ox = px + pageW - pad - tw(r.amt, af) - fs * 0.5, ow = tw(was[r.key], of), ks = isNew ? 1 : ph(s, 0, 0.4);
        g += T(was[r.key], ox, cy, of, "#8a94a3", 700, "end") + `<path d="M${f1(ox - ow - of * 0.1)} ${f1(cy)} L${f1(ox - ow - of * 0.1 + (ow + of * 0.2) * ks)} ${f1(cy)}" stroke="#e5484d" stroke-width="${f1(of * 0.12)}" stroke-linecap="round"/>`; }
      out += `<g transform="translate(${f1(dx)},0)" opacity="${clamp01(k * 1.6).toFixed(3)}">${g}</g>`;
    });
    if (totals) {
      const ty = y0 + headH + nRows * rowH + rowH * 0.62, tot = rows.reduce((a, r) => a + (r.key === "NET" ? r.net : shown.has(r.key) ? firstNum(r.amt) || 0 : 0), 0);
      out += `<path d="M${f1(px + pageW * 0.45)} ${f1(ty - rowH * 0.48)} L${f1(px + pageW - pad)} ${f1(ty - rowH * 0.48)} M${f1(px + pageW * 0.45)} ${f1(ty - rowH * 0.4)} L${f1(px + pageW - pad)} ${f1(ty - rowH * 0.4)}" stroke="${INK}" stroke-width="${f1(w * 0.002)}"/>` +
        T("Σ", px + pad, ty, fs * 1.1, "#4a5568", 800, "start") + T(fmtNum(tot, grp), px + pageW - pad, ty, Math.min(fs * 1.05, fitT(fmtNum(tot, grp), pageW * 0.4, fs * 1.05)), INK, 800, "end");
      if (d < 0) out += `<!--L${tot}-->`;
      if (d > 0) {
        const lt = Number((out.match(/<!--L(-?[\d.e+-]+)-->/) || [])[1]), eq = Math.abs(lt - tot) <= 1e-6 * Math.max(1, Math.abs(tot)) && (lt !== 0 || tot !== 0);
        out = out.replace(/<!--L-?[\d.e+-]+-->/, "");
        out += eq ? `<g transform="translate(0,${f1(ty)})">${mark("tick", rowH * 0.62, "#2fa35b", 1)}</g>`
          : `<g transform="translate(0,${f1(ty)})"><circle r="${f1(rowH * 0.31)}" fill="#e5484d"/>${T("≠", 0, 0, rowH * 0.42, "#ffffff", 800)}</g>`;
      }
    }
  });
  out += `<path d="M0 ${f1(y0 + w * 0.01)} L0 ${f1(y0 + pageH - w * 0.01)}" stroke="#c9bfa8" stroke-width="${f1(w * 0.004)}"/>`;
  // the capital cushion under the left page, and a loss that presses on it
  const cap = N(p.capital, 0), loss = Math.max(0, N(p.loss, 0));
  if (cap > 0) {
    const kL = loss > 0 ? ease(ph(s, 0.1, 0.6)) : 1, left0 = -w * 0.49 + pad, cwid = pageW * 0.5, full = rowH * 1.3, yb = y0 + pageH + rowH * 2.6;
    const rest = Math.max(0, cap - loss), broken = loss >= cap, ch = lerp(full, Math.max(rowH * 0.18, full * (rest / cap)), kL);
    const cc = broken ? "#e5484d" : "#2fa35b";
    let cush = `<rect x="${f1(left0)}" y="${f1(yb - ch)}" width="${f1(cwid)}" height="${f1(ch)}" rx="${f1(Math.min(ch / 2, rowH * 0.3))}" fill="${tint(cc)}" stroke="${cc}" stroke-width="${f1(w * 0.003)}"/>`;
    for (let k = 1; k < 6; k++) cush += `<path d="M${f1(left0 + (cwid * k) / 6)} ${f1(yb - ch + w * 0.006)} L${f1(left0 + (cwid * k) / 6)} ${f1(yb - w * 0.006)}" stroke="${cc}" stroke-width="${f1(w * 0.002)}" opacity="0.5"/>`;
    if (broken && kL > 0.95) cush += `<path d="M${f1(left0 + cwid * 0.2)} ${f1(yb - ch)} l${f1(cwid * 0.08)} ${f1(ch)} l${f1(cwid * 0.08)} ${f1(-ch)} l${f1(cwid * 0.08)} ${f1(ch)}" fill="none" stroke="#5a1f1f" stroke-width="${f1(w * 0.004)}"/>`;
    out += cush;
    const capTxt = `${p.capitalLabel ? p.capitalLabel + " " : ""}${fmtNum(loss > 0 ? lerp(cap, rest, kL) : cap)}`;
    out += T(capTxt, left0 + cwid + w * 0.012, yb - ch / 2, Math.min(fs, fitT(capTxt, pageW * 0.46, fs)), shade(cc, 0.6), 800, "start");
    if (loss > 0) {
      const lh = Math.max(rowH * 0.7, Math.min(full, full * (loss / cap))), ly = yb - ch - lh - (1 - kL) * rowH * 2.2;
      const lt = `${p.lossLabel ? p.lossLabel + " " : ""}${fmtNum(loss)}`;
      out += `<rect x="${f1(left0 + cwid * 0.12)}" y="${f1(ly)}" width="${f1(cwid * 0.76)}" height="${f1(lh)}" rx="${f1(w * 0.006)}" fill="#4a1d1d" opacity="${clamp01(kL * 3).toFixed(3)}"/>` +
        T(lt, left0 + cwid * 0.5, ly + lh / 2, Math.min(fs, fitT(lt, cwid * 0.7, fs), lh * 0.6), "#ffffff", 800);
    }
  }
  let top = y0;
  if (p.unit) { out += T(p.unit, 0, top - fs * 0.75, Math.min(fs * 0.85, fitT(p.unit, w * 0.5, fs * 0.85)), "#6b7280", 700); top -= fs * 1.4; }
  if (p.title) out += T(p.title, 0, top - fs * 0.85, fitT(p.title, w * 0.9, fs * 1.25), INK, 800);
  return out;
}

// ---------------------------------------------------------------- choicePaths: the road taken and the best road not taken
function choicePaths(p) {
  const w = N(p.w, 1300), s = stepS(p), col = p.color || "#2459a6";
  const opts = parts(p.options ?? "A;B;C").filter(Boolean).slice(0, 4);
  if (!opts.length) opts.push("");
  const n = opts.length, chosen = Math.round(N(p.chosen, 0)), best = Math.round(N(p.best, 0));
  const H = w * 0.6, gapY = Math.min(w * 0.17, (H * 0.95) / n), cardH = Math.min(w * 0.11, gapY * 0.8), cardW = w * 0.34, cx0 = -w * 0.08, sx = -w * 0.42, r = w * 0.035;
  const kDraw = chosen ? ph(s, 0, 0.6) : 1, kFade = chosen ? ease(ph(s, 0.2, 0.6)) : 0, fs = w * 0.034;
  let out = "";
  opts.forEach((o, i) => {
    const y = (i - (n - 1) / 2) * gapY, isC = chosen === i + 1, isB = best === i + 1 && !isC;
    const d = `M${f1(sx + r)} 0 C${f1(sx + w * 0.17)} 0 ${f1(cx0 - w * 0.17)} ${f1(y)} ${f1(cx0 - w * 0.008)} ${f1(y)}`;
    const c = isC ? col : isB ? "#f29f05" : chosen ? "#b8c0cc" : "#7a8594";
    out += isC ? `<path d="${d}" fill="none" stroke="#dfe5ee" stroke-width="${f1(w * 0.012)}" stroke-linecap="round"/><path d="${d}" fill="none" stroke="${col}" stroke-width="${f1(w * 0.014)}" stroke-linecap="round" pathLength="1" stroke-dasharray="${kDraw.toFixed(3)} 1"/>`
      : `<path d="${d}" fill="none" stroke="${c}" stroke-width="${f1(w * (chosen ? 0.007 : 0.009))}" stroke-linecap="round"${chosen ? ` stroke-dasharray="${f1(w * 0.014)} ${f1(w * 0.01)}"` : ""} opacity="${(chosen && !isB ? 1 - 0.5 * kFade : 1).toFixed(3)}"/>`;
    const op = chosen && !isC && !isB ? 1 - 0.55 * kFade : 1;
    const fill = isC ? tint(col) : isB ? "#fff4dc" : "#ffffff", stroke = isC ? col : isB ? "#f29f05" : "#9aa5b1";
    out += `<g opacity="${op.toFixed(3)}">` + (isB ? `<rect x="${f1(cx0 - w * 0.008)}" y="${f1(y - cardH / 2 - w * 0.008)}" width="${f1(cardW + w * 0.016)}" height="${f1(cardH + w * 0.016)}" rx="${f1(cardH * 0.28)}" fill="#ffe7a8" opacity="${(0.6 + 0.4 * kFade).toFixed(3)}"/>` : "") +
      chipBox(cx0 + cardW / 2, y, cardW, cardH, fill, stroke, w * (isC || isB ? 0.004 : 0.0025), cardH * 0.22) +
      linesSvg(wrap2(o, cardW * 0.86, fs), cx0 + cardW / 2, y, isC || !chosen || isB ? INK : "#6b7280", 800) + `</g>`;
    if (isC) out += `<g transform="translate(${f1(cx0 + cardW + w * 0.04)},${f1(y)})">${mark("tick", cardH * 0.55, "#2fa35b", ph(s, 0.55, 0.35) || (s > 50 ? 1 : 0))}</g>`;
    if (isB && p.tag) { const kT = ph(s, 0.8, 0.4) || (s > 50 ? 1 : 0), wr = wrap2(p.tag, w * 0.16, fs * 0.9), tx0 = cx0 + cardW + w * 0.025, cw = Math.max(...wr.lines.map((l) => tw(l, wr.fs))) + wr.fs, hh = wr.lines.length * wr.fs * 1.2 + wr.fs * 0.5;
      out += `<g transform="translate(${f1(tx0 + cw / 2)},${f1(y - (1 - backOut(kT)) * w * 0.05)})" opacity="${clamp01(kT * 2).toFixed(3)}">` +
        `<path d="M${f1(-cw / 2 - w * 0.012)} 0 L${f1(-cw / 2)} ${f1(-hh / 2)} L${f1(cw / 2)} ${f1(-hh / 2)} L${f1(cw / 2)} ${f1(hh / 2)} L${f1(-cw / 2)} ${f1(hh / 2)} Z" fill="#f29f05" stroke="#c77700" stroke-width="${f1(w * 0.003)}"/>` +
        linesSvg(wr, 0, 0, "#ffffff", 800) + `</g>`; }
  });
  out += `<circle cx="${f1(sx)}" cy="0" r="${f1(r)}" fill="${col}" stroke="#ffffff" stroke-width="${f1(w * 0.004)}"/>`;
  if (p.from) out += T(p.from, sx, r + fs * 0.95, fitT(p.from, w * 0.2, fs), INK, 800);
  if (p.title) out += T(p.title, 0, -((n - 1) / 2) * gapY - cardH / 2 - fs * 1.1, fitT(p.title, w * 0.9, fs * 1.1), INK, 800);
  return out;
}

// ---------------------------------------------------------------- incomeLine: a line over people standing at their incomes
function incomeLine(p) {
  const w = N(p.w, 1400), s = stepS(p);
  let vals = parts(p.values ?? "2;3;4;5;7;9;12;16").map((v) => firstNum(v)).filter((v) => v !== null && v >= 0).slice(0, 24).sort((a, b) => a - b);
  if (!vals.length) vals = [1];
  const rise = Math.max(0, N(p.rise, 1)), riseFrom = isNum(p.riseFrom) ? Math.max(0, +p.riseFrom) : rise, r = lerp(riseFrom, rise, ease(s / N(p.glide, 1.5)));
  const mean = (vals.reduce((a, v) => a + v, 0) / vals.length) * r, rel = p.mode === "relative";
  const line = rel ? clampN(N(p.share, 0.6), 0, 2) * mean : N(p.line, 5);
  const maxV = N(p.max, 0) > 0 ? +p.max : Math.max(Math.max(...vals) * Math.max(rise, riseFrom, 0.01), line, rel ? mean : 0) * 1.12 || 1;
  const Hp = w * 0.4, Y = (v) => -Hp * clampN(v / maxV, 0, 1.05), n = vals.length, slot = (w * 0.66) / n, bw = slot * 0.5, fs = w * 0.028;
  const fh = Math.min(slot * 0.95, w * 0.075);
  let out = `<path d="M${f1(-w * 0.48)} 0 L${f1(w * 0.48)} 0" stroke="#9aa5b1" stroke-width="${f1(w * 0.003)}"/>`;
  let below = 0;
  vals.forEach((v, i) => {
    const x = -w * 0.46 + slot * (i + 0.5), vv = v * r, under = vv < line, y = Y(vv), c = under ? "#e5484d" : "#2459a6";
    if (under) below++;
    out += `<rect x="${f1(x - bw / 2)}" y="${f1(y)}" width="${f1(bw)}" height="${f1(-y)}" rx="${f1(Math.min(bw * 0.15, -y / 2))}" fill="${tint(c)}" stroke="${c}" stroke-width="${f1(w * 0.002)}"/>` +
      `<g transform="translate(${f1(x)},${f1(y)})">${figure(fh, c)}</g>`;
  });
  // the line, its name, the count of people below it (under the name when there is room above the floor, else over it)
  const ly = Y(line), cnt = String(p.countLabel ?? "{n}").replace("{n}", String(below));
  const cntUnder = ly + fs * 3.1 <= -fs * 0.2, cy = cntUnder ? ly + fs * 2.1 : ly - fs * 2.1;
  if (rel) { const my = Y(mean);
    let myy = Math.abs(my - ly) < fs * 1.7 ? ly - fs * 1.7 : my;
    if (cnt && !cntUnder && Math.abs(myy - cy) < fs * 1.8) myy = cy - fs * 1.8;
    out += `<path d="M${f1(-w * 0.47)} ${f1(my)} L${f1(w * 0.2)} ${f1(my)}" stroke="#7a8594" stroke-width="${f1(w * 0.002)}" stroke-dasharray="${f1(w * 0.004)} ${f1(w * 0.006)}"/>`;
    if (p.meanLabel) out += T(p.meanLabel, w * 0.35, myy, Math.min(fs * 0.9, fitT(p.meanLabel, w * 0.26, fs * 0.9)), "#4a5568", 700); }
  out += `<path d="M${f1(-w * 0.48)} ${f1(ly)} L${f1(w * 0.22)} ${f1(ly)}" stroke="#c0392b" stroke-width="${f1(w * 0.005)}" stroke-dasharray="${f1(w * 0.014)} ${f1(w * 0.008)}"/>`;
  const lab = [p.lineLabel, p.showValue === true ? fmtNum(line) + (p.unit || "") : ""].filter(Boolean).join(" ");
  if (lab) { const f = Math.min(fs, fitT(lab, w * 0.24, fs)), cw = tw(lab, f) + f;
    out += chipBox(w * 0.35, ly, cw, f * 1.5, "#ffffff", "#c0392b", w * 0.003) + T(lab, w * 0.35, ly, f, "#c0392b", 800); }
  if (cnt) { const f = Math.min(fs * 1.1, fitT(cnt, w * 0.24, fs * 1.1)), cw = tw(cnt, f) + f;
    out += chipBox(w * 0.35, cy, cw, f * 1.5, "#e5484d", "#a3273a", w * 0.003) + T(cnt, w * 0.35, cy, f, "#ffffff", 800); }
  if (p.title) out += T(p.title, 0, -Hp - fh - fs * 1.4, fitT(p.title, w * 0.9, fs * 1.2), INK, 800);
  return out;
}

// ---------------------------------------------------------------- doorway: a threshold crossed once
function doorway(p) {
  const w = N(p.w, 520), s = stepS(p), col = p.color || "#8a5a2b";
  const open = clamp01(N(p.open, 0)), o = lerp(isNum(p.openFrom) ? clamp01(+p.openFrom) : 0, open, ease(s / N(p.glide, 0.9)));
  const dw = w * 0.62, dh = w * 1.12, ft = w * 0.07, sill = w * 0.05, top = -dh - sill, lh = w * 0.16;
  let out = `<rect x="${f1(-w * 0.5)}" y="${f1(-sill)}" width="${f1(w)}" height="${f1(sill)}" rx="${f1(w * 0.01)}" fill="#b7aa95" stroke="#8a7d68" stroke-width="${f1(w * 0.005)}"/>` +
    `<rect x="${f1(-dw / 2)}" y="${f1(top)}" width="${f1(dw)}" height="${f1(dh)}" fill="${mixHex("#3b4a5c", "#fff4c2", o)}"/>`;
  if (o > 0.05) out += `<path d="M${f1(-dw / 2)} ${f1(-sill)} L${f1(dw / 2)} ${f1(-sill)} L${f1(dw * 0.8)} 0 L${f1(-dw * 0.8)} 0 Z" fill="#fff4c2" opacity="${(0.45 * o).toFixed(3)}"/>`;
  if (p.beyond) { const wr = wrap2(p.beyond, dw * 0.8, w * 0.08), k = Math.pow(o, 1.5);
    out += `<g opacity="${k.toFixed(3)}" transform="translate(0,${f1(top + dh * 0.42)}) scale(${(0.88 + 0.12 * o).toFixed(3)})">${linesSvg(wr, 0, 0, "#7a4b00", 800)}</g>`; }
  const ang = (o * 80 * Math.PI) / 180, fx = -dw / 2 + dw * Math.cos(ang), e = dh * 0.07 * Math.sin(ang), bot = -sill;
  if (fx > -dw / 2 + 2) out += `<path d="M${f1(-dw / 2)} ${f1(top)} L${f1(fx)} ${f1(top - e)} L${f1(fx)} ${f1(bot + e * 0.4)} L${f1(-dw / 2)} ${f1(bot)} Z" fill="${col}" stroke="${shade(col, 0.7)}" stroke-width="${f1(w * 0.006)}"/>` +
    `<path d="M${f1(-dw / 2 + (fx + dw / 2) * 0.15)} ${f1(top + dh * 0.08)} L${f1(-dw / 2 + (fx + dw / 2) * 0.85)} ${f1(top + dh * 0.08 - e * 0.7)} L${f1(-dw / 2 + (fx + dw / 2) * 0.85)} ${f1(top + dh * 0.45)} L${f1(-dw / 2 + (fx + dw / 2) * 0.15)} ${f1(top + dh * 0.45)} Z" fill="none" stroke="${shade(col, 0.8)}" stroke-width="${f1(w * 0.005)}"/>` +
    `<circle cx="${f1(fx - (fx + dw / 2) * 0.1)}" cy="${f1(top + dh * 0.55)}" r="${f1(w * 0.018)}" fill="#e6c25a" stroke="#a7862d" stroke-width="${f1(w * 0.004)}"/>`;
  out += `<rect x="${f1(-dw / 2 - ft)}" y="${f1(top)}" width="${f1(ft)}" height="${f1(dh)}" fill="#e9e2d2" stroke="#b5aa94" stroke-width="${f1(w * 0.005)}"/>` +
    `<rect x="${f1(dw / 2)}" y="${f1(top)}" width="${f1(ft)}" height="${f1(dh)}" fill="#e9e2d2" stroke="#b5aa94" stroke-width="${f1(w * 0.005)}"/>` +
    `<rect x="${f1(-dw / 2 - ft * 1.4)}" y="${f1(top - lh)}" width="${f1(dw + ft * 2.8)}" height="${f1(lh)}" rx="${f1(w * 0.012)}" fill="#d9cfb9" stroke="#b5aa94" stroke-width="${f1(w * 0.005)}"/>`;
  if (p.label) out += T(p.label, 0, top - lh / 2, fitT(p.label, (dw + ft * 2.8) * 0.9, lh * 0.55), INK, 800);
  return out;
}

// ---------------------------------------------------------------- registry (anchor "bottom": stands on its origin)
export const DRAWS = {
  formula: { fn: formula, anchor: "center" },
  scaleBalance: { fn: scaleBalance, anchor: "bottom" },
  causeChain: { fn: causeChain, anchor: "center" },
  sorter: { fn: sorter, anchor: "center" },
  spectrum: { fn: spectrum, anchor: "center" },
  padlocks: { fn: padlocks, anchor: "center" },
  tugOfWar: { fn: tugOfWar, anchor: "bottom" },
  oneVsAll: { fn: oneVsAll, anchor: "center" },
  tAccount: { fn: tAccount, anchor: "center" },
  choicePaths: { fn: choicePaths, anchor: "center" },
  incomeLine: { fn: incomeLine, anchor: "bottom" },
  doorway: { fn: doorway, anchor: "bottom" },
};
export const _test = { evaluate, parseRow, substitute };
