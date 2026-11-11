// The econ_charts family (Sloman economics book, 5 November 2026): the data charts and counted pictures the book's
// videos asked for most, each one parametric and built at the voice's speed. Bars that draw themselves on their names
// (barChart), per-unit marginal bars over a price or wage line with ticks, crosses, a stop line, shaded surplus that
// slides into one block and a total tower (marginalBars), a waterfall of signed contributions (waterfall), a pie that
// draws and morphs between two states (pieChart), a bar of parts with a running total that may pass 100% (shareBar),
// rows of countable things (pictogram), an icon array split twice (iconArray), a year-axis time series with eras, a
// second axis, events, marked extremes and a travelling pointer (timeSeries), a scatter with its fitted line and
// residual gaps (scatterFit), the business-cycle wave (cycleWave), a day of hours split between work and leisure
// (dayHours), the multiplier's shrinking rounds (roundBars), risk-weighted assets (weightBars), a pump-jack (pumpJack)
// and a bargaining table with cards (bargainTable).
//
// Conventions of the family: words come only through parameters; _t is seconds since the item appeared and _s since
// its last step; without times a drawing shows its end state (the box rule measures that). A change on a cue word
// glides instead of jumping where the drawing is told where it came from (from, lineFrom, windowFrom, modelFrom ...):
// the engine merges steps, so a later step that should not replay the glide sets from to "" (or grow to 0).
import { tx, shade, INK, FONT, esc, clamp01, parts, idxSet, isNum, easeIO } from "../draw.mjs";
import { textWidth } from "../boxes.mjs";

const PAL = ["#2459a6", "#f29f05", "#2fa35b", "#e2558f", "#7b61ff", "#2a9d8f", "#c0563f", "#9b6b43", "#5b7fb8", "#d6454f", "#8cc152", "#6b7280"];
const UP = "#2fa35b", DOWN = "#e5484d", TOTAL = "#2459a6", GOLD = "#f2c14e", GRID = "#d5dbe1", MUTED = "#6b7280", RED = "#c0392b";

// ---------------------------------------------------------------- small helpers (no imported helper runs at load time)
const r1 = (v) => Math.round(v * 10) / 10;
const tnum = (v) => (v === null || v === undefined || v === "" ? NaN : Number(v));
const sinceStep = (p) => { const s = tnum(p._s); if (Number.isFinite(s)) return Math.max(0, s); const t = tnum(p._t); return Number.isFinite(t) ? Math.max(0, t) : Infinity; };
const sinceStart = (p) => { const t = tnum(p._t); return Number.isFinite(t) ? Math.max(0, t) : Infinity; };
const prog = (sec, dur) => (!(dur > 0) || !Number.isFinite(sec) ? 1 : clamp01(sec / dur));
const num = (v, d = 0) => { const n = tnum(v); return Number.isFinite(n) ? n : d; };
const listN = (s) => String(s ?? "").split(/[;,\s]+/).filter((x) => x !== "").map(Number);           // keeps NaN in place
const pairs = (s) => parts(s).filter(Boolean).map((t) => { const b = t.split(":"); return { l: b[0].trim(), v: tnum((b[1] ?? "").trim()), f: b.slice(1).map((x) => x.trim()) }; });
const fitT = (t, maxW, cap) => Math.min(cap, Math.max(1, maxW) / Math.max(0.3, textWidth(String(t), 1)));
const tw = (t, px) => textWidth(String(t), px);
const decOf = (v) => { const s = String(v); const i = s.indexOf("."); return i < 0 || /e/i.test(s) ? 0 : Math.min(3, s.length - i - 1); };
function fmt(v, like, dec) {
  if (!Number.isFinite(v)) return "";
  if (isNum(dec) && Number(dec) >= 0) return Number(v).toFixed(Math.min(4, Math.round(Number(dec))));
  if (like !== undefined && like !== null && like !== "" && Number.isFinite(Number(like))) { const d = decOf(like); const s = Number(v).toFixed(d); return /^-0(\.0*)?$/.test(s) ? s.slice(1) : s; }
  const a = Math.abs(v), s = a >= 100 ? String(Math.round(v)) : a >= 10 ? String(Math.round(v * 10) / 10) : a >= 1 ? String(Math.round(v * 100) / 100) : String(Math.round(v * 1000) / 1000);
  return s === "-0" ? "0" : s;
}
function withUnit(s, unit) {
  const u = String(unit ?? "");
  if (!u || s === "") return s;
  const m = u.match(/^([₹$£€¥])\s*(.*)$/);
  if (m) return (s.startsWith("-") ? "−" + m[1] + s.slice(1) : m[1] + s) + (m[2] ? " " + m[2] : "");
  return (s.startsWith("-") ? "−" + s.slice(1) : s) + u;
}
const signed = (s) => (s.startsWith("−") || s.startsWith("-") ? s : "+" + s);
// text with an anchor ("start" | "middle" | "end"), cy is the vertical centre
const PAPER = "#f7f1e5";
const txa = (t, x, cy, size, fill = INK, weight = 700, anchor = "middle", halo = "") => (t === "" || t == null ? "" :
  `<text x="${r1(x)}" y="${r1(cy + size * 0.35)}" font-family=${JSON.stringify(FONT)} font-size="${r1(size)}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}"` +
  (halo ? ` paint-order="stroke" stroke="${halo}" stroke-width="${r1(size * 0.22)}" stroke-linejoin="round"` : "") + `>${esc(t)}</text>`);
const rect = (x, y, w, h, fill, extra = "") => { const X = Math.min(x, x + w), Y = Math.min(y, y + h), W = Math.abs(w), H = Math.abs(h);
  return `<rect x="${r1(X)}" y="${r1(Y)}" width="${r1(W)}" height="${r1(H)}" fill="${fill}"${extra ? " " + extra : ""}/>`; };
const line = (x1, y1, x2, y2, stroke, sw, extra = "") => `<path d="M${r1(x1)} ${r1(y1)} L${r1(x2)} ${r1(y2)}" stroke="${stroke}" stroke-width="${r1(sw)}"${extra ? " " + extra : ""}/>`;
const pill = (t, x, cy, size, bg, fg = "#ffffff") => { if (!t) return ""; const w = tw(t, size) + size * 0.9, h = size * 1.45;
  return `<rect x="${r1(x - w / 2)}" y="${r1(cy - h / 2)}" width="${r1(w)}" height="${r1(h)}" rx="${r1(h / 2)}" fill="${bg}"/>` + txa(t, x, cy, size, fg, 800); };
const tick = (x, y, s, c = UP) => `<g transform="translate(${r1(x)},${r1(y)})"><circle r="${r1(s / 2)}" fill="${c}"/><path d="M${r1(-s * 0.21)} ${r1(s * 0.01)} L${r1(-s * 0.04)} ${r1(s * 0.18)} L${r1(s * 0.23)} ${r1(-s * 0.16)}" stroke="#ffffff" stroke-width="${r1(s * 0.12)}" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>`;
const cross = (x, y, s, c = DOWN) => `<g transform="translate(${r1(x)},${r1(y)})"><circle r="${r1(s / 2)}" fill="${c}"/><path d="M${r1(-s * 0.18)} ${r1(-s * 0.18)} L${r1(s * 0.18)} ${r1(s * 0.18)} M${r1(s * 0.18)} ${r1(-s * 0.18)} L${r1(-s * 0.18)} ${r1(s * 0.18)}" stroke="#ffffff" stroke-width="${r1(s * 0.12)}" stroke-linecap="round"/></g>`;
const colorMap = (s) => { const m = {}; parts(s).forEach((c) => { const i = c.indexOf(":"); if (i > 0 && /^#[0-9a-f]{3,6}$/i.test(c.slice(i + 1).trim())) m[c.slice(0, i).trim()] = c.slice(i + 1).trim(); }); return m; };
const okColor = (c, d) => (typeof c === "string" && /^#[0-9a-f]{3}([0-9a-f]{3})?$/i.test(c) ? c : d);
function niceStep(range, want = 5) {
  const raw = Math.max(1e-9, range / Math.max(1, want)), mag = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / mag;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * mag;
}
function niceRange(lo, hi, want = 5) {
  if (!(hi > lo)) { hi = lo + 1; }
  const st = niceStep(hi - lo, want);
  return [Math.floor(lo / st + 1e-9) * st, Math.ceil(hi / st - 1e-9) * st, st];
}
// the share of the newest revealed part that has grown: the newest of upto grows after the step, all grow from the start
function growOf(p, j, shown, upto, dur) {
  if (upto > 0) return j < shown - 1 ? 1 : easeIO(prog(sinceStep(p), dur));
  return easeIO(prog(sinceStart(p), dur));
}

// ---------------------------------------------------------------- barChart
// Ranking or grouped bars that grow on their names; a second value per bar ("label:v1:v2") makes grouped pairs; from
// morphs the bars from earlier values (before and after tax, 1990 and 2014); refLine is a reference value; group splits
// the list in two with captions; glow marks the bars being spoken of.
function barChart(p) {
  const w = Math.max(200, num(p.w, 1100)), vertical = p.dir === "vertical";
  const raw = pairs(p.bars ?? "क:40;ख:65;ग:25");
  let data = raw.map((d, i) => ({ l: d.l, v: Number.isFinite(d.v) ? d.v : 0, v2: d.f.length > 1 ? tnum(d.f[1]) : NaN, i, r1: d.f[0], r2: d.f[1] }));
  if (!data.length) data = [{ l: "", v: 0, v2: NaN, i: 0 }];
  const two = data.some((d) => Number.isFinite(d.v2));
  const fr = parts(p.from).map((t) => t.split(":").map((x) => tnum(x.trim())));
  const gk = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
  data.forEach((d) => { const f = fr[d.i] || [];
    d.cv = Number.isFinite(f[0]) ? f[0] + (d.v - f[0]) * gk : d.v;
    d.cv2 = Number.isFinite(d.v2) ? (Number.isFinite(f[1]) ? f[1] + (d.v2 - f[1]) * gk : d.v2) : NaN; });
  if (p.sort === "desc") data.sort((a, b) => b.v - a.v); else if (p.sort === "asc") data.sort((a, b) => a.v - b.v);
  const n = data.length, upto = Math.max(0, Math.round(num(p.upto, 0))), shown = upto > 0 ? Math.min(n, upto) : n;
  const grow = num(p.grow, 0.8), unit = p.unit ?? "", dec = p.decimals, glow = idxSet(p.glow), dim = p.dim === true && glow.size > 0;
  const cmap = colorMap(p.colors), c1 = okColor(p.color, "#2459a6"), c2 = okColor(p.color2, "#f29f05");
  const [refV, refL] = (() => { const s = String(p.refLine ?? ""), i = s.indexOf(":"); const v = tnum(i >= 0 ? s.slice(0, i) : s); return [v, i >= 0 ? s.slice(i + 1).trim() : ""]; })();
  const all = data.flatMap((d) => [d.v, d.cv, d.v2, d.cv2, ...(fr[d.i] || [])]).filter(Number.isFinite).concat(Number.isFinite(refV) ? [refV] : []);
  let lo = Math.min(0, ...all), hi = Math.max(0, ...all);
  if (num(p.max, 0) > 0) hi = Math.max(num(p.max, 0), 0);
  if (!(hi > lo)) hi = lo + 1;
  const names = parts(p.names).filter(Boolean);
  const [gk1, gcap1, gcap2] = (() => { const b = String(p.group ?? "").split(":"); return [Math.round(num(b[0], 0)), (b[1] || "").trim(), (b[2] || "").trim()]; })();
  const groupOn = gk1 > 0 && gk1 < n, gGlow = Math.round(num(p.groupGlow, 0));
  const vstr = (v, like) => withUnit(fmt(v, like, dec), unit);
  const vals = [];                                   // value words go over the reference line
  let out = "", H, top;
  const fsT = w * 0.042;
  const legend = (y) => { if (!two || !names.length) return "";
    const fsL = w * 0.034, items = names.slice(0, 2).map((nm, k) => ({ nm, c: k ? c2 : c1, w: fsL * 1.4 + tw(nm, fsL) }));
    const tot = items.reduce((a, it) => a + it.w, 0) + fsL * 1.5 * (items.length - 1);
    let x = -tot / 2, s = "";
    items.forEach((it) => { s += rect(x, y - fsL * 0.45, fsL * 0.9, fsL * 0.9, it.c, `rx="${r1(fsL * 0.15)}"`) + txa(it.nm, x + fsL * 1.25, y, fsL, INK, 700, "start"); x += it.w + fsL * 1.5; });
    return s; };
  if (!vertical) {
    const rh = Math.min(w * (two ? 0.11 : 0.085), (w * (two ? 0.95 : 0.8)) / n), fs = Math.min(w * 0.04, rh * (two ? 0.42 : 0.5));
    const lw = Math.min(w * 0.3, Math.max(0, ...data.map((d) => tw(d.l, fs))) + fs * 0.6);
    const fsV = fs * 0.92, vw = Math.max(...data.flatMap((d) => [d.v, d.v2].filter(Number.isFinite).map((v) => tw(vstr(v, v), fsV)))) + fsV * 0.6;
    const gcol = groupOn ? fs * 1.8 : 0;
    const head = (p.title ? fsT * 1.6 : 0) + (two && names.length ? w * 0.05 : 0) + (Number.isFinite(refV) ? fs * 1.5 : 0);
    H = head + n * rh; top = -H / 2;
    let bx0 = -w / 2 + lw + fs * 0.3, bx1 = w / 2 - vw - gcol;
    if (lo < 0) bx0 += vw;
    const X = (v) => bx0 + ((Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo)) * (bx1 - bx0), y0 = top + head;
    let hy = top;
    if (p.title) { out += tx(p.title, 0, hy + fsT * 0.7, fitT(p.title, w * 0.95, fsT), INK, 800); hy += fsT * 1.6; }
    if (two && names.length) { out += legend(hy + w * 0.022); hy += w * 0.05; }
    data.forEach((d, j) => {
      const y = y0 + j * rh, g = glow.has(d.i + 1), inGroup = groupOn && gGlow ? (gGlow === 1 ? j < gk1 : j >= gk1) : false;
      if (g || inGroup) out += rect(-w / 2, y + rh * 0.04, w - gcol, rh * 0.92, GOLD, `opacity="${g ? 0.45 : 0.22}" rx="${r1(rh * 0.15)}"`);
      if (j >= shown) return;
      const k = growOf(p, j, shown, upto, grow), op = dim && !g ? ` opacity="0.35"` : "";
      const lab = fitT(d.l, lw - fs * 0.3, fs);
      out += `<g${op}>` + txa(d.l, bx0 - (lo < 0 ? vw : 0) - fs * 0.3, y + rh / 2, lab, INK, g ? 800 : 700, "end");
      const series = two ? [[d.cv, cmap[String(d.i + 1)] || c1, -0.2, d.r1], [d.cv2, c2, 0.2, d.r2]] : [[d.cv, cmap[String(d.i + 1)] || c1, 0, d.r1]];
      const bt = rh * (two ? 0.34 : 0.62);
      series.forEach(([v, c, off, like]) => {
        if (!Number.isFinite(v)) return;
        const vv = v * k, x0 = X(0), x1 = X(vv), cy = y + rh / 2 + off * rh;
        out += rect(x0, cy - bt / 2, x1 - x0, bt, c, `rx="${r1(Math.min(bt * 0.18, Math.abs(x1 - x0) / 2))}"` + (g ? ` stroke="${shade(GOLD, 0.8)}" stroke-width="${r1(Math.max(3, rh * 0.06))}"` : ""));
        if (k > 0.05 && p.values !== false) vals.push(`<g${op}>` + txa(vstr(vv, like ?? v), vv >= 0 ? x1 + fsV * 0.25 : x1 - fsV * 0.25, cy, two ? Math.min(fsV, bt * 1.1) : fsV, g ? INK : "#3b4250", 800, vv >= 0 ? "start" : "end", PAPER) + `</g>`);
      });
      out += `</g>`;
    });
    out += line(X(0), y0, X(0), y0 + n * rh, INK, Math.max(2, w * 0.003));
    if (Number.isFinite(refV)) {
      const x = X(refV);
      out += line(x, y0 - fs * 0.2, x, y0 + n * rh, RED, Math.max(3, w * 0.004), `stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"`);
      if (refL) { const f = fitT(refL, w * 0.5, fs * 0.9), half = tw(refL, f) / 2; out += txa(refL, Math.max(-w / 2 + half, Math.min(w / 2 - half, x)), y0 - fs * 0.75, f, RED, 800); }
    }
    if (groupOn) {
      const yd = y0 + gk1 * rh;
      out += line(-w / 2, yd, w / 2 - gcol * 0.3, yd, MUTED, Math.max(2, w * 0.003), `stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.007)}"`);
      [[0, gk1, gcap1, 1], [gk1, n, gcap2, 2]].forEach(([a, b, cap, gi]) => {
        const ya = y0 + a * rh + rh * 0.15, yb = y0 + b * rh - rh * 0.15, x = w / 2 - gcol * 0.75, c = gGlow === gi ? shade(GOLD, 0.75) : MUTED;
        out += `<path d="M${r1(x - fs * 0.3)} ${r1(ya)} L${r1(x)} ${r1(ya)} L${r1(x)} ${r1(yb)} L${r1(x - fs * 0.3)} ${r1(yb)}" fill="none" stroke="${c}" stroke-width="${r1(Math.max(3, w * 0.004))}"/>`;
        if (cap) out += `<g transform="translate(${r1(x + fs * 0.62)},${r1((ya + yb) / 2)}) rotate(90)">` + tx(cap, 0, 0, fitT(cap, yb - ya, fs * 0.85), c, 800) + `</g>`;
      });
    }
    return out + vals.join("");
  }
  // vertical: categories across, bars up (or down for negatives)
  const ph = w * 0.42, sw = w / n, fsCap = w * 0.034;
  const fsLab = Math.min(fsCap, ...data.map((d) => fitT(d.l || " ", sw * 0.94, fsCap)));
  const fsV = Math.min(fsCap, ...data.flatMap((d) => [d.v, d.v2].filter(Number.isFinite).map((v) => fitT(vstr(v, v), sw * (two ? 0.98 : 0.94), fsCap))));
  const refW = Number.isFinite(refV) && refL ? Math.min(w * 0.22, tw(refL, fsCap) + fsCap * 0.5) : 0;
  const L = -w / 2, R = w / 2 - refW, slot = (R - L) / n;
  const head = (p.title ? fsT * 1.6 : 0) + (two && names.length ? w * 0.05 : 0) + (groupOn ? fsCap * 1.6 : 0);
  H = head + fsV * 1.4 + ph + (lo < 0 ? fsV * 1.4 : 0) + fsLab * 1.8; top = -H / 2;
  const pt = top + head + fsV * 1.4, pb = pt + ph, Y = (v) => pb - ((Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo)) * ph;
  let hy = top;
  if (p.title) { out += tx(p.title, 0, hy + fsT * 0.7, fitT(p.title, w * 0.95, fsT), INK, 800); hy += fsT * 1.6; }
  if (two && names.length) { out += legend(hy + w * 0.022); hy += w * 0.05; }
  const labY = pb + (lo < 0 ? fsV * 1.4 : 0) + fsLab * 0.9;
  data.forEach((d, j) => {
    const cx = L + (j + 0.5) * slot, g = glow.has(d.i + 1), inGroup = groupOn && gGlow ? (gGlow === 1 ? j < gk1 : j >= gk1) : false;
    if (g || inGroup) out += rect(L + j * slot + slot * 0.04, pt - fsV * 1.3, slot * 0.92, labY + fsLab * 0.8 - pt + fsV * 1.3, GOLD, `opacity="${g ? 0.45 : 0.22}" rx="${r1(slot * 0.08)}"`);
    if (j >= shown) return;
    const k = growOf(p, j, shown, upto, grow), op = dim && !g ? ` opacity="0.35"` : "", bwid = slot * (two ? 0.36 : 0.6);
    out += `<g${op}>` + txa(d.l, cx, labY, fitT(d.l || " ", slot * 0.94, fsLab), INK, g ? 800 : 700);
    const series = two ? [[d.cv, cmap[String(d.i + 1)] || c1, -0.5, d.r1], [d.cv2, c2, 0.5, d.r2]] : [[d.cv, cmap[String(d.i + 1)] || c1, 0, d.r1]];
    series.forEach(([v, c, off, like]) => {
      if (!Number.isFinite(v)) return;
      const vv = v * k, x = cx + off * bwid * 1.08 - bwid / 2, y0 = Y(0), y1 = Y(vv);
      out += rect(x, y0, bwid, y1 - y0, c, `rx="${r1(Math.min(bwid * 0.12, Math.abs(y1 - y0) / 2))}"` + (g ? ` stroke="${shade(GOLD, 0.8)}" stroke-width="${r1(Math.max(3, w * 0.004))}"` : ""));
      if (k > 0.05 && p.values !== false) vals.push(`<g${op}>` + txa(vstr(vv, like ?? v), x + bwid / 2, vv >= 0 ? y1 - fsV * 0.7 : y1 + fsV * 0.7, two ? fitT(vstr(v, like ?? v), slot * 0.5, fsCap) : fsV, INK, 800, "middle", PAPER) + `</g>`);
    });
    out += `</g>`;
  });
  out += line(L, Y(0), R, Y(0), INK, Math.max(2, w * 0.003));
  if (Number.isFinite(refV)) {
    out += line(L, Y(refV), R, Y(refV), RED, Math.max(3, w * 0.004), `stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"`);
    if (refL) out += txa(refL, R + fsCap * 0.3, Y(refV), fitT(refL, refW - fsCap * 0.4, fsCap), RED, 800, "start");
  }
  if (groupOn) {
    const xd = L + gk1 * slot;
    out += line(xd, pt - fsV * 1.3, xd, labY + fsLab * 0.6, MUTED, Math.max(2, w * 0.003), `stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.007)}"`);
    [[L, xd, gcap1, 1], [xd, R, gcap2, 2]].forEach(([a, b, cap, gi]) => { if (cap) out += txa(cap, (a + b) / 2, pt - fsV * 1.4 - fsCap * 0.85, fitT(cap, (b - a) * 0.95, fsCap), gGlow === gi ? shade(GOLD, 0.6) : MUTED, 800); });
  }
  return out + vals.join("");
}

// ---------------------------------------------------------------- marginalBars (bottom)
// One bar per extra unit (the samosa's utils, the tailor's MRP, the scooter's benefit) arriving on its word, a price or
// wage line across that can slide, a tick above it and a cross below it, a stop line where it stops paying, the part
// above the line shaded as surplus (and gathered into one block), or the bars stacked into a total tower (TU) that a
// negative unit makes shorter. A second value per unit (costs) makes pairs: benefit against cost.
function marginalBars(p) {
  const w = Math.max(200, num(p.w, 1100)), vals = listN(p.values ?? "7;4;2;1;0;-1").map((v) => (Number.isFinite(v) ? v : 0));
  if (!vals.length) vals.push(0);
  const costs = listN(p.costs), paired = costs.some(Number.isFinite), n = vals.length;
  // labels are ;-separated; a ,-separated list with one name per bar is read the same way (ch12: "a,b,c" put every
  // name under bar 1)
  const labS = String(p.labels ?? ""), labC = labS.split(",").map((t) => t.trim());
  const labs = (!labS.includes(";") && n > 1 && labC.length === n ? labC : parts(p.labels)).filter((x, i, a) => a.length > 1 || x);
  const unit = p.unit ?? "", dec = p.decimals, c1 = okColor(p.color, "#2459a6"), c2 = okColor(p.color2, "#e07b24");
  const lineS = String(p.line ?? ""), li = lineS.indexOf(":"), lineV0 = tnum(li >= 0 ? lineS.slice(0, li) : lineS), lineL = li >= 0 ? lineS.slice(li + 1).trim() : "";
  const glk = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
  const lineV = Number.isFinite(lineV0) && isNum(p.lineFrom) ? +p.lineFrom + (lineV0 - +p.lineFrom) * glk : lineV0, hasLine = Number.isFinite(lineV);
  const upto = Math.max(0, Math.round(num(p.upto, 0))), shown = upto > 0 ? Math.min(n, upto) : n, grow = num(p.grow, 0.7);
  const towerMode = ["beside", "only"].includes(p.tower) ? p.tower : "off", gather = p.gather === true && towerMode === "off" && hasLine && !paired;
  const cum = []; vals.reduce((a, v, i) => (cum[i] = a + v), 0);
  const names = parts(p.names).filter(Boolean);
  const vstr = (v, like) => withUnit(fmt(v, like, dec), unit);
  const surplus = vals.map((v) => (hasLine ? Math.max(0, v - lineV) : 0)), sumSur = surplus.slice(0, shown).reduce((a, b) => a + b, 0);
  let lo = Math.min(0, ...vals, ...costs.filter(Number.isFinite)), hi = Math.max(0, ...vals, ...costs.filter(Number.isFinite), hasLine ? lineV0 : 0, isNum(p.lineFrom) ? +p.lineFrom : 0);
  if (towerMode !== "off") hi = Math.max(hi, ...cum);
  if (gather) hi = Math.max(hi, surplus.reduce((a, b) => a + b, 0));
  if (num(p.max, 0) > 0) hi = num(p.max, 0);
  if (!(hi > lo)) hi = lo + 1;
  const ph = w * 0.42, fsCap = w * 0.034;
  const Y = (v) => -((Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo)) * ph, base = Y(0);
  const lineW = hasLine && lineL ? Math.min(w * 0.24, tw(lineL, fsCap) + fsCap * 0.6) : 0;
  const colW = towerMode === "only" ? w * 0.5 : towerMode === "beside" || gather ? w * 0.24 : 0;
  const L = towerMode === "only" ? -colW / 2 : -w / 2, R = towerMode === "only" ? colW / 2 : w / 2 - colW - lineW;
  const slot = (R - L) / n, bw = Math.min(w * 0.12, slot * (paired ? 0.36 : 0.58));
  const fsV = Math.min(fsCap, ...vals.concat(costs.filter(Number.isFinite)).map((v) => fitT(vstr(v, v), paired ? bw * 1.05 : slot * 0.92, fsCap)));
  const fsLab = Math.min(fsCap, ...Array.from({ length: n }, (_, i) => fitT(labs[i] ?? String(i + 1), slot * 0.9, fsCap)));
  const mk = Math.min(fsCap * 1.25, slot * 0.4), labOff = lo < 0 ? fsV * 1.4 : 0;     // a negative bar's value sits above the unit names
  let out = "", words = "", topY = Y(hi) - fsV * 1.4 - (p.marks !== false && (hasLine || paired) ? mk * 1.1 : 0);
  if (towerMode !== "only") {
    out += line(L, base, R, base, INK, Math.max(2, w * 0.003));
    // a pair is judged by its cost, a single bar by the line: the first unit that does not pay is where to stop
    const pays = vals.map((v, i) => (paired ? v >= (Number.isFinite(costs[i]) ? costs[i] : -Infinity) : hasLine ? v >= lineV : true));
    const firstNo = pays.findIndex((x) => !x);
    for (let i = 0; i < shown; i++) {
      const cx = L + (i + 0.5) * slot, k = growOf(p, i, shown, upto, grow);
      out += txa(labs[i] ?? String(i + 1), cx, labOff + fsLab * 0.9, fitT(labs[i] ?? String(i + 1), slot * 0.9, fsLab), INK, 700);
      const bars = paired ? [[vals[i], c1, -0.55], [costs[i], c2, 0.55]] : [[vals[i], c1, 0]];
      let topBar = base;
      bars.forEach(([v, c, off]) => {
        if (!Number.isFinite(v)) return;
        const vv = v * k, x = cx + off * bw - bw / 2, y1 = Y(vv);
        const above = !paired && hasLine && vv > lineV && p.shade !== false && !gather;
        out += rect(x, base, bw, y1 - base, c, `rx="${r1(Math.min(bw * 0.1, Math.abs(y1 - base) / 2))}"`);
        if (!paired && hasLine && v > lineV && p.shade !== false && k >= 1) {
          const ys = Y(lineV);
          if (gather) out += rect(x, ys, bw, Y(v) - ys, "none", `stroke="${shade(GOLD, 0.7)}" stroke-width="${r1(Math.max(2, w * 0.003))}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"`);
          else if (above) {
            out += rect(x, ys, bw, Y(v) - ys, GOLD, `opacity="0.9"`) + `<path d="${Array.from({ length: 6 }, (_, q) => `M${r1(x)} ${r1(ys + (Y(v) - ys) * (q / 6))} L${r1(x + bw)} ${r1(ys + (Y(v) - ys) * ((q + 1) / 6))}`).join(" ")}" stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.002))}" opacity="0.6"/>`;
            const sv = vstr(v - lineV, v), fsS = fitT(sv, bw * 0.92, fsV * 0.9);
            if (Math.abs(Y(v) - ys) > fsS * 1.2) out += txa(sv, x + bw / 2, (ys + Y(v)) / 2, fsS, "#6b4a00", 800);
          }
        }
        if (k > 0.05 && p.numbers !== false) words += txa(vstr(vv, v), x + bw / 2, vv >= 0 ? y1 - fsV * 0.7 : y1 + fsV * 0.7, fsV, INK, 800, "middle", PAPER);
        topBar = Math.min(topBar, y1);
      });
      if (p.marks !== false && (hasLine || paired) && k >= 1) {
        const my = Math.min(topBar, base) - fsV * 1.4 - mk * 0.55;
        out += pays[i] ? tick(cx, my, mk) : cross(cx, my, mk);
      }
    }
    if (paired && names.length) {
      const fsN = fsCap * 0.95; let x = L;
      names.slice(0, 2).forEach((nm, k) => { out += rect(x, topY - fsN * 1.5, fsN * 0.9, fsN * 0.9, k ? c2 : c1, `rx="${r1(fsN * 0.15)}"`) + txa(nm, x + fsN * 1.25, topY - fsN * 1.05, fsN, INK, 700, "start"); x += fsN * 2.2 + tw(nm, fsN); });
      topY -= fsN * 1.8;
    }
    if (hasLine) {
      const y = Y(lineV);
      out += line(L - slot * 0.1, y, R + slot * 0.05, y, RED, Math.max(3, w * 0.005), `stroke-dasharray="${r1(w * 0.014)} ${r1(w * 0.008)}"`) + words;
      words = "";
      if (lineL) out += txa(lineL, R + fsCap * 0.3, y, fitT(lineL, lineW - fsCap * 0.4, fsCap), RED, 800, "start");
    }
    if (p.stop === true && firstNo > 0 && firstNo < shown) {
      const xs = L + firstNo * slot, ys = topY - fsCap * 0.2;
      out += line(xs, labOff + fsLab * 1.8, xs, ys + fsCap * 0.7, DOWN, Math.max(4, w * 0.005), `stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"`);
      if (p.stopLabel) out += pill(p.stopLabel, Math.max(L + tw(p.stopLabel, fsCap) / 2 + fsCap, Math.min(R - tw(p.stopLabel, fsCap) / 2 - fsCap, xs)), ys, fitT(p.stopLabel, w * 0.3, fsCap), DOWN);
      topY = ys - fsCap;
    }
  }
  out += words;
  // the right column: a total tower, or the gathered surplus block
  const cx = towerMode === "only" ? 0 : w / 2 - colW / 2, cwid = Math.min(w * 0.14, colW * 0.55);
  if (towerMode !== "off") {
    let level = 0, s = "";
    const last = shown - 1, kNew = growOf(p, last, shown, upto, grow);
    for (let i = 0; i < shown; i++) {
      const v = vals[i], isNew = i === last && upto > 0, kk = isNew ? kNew : 1;
      if (v >= 0) {
        const y0 = Y(level), y1 = Y(level + v * kk), c = i % 2 ? shade(c1, 1.25) : c1;
        s += rect(cx - cwid / 2, y0, cwid, y1 - y0, c, `stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.003))}"` + (isNew && kk < 1 ? ` opacity="${r1(0.3 + 0.7 * kk)}"` : ""));
        const vs = vstr(v, v), f = fitT(vs, cwid * 0.85, fsV);
        if (Math.abs(y1 - y0) > f * 1.15) s += txa(vs, cx, (y0 + y1) / 2, f, "#ffffff", 800);
        level += v;
      } else {
        const y0 = Y(level + v), y1 = Y(level);
        s += `<rect x="${r1(cx - cwid / 2)}" y="${r1(y1)}" width="${r1(cwid)}" height="${r1(y0 - y1)}" fill="${DOWN}" opacity="${r1(isNew ? 0.85 * (1 - kk) + 0.15 : 0.15)}"/>` +
          rect(cx - cwid / 2, y1, cwid, y0 - y1, "none", `stroke="${DOWN}" stroke-width="${r1(Math.max(3, w * 0.004))}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"`);
        level += v;
      }
    }
    const lab = (p.towerLabel ? p.towerLabel + " " : "") + vstr(level, vals[0]), fl = fitT(lab, colW * 0.95, fsCap);
    out += line(cx - colW * 0.42, base, cx + colW * 0.42, base, INK, Math.max(2, w * 0.003)) + s +
      pill(lab, cx, Math.min(Y(Math.max(...cum.slice(0, Math.max(1, shown)), 0)), Y(hi)) - fl * 1.3, fl, INK);
  } else if (gather) {
    const k = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
    let acc = 0;
    out += line(cx - colW * 0.42, base, cx + colW * 0.42, base, INK, Math.max(2, w * 0.003));
    for (let i = 0; i < shown; i++) {
      if (!(surplus[i] > 0)) continue;
      const fx = L + (i + 0.5) * slot - bw / 2, fy0 = Y(lineV), fy1 = Y(vals[i]);
      const tx0 = cx - cwid / 2, ty0 = Y(acc), ty1 = Y(acc + surplus[i]);
      const x = fx + (tx0 - fx) * k, y0 = fy0 + (ty0 - fy0) * k, y1 = fy1 + (ty1 - fy1) * k, wd = bw + (cwid - bw) * k;
      out += rect(x, y0, wd, y1 - y0, GOLD, `stroke="${shade(GOLD, 0.7)}" stroke-width="${r1(Math.max(2, w * 0.003))}"`);
      const sv = vstr(surplus[i], vals[i]), fsS = fitT(sv, wd * 0.9, fsV * 0.9);
      if (Math.abs(y1 - y0) > fsS * 1.2) out += txa(sv, x + wd / 2, (y0 + y1) / 2, fsS, "#6b4a00", 800);
      acc += surplus[i];
    }
    if (k >= 1 && sumSur > 0) {
      const lab = (p.gatherLabel ? p.gatherLabel + " " : "") + vstr(sumSur, vals[0]), fl = fitT(lab, colW * 0.95, fsCap);
      out += pill(lab, cx, Y(sumSur) - fl * 1.3, fl, "#6b4a00");
    }
  }
  if (p.title) out += tx(p.title, 0, Math.min(topY, towerMode !== "off" ? Y(hi) - fsCap * 3 : topY) - w * 0.035, fitT(p.title, w * 0.95, w * 0.042), INK, 800);
  return out;
}

// ---------------------------------------------------------------- waterfall
// A bridge from zero (or a start bar) to a total: each signed part steps up (green) or down (red) from the running
// level on its word, the level line and its tag follow, the total bar rises last.
function waterfall(p) {
  const w = Math.max(200, num(p.w, 1100)), unit = p.unit ?? "", dec = p.decimals;
  const ps = pairs(p.parts ?? "क:+100;ख:-40;ग:+150;घ:-10").map((d) => ({ l: d.l, v: Number.isFinite(d.v) ? d.v : 0, raw: d.f[0] || "" }));
  const st = String(p.start ?? ""), si = st.indexOf(":"), startV = tnum(si >= 0 ? st.slice(si + 1) : ""), startL = si >= 0 ? st.slice(0, si).trim() : "";
  const hasStart = Number.isFinite(startV), np = ps.length, upto = Math.max(0, Math.round(num(p.upto, 0)));
  const shownP = upto > 0 ? Math.min(np, upto) : np, showTotal = !!p.total && (upto === 0 || upto > np), grow = num(p.grow, 0.7);
  const glow = idxSet(p.glow);
  const levels = [hasStart ? startV : 0]; ps.forEach((d) => levels.push(levels[levels.length - 1] + d.v));
  const bars = [];
  if (hasStart) bars.push({ l: startL, a: 0, b: startV, c: TOTAL, kind: "start", v: startV });
  ps.forEach((d, i) => bars.push({ l: d.l, a: levels[i], b: levels[i + 1], c: d.v >= 0 ? UP : DOWN, kind: "part", v: d.v, gi: i + 1 }));
  if (p.total) bars.push({ l: String(p.total), a: 0, b: levels[np], c: TOTAL, kind: "total", v: levels[np] });
  const nb = bars.length;
  let lo = Math.min(0, ...levels), hi = Math.max(0, ...levels);
  if (!(hi > lo)) hi = lo + 1;
  const fsCap = w * 0.034, tagW = p.running === false ? 0 : Math.min(w * 0.16, Math.max(...levels.map((v) => tw("= " + withUnit(fmt(v, undefined, dec), unit), fsCap))) + fsCap);
  const L = -w / 2, R = w / 2 - tagW, slot = (R - L) / nb, bw = slot * 0.62;
  const fsV = Math.min(fsCap, ...bars.map((b) => fitT(b.kind === "part" ? signed(withUnit(fmt(b.v, undefined, dec), unit)) : withUnit(fmt(b.v, undefined, dec), unit), slot * 0.95, fsCap)));
  const fsL = Math.min(fsCap, ...bars.map((b) => fitT(b.l || " ", slot * 0.95, fsCap)));
  const ph = w * 0.4, fsT = w * 0.042, head = p.title ? fsT * 1.7 : 0;
  const H = head + fsV * 1.5 + ph + fsV * 1.5 + fsL * 1.8, top = -H / 2, pt = top + head + fsV * 1.5, pb = pt + ph;
  const Y = (v) => pb - ((v - lo) / (hi - lo)) * ph;
  let out = p.title ? tx(p.title, 0, top + fsT * 0.75, fitT(p.title, w * 0.95, fsT), INK, 800) : "";
  out += line(L, Y(0), R, Y(0), INK, Math.max(2, w * 0.003));
  const visible = bars.map((b, j) => (b.kind === "start" ? true : b.kind === "total" ? showTotal : b.gi <= shownP));
  const newest = upto > 0 ? (showTotal ? nb - 1 : bars.findIndex((b) => b.kind === "part" && b.gi === shownP)) : -1;
  const kNew = newest >= 0 ? easeIO(prog(sinceStep(p), grow)) : 1, kAll = upto > 0 ? 1 : easeIO(prog(sinceStart(p), grow));
  let runLevel = hasStart ? startV : 0, lastX = L;
  bars.forEach((b, j) => {
    if (!visible[j]) return;
    const k = j === newest ? kNew : kAll, x = L + (j + 0.5) * slot - bw / 2, end = b.a + (b.b - b.a) * k, g = b.kind === "part" && glow.has(b.gi);
    if (g) out += rect(L + j * slot + slot * 0.03, pt - fsV * 1.45, slot * 0.94, pb + fsV * 1.5 + fsL * 1.7 - pt + fsV * 1.45, GOLD, `opacity="0.25" rx="${r1(slot * 0.08)}"`);
    out += rect(x, Y(b.a), bw, Y(end) - Y(b.a), b.c, `rx="${r1(Math.min(bw * 0.06, Math.abs(Y(end) - Y(b.a)) / 2))}"` + (g ? ` stroke="${shade(GOLD, 0.8)}" stroke-width="${r1(Math.max(4, w * 0.006))}"` : ""));
    const vs = b.kind === "part" ? signed(withUnit(fmt(b.v * k, b.v, dec), unit)) : withUnit(fmt(b.v * k, b.v, dec), unit);
    const upw = b.b >= b.a, yv = upw ? Math.min(Y(b.a), Y(end)) - fsV * 0.75 : Math.max(Y(b.a), Y(end)) + fsV * 0.75;
    if (k > 0.05) out += txa(vs, x + bw / 2, yv, fsV, b.kind === "part" ? shade(b.c, 0.75) : INK, 800);
    out += txa(b.l, x + bw / 2, pb + fsV * 1.5 + fsL * 0.85, fitT(b.l || " ", slot * 0.95, fsL), INK, g ? 800 : 700);
    if (j > 0 && visible[j - 1] && b.kind !== "total") out += line(L + (j - 0.5) * slot + bw / 2, Y(b.a), x, Y(b.a), MUTED, Math.max(2, w * 0.0025), `stroke-dasharray="${r1(w * 0.006)} ${r1(w * 0.005)}"`);
    if (b.kind !== "total") { runLevel = end; lastX = x + bw; }
  });
  if (p.running !== false) {
    const y = Y(runLevel), t = "= " + withUnit(fmt(runLevel, levels[Math.min(np, shownP)], dec), unit), f = fitT(t, tagW - fsCap * 0.3, fsCap);
    out += line(lastX, y, R + fsCap * 0.1, y, INK, Math.max(2, w * 0.003), `stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.006)}"`) +
      pill(t, R + tagW / 2, y, f, INK);
  }
  return out;
}

// ---------------------------------------------------------------- pieChart
// A pie (roti) of shares: slices sweep in one by one on their numbers, morph to other values (from), the spoken slice
// glows and stands out, a small spike rises from one slice (the top 1%), names in a legend beside it.
function pieChart(p) {
  const w = Math.max(200, num(p.w, 1000)), unit = p.unit ?? "%", dec = p.decimals;
  let sl = pairs(p.slices ?? "क:50;ख:30;ग:20").map((d, i) => ({ l: d.l, v: Math.max(0, Number.isFinite(d.v) ? d.v : 0), i, c: okColor(d.f[1], PAL[i % PAL.length]) }));
  if (!sl.length) sl = [{ l: "", v: 1, i: 0, c: PAL[0] }];
  const fr = listN(p.from), gk = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
  sl.forEach((s) => { const f = fr[s.i]; s.cv = Number.isFinite(f) ? Math.max(0, f + (s.v - f) * gk) : s.v; });
  const n = sl.length, upto = Math.max(0, Math.round(num(p.upto, 0))), shown = upto > 0 ? Math.min(n, upto) : n, grow = num(p.grow, 0.8);
  const total = sl.reduce((a, s) => a + s.cv, 0) || 1, glow = idxSet(p.glow), legend = p.legend !== false && sl.some((s) => s.l);
  const fsT = w * 0.044, head = p.title ? fsT * 1.7 : 0;
  // legendSize: the legend's letters as a share of w (default 0.036); a small pie (two pies side by side) takes up to
  // 0.09 so its names stay readable, and the pie gives the legend the room
  const ls = Math.min(0.09, Math.max(0.02, num(p.legendSize, 0.036))), rowCap = Math.max(0.08, ls * 2.2);
  const R = legend ? w * Math.max(0.15, 0.24 - Math.max(0, ls - 0.036) * 1.6) : w * 0.36;
  const legFs = Math.min(w * ls, Math.min((2 * R) / sl.length, w * rowCap) * 0.5), legW = legend ? Math.min(w - R * 2.5, Math.max(...sl.map((s) => tw(s.l + "  00.0" + unit, legFs))) + legFs * 1.6) : 0;
  const cx = legend ? -(R * 2.25 + legW) / 2 + R : 0;
  const hole = p.donut === true ? R * 0.52 : 0;
  const [tk, tlab] = (() => { const s = String(p.tower ?? ""), i = s.indexOf(":"); return [Math.round(num(i >= 0 ? s.slice(0, i) : s, 0)), i >= 0 ? s.slice(i + 1).trim() : ""]; })();
  const hgt = R * clamp01(num(p.towerSize, 0.35)), towerOn = tk >= 1 && tk <= n, extra = towerOn ? hgt + R * 0.12 : 0;
  const Htot = head + extra + 2 * R, cy = -Htot / 2 + head + extra + R;
  let out = p.title ? tx(p.title, 0, -Htot / 2 + fsT * 0.75, fitT(p.title, w * 0.95, fsT), INK, 800) : "";
  out += `<circle cx="${r1(cx)}" cy="${r1(cy)}" r="${r1(R)}" fill="#eef0f3" stroke="#d5dbe1" stroke-width="${r1(Math.max(2, w * 0.003))}"/>`;
  let a0 = -Math.PI / 2;
  const fsV = Math.min(w * 0.036, R * 0.17), small = new Set();
  sl.forEach((s, j) => {
    const span = (s.cv / total) * Math.PI * 2;
    if (j < shown) {
      const k = growOf(p, j, shown, upto, grow), a1 = a0 + span * k, mid = (a0 + a1) / 2, g = glow.has(s.i + 1), off = g ? R * 0.07 : 0;
      const ox = cx + Math.cos(mid) * off, oy = cy + Math.sin(mid) * off, big = a1 - a0 > Math.PI ? 1 : 0;
      if (a1 - a0 > 1e-4) {
        const P = (a, r) => `${r1(ox + Math.cos(a) * r)} ${r1(oy + Math.sin(a) * r)}`;
        const d = a1 - a0 >= Math.PI * 2 - 1e-6
          ? `M${P(a0, R)} A${r1(R)} ${r1(R)} 0 1 1 ${P(a0 + Math.PI, R)} A${r1(R)} ${r1(R)} 0 1 1 ${P(a0, R)} Z`
          : hole ? `M${P(a0, R)} A${r1(R)} ${r1(R)} 0 ${big} 1 ${P(a1, R)} L${P(a1, hole)} A${r1(hole)} ${r1(hole)} 0 ${big} 0 ${P(a0, hole)} Z`
            : `M${r1(ox)} ${r1(oy)} L${P(a0, R)} A${r1(R)} ${r1(R)} 0 ${big} 1 ${P(a1, R)} Z`;
        out += `<path d="${d}" fill="${s.c}" stroke="${g ? shade(GOLD, 0.8) : "#ffffff"}" stroke-width="${r1(g ? Math.max(5, w * 0.007) : Math.max(2, w * 0.003))}" stroke-linejoin="round"/>`;
        const vs = withUnit(fmt(s.cv, s.v, dec), unit), rr = hole ? (R + hole) / 2 : R * 0.64, f = fitT(vs, R * 0.5, fsV);
        const room = (a1 - a0) * rr;
        if (p.values !== false) {
          if (ls <= 0.05 && room > tw(vs, f) * 1.1 && f >= fsV * 0.8 && k >= 1) out += txa(vs, ox + Math.cos(mid) * rr, oy + Math.sin(mid) * rr, f, "#ffffff", 800);
          else small.add(j);
        }
        if (tk === s.i + 1 && k >= 1) {                   // the spike rises straight up from the slice's highest point
          const top = a0 <= -Math.PI / 2 + 1e-9 || a1 >= Math.PI * 1.5 - 1e-9 ? -Math.PI / 2 : Math.sin(a0) < Math.sin(a1) ? a0 : a1;
          const x1 = ox + Math.cos(top) * R, y1 = oy + Math.sin(top) * R, x2 = x1, y2 = y1 - hgt;
          out += line(x1, y1, x2, y2, shade(s.c, 0.7), Math.max(8, w * 0.016), `stroke-linecap="round"`) + `<circle cx="${r1(x2)}" cy="${r1(y2)}" r="${r1(Math.max(7, w * 0.011))}" fill="${GOLD}" stroke="${shade(s.c, 0.7)}" stroke-width="${r1(Math.max(2, w * 0.003))}"/>`;
          if (tlab) { const f2 = fitT(tlab, w * 0.3, fsV), right = x2 <= cx + R * 0.3;
            out += txa(tlab, x2 + (right ? 1 : -1) * f2 * 0.6, y2, f2, shade(s.c, 0.6), 800, right ? "start" : "end"); }
        }
      }
    }
    a0 += span;
  });
  if (hole) out += `<circle cx="${r1(cx)}" cy="${r1(cy)}" r="${r1(hole)}" fill="#ffffff"/>` + (p.center ? tx(p.center, cx, cy, fitT(p.center, hole * 1.6, w * 0.04), INK, 800) : "");
  if (legend) {
    const lx = cx + R * 1.25, lw = w / 2 - lx, rh = Math.min((2 * R) / n, w * rowCap), fs = Math.min(w * ls, rh * 0.5);
    sl.forEach((s, j) => {
      const y = cy - (n * rh) / 2 + (j + 0.5) * rh, on = j < shown, g = glow.has(s.i + 1);
      const t = s.l + (small.has(j) ? "  " + withUnit(fmt(s.cv, s.v, dec), unit) : "");
      if (g) out += rect(lx - fs * 0.3, y - rh * 0.46, lw + fs * 0.2, rh * 0.92, GOLD, `opacity="0.35" rx="${r1(rh * 0.2)}"`);
      out += `<g opacity="${on ? 1 : 0.35}">` + rect(lx, y - fs * 0.45, fs * 0.9, fs * 0.9, s.c, `rx="${r1(fs * 0.15)}"`) + txa(t, lx + fs * 1.3, y, fitT(t, lw - fs * 1.5, fs), INK, g ? 800 : 700, "start") + `</g>`;
    });
  }
  return out;
}

// ---------------------------------------------------------------- shareBar
// Parts added to a whole one at a time with a running total tag; with overflow the parts may pass the whole (100%) and
// the excess is painted red (a rupee of extra pay split into tax, NI, lost credit and what is kept). Several bars
// ("a:1;b:2|a:3;b:4" with bars "1990;2014") make stacked shares over years.
function shareBar(p) {
  const w = Math.max(200, num(p.w, 1200)), unit = p.unit ?? "%", dec = p.decimals;
  const rowsRaw = String(p.parts ?? "क:20;ख:12;ग:41;घ:27").split("|");
  const rows = rowsRaw.map((r) => pairs(r).map((d, i) => ({ l: d.l, v: Math.max(0, Number.isFinite(d.v) ? d.v : 0), i })));
  const multi = rows.length > 1, rl = parts(p.bars), whole = num(p.whole, 100) > 0 ? num(p.whole, 100) : 100;
  const upto = Math.max(0, Math.round(num(p.upto, 0))), grow = num(p.grow, 0.7), glow = idxSet(p.glow), over = p.overflow === true;
  const fr = listN(p.from), gk = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
  if (!multi) rows[0].forEach((s) => { const f = fr[s.i]; s.cv = Number.isFinite(f) ? Math.max(0, f + (s.v - f) * gk) : s.v; });
  else rows.forEach((r) => r.forEach((s) => (s.cv = s.v)));
  const fsT = w * 0.04;
  let out = "";
  if (!multi) {
    const segs = rows[0], n = segs.length, shown = upto > 0 ? Math.min(n, upto) : n, h = w * 0.12;
    const sum = segs.reduce((a, s) => a + s.cv, 0), full = Math.max(whole, over ? sum : whole);
    const scale = over ? Math.max(whole * 1.18, sum) : Math.max(whole, sum), bw = w * 0.92, x0 = -bw / 2, X = (v) => x0 + (v / scale) * bw;
    const frameW = over ? X(whole) - x0 : X(Math.max(whole, sum)) - x0;
    out += rect(x0 - 3, -h / 2 - 3, frameW + 6, h + 6, "none", `rx="${r1(h * 0.12)}" stroke="#2d3748" stroke-width="3"`);
    let acc = 0, narrow = 0, endX = x0;
    const k = (j) => growOf(p, j, shown, upto, grow);
    for (let j = 0; j < shown; j++) {
      const s = segs[j], kk = k(j), c = PAL[s.i % PAL.length], from = X(acc), wd = (s.cv / scale) * bw, slide = (1 - kk) * w * 0.25;
      const xs = from + slide, g = glow.has(s.i + 1);
      out += `<g opacity="${r1(0.2 + 0.8 * kk)}">` + rect(xs, -h / 2, wd, h, c, `stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.004))}"`);
      if (over && acc + s.cv > whole) {                       // the part past the whole, painted red and hatched
        const ex0 = Math.max(xs, X(whole) + slide), ex1 = xs + wd;
        out += rect(ex0, -h / 2, ex1 - ex0, h, DOWN, `opacity="0.85"`) + `<path d="${Array.from({ length: Math.max(1, Math.ceil((ex1 - ex0) / (h * 0.25))) }, (_, q) => `M${r1(ex0 + q * h * 0.25)} ${r1(h / 2)} L${r1(Math.min(ex1, ex0 + q * h * 0.25 + h * 0.4))} ${r1(-h / 2)}`).join(" ")}" stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.003))}" opacity="0.55"/>`;
      }
      const vs = withUnit(fmt(s.cv, s.v, dec), unit), fsIn = Math.min(h * 0.32, fitT(s.l || vs, wd * 0.9, h * 0.32), p.values === false ? h * 0.32 : fitT(vs, wd * 0.9, h * 0.32));
      if (fsIn >= h * 0.24) out += (s.l ? tx(s.l, xs + wd / 2, -h * 0.13, fsIn, "#ffffff", 800) : "") + (p.values === false ? "" : tx(vs, xs + wd / 2, s.l ? h * 0.23 : 0, fsIn * 0.9, "#ffffff", 700));
      else if (kk >= 1) { const below = narrow++ % 2 === 0, fo = Math.min(h * 0.3, w * 0.034), yy = below ? h / 2 + fo * 1.3 : -h / 2 - fo * 1.3, t = s.l + (p.values === false ? "" : " " + vs);
        out += line(xs + wd / 2, below ? h / 2 : -h / 2, xs + wd / 2, below ? yy - fo * 0.6 : yy + fo * 0.6, c, 3) + tx(t, xs + wd / 2, yy, fitT(t, w * 0.3, fo), shade(c, 0.8), 800); }
      if (g) out += rect(xs - 4, -h / 2 - 4, wd + 8, h + 8, "none", `stroke="${GOLD}" stroke-width="${r1(Math.max(5, h * 0.07))}"`);
      out += `</g>`;
      acc += s.cv * kk; endX = X(acc);
    }
    if (over) {
      const xw = X(whole), wl = p.wholeLabel ?? withUnit(fmt(whole, whole, dec), unit), fw = Math.min(w * 0.034, h * 0.3);
      out += line(xw, -h / 2 - h * 0.25, xw, h / 2 + h * 0.25, INK, Math.max(4, w * 0.004)) + (wl ? tx(wl, xw, h / 2 + h * 0.25 + fw * 1.4 + (narrow ? fw * 1.6 : 0), fw, INK, 800) : "");
    }
    if (p.running === true && shown > 0) {
      const t = String(p.runningLabel || "{v}").replace("{v}", withUnit(fmt(acc, segs.slice(0, shown).reduce((a, s) => a + s.cv, 0), dec), unit)), f = Math.min(w * 0.036, h * 0.34);
      const half = tw(t, f) / 2 + f * 0.5, xr = Math.max(x0 + half, Math.min(w / 2 - half, endX)), yr = -h / 2 - f * 1.6 - (narrow > 1 ? f * 1.9 : 0);
      out += `<path d="M${r1(endX)} ${r1(-h / 2 - 2)} L${r1(endX - f * 0.35)} ${r1(yr + f * 0.7)} L${r1(endX + f * 0.35)} ${r1(yr + f * 0.7)} Z" fill="${INK}"/>` + pill(t, xr, yr, f, INK);
    }
    if (p.label) out += tx(p.label, 0, -h / 2 - h * 0.5 - (p.running === true ? Math.min(w * 0.036, h * 0.34) * 2.1 : 0) - (narrow > 1 ? h * 0.4 : 0) - w * 0.02, fitT(p.label, w * 0.9, fsT), INK, 800);
    return out;
  }
  // several bars: stacked shares, one row per year (upto reveals rows)
  const nr = rows.length, shownR = upto > 0 ? Math.min(nr, upto) : nr, names = rows[0].map((s) => s.l);
  const rh = Math.min(w * 0.1, (w * 0.6) / nr), fs = Math.min(w * 0.034, rh * 0.42), lw = Math.min(w * 0.18, Math.max(0, ...rl.map((t) => tw(t, fs))) + fs * 0.8);
  const bx0 = -w / 2 + lw, bw = w / 2 - bx0, legH = names.some(Boolean) ? fs * 2.2 : 0, head = (p.label ? fsT * 1.6 : 0) + legH;
  const H = head + nr * rh, top = -H / 2;
  if (p.label) out += tx(p.label, 0, top + fsT * 0.7, fitT(p.label, w * 0.95, fsT), INK, 800);
  if (legH) {
    const fl = fs, items = names.map((nm, i) => ({ nm, w: fl * 1.4 + tw(nm, fl) })), tot = items.reduce((a, it) => a + it.w, 0) + fl * (items.length - 1);
    const sc = Math.min(1, (w * 0.98) / tot); let x = -Math.min(tot, w * 0.98) / 2;
    items.forEach((it, i) => { out += rect(x, top + head - legH / 2 - fl * sc * 0.45, fl * sc * 0.9, fl * sc * 0.9, PAL[i % PAL.length], `rx="${r1(fl * 0.15)}"`) + txa(it.nm, x + fl * sc * 1.25, top + head - legH / 2, fl * sc, glow.has(i + 1) ? INK : "#3b4250", glow.has(i + 1) ? 800 : 700, "start"); x += (it.w + fl) * sc; });
  }
  rows.forEach((segs, r) => {
    const y = top + head + r * rh, sum = segs.reduce((a, s) => a + s.cv, 0) || 1;
    out += txa(rl[r] ?? "", bx0 - fs * 0.4, y + rh / 2, fitT(rl[r] ?? "", lw - fs * 0.6, fs), INK, 800, "end");
    if (r >= shownR) return;
    const k = upto > 0 && r === shownR - 1 ? easeIO(prog(sinceStep(p), grow)) : upto > 0 ? 1 : easeIO(prog(sinceStart(p), grow));
    let x = bx0;
    segs.forEach((s) => {
      const wd = (s.cv / sum) * bw * k, c = PAL[s.i % PAL.length], g = glow.has(s.i + 1), vs = withUnit(fmt(s.cv, s.v, dec), unit);
      out += rect(x, y + rh * 0.12, wd, rh * 0.76, c, `stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.003))}"`) + (g ? rect(x - 3, y + rh * 0.08, wd + 6, rh * 0.84, "none", `stroke="${GOLD}" stroke-width="${r1(Math.max(4, rh * 0.06))}"`) : "");
      const f = fitT(vs, wd * 0.9, fs);
      if (p.values !== false && k >= 1 && f >= fs * 0.75) out += tx(vs, x + wd / 2, y + rh / 2, f, "#ffffff", 800);
      x += wd;
    });
  });
  return out;
}

// ---------------------------------------------------------------- pictogram
// n identical things (cups, tea glasses, scooters, sacks, seats, people, packets, shares, barrels, blocks of hours,
// coins, notes, houses, cars, plates) of which on are lit; a step that moves on from `from` turns them off (or pops them
// in) one after another on the number word. Row labels make a week of hours; count writes the live count.
const ICON_COLOR = { cup: "#e07b24", tea: "#b5651d", scooter: "#e5484d", sack: "#c08a3e", seat: "#3a7bd5", person: "#3a7bd5", packet: "#e2558f",
  share: "#c0563f", barrel: "#2d3748", block: "#2a9d8f", coin: "#f2c14e", note: "#1f8a70", house: "#c0563f", car: "#2459a6", plate: "#d9a44a" };
function iconSvg(kind, s, c) {
  const d = shade(c, 0.7), sw = r1(Math.max(1.5, s * 0.03)), h = s / 2;
  switch (kind) {
    case "cup": return `<path d="M${r1(-h * 0.62)} ${r1(-h * 0.45)} L${r1(h * 0.42)} ${r1(-h * 0.45)} L${r1(h * 0.32)} ${r1(h * 0.5)} Q${r1(-h * 0.1)} ${r1(h * 0.62)} ${r1(-h * 0.52)} ${r1(h * 0.5)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(h * 0.4)} ${r1(-h * 0.25)} Q${r1(h * 0.85)} ${r1(-h * 0.25)} ${r1(h * 0.78)} ${r1(h * 0.05)} Q${r1(h * 0.72)} ${r1(h * 0.3)} ${r1(h * 0.34)} ${r1(h * 0.3)}" fill="none" stroke="${d}" stroke-width="${r1(s * 0.06)}"/>` +
      `<ellipse cx="${r1(-h * 0.1)}" cy="${r1(-h * 0.45)}" rx="${r1(h * 0.52)}" ry="${r1(h * 0.12)}" fill="#7a3f12"/><ellipse cx="${r1(-h * 0.1)}" cy="${r1(h * 0.66)}" rx="${r1(h * 0.78)}" ry="${r1(h * 0.13)}" fill="${shade(c, 1.3)}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.3)} ${r1(-h * 0.62)} q${r1(h * 0.12)} ${r1(-h * 0.15)} 0 ${r1(-h * 0.3)} M${r1(h * 0.05)} ${r1(-h * 0.62)} q${r1(h * 0.12)} ${r1(-h * 0.15)} 0 ${r1(-h * 0.3)}" stroke="#9aa5b1" stroke-width="${sw}" fill="none" stroke-linecap="round"/>`;
    case "tea": return `<path d="M${r1(-h * 0.42)} ${r1(-h * 0.7)} L${r1(h * 0.42)} ${r1(-h * 0.7)} L${r1(h * 0.3)} ${r1(h * 0.75)} L${r1(-h * 0.3)} ${r1(h * 0.75)} Z" fill="#eaf2f7" stroke="#9db3c7" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.39)} ${r1(-h * 0.35)} L${r1(h * 0.39)} ${r1(-h * 0.35)} L${r1(h * 0.3)} ${r1(h * 0.72)} L${r1(-h * 0.3)} ${r1(h * 0.72)} Z" fill="${c}"/><path d="M${r1(-h * 0.39)} ${r1(-h * 0.35)} L${r1(h * 0.39)} ${r1(-h * 0.35)}" stroke="${shade(c, 1.4)}" stroke-width="${r1(s * 0.05)}"/>` +
      `<path d="M${r1(-h * 0.2)} ${r1(-h * 0.2)} L${r1(-h * 0.14)} ${r1(h * 0.55)}" stroke="#ffffff" stroke-width="${sw}" opacity="0.5"/>`;
    case "scooter": return `<circle cx="${r1(-h * 0.55)}" cy="${r1(h * 0.55)}" r="${r1(h * 0.25)}" fill="${INK}"/><circle cx="${r1(h * 0.62)}" cy="${r1(h * 0.55)}" r="${r1(h * 0.25)}" fill="${INK}"/>` +
      `<circle cx="${r1(-h * 0.55)}" cy="${r1(h * 0.55)}" r="${r1(h * 0.1)}" fill="#cfd6de"/><circle cx="${r1(h * 0.62)}" cy="${r1(h * 0.55)}" r="${r1(h * 0.1)}" fill="#cfd6de"/>` +
      `<path d="M${r1(-h * 0.88)} ${r1(h * 0.45)} C${r1(-h * 0.95)} ${r1(0)} ${r1(-h * 0.72)} ${r1(-h * 0.22)} ${r1(-h * 0.3)} ${r1(-h * 0.2)} L${r1(-h * 0.08)} ${r1(-h * 0.2)} L${r1(-h * 0.02)} ${r1(h * 0.28)} L${r1(h * 0.28)} ${r1(h * 0.28)} L${r1(h * 0.42)} ${r1(-h * 0.58)} L${r1(h * 0.62)} ${r1(-h * 0.58)} L${r1(h * 0.82)} ${r1(h * 0.45)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}" stroke-linejoin="round"/>` +
      `<rect x="${r1(-h * 0.66)}" y="${r1(-h * 0.36)}" width="${r1(h * 0.56)}" height="${r1(h * 0.17)}" rx="${r1(h * 0.08)}" fill="${INK}"/>` +
      `<path d="M${r1(h * 0.3)} ${r1(-h * 0.66)} L${r1(h * 0.78)} ${r1(-h * 0.66)}" stroke="${INK}" stroke-width="${r1(s * 0.06)}" stroke-linecap="round"/><circle cx="${r1(h * 0.6)}" cy="${r1(-h * 0.4)}" r="${r1(h * 0.08)}" fill="#fff3c4"/>`;
    case "sack": return `<path d="M${r1(-h * 0.7)} ${r1(h * 0.75)} Q${r1(-h * 0.9)} ${r1(-h * 0.2)} ${r1(-h * 0.3)} ${r1(-h * 0.55)} L${r1(-h * 0.22)} ${r1(-h * 0.8)} L${r1(h * 0.22)} ${r1(-h * 0.8)} L${r1(h * 0.3)} ${r1(-h * 0.55)} Q${r1(h * 0.9)} ${r1(-h * 0.2)} ${r1(h * 0.7)} ${r1(h * 0.75)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.26)} ${r1(-h * 0.6)} L${r1(h * 0.26)} ${r1(-h * 0.6)}" stroke="${d}" stroke-width="${r1(s * 0.06)}" stroke-linecap="round"/>`;
    case "seat": return `<rect x="${r1(-h * 0.5)}" y="${r1(-h * 0.85)}" width="${r1(h * 0.95)}" height="${r1(h * 1.05)}" rx="${r1(h * 0.18)}" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<rect x="${r1(-h * 0.62)}" y="${r1(h * 0.1)}" width="${r1(h * 1.3)}" height="${r1(h * 0.38)}" rx="${r1(h * 0.12)}" fill="${shade(c, 0.85)}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.45)} ${r1(h * 0.48)} L${r1(-h * 0.45)} ${r1(h * 0.85)} M${r1(h * 0.5)} ${r1(h * 0.48)} L${r1(h * 0.5)} ${r1(h * 0.85)}" stroke="${INK}" stroke-width="${r1(s * 0.06)}" stroke-linecap="round"/>`;
    case "person": return `<path d="M${r1(-h * 0.5)} ${r1(h * 0.9)} L${r1(-h * 0.5)} ${r1(h * 0.05)} Q${r1(-h * 0.5)} ${r1(-h * 0.32)} 0 ${r1(-h * 0.32)} Q${r1(h * 0.5)} ${r1(-h * 0.32)} ${r1(h * 0.5)} ${r1(h * 0.05)} L${r1(h * 0.5)} ${r1(h * 0.9)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<circle cy="${r1(-h * 0.62)}" r="${r1(h * 0.27)}" fill="#c68a5c" stroke="${shade("#c68a5c")}" stroke-width="${sw}"/>`;
    case "packet": return `<path d="M${r1(-h * 0.55)} ${r1(-h * 0.75)} L${r1(h * 0.55)} ${r1(-h * 0.75)} L${r1(h * 0.5)} ${r1(h * 0.8)} L${r1(-h * 0.5)} ${r1(h * 0.8)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.55)} ${r1(-h * 0.75)} l${r1(h * 0.14)} ${r1(-h * 0.12)} l${r1(h * 0.14)} ${r1(h * 0.12)} l${r1(h * 0.14)} ${r1(-h * 0.12)} l${r1(h * 0.14)} ${r1(h * 0.12)} l${r1(h * 0.14)} ${r1(-h * 0.12)} l${r1(h * 0.14)} ${r1(h * 0.12)} l${r1(h * 0.14)} ${r1(-h * 0.12)} l${r1(h * 0.1)} ${r1(h * 0.12)}" fill="${shade(c, 0.85)}" stroke="${d}" stroke-width="${sw}"/>` +
      `<circle cy="${r1(h * 0.05)}" r="${r1(h * 0.3)}" fill="#ffffff" opacity="0.85"/><circle cy="${r1(h * 0.05)}" r="${r1(h * 0.16)}" fill="${GOLD}"/>`;
    case "share": return `<rect x="${r1(-h * 0.62)}" y="${r1(-h * 0.8)}" width="${r1(h * 1.24)}" height="${r1(h * 1.6)}" rx="${r1(h * 0.08)}" fill="#fbefe9" stroke="${c}" stroke-width="${r1(s * 0.04)}"/>` +
      `<path d="M${r1(-h * 0.4)} ${r1(-h * 0.4)} L${r1(h * 0.4)} ${r1(-h * 0.4)} M${r1(-h * 0.4)} ${r1(-h * 0.1)} L${r1(h * 0.4)} ${r1(-h * 0.1)} M${r1(-h * 0.4)} ${r1(h * 0.2)} L${r1(h * 0.1)} ${r1(h * 0.2)}" stroke="${shade(c, 1.2)}" stroke-width="${r1(s * 0.04)}" stroke-linecap="round"/>` +
      `<circle cx="${r1(h * 0.28)}" cy="${r1(h * 0.48)}" r="${r1(h * 0.2)}" fill="${c}"/>`;
    case "barrel": return `<path d="M${r1(-h * 0.55)} ${r1(-h * 0.78)} Q${r1(-h * 0.7)} 0 ${r1(-h * 0.55)} ${r1(h * 0.78)} L${r1(h * 0.55)} ${r1(h * 0.78)} Q${r1(h * 0.7)} 0 ${r1(h * 0.55)} ${r1(-h * 0.78)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.64)} ${r1(-h * 0.3)} L${r1(h * 0.64)} ${r1(-h * 0.3)} M${r1(-h * 0.64)} ${r1(h * 0.3)} L${r1(h * 0.64)} ${r1(h * 0.3)}" stroke="${shade(c, 1.6)}" stroke-width="${r1(s * 0.05)}"/>` +
      `<ellipse cy="${r1(-h * 0.78)}" rx="${r1(h * 0.55)}" ry="${r1(h * 0.12)}" fill="${shade(c, 1.4)}" stroke="${d}" stroke-width="${sw}"/><circle cx="${r1(h * 0.25)}" cy="${r1(-h * 0.78)}" r="${r1(h * 0.06)}" fill="${d}"/>`;
    case "block": return `<rect x="${r1(-h * 0.82)}" y="${r1(-h * 0.82)}" width="${r1(h * 1.64)}" height="${r1(h * 1.64)}" rx="${r1(h * 0.22)}" fill="${c}" stroke="${d}" stroke-width="${sw}"/>`;
    case "coin": return `<circle r="${r1(h * 0.8)}" fill="${c}" stroke="${shade(c, 0.7)}" stroke-width="${r1(s * 0.06)}"/><circle r="${r1(h * 0.56)}" fill="none" stroke="${shade(c, 0.7)}" stroke-width="${r1(s * 0.03)}"/>` + tx("₹", 0, 0, h * 0.8, shade(c, 0.55), 800);
    case "note": return `<rect x="${r1(-h * 0.9)}" y="${r1(-h * 0.45)}" width="${r1(h * 1.8)}" height="${r1(h * 0.9)}" rx="${r1(h * 0.06)}" fill="${c}" stroke="${d}" stroke-width="${sw}"/><circle cx="${r1(-h * 0.45)}" r="${r1(h * 0.27)}" fill="#f7f1e5" opacity="0.9"/>` +
      `<rect x="${r1(h * 0.62)}" y="${r1(-h * 0.38)}" width="${r1(h * 0.09)}" height="${r1(h * 0.76)}" fill="#f7f1e5" opacity="0.5"/>`;
    case "house": return `<rect x="${r1(-h * 0.6)}" y="${r1(-h * 0.15)}" width="${r1(h * 1.2)}" height="${r1(h * 0.95)}" fill="#f4ead9" stroke="${d}" stroke-width="${sw}"/><path d="M${r1(-h * 0.8)} ${r1(-h * 0.1)} L0 ${r1(-h * 0.85)} L${r1(h * 0.8)} ${r1(-h * 0.1)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}" stroke-linejoin="round"/>` +
      `<rect x="${r1(-h * 0.15)}" y="${r1(h * 0.25)}" width="${r1(h * 0.3)}" height="${r1(h * 0.55)}" fill="${d}"/>`;
    case "car": return `<path d="M${r1(-h * 0.9)} ${r1(h * 0.4)} L${r1(-h * 0.9)} ${r1(0)} Q${r1(-h * 0.85)} ${r1(-h * 0.12)} ${r1(-h * 0.6)} ${r1(-h * 0.15)} L${r1(-h * 0.35)} ${r1(-h * 0.55)} L${r1(h * 0.35)} ${r1(-h * 0.55)} L${r1(h * 0.6)} ${r1(-h * 0.15)} Q${r1(h * 0.9)} ${r1(-h * 0.1)} ${r1(h * 0.9)} ${r1(h * 0.1)} L${r1(h * 0.9)} ${r1(h * 0.4)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.28)} ${r1(-h * 0.45)} L${r1(-h * 0.45)} ${r1(-h * 0.17)} L${r1(h * 0.45)} ${r1(-h * 0.17)} L${r1(h * 0.28)} ${r1(-h * 0.45)} Z" fill="#cfe3f5"/>` +
      `<circle cx="${r1(-h * 0.5)}" cy="${r1(h * 0.42)}" r="${r1(h * 0.22)}" fill="${INK}"/><circle cx="${r1(h * 0.5)}" cy="${r1(h * 0.42)}" r="${r1(h * 0.22)}" fill="${INK}"/>`;
    case "plate": return `<ellipse cy="${r1(h * 0.35)}" rx="${r1(h * 0.9)}" ry="${r1(h * 0.3)}" fill="#f2f4f7" stroke="#aab4c0" stroke-width="${sw}"/>` +
      `<path d="M${r1(-h * 0.6)} ${r1(h * 0.3)} L${r1(-h * 0.2)} ${r1(-h * 0.45)} L${r1(h * 0.15)} ${r1(h * 0.3)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}" stroke-linejoin="round"/>` +
      `<path d="M${r1(-h * 0.05)} ${r1(h * 0.3)} L${r1(h * 0.3)} ${r1(-h * 0.35)} L${r1(h * 0.62)} ${r1(h * 0.3)} Z" fill="${shade(c, 1.1)}" stroke="${d}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    default: return `<circle r="${r1(h * 0.7)}" fill="${c}"/>`;
  }
}
const PICTO_ICONS = Object.keys(ICON_COLOR);
function pictogram(p) {
  const w = Math.max(100, num(p.w, 900)), icon = PICTO_ICONS.includes(p.icon) ? p.icon : "cup";
  const n = Math.max(1, Math.min(120, Math.round(num(p.n, 6)))), on = num(p.on, -1) < 0 ? n : Math.max(0, Math.min(n, Math.round(num(p.on, n))));
  const from = isNum(p.from) && +p.from >= 0 ? Math.max(0, Math.min(n, Math.round(+p.from))) : on;
  const rowL = parts(p.rowLabels).filter((x, i, a) => a.length > 1 || x);
  const autoCols = () => { if (n <= 10) return n; const t = Math.ceil(Math.sqrt(n * 2.2)); let best = t, bad = Infinity;
    for (let c = Math.max(2, t - 4); c <= t + 4; c++) { const r = n % c, b = (r ? c - r : 0) * 2 + Math.abs(c - t); if (b < bad) { bad = b; best = c; } } return best; };
  const cols = Math.round(num(p.cols, 0)) > 0 ? Math.min(n, Math.round(num(p.cols, 0))) : autoCols();
  const rows = Math.ceil(n / cols), c = okColor(p.color, ICON_COLOR[icon]), off = ["fade", "hide", "cross"].includes(p.off) ? p.off : "fade";
  const fsR = w * 0.036, lw = rowL.length ? Math.min(w * 0.22, Math.max(...rowL.map((t) => tw(t, fsR))) + fsR * 0.6) : 0;
  const s = Math.min((w - lw) / cols, w * 0.2), gw = s * cols, x0 = -w / 2 + lw + (w - lw - gw) / 2;
  const each = Math.max(0, num(p.each, 0.22)), since = sinceStep(p), startFirst = p.order === "start";
  const litIdx = (j, k) => (startFirst ? j >= n - k : j < k);
  // which icons change, in the order they change: the ones nearest the lit edge last when turning off, first when popping in
  const changing = [];
  for (let j = 0; j < n; j++) if (litIdx(j, on) !== litIdx(j, from)) changing.push(j);
  if (on < from) changing.sort((a, b) => (startFirst ? a - b : b - a)); else changing.sort((a, b) => (startFirst ? b - a : a - b));
  const order = new Map(changing.map((j, q) => [j, q]));
  const fsCount = w * 0.05, hasCount = !!p.count, fsLab = w * 0.042;
  const H = rows * s + (hasCount ? fsCount * 1.7 : 0) + (p.label ? fsLab * 1.7 : 0), top = -H / 2, gy0 = top + (hasCount ? fsCount * 1.7 : 0);
  let out = `<rect x="${r1(x0)}" y="${r1(gy0)}" width="${r1(gw)}" height="${r1(rows * s)}" fill="none"/>`, lit = 0;   // the grid keeps its box when things go dark
  for (let j = 0; j < n; j++) {
    const r = Math.floor(j / cols), cc = j % cols, x = x0 + (cc + 0.5) * s, y = gy0 + (r + 0.5) * s;
    let a = litIdx(j, on) ? 1 : 0;
    if (order.has(j)) { const k = Number.isFinite(since) ? clamp01((since - order.get(j) * each) / 0.3) : 1; a = on < from ? 1 - k : k; }
    if (a > 0.5) lit++;
    const pop = order.has(j) && on > from && a > 0 && a < 1 ? 1 + 0.25 * Math.sin(a * Math.PI) : 1;
    const ghost = off === "hide" ? 0 : off === "cross" ? 0.55 : 0.16, op = ghost + (1 - ghost) * a;
    if (op <= 0.01) continue;
    out += `<g transform="translate(${r1(x)},${r1(y)}) scale(${r1(pop * 100) / 100})" opacity="${r1(op * 100) / 100}">${iconSvg(icon, s * 0.84, a > 0.5 || off !== "fade" ? c : "#9aa5b1")}</g>`;
    if (off === "cross" && a < 0.5) out += line(x - s * 0.36, y - s * 0.36, x + s * 0.36, y + s * 0.36, DOWN, s * 0.08, `stroke-linecap="round"`) + line(x + s * 0.36, y - s * 0.36, x - s * 0.36, y + s * 0.36, DOWN, s * 0.08, `stroke-linecap="round"`);
  }
  rowL.forEach((t, r) => { if (r < rows) out += txa(t, x0 - fsR * 0.4, gy0 + (r + 0.5) * s, fitT(t, lw - fsR * 0.5, Math.min(fsR, s * 0.5)), INK, 800, "end"); });
  if (hasCount) { const t = String(p.count).replace("{n}", String(lit)).replace("{total}", String(n)); out += tx(t, 0, top + fsCount * 0.75, fitT(t, w * 0.9, fsCount), INK, 800); }
  if (p.label) out += tx(p.label, 0, gy0 + rows * s + fsLab * 0.9, fitT(p.label, w * 0.95, fsLab), INK, 800);
  return out;
}

// ---------------------------------------------------------------- iconArray
// A frequency grid for base rates: n small people coloured by group (with their real counts), then a second split marks
// some of each group (tested positive, claims), and on gather the marked ones come together so their split is seen.
function iconArray(p) {
  const w = Math.max(100, num(p.w, 1000)), n = Math.max(1, Math.min(1000, Math.round(num(p.n, 100))));
  const shape = ["person", "dot", "square"].includes(p.shape) ? p.shape : "person";
  let groups = pairs(p.groups ?? "क:10;ख:90").map((d, i) => ({ l: d.l, count: Math.max(0, Number.isFinite(d.v) ? d.v : 0), c: okColor(d.f[1], PAL[(i * 3 + 1) % PAL.length]), i }));
  if (!groups.length) groups = [{ l: "", count: n, c: PAL[0], i: 0 }];
  const total = groups.reduce((a, g) => a + g.count, 0) || 1;
  // icons per group by the largest remainder, so they add to n
  const ex = groups.map((g) => (g.count / total) * n), base = ex.map(Math.floor);
  let left = n - base.reduce((a, b) => a + b, 0);
  ex.map((e, i) => [e - Math.floor(e), i]).sort((a, b) => b[0] - a[0]).forEach(([, i]) => { if (left > 0) { base[i]++; left--; } });
  const split = listN(p.split), marksOn = p.marks === true && split.some(Number.isFinite);
  groups.forEach((g, i) => { g.icons = base[i]; const m = Number.isFinite(split[i]) ? Math.max(0, split[i]) : 0; g.marked = m; g.mIcons = g.count > 0 ? Math.min(g.icons, Math.max(m > 0 ? 1 : 0, Math.round((m / g.count) * g.icons))) : 0; });
  const cols = Math.round(num(p.cols, 0)) > 0 ? Math.min(n, Math.round(num(p.cols, 0))) : Math.max(1, Math.min(n, Math.ceil(Math.sqrt(n * 2))));
  const rows = Math.ceil(n / cols), cell = w / cols, upto = Math.max(0, Math.round(num(p.upto, 0))), hl = Math.round(num(p.highlight, 0));
  // two layouts: by group (marked first inside each group), and gathered (all marked first)
  const icons = [];
  groups.forEach((g) => { for (let k = 0; k < g.icons; k++) icons.push({ g, m: marksOn && k < g.mIcons }); });
  const slotA = icons.map((_, j) => j), orderB = icons.map((ic, j) => [ic.m ? 0 : 1, j]).sort((a, b) => a[0] - b[0] || a[1] - b[1]), slotB = new Array(icons.length);
  orderB.forEach(([, j], q) => (slotB[j] = q));
  const gk = p.gather === true && marksOn ? easeIO(prog(sinceStep(p), num(p.glide, 1.4))) : 0;
  const markK = marksOn ? easeIO(prog(sinceStep(p), 0.6)) : 0;
  const markKind = ["ring", "dot", "tick", "cross"].includes(p.mark) ? p.mark : "ring";
  const fs = Math.min(w * 0.036, w * 0.05), titleH = p.title ? w * 0.06 : 0;
  const legRows = groups.length, legH = legRows * fs * 1.6 + (p.per ? fs * 1.5 : 0) + (p.gather === true && marksOn && p.gatherLabel ? fs * 1.9 : 0);
  const H = titleH + rows * cell + fs * 0.6 + legH, top = -H / 2, gy0 = top + titleH, x0 = -w / 2;
  let out = p.title ? tx(p.title, 0, top + titleH * 0.45, fitT(p.title, w * 0.95, w * 0.042), INK, 800) : "";
  const pos = (q) => [x0 + ((q % cols) + 0.5) * cell, gy0 + (Math.floor(q / cols) + 0.5) * cell];
  icons.forEach((ic, j) => {
    const [ax, ay] = pos(slotA[j]), [bx, by] = pos(slotB[j]), x = ax + (bx - ax) * gk, y = ay + (by - ay) * gk;
    const coloured = upto === 0 || ic.g.i < upto, col = coloured ? ic.g.c : "#c5ccd6", dim = (hl > 0 && ic.g.i + 1 !== hl) || (gk > 0.5 && !ic.m) ? 0.3 : 1;
    const s = cell * 0.84;
    let body;
    if (shape === "dot") body = `<circle r="${r1(s * 0.42)}" fill="${col}"/>`;
    else if (shape === "square") body = `<rect x="${r1(-s * 0.4)}" y="${r1(-s * 0.4)}" width="${r1(s * 0.8)}" height="${r1(s * 0.8)}" rx="${r1(s * 0.12)}" fill="${col}"/>`;
    else body = `<circle cy="${r1(-s * 0.26)}" r="${r1(s * 0.17)}" fill="${col}"/><path d="M${r1(-s * 0.3)} ${r1(s * 0.44)} L${r1(-s * 0.3)} ${r1(s * 0.08)} Q${r1(-s * 0.3)} ${r1(-s * 0.06)} 0 ${r1(-s * 0.06)} Q${r1(s * 0.3)} ${r1(-s * 0.06)} ${r1(s * 0.3)} ${r1(s * 0.08)} L${r1(s * 0.3)} ${r1(s * 0.44)} Z" fill="${col}"/>`;
    let mark = "";
    if (ic.m && markK > 0) {
      const mk = s * 0.5 * markK;
      mark = markKind === "ring" ? `<circle r="${r1(s * 0.5)}" fill="none" stroke="${INK}" stroke-width="${r1(Math.max(1.5, s * 0.1 * markK))}"/>`
        : markKind === "dot" ? `<circle cx="${r1(s * 0.3)}" cy="${r1(-s * 0.3)}" r="${r1(mk * 0.38)}" fill="${INK}" stroke="#ffffff" stroke-width="${r1(Math.max(1, s * 0.04))}"/>`
          : markKind === "tick" ? tick(s * 0.28, -s * 0.28, mk) : cross(s * 0.28, -s * 0.28, mk);
    }
    out += `<g transform="translate(${r1(x)},${r1(y)})" opacity="${dim}">${body}${mark}</g>`;
  });
  // the legend: each group's name, count and marked count
  let ly = gy0 + rows * cell + fs * 0.6;
  if (p.gather === true && marksOn && p.gatherLabel && gk >= 1) {
    const tot = groups.reduce((a, g) => a + g.marked, 0), t = String(p.gatherLabel).replace("{n}", fmt(tot)).replace(/\{(\d)\}/g, (_, d) => fmt(groups[+d - 1]?.marked ?? NaN))
      .replace(/\{p(\d)\}/g, (_, d) => (tot > 0 && groups[+d - 1] ? fmt(Math.round((groups[+d - 1].marked / tot) * 1000) / 10) : ""));
    out += pill(t, 0, ly + fs * 0.85, fitT(t, w * 0.9, fs), INK); ly += fs * 1.9;
  }
  groups.forEach((g) => {
    const y = ly + fs * 0.8, coloured = upto === 0 || g.i < upto;
    const t1 = g.l + (p.counts !== false && coloured ? " " + fmt(g.count) : ""), t2 = marksOn && markK >= 1 ? `${p.splitLabel ? p.splitLabel + " " : ""}${fmt(g.marked)}` : "";
    const f = Math.min(fs, fitT(t1, w * 0.5, fs), t2 ? fitT(t2, w * 0.36, fs) : fs);
    out += `<g opacity="${hl > 0 && g.i + 1 !== hl ? 0.45 : 1}">` + rect(-w / 2, y - f * 0.45, f * 0.9, f * 0.9, coloured ? g.c : "#c5ccd6", `rx="${r1(f * 0.15)}"`) + txa(t1, -w / 2 + f * 1.3, y, f, INK, 800, "start");
    if (t2) { const mx = w * 0.08; out += (markKind === "ring" ? `<circle cx="${r1(mx)}" cy="${r1(y)}" r="${r1(f * 0.42)}" fill="none" stroke="${INK}" stroke-width="${r1(f * 0.12)}"/>` : markKind === "dot" ? `<circle cx="${r1(mx)}" cy="${r1(y)}" r="${r1(f * 0.3)}" fill="${INK}"/>` : markKind === "tick" ? tick(mx, y, f) : cross(mx, y, f)) + txa(t2, mx + f * 0.8, y, f, INK, 700, "start"); }
    out += `</g>`;
    ly += fs * 1.6;
  });
  if (p.per) out += tx(p.per, 0, ly + fs * 0.6, fitT(p.per, w * 0.9, fs * 0.9), MUTED, 700);
  return out;
}

// ---------------------------------------------------------------- timeSeries
// A year-axis chart of real series ("name:1990=3.1 2.4 ..." yearly from 1990, or "name:1990,3.1 1991,2.4"; "name@2:" on
// the right axis): series draw left to right, eras as shaded bands, a glow window that slides from era to era, event
// flags, marked points (highest, lowest, or a year) and a pointer that travels along a series with a live readout.
function parseSeries(s) {
  return parts(s).filter(Boolean).slice(0, 6).map((sr) => {
    const i = sr.indexOf(":"); let name = i >= 0 ? sr.slice(0, i).trim() : "", body = i >= 0 ? sr.slice(i + 1).trim() : sr.trim(), axis = 1;
    const at = name.lastIndexOf("@"); if (at >= 0) { axis = name.slice(at + 1).trim() === "2" ? 2 : 1; name = name.slice(0, at).trim(); }
    let pts = [];
    const eq = body.match(/^(-?[\d.]+)\s*=\s*(.*)$/);
    if (eq) { const x0 = +eq[1]; pts = eq[2].trim().split(/[\s;]+/).filter(Boolean).map((v, k) => [x0 + k, tnum(v)]).filter((q) => Number.isFinite(q[1])); }
    else pts = body.split(/\s+/).map((q) => q.split(",").map(Number)).filter((q) => q.length === 2 && q.every(Number.isFinite));
    pts.sort((a, b) => a[0] - b[0]);
    return { name, axis, pts };
  });
}
const rangeOf = (s) => { const m = String(s ?? "").match(/^\s*(-?[\d.]+)\s*-\s*(-?[\d.]+)\s*(?::(.*))?$/); return m ? [Math.min(+m[1], +m[2]), Math.max(+m[1], +m[2]), (m[3] || "").trim()] : null; };
const yAt = (pts, x) => { if (!pts.length) return NaN; if (x <= pts[0][0]) return pts[0][1]; for (let k = 1; k < pts.length; k++) if (x <= pts[k][0]) { const [a, b] = [pts[k - 1], pts[k]]; return a[1] + ((b[1] - a[1]) * (x - a[0])) / ((b[0] - a[0]) || 1); } return pts[pts.length - 1][1]; };
function timeSeries(p) {
  const w = Math.max(300, num(p.w, 1300)), h = w * 0.6;
  let series = parseSeries(p.series ?? "क:2000=3 4 6 5 7 9 8 6 4 5 7");
  if (!series.length) series = [{ name: "", axis: 1, pts: [[0, 0], [1, 0]] }];
  const cmap = colorMap(p.colors), shown = String(p.show ?? "").trim() ? idxSet(p.show) : null, grow = new Set(parts(p.grow).filter(Boolean));
  const drawIn = Math.max(0, num(p.drawIn, 0)), pAll = prog(sinceStart(p), drawIn), pStep = prog(sinceStep(p), drawIn);
  const allX = series.flatMap((s) => s.pts.map((q) => q[0]));
  let xmin = num(p.xmin, 0), xmax = num(p.xmax, 0);
  if (!(xmax > xmin)) { xmin = allX.length ? Math.min(...allX) : 0; xmax = allX.length ? Math.max(...allX) : 1; if (!(xmax > xmin)) xmax = xmin + 1; }
  const yr = (ax) => { const v = series.filter((s) => s.axis === ax).flatMap((s) => s.pts.map((q) => q[1])); return v.length ? [Math.min(...v), Math.max(...v)] : null; };
  const auto1 = yr(1) || [0, 1], auto2 = yr(2), has2 = !!auto2, zeroOn = p.zero !== false;
  const nice = (a) => { const lo = Math.min(a[0], zeroOn ? 0 : a[0]), hi = Math.max(a[1], zeroOn ? 0 : a[1]); return niceRange(lo, hi > lo ? hi : lo + 1); };
  let [ymin, ymax] = [num(p.ymin, 0), num(p.ymax, 0)];
  if (!(ymax > ymin)) [ymin, ymax] = nice(auto1);
  let [y2min, y2max] = [num(p.y2min, 0), num(p.y2max, 0)];
  if (has2 && !(y2max > y2min)) [y2min, y2max] = nice(auto2);
  const fs = w * 0.03, fsT = w * 0.036, fsK = fs * 0.95, unit2 = p.unit2 ?? "";
  const ticks = (lo, hi) => { const st = niceStep(hi - lo, 5), out = []; for (let v = Math.ceil(lo / st - 1e-9) * st; v <= hi + 1e-9; v += st) out.push([v, st]); return out; };
  const t1 = ticks(ymin, ymax).map(([v, st]) => [v, withUnit(fmt(v, st), p.unit)]), t2 = has2 ? ticks(y2min, y2max).map(([v, st]) => [v, withUnit(fmt(v, st), unit2)]) : [];
  const L0 = -w / 2 + (p.yLabel ? fs * 1.5 : 0) + Math.max(...t1.map((t) => tw(t[1], fsK))) + fs * 0.45;
  const R0 = w / 2 - (has2 ? (p.y2Label ? fs * 1.5 : 0) + Math.max(...t2.map((t) => tw(t[1], fsK))) + fs * 0.45 : fs);
  const X = (v) => L0 + ((v - xmin) / (xmax - xmin)) * (R0 - L0);
  const legendOn = p.legend !== false && series.some((s) => s.name);
  const events = parts(p.events).filter(Boolean).slice(0, 8).map((e) => { const i = e.indexOf(":"); return [tnum(i >= 0 ? e.slice(0, i) : e), i >= 0 ? e.slice(i + 1).trim() : ""]; }).filter((e) => Number.isFinite(e[0]));
  const bands = parts(p.bands).filter(Boolean).slice(0, 8).map(rangeOf).filter(Boolean);
  const BAND_C = ["#f2c14e", "#8ecae6", "#b5838d", "#90be6d", "#f4a261", "#cdb4db", "#a3c4bc", "#e9c46a"];
  // names of bands and events stand in tiers above the plot, never inside it (the lines and marks own the plot)
  const flags = [];
  bands.forEach(([a, b, lab], k) => { const xa = X(Math.max(a, xmin)), xb = X(Math.min(b, xmax)); if (lab && xb > xa) flags.push({ x: (xa + xb) / 2, t: lab, kind: "band", c: BAND_C[k % 8] }); });
  events.forEach(([x, lab]) => { if (lab && x >= xmin && x <= xmax) flags.push({ x: X(x), t: lab, kind: "event", c: "#7b61ff" }); });
  flags.sort((a, b) => a.x - b.x);
  const tiers = [[], [], []], fsF = fs * 0.95;
  flags.forEach((fl) => { const wd = tw(fl.t, fsF) + fsF * 0.8, x = Math.max(-w / 2 + wd / 2, Math.min(w / 2 - wd / 2, fl.x));
    let t = tiers.findIndex((tr) => tr.every((o) => Math.abs(o.lx - x) > (o.wd + wd) / 2 + fsF * 0.2)); if (t < 0) t = tiers.length - 1;
    fl.tier = t; fl.lx = x; fl.wd = wd; tiers[t].push(fl); });
  const nt = tiers.filter((t) => t.length).length;
  const head = (p.title ? fsT * 1.6 : 0) + (legendOn ? fs * 1.8 : 0) + nt * fsF * 1.7;
  const T = -h / 2 + head + fs * 0.6, B = h / 2 - fs * 1.8 - (p.xLabel ? fs * 1.5 : 0);
  const Y = (v, ax = 1) => (ax === 2 ? B - ((v - y2min) / ((y2max - y2min) || 1)) * (B - T) : B - ((v - ymin) / ((ymax - ymin) || 1)) * (B - T));
  let out = "", hy = -h / 2;
  if (p.title) { out += tx(p.title, 0, hy + fsT * 0.75, fitT(p.title, w * 0.95, fsT), INK, 800); hy += fsT * 1.6; }
  const colOf = (k) => cmap[String(k + 1)] || PAL[k % PAL.length];
  const ax2c = colOf(Math.max(0, series.findIndex((s) => s.axis === 2)));
  if (legendOn) {
    const items = series.map((s, k) => ({ t: s.name + (has2 ? (s.axis === 2 ? " ▸" : " ◂") : ""), c: colOf(k), k })).filter((it) => it.t.trim() && (!shown || shown.has(it.k + 1)));
    const tot = items.reduce((a, it) => a + fs * 1.6 + tw(it.t, fs), 0) + fs * (items.length - 1), sc = Math.min(1, (w * 0.96) / Math.max(1, tot));
    let x = -Math.min(tot, w * 0.96) / 2;
    items.forEach((it) => { out += line(x, hy + fs * 0.9, x + fs * 1.2 * sc, hy + fs * 0.9, it.c, fs * 0.28, `stroke-linecap="round"`) + txa(it.t, x + fs * 1.45 * sc, hy + fs * 0.9, fs * sc, INK, 700, "start"); x += (fs * 1.6 + tw(it.t, fs) + fs) * sc; });
    hy += fs * 1.8;
  }
  bands.forEach(([a, b], k) => { const xa = X(Math.max(a, xmin)), xb = X(Math.min(b, xmax)); if (xb > xa) out += rect(xa, T, xb - xa, B - T, BAND_C[k % 8], `opacity="0.28"`); });
  for (const [v, s] of t1) { const y = Y(v); out += line(L0, y, R0, y, GRID, Math.max(1, w * 0.0012)) + txa(s, L0 - fs * 0.3, y, fsK, MUTED, 700, "end"); }
  for (const [v, s] of t2) out += txa(s, R0 + fs * 0.3, Y(v, 2), fsK, ax2c, 700, "start");
  const xstep = num(p.step, 0) > 0 ? num(p.step, 0) : [1, 2, 5, 10, 20, 25, 50, 100, 200, 500].find((s) => (xmax - xmin) / s <= 8 && tw(fmt(xmax), fsK) * 1.6 < (s / (xmax - xmin)) * (R0 - L0)) || 1000;
  for (let v = Math.ceil(xmin / xstep - 1e-9) * xstep; v <= xmax + 1e-9; v += xstep) { const x = X(v); out += line(x, B, x, B + fs * 0.3, INK, Math.max(2, w * 0.002)) + tx(fmt(v, xstep), x, B + fs * 0.95, fsK, MUTED, 700); }
  out += line(L0, T, L0, B, INK, Math.max(2, w * 0.003)) + line(L0, B, R0, B, INK, Math.max(2, w * 0.003)) + (has2 ? line(R0, T, R0, B, INK, Math.max(2, w * 0.003)) : "");
  if (zeroOn && ymin < 0 && ymax > 0) out += line(L0, Y(0), R0, Y(0), INK, Math.max(3, w * 0.003));
  if (p.xLabel) out += tx(p.xLabel, (L0 + R0) / 2, B + fs * 2.3, fitT(p.xLabel, w * 0.6, fs), INK, 800);
  if (p.yLabel) out += `<g transform="translate(${r1(-w / 2 + fs * 0.65)},${r1((T + B) / 2)}) rotate(-90)">${tx(p.yLabel, 0, 0, fitT(p.yLabel, B - T, fs * 0.9), INK, 800)}</g>`;
  if (p.y2Label && has2) out += `<g transform="translate(${r1(w / 2 - fs * 0.65)},${r1((T + B) / 2)}) rotate(90)">${tx(p.y2Label, 0, 0, fitT(p.y2Label, B - T, fs * 0.9), ax2c, 800)}</g>`;
  events.forEach(([x]) => { if (x >= xmin && x <= xmax) out += line(X(x), T, X(x), B, "#7b61ff", Math.max(2, w * 0.0025), `stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"`); });
  flags.forEach((fl) => { const y = hy + (fl.tier + 0.5) * fsF * 1.7, ev = fl.kind === "event";
    out += line(fl.x, y + fsF * 0.65, fl.x, T, ev ? fl.c : shade(fl.c, 0.7), Math.max(1.5, w * 0.0018)) +
      rect(fl.lx - fl.wd / 2, y - fsF * 0.68, fl.wd, fsF * 1.36, ev ? "#ffffff" : shade(fl.c, 1.25), `rx="${r1(fsF * 0.3)}" stroke="${ev ? fl.c : shade(fl.c, 0.75)}" stroke-width="${r1(Math.max(2, w * 0.002))}"`) + tx(fl.t, fl.lx, y, fsF, INK, 800); });
  const drawn = [];
  series.forEach((s, k) => {
    if ((shown && !shown.has(k + 1)) || s.pts.length < 1) return;
    const pr = grow.size ? (grow.has(String(k + 1)) ? pStep : 1) : pAll, xa = s.pts[0][0], xb = s.pts[s.pts.length - 1][0], cut = xa + (xb - xa) * pr;
    const q = s.pts.filter((pt) => pt[0] <= cut); if (q.length && q[q.length - 1][0] < cut) q.push([cut, yAt(s.pts, cut)]);
    drawn[k] = cut;
    const c = colOf(k), ax = s.axis;
    if (q.length > 1) out += `<path d="${q.map((pt, j) => `${j ? "L" : "M"}${r1(X(pt[0]))} ${r1(Y(pt[1], ax))}`).join(" ")}" fill="none" stroke="${c}" stroke-width="${r1(w * 0.005)}" stroke-linejoin="round" stroke-linecap="round"${idxSet(p.dashed).has(k + 1) ? ` stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"` : ""}/>`;
    if (pr < 1 && q.length) { const e = q[q.length - 1]; out += `<circle cx="${r1(X(e[0]))}" cy="${r1(Y(e[1], ax))}" r="${r1(w * 0.006)}" fill="${c}"/>`; }
  });
  const win = rangeOf(p.window), winF = rangeOf(p.windowFrom);
  if (win) {
    const k = winF ? easeIO(prog(sinceStep(p), num(p.glide, 1.2))) : 1, a = winF ? winF[0] + (win[0] - winF[0]) * k : win[0], b = winF ? winF[1] + (win[1] - winF[1]) * k : win[1];
    const xa = X(Math.max(xmin, a)), xb = X(Math.min(xmax, b));
    if (xa > L0) out += rect(L0, T, xa - L0, B - T, PAPER, `opacity="0.62"`);
    if (xb < R0) out += rect(xb, T, R0 - xb, B - T, PAPER, `opacity="0.62"`);
    if (xb > xa) out += rect(xa, T, xb - xa, B - T, "none", `stroke="${GOLD}" stroke-width="${r1(Math.max(4, w * 0.005))}" rx="${r1(w * 0.006)}"`);
  }
  // marked points "1@2008:{y}", "1@max", "2@min": {x} is the year, {y} the value with its unit
  parts(p.marks).filter(Boolean).slice(0, 8).forEach((mk) => {
    const i = mk.indexOf(":"), body = i >= 0 ? mk.slice(0, i) : mk, t = i >= 0 ? mk.slice(i + 1).trim() : "{y}", [ks, where0] = body.split("@"), where = (where0 || "").trim();
    const k = Math.round(num(ks, 0)) - 1, s = series[k]; if (!s || (shown && !shown.has(k + 1)) || !s.pts.length) return;
    let pt = null;
    if (/^max$/i.test(where)) pt = s.pts.reduce((a, b) => (b[1] > a[1] ? b : a));
    else if (/^min$/i.test(where)) pt = s.pts.reduce((a, b) => (b[1] < a[1] ? b : a));
    else if (isNum(where)) { const x = +where; pt = s.pts.reduce((a, b) => (Math.abs(b[0] - x) < Math.abs(a[0] - x) ? b : a)); }
    if (!pt || (drawn[k] !== undefined && pt[0] > drawn[k] + 1e-9)) return;
    const x = X(pt[0]), y = Y(pt[1], s.axis), c = colOf(k), u = s.axis === 2 ? unit2 : p.unit;
    const tt = String(t).replace("{x}", String(Math.round(pt[0]))).replace("{y}", withUnit(fmt(pt[1]), u)), f = fitT(tt, w * 0.3, fs) * 0.9, half = tw(tt, f) / 2 + f * 0.5;
    const lowWant = /^min$/i.test(where) || (!/^max$/i.test(where) && pt[1] < 0);
    let ly = lowWant ? y + f * 1.7 : y - f * 1.7, lx = Math.max(L0 + half, Math.min(R0 - half, x));
    if (ly - f < T || ly + f > B) {                         // no room above (or below): beside the point instead
      ly = Math.max(T + f, Math.min(B - f, y)); lx = x + w * 0.016 + half <= R0 ? x + w * 0.016 + half : x - w * 0.016 - half;
    }
    out += `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(w * 0.011)}" fill="none" stroke="${c}" stroke-width="${r1(Math.max(3, w * 0.004))}"/><circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(w * 0.005)}" fill="${c}"/>` + pill(tt, lx, ly, f, shade(c, 0.85));
  });
  // a pointer travelling along a series: "1@2008<1@1997"
  if (p.pointer) {
    const [to, fromS] = String(p.pointer).split("<"), [ks, xs] = (to || "").split("@"), k = Math.round(num(ks, 0)) - 1, s = series[k];
    if (s && s.pts.length && isNum(xs)) {
      const x1 = +xs, x0 = fromS && isNum((fromS.split("@")[1] || "").trim()) ? +fromS.split("@")[1] : x1, e = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
      const xv = Math.max(s.pts[0][0], Math.min(s.pts[s.pts.length - 1][0], x0 + (x1 - x0) * e)), yv = yAt(s.pts, xv), x = X(xv), y = Y(yv, s.axis), c = colOf(k);
      const t = String(p.pointerLabel ?? "{x}: {y}").replace("{x}", String(Math.round(xv))).replace("{y}", withUnit(fmt(yv, s.pts[0][1]), s.axis === 2 ? unit2 : p.unit)), f = fs * 0.95;
      const half = tw(t, f) / 2 + f * 0.6, lx = Math.max(L0 + half, Math.min(R0 - half, x)), ly = y - f * 2.2 < T + f ? y + f * 2.2 : y - f * 2.2;
      out += line(x, T, x, B, INK, Math.max(2, w * 0.002), `stroke-dasharray="${r1(w * 0.005)} ${r1(w * 0.005)}"`) + `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(w * 0.009)}" fill="${DOWN}" stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.003))}"/>` + pill(t, lx, ly, f, c);
    }
  }
  return out;
}

// ---------------------------------------------------------------- scatterFit
// Yearly data as dots, the fitted line settling through them, each point's gap to the fit (the residual), and an R²
// bar; a step to model 2 (fitted values given per point, e.g. with TIME added) glides the fit, the gaps shrink and the
// R² rises.
function scatterFit(p) {
  const w = Math.max(300, num(p.w, 1100)), h = w * 0.62;
  let pts = String(p.points ?? "1,2 2,3.1 3,3.4 4,5.2 5,4.8 6,6.5 7,6.9 8,8.4").trim().split(/\s+/).map((q) => q.split(",").map(Number)).filter((q) => q.length === 2 && q.every(Number.isFinite));
  if (!pts.length) pts = [[0, 0]];
  const n = pts.length, mx = pts.reduce((a, q) => a + q[0], 0) / n, my = pts.reduce((a, q) => a + q[1], 0) / n;
  const sxx = pts.reduce((a, q) => a + (q[0] - mx) ** 2, 0), sxy = pts.reduce((a, q) => a + (q[0] - mx) * (q[1] - my), 0);
  let a = my, b = sxx > 0 ? sxy / sxx : 0;
  const fitS = String(p.fit ?? "auto").trim();
  if (/^-?[\d.]+\s*,\s*-?[\d.]+$/.test(fitS)) [a, b] = fitS.split(",").map(Number); else if (fitS !== "none") a = my - b * mx;
  const f1 = pts.map((q) => a + b * q[0]), f2raw = listN(p.fit2), f2 = pts.map((q, i) => (Number.isFinite(f2raw[i]) ? f2raw[i] : f1[i]));
  const sst = pts.reduce((s, q) => s + (q[1] - my) ** 2, 0) || 1, r2c = (f) => 1 - pts.reduce((s, q, i) => s + (q[1] - f[i]) ** 2, 0) / sst;
  const r2a = num(p.r2, -1) >= 0 ? num(p.r2, -1) : r2c(f1), r2b = num(p.r2b, -1) >= 0 ? num(p.r2b, -1) : r2c(f2);
  const model = Math.round(num(p.model, 1)) === 2 ? 2 : 1, fromM = Math.round(num(p.modelFrom, 0)), gk = easeIO(prog(sinceStep(p), num(p.glide, 1.4)));
  const target = model === 2 ? f2 : f1, start = fromM === 1 ? f1 : fromM === 2 ? f2 : p.settle === true ? pts.map(() => my) : target;
  const cur = target.map((v, i) => start[i] + (v - start[i]) * gk);
  const r2t = model === 2 ? r2b : r2a, r2s = fromM === 1 ? r2a : fromM === 2 ? r2b : p.settle === true ? 0 : r2t, r2v = r2s + (r2t - r2s) * gk;
  const xs = pts.map((q) => q[0]), ys = pts.flatMap((q, i) => [q[1], f1[i], f2[i]]);
  let [xmin, xmax] = [num(p.xmin, 0), num(p.xmax, 0)], [ymin, ymax] = [num(p.ymin, 0), num(p.ymax, 0)];
  if (!(xmax > xmin)) { const pad = (Math.max(...xs) - Math.min(...xs)) * 0.06 || 1; xmin = Math.min(...xs) - pad; xmax = Math.max(...xs) + pad; }
  if (!(ymax > ymin)) { const pad = (Math.max(...ys) - Math.min(...ys)) * 0.08 || 1; ymin = Math.min(...ys) - pad; ymax = Math.max(...ys) + pad; }
  const fs = w * 0.033, fsK = fs * 1.0, gauge = p.gauge !== false, gW = gauge ? w * 0.16 : 0, fsT = w * 0.04;
  const [, , xst] = niceRange(xmin, xmax, 6), [, , yst] = niceRange(ymin, ymax, 5), yt = [];
  for (let v = Math.ceil(ymin / yst - 1e-9) * yst; v <= ymax + 1e-9; v += yst) yt.push([v, fmt(v, yst)]);
  const L = -w / 2 + (p.yLabel ? fs * 1.5 : 0) + Math.max(0, ...yt.map((q) => tw(q[1], fsK))) + fs * 0.45, R = w / 2 - gW - w * 0.03, T = -h / 2 + (p.title ? fsT * 1.7 : fs), B = h / 2 - fs * (p.xLabel ? 3.2 : 1.8);
  const X = (v) => L + ((v - xmin) / (xmax - xmin)) * (R - L), Y = (v) => B - ((v - ymin) / (ymax - ymin)) * (B - T);
  let out = p.title ? tx(p.title, 0, -h / 2 + fsT * 0.8, fitT(p.title, w * 0.95, fsT), INK, 800) : "";
  out += line(L, T, L, B, INK, Math.max(2, w * 0.003)) + line(L, B, R, B, INK, Math.max(2, w * 0.003));
  for (let v = Math.ceil(xmin / xst - 1e-9) * xst; v <= xmax + 1e-9; v += xst) out += tx(fmt(v, xst), X(v), B + fs * 0.9, fsK, MUTED, 700);
  for (const [v, t] of yt) out += line(L, Y(v), R, Y(v), GRID, Math.max(1, w * 0.0012)) + txa(t, L - fs * 0.3, Y(v), fsK, MUTED, 700, "end");
  if (p.xLabel) out += tx(p.xLabel, (L + R) / 2, B + fs * 2.2, fitT(p.xLabel, w * 0.6, fs), INK, 800);
  if (p.yLabel) out += `<g transform="translate(${r1(-w / 2 + fs * 0.65)},${r1((T + B) / 2)}) rotate(-90)">${tx(p.yLabel, 0, 0, fitT(p.yLabel, B - T, fs), INK, 800)}</g>`;
  const upto = Math.max(0, Math.round(num(p.upto, 0))), shown = upto > 0 ? Math.min(n, upto) : n, popK = upto > 0 ? easeIO(prog(sinceStep(p), 0.35)) : 1;
  const lineOn = fitS !== "none" && p.line !== false;
  if (lineOn) {
    const ord = pts.map((q, i) => [q[0], cur[i]]).sort((u, v) => u[0] - v[0]);
    out += `<path d="${ord.map((q, j) => `${j ? "L" : "M"}${r1(X(q[0]))} ${r1(Y(q[1]))}`).join(" ")}" fill="none" stroke="${DOWN}" stroke-width="${r1(w * 0.006)}" stroke-linejoin="round" stroke-linecap="round"/>`;
    if (p.residuals === true) pts.slice(0, shown).forEach((q, i) => { out += line(X(q[0]), Y(q[1]), X(q[0]), Y(cur[i]), "#7b61ff", Math.max(2, w * 0.003), `stroke-dasharray="${r1(w * 0.005)} ${r1(w * 0.004)}"`); });
  }
  pts.slice(0, shown).forEach((q, i) => { const s = i === shown - 1 ? popK : 1; out += `<circle cx="${r1(X(q[0]))}" cy="${r1(Y(q[1]))}" r="${r1(w * 0.009 * s)}" fill="${okColor(p.color, "#2459a6")}" stroke="#ffffff" stroke-width="${r1(Math.max(1.5, w * 0.002))}"/>`; });
  if (gauge) {
    const gx = w / 2 - gW / 2, bw2 = gW * 0.38, gt = T + fs * 2.6, gb = B, v = clamp01(r2v), lab = String(p.r2Label ?? "R²");
    out += rect(gx - bw2 / 2, gt, bw2, gb - gt, "#eef0f3", `rx="${r1(bw2 * 0.2)}" stroke="#cfd6de" stroke-width="${r1(Math.max(2, w * 0.002))}"`) +
      rect(gx - bw2 / 2, gb - (gb - gt) * v, bw2, (gb - gt) * v, v > 0.8 ? UP : v > 0.5 ? GOLD : DOWN, `rx="${r1(bw2 * 0.2)}"`) +
      txa("1", gx + bw2 / 2 + fs * 0.25, gt, fsK, MUTED, 700, "start") + txa("0", gx + bw2 / 2 + fs * 0.25, gb, fsK, MUTED, 700, "start");
    out += tx(lab, gx, T + fs * 0.5, fitT(lab, gW * 0.95, fs), INK, 800) + tx(fmt(r2v, 0.001), gx, T + fs * 1.65, fitT(fmt(r2v, 0.001), gW * 0.95, fs * 1.05), INK, 800);
  }
  return out;
}

// ---------------------------------------------------------------- cycleWave
// Output over time as a wave around a rising trend (potential output), its phases as named bands (upturn, expansion,
// peaking out, recession), a full-employment ceiling and a floor; a dot rides the wave as the video plays and the band
// under it glows (or at names the phase).
function cycleWave(p) {
  const w = Math.max(300, num(p.w, 1200)), h = w * 0.55, cyc = Math.max(1, Math.min(4, Math.round(num(p.cycles, 2))));
  let ph = parts(p.phases ?? "उठान;विस्तार;शिखर;मंदी").filter(Boolean).slice(0, 6);
  if (!ph.length) ph = ["", "", "", ""];
  const np = ph.length, cuts = np === 4 ? [0, 0.12, 0.38, 0.56, 1] : Array.from({ length: np + 1 }, (_, i) => i / np);
  const fs = w * 0.032, fsT = w * 0.04, amp = Math.max(0.05, Math.min(0.45, num(p.amp, 0.22)));
  const rightW = Math.max(...[p.ceiling, p.floor, p.trend === false ? "" : p.trendLabel].filter(Boolean).map((t) => tw(t, fs) + fs * 0.6), 0);
  const L = -w / 2 + w * 0.06, R = w / 2 - Math.min(w * 0.22, rightW) - w * 0.01, head = (p.title ? fsT * 1.6 : 0) + fs * 3.4;
  const T = -h / 2 + head, B = h / 2 - fs * (p.xLabel ? 2.2 : 0.8);
  const A = (B - T) * amp, tr = (u) => B - (B - T) * (0.3 + 0.32 * u), X = (u) => L + u * (R - L), out1 = (u) => tr(u) + A * Math.cos(2 * Math.PI * cyc * u);
  const ride = Math.max(0, num(p.ride, 6)), t = sinceStart(p);
  const f = p.dot === false ? -1 : ride > 0 && Number.isFinite(t) ? ((t / ride) / cyc) % 1 : clamp01(num(p.pos, 0.3));
  const phaseAt = (u) => { const q = (u * cyc) % 1; for (let i = 0; i < np; i++) if (q >= cuts[i] && q < cuts[i + 1]) return i; return np - 1; };
  const at = Math.round(num(p.at, 0)), glowI = at > 0 ? at - 1 : f >= 0 ? phaseAt(f) : -1;
  const colors = ["#8ecae6", "#90be6d", "#f9c74f", "#f4a261", "#cdb4db", "#a3c4bc"];
  let out = p.title ? tx(p.title, 0, -h / 2 + fsT * 0.75, fitT(p.title, w * 0.95, fsT), INK, 800) : "";
  for (let c = 0; c < cyc; c++) for (let i = 0; i < np; i++) {
    const u0 = (c + cuts[i]) / cyc, u1 = (c + cuts[i + 1]) / cyc, g = i === glowI;
    out += rect(X(u0), T, X(u1) - X(u0), B - T, colors[i % colors.length], `opacity="${g ? 0.6 : 0.22}"`);
  }
  // phase names once, over the first cycle, in two tiers when narrow
  const tierY = [T - fs * 2.3, T - fs * 0.9];
  let lastEnd = [-Infinity, -Infinity];
  for (let i = 0; i < np; i++) {
    if (!ph[i]) continue;
    const u0 = cuts[i] / cyc, u1 = cuts[i + 1] / cyc, cx = (X(u0) + X(u1)) / 2, g = i === glowI, wd = tw(ph[i], fs) + fs * 0.4;
    let tier = 1; if (cx - wd / 2 < lastEnd[1]) tier = 0;
    const x = Math.max(-w / 2 + wd / 2, cx); lastEnd[tier] = x + wd / 2;
    out += line(cx, tierY[tier] + fs * 0.55, cx, T, shade(colors[i % colors.length], 0.6), Math.max(2, w * 0.002)) + (g ? pill(ph[i], x, tierY[tier], fs, shade(colors[i % colors.length], 0.55)) : tx(ph[i], x, tierY[tier], fs, shade(colors[i % colors.length], 0.45), 800));
  }
  const pathOf = (fn) => Array.from({ length: 121 }, (_, k) => `${k ? "L" : "M"}${r1(X(k / 120))} ${r1(fn(k / 120))}`).join(" ");
  out += line(L, T - fs * 0.2, L, B, INK, Math.max(2, w * 0.003)) + line(L, B, R + w * 0.01, B, INK, Math.max(2, w * 0.003));
  if (p.trend !== false) out += `<path d="${pathOf(tr)}" fill="none" stroke="${MUTED}" stroke-width="${r1(Math.max(3, w * 0.003))}" stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"/>` + (p.trendLabel ? txa(p.trendLabel, R + fs * 0.3, tr(1), fs, MUTED, 800, "start") : "");
  if (p.ceiling) out += `<path d="${pathOf((u) => tr(u) - A)}" fill="none" stroke="${RED}" stroke-width="${r1(Math.max(4, w * 0.004))}"/>` + txa(p.ceiling, R + fs * 0.3, tr(1) - A, fs, RED, 800, "start");
  if (p.floor) out += `<path d="${pathOf((u) => tr(u) + A)}" fill="none" stroke="#2459a6" stroke-width="${r1(Math.max(4, w * 0.004))}"/>` + txa(p.floor, R + fs * 0.3, tr(1) + A, fs, "#2459a6", 800, "start");
  out += `<path d="${pathOf(out1)}" fill="none" stroke="${INK}" stroke-width="${r1(w * 0.006)}" stroke-linecap="round"/>`;
  if (f >= 0) {
    const x = X(f), y = out1(f), q = (f * cyc) % 1, near = Math.min(Math.abs(q - 0.5), Math.min(q, 1 - q));
    const hit = (p.ceiling && Math.abs(q - 0.5) < 0.035) || (p.floor && Math.min(q, 1 - q) < 0.035);
    if (hit) { const r = w * 0.03 * (1 - near / 0.035); out += `<g transform="translate(${r1(x)},${r1(y)})">${Array.from({ length: 8 }, (_, k) => { const a = (k / 8) * Math.PI * 2; return line(Math.cos(a) * r * 0.5, Math.sin(a) * r * 0.5, Math.cos(a) * r * 1.2, Math.sin(a) * r * 1.2, GOLD, Math.max(3, w * 0.004), `stroke-linecap="round"`); }).join("")}</g>`; }
    out += `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(w * 0.014)}" fill="${DOWN}" stroke="#ffffff" stroke-width="${r1(Math.max(3, w * 0.003))}"/>`;
  }
  if (p.xLabel) out += tx(p.xLabel, (L + R) / 2, B + fs * 1.2, fitT(p.xLabel, w * 0.5, fs), INK, 800);
  if (p.yLabel) out += `<g transform="translate(${r1(L - fs * 0.8)},${r1((T + B) / 2)}) rotate(-90)">${tx(p.yLabel, 0, 0, fitT(p.yLabel, B - T, fs), INK, 800)}</g>`;
  return out;
}

// ---------------------------------------------------------------- dayHours
// A day of hours split between work and leisure, as a bar (with a divider that is dragged and an earnings counter that
// follows, a tax above a threshold changing its slope) or as a clock dial whose hours fill.
function dayHours(p) {
  const w = Math.max(200, num(p.w, 1000)), hours = Math.max(1, Math.min(24, Math.round(num(p.hours, 16))));
  const work0 = Math.max(0, Math.min(hours, num(p.work, 8))), from = num(p.from, -1);
  const k = easeIO(prog(sinceStep(p), num(p.glide, 1)));
  const work = from >= 0 ? Math.max(0, Math.min(hours, from)) + (work0 - Math.max(0, Math.min(hours, from))) * k : work0;
  const [lw, ll] = (() => { const l = parts(p.labels ?? "काम;आराम"); return [l[0] || "", l[1] || ""]; })();
  const uh = p.unitH ?? "", cW = okColor(p.colorWork, "#e07b24"), cL = okColor(p.colorRest, "#2a9d8f"), hl = Math.round(num(p.highlight, 0));
  const pulse = Number.isFinite(sinceStart(p)) ? 0.55 + 0.45 * Math.sin(sinceStart(p) * 6) : 1;
  const wage = num(p.wage, 0), tax = clamp01(num(p.tax, 0)), above = num(p.taxAbove, 0);
  const gross = wage * work, net = gross - tax * Math.max(0, gross - above);
  const earn = wage > 0 ? String(p.earn || "₹{v}").replace("{v}", fmt(Math.round(net))) : "";
  const hstr = (v) => fmt(Math.round(v * 2) / 2) + uh;
  let out = "";
  if (p.shape === "dial") {
    const R = w * 0.3, fs = w * 0.04, head = p.title ? w * 0.06 : 0, cy = head / 2 - (lw || ll ? fs * 0.9 : 0) - (earn ? fs * 0.9 : 0);
    if (p.title) out += tx(p.title, 0, cy - R - w * 0.05, fitT(p.title, w * 0.95, w * 0.042), INK, 800);
    out += `<circle cx="0" cy="${r1(cy)}" r="${r1(R * 1.06)}" fill="#ffffff" stroke="#2d3748" stroke-width="${r1(Math.max(4, w * 0.008))}"/>`;
    for (let i = 0; i < hours; i++) {
      const a0 = -Math.PI / 2 + (i / hours) * Math.PI * 2, a1 = -Math.PI / 2 + ((i + 1) / hours) * Math.PI * 2, fill = clamp01(work - i);
      const P = (a, r) => `${r1(Math.cos(a) * r)} ${r1(cy + Math.sin(a) * r)}`, wedge = (b0, b1, c) => `<path d="M0 ${r1(cy)} L${P(b0, R)} A${r1(R)} ${r1(R)} 0 0 1 ${P(b1, R)} Z" fill="${c}" stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.004))}"/>`;
      out += wedge(a0, a1, cL);
      if (fill > 0) out += wedge(a0, a0 + (a1 - a0) * fill, cW);
      if (hl === i + 1) out += `<path d="M0 ${r1(cy)} L${P(a0, R)} A${r1(R)} ${r1(R)} 0 0 1 ${P(a1, R)} Z" fill="none" stroke="${GOLD}" stroke-width="${r1(Math.max(5, w * 0.01) * (0.6 + 0.4 * pulse))}"/>`;
    }
    const cr = R * 0.42, ct = hstr(work);
    out += `<circle cx="0" cy="${r1(cy)}" r="${r1(cr)}" fill="#ffffff" stroke="#2d3748" stroke-width="${r1(Math.max(2, w * 0.004))}"/>` + tx(ct, 0, cy, fitT(ct, cr * 1.7, cr * 0.55), cW, 800);
    let ly = cy + R * 1.06 + fs * 1.1;
    if (lw || ll) {
      const items = [[lw, cW], [ll, cL]].filter((it) => it[0]), tot = items.reduce((a, it) => a + fs * 1.3 + tw(it[0], fs), 0) + fs * (items.length - 1), sc = Math.min(1, (w * 0.96) / tot);
      let x = -Math.min(tot, w * 0.96) / 2;
      items.forEach(([t, c]) => { out += rect(x, ly - fs * sc * 0.45, fs * sc * 0.9, fs * sc * 0.9, c, `rx="${r1(fs * 0.15)}"`) + txa(t, x + fs * sc * 1.2, ly, fs * sc, INK, 800, "start"); x += (fs * 1.3 + tw(t, fs) + fs) * sc; });
      ly += fs * 1.7;
    }
    if (earn) out += pill(earn, 0, ly, fitT(earn, w * 0.8, fs), INK);
    return out;
  }
  const bw = w * 0.92, bh = w * 0.12, x0 = -bw / 2, cell = bw / hours, fs = w * 0.036, xd = x0 + work * cell;
  const top = -bh / 2 - fs * 1.9 - (p.title ? w * 0.055 : 0);
  if (p.title) out += tx(p.title, 0, top + w * 0.02, fitT(p.title, w * 0.95, w * 0.042), INK, 800);
  for (let i = 0; i < hours; i++) {
    const fill = clamp01(work - i), x = x0 + i * cell;
    out += rect(x + cell * 0.04, -bh / 2, cell * 0.92, bh, cL, `rx="${r1(Math.min(cell, bh) * 0.12)}"`);
    if (fill > 0) out += rect(x + cell * 0.04, -bh / 2, cell * 0.92 * fill, bh, cW, `rx="${r1(Math.min(cell * fill, bh) * 0.12)}"`);
    if (hl === i + 1) out += rect(x, -bh / 2 - 4, cell, bh + 8, "none", `rx="${r1(Math.min(cell, bh) * 0.15)}" stroke="${GOLD}" stroke-width="${r1(Math.max(5, w * 0.008) * (0.6 + 0.4 * pulse))}"`);
  }
  out += rect(xd - w * 0.006, -bh / 2 - bh * 0.22, w * 0.012, bh * 1.3, INK, `rx="${r1(w * 0.004)}"`) + `<circle cx="${r1(xd)}" cy="${r1(-bh / 2 - bh * 0.22)}" r="${r1(w * 0.016)}" fill="${INK}"/>`;
  const tW = lw ? lw + " " + hstr(work) : hstr(work), tL = ll ? ll + " " + hstr(hours - work) : hstr(hours - work);
  const yL = -bh / 2 - fs * 1.2, fW = Math.min(fs, fitT(tW, Math.max(w * 0.2, xd - x0 - fs * 0.6), fs)), fL = Math.min(fs, fitT(tL, Math.max(w * 0.2, x0 + bw - xd - fs * 0.6), fs));
  const wW = tw(tW, fW), wL = tw(tL, fL);
  let cxW = Math.max(x0 + wW / 2, (x0 + xd) / 2), cxL = Math.min(x0 + bw - wL / 2, (xd + x0 + bw) / 2);
  if (cxW + wW / 2 + fs * 0.8 > cxL - wL / 2) { const over = cxW + wW / 2 + fs * 0.8 - (cxL - wL / 2); cxW -= over / 2; cxL += over / 2; cxW = Math.max(x0 + wW / 2, cxW); cxL = Math.min(x0 + bw - wL / 2, cxL); }
  out += (work > 0.01 ? tx(tW, cxW, yL, fW, shade(cW, 0.75), 800) : "") + (hours - work > 0.01 ? tx(tL, cxL, yL, fL, shade(cL, 0.7), 800) : "");
  const step = hours <= 8 ? 1 : hours <= 16 ? 2 : 4;
  for (let v = 0; v <= hours; v += step) out += tx(String(v), x0 + v * cell, bh / 2 + fs * 0.85, fs, MUTED, 700);
  if (earn) out += pill(earn, Math.max(x0 + tw(earn, fs) / 2 + fs, Math.min(x0 + bw - tw(earn, fs) / 2 - fs, xd)), bh / 2 + fs * 2.6, fs, INK);
  return out;
}

// ---------------------------------------------------------------- roundBars (bottom)
// The multiplier as rounds: round 1 spends the injection, each next round re-spends the kept share; every bar's top
// slice leaks (saving, tax, imports) into its jar; the cumulative bar climbs toward its limit. dir "down" runs the same
// rounds downward (the paradox of thrift).
function roundBars(p) {
  const w = Math.max(300, num(p.w, 1200)), first = Math.max(0, num(p.first, 100)), keep = Math.max(0, Math.min(0.99, num(p.keep, 0.8)));
  const rounds = Math.max(1, Math.min(12, Math.round(num(p.rounds, 6)))), unit = p.unit ?? "₹", dec = p.decimals, down = p.dir === "down";
  const leaks = parts(p.leaks ?? "बचत;कर;आयात").filter(Boolean).slice(0, 4), shares = listN(p.leakShares);
  const sh = leaks.map((_, i) => (Number.isFinite(shares[i]) && shares[i] > 0 ? shares[i] : 1)), shSum = sh.reduce((a, b) => a + b, 0) || 1;
  const limit = keep < 1 ? first / (1 - keep) : first, amt = Array.from({ length: rounds }, (_, k) => first * Math.pow(keep, k));
  const grow = num(p.grow, 0.6), kNew = easeIO(prog(sinceStep(p), grow)), kFly = easeIO(clamp01((sinceStep(p) - grow) / 0.9));
  const jars = p.jars !== false && leaks.length > 0, totalOn = p.total !== false;
  const fs = w * 0.032, jarW = jars ? w * 0.2 : 0, totW = totalOn ? w * 0.17 : 0;
  const L = -w / 2, R = w / 2 - jarW - totW, slot = (R - L) / rounds, bw = slot * 0.62, ph = w * 0.42;
  const hiV = totalOn ? limit : first, sc = ph / (hiV || 1);
  const cSpend = down ? "#c0563f" : "#2459a6", cLeak = "#f29f05";
  const Y = (v) => (down ? -ph - fs * 1.2 + v * sc : -v * sc);
  const baseY = Y(0);
  const vs = (v, like) => withUnit(fmt(v, like ?? (dec != null ? undefined : v >= 10 ? 1 : 0.1), dec), unit);
  let out = line(L, baseY, R, baseY, INK, Math.max(2, w * 0.003));
  const fsV = Math.min(fs, ...amt.map((a) => fitT(vs(a), slot * 0.95, fs)));
  for (let k = 0; k < rounds; k++) {
    const isNew = k === rounds - 1, g = isNew ? kNew : 1, a = amt[k] * g, x = L + (k + 0.5) * slot - bw / 2, leak = a * (1 - keep);
    out += rect(x, Y(0), bw, Y(a - leak) - Y(0), cSpend) + rect(x, Y(a - leak), bw, Y(a) - Y(a - leak), cLeak, `opacity="${isNew ? r1(1 - 0.6 * kFly) : 0.4}"`);
    if (g > 0.05) out += txa(vs(a, amt[k] >= 10 ? 1 : 0.1), x + bw / 2, down ? Y(a) + fsV * 0.8 : Y(a) - fsV * 0.8, fsV, INK, 800);
    const rl = String(p.roundLabel ?? "{k}").replace("{k}", String(k + 1));
    out += txa(rl, x + bw / 2, down ? baseY - fs * 0.9 : fs * 0.9, fitT(rl, slot * 0.95, fs), MUTED, 700);
  }
  if (totalOn) {
    const cx = R + totW / 2, cw = totW * 0.55;
    let acc = 0;
    amt.forEach((a0, k) => { const a = k === rounds - 1 ? a0 * kNew : a0; out += rect(cx - cw / 2, Y(acc), cw, Y(acc + a) - Y(acc), k % 2 ? shade(cSpend, 1.3) : cSpend, `stroke="#ffffff" stroke-width="${r1(Math.max(1.5, w * 0.002))}"`); acc += a; });
    out += line(cx - totW * 0.45, baseY, cx + totW * 0.45, baseY, INK, Math.max(2, w * 0.003));
    if (p.limit !== false) {
      const t = vs(limit, 1);
      out += line(L, Y(limit), cx + totW * 0.45, Y(limit), RED, Math.max(3, w * 0.004), `stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"`) + txa(t, L + fs * 0.2, down ? Y(limit) + fs * 0.75 : Y(limit) - fs * 0.75, fitT(t, w * 0.25, fs), RED, 800, "start");
    }
    const tl = (p.totalLabel ? p.totalLabel + " " : "") + vs(acc, 1), f = fitT(tl, totW * 1.15, fs);
    out += tx(tl, cx, down ? baseY - fs * 0.9 : fs * 0.9, f, INK, 800);
  }
  if (jars) {
    const jx = w / 2 - jarW / 2, nJ = leaks.length, jh = Math.min(ph / nJ, w * 0.13), leaked = amt.reduce((s, a, k) => s + a * (k === rounds - 1 ? kNew * (kFly > 0 ? 1 : 0) : 1) * (1 - keep), 0);
    leaks.forEach((lab, j) => {
      const top = down ? Y(0) + j * jh + fs * 0.4 : -ph + j * jh, jw = jarW * 0.36, jy0 = top + jh * 0.1, jy1 = top + jh * 0.62, fill = clamp01(first > 0 ? leaked / first : 0);
      const fx = jx - jarW * 0.22;
      out += `<path d="M${r1(fx - jw / 2)} ${r1(jy0)} L${r1(fx - jw / 2)} ${r1(jy1)} Q${r1(fx - jw / 2)} ${r1(jy1 + jh * 0.06)} ${r1(fx - jw / 2 + jw * 0.12)} ${r1(jy1 + jh * 0.06)} L${r1(fx + jw / 2 - jw * 0.12)} ${r1(jy1 + jh * 0.06)} Q${r1(fx + jw / 2)} ${r1(jy1 + jh * 0.06)} ${r1(fx + jw / 2)} ${r1(jy1)} L${r1(fx + jw / 2)} ${r1(jy0)}" fill="#eef6fb" stroke="#7a8ca0" stroke-width="${r1(Math.max(2, w * 0.003))}"/>` +
        rect(fx - jw / 2 + 3, jy1 + jh * 0.05 - (jy1 - jy0) * fill, jw - 6, (jy1 - jy0) * fill, cLeak, `opacity="0.9"`);
      out += txa(lab, fx + jw / 2 + fs * 0.3, (jy0 + jy1) / 2, fitT(lab, jarW * 0.55, fs), INK, 800, "start");
      out += txa(vs(leaked * (sh[j] / shSum), 1), fx + jw / 2 + fs * 0.3, (jy0 + jy1) / 2 + fs * 1.1, Math.min(fs * 0.95, fitT(vs(first), jarW * 0.55, fs)), MUTED, 700, "start");
    });
    if (kFly > 0 && kFly < 1) {                                   // the newest leak travels to the jars
      const k = rounds - 1, x = L + (k + 0.5) * slot, y = Y(amt[k] * (1 - (1 - keep) / 2)), tx2 = jx - jarW * 0.22, ty = down ? Y(0) + jh * 0.3 : -ph + jh * 0.2;
      const cx2 = x + (tx2 - x) * kFly, cy2 = y + (ty - y) * kFly - Math.sin(kFly * Math.PI) * ph * 0.2;
      out += `<circle cx="${r1(cx2)}" cy="${r1(cy2)}" r="${r1(w * 0.012)}" fill="${cLeak}" stroke="${shade(cLeak)}" stroke-width="${r1(Math.max(2, w * 0.003))}"/>`;
    }
  }
  if (p.title) out += tx(p.title, 0, (down ? -ph - fs * 1.2 : -ph) - fs * 2.4, fitT(p.title, w * 0.95, w * 0.04), INK, 800);
  return out;
}

// ---------------------------------------------------------------- weightBars
// Risk-weighted assets: each asset a bar that shrinks to its weight when the weight is applied (cash to nothing, home
// loans to 35%), the weighted bars stack into RWA, and capital over that stack is the ratio on a ruler against its
// threshold; a what-if step glides the amounts (from) and the pointer follows.
function weightBars(p) {
  const w = Math.max(300, num(p.w, 1200)), unit = p.unit ?? "₹", dec = p.decimals;
  let as = parts(p.assets ?? "नकद:100:0;बॉन्ड:200:0.2;होम लोन:400:0.35;कर्ज़:300:1").filter(Boolean).map((t, i) => { const b = t.split(":"); return { l: b[0].trim(), v: Math.max(0, num(b[1], 0)), wt: Math.max(0, Math.min(2, num(b[2], 1))), i }; });
  if (!as.length) as = [{ l: "", v: 0, wt: 1, i: 0 }];
  const n = as.length, fr = listN(p.from), gk = easeIO(prog(sinceStep(p), num(p.glide, 1.2)));
  as.forEach((a) => { const f = fr[a.i]; a.cv = Number.isFinite(f) ? f + (a.v - f) * gk : a.v; });
  const applied = Math.max(0, Math.min(n, Math.round(num(p.applied, 0)))), unw = p.unweighted === true;
  const wf = as.map((a, i) => (unw ? 1 : i < applied - 1 ? a.wt : i === applied - 1 ? 1 + (a.wt - 1) * gk : 1));
  const shownV = as.map((a, i) => a.cv * wf[i]), rwa = shownV.reduce((s, v) => s + v, 0);
  const fs = w * 0.032, fsT = w * 0.04, stack = p.stack === true, ratioOn = p.ratio !== false && num(p.capital, 0) > 0;
  const colW = stack ? w * 0.24 : 0, L = -w / 2, R = w / 2 - colW, slot = (R - L) / n, bw = slot * 0.5, ph = w * 0.3;
  const hi = Math.max(...as.map((a) => Math.max(a.v, a.cv, Number.isFinite(fr[a.i]) ? fr[a.i] : 0)), stack ? rwa : 0, stack ? as.reduce((s, a) => s + a.v * (unw ? 1 : a.wt), 0) : 0, 1);
  const rulerH = ratioOn ? fs * 4.6 : 0, head = p.title ? fsT * 1.6 : 0;
  const H = head + fs * 2.6 + ph + fs * 1.8 + rulerH, top = -H / 2, pb = top + head + fs * 2.6 + ph, Y = (v) => pb - (v / hi) * ph;
  const vs = (v) => withUnit(fmt(v, 1, dec), unit);
  let out = p.title ? tx(p.title, 0, top + fsT * 0.75, fitT(p.title, w * 0.95, fsT), INK, 800) : "";
  out += line(L, pb, R, pb, INK, Math.max(2, w * 0.003));
  const fsV = Math.min(fs, ...as.map((a) => fitT(vs(a.v), slot * 0.95, fs)));
  as.forEach((a, i) => {
    const cx = L + (i + 0.5) * slot, c = PAL[i % PAL.length], hv = shownV[i];
    out += rect(cx - bw / 2, Y(a.cv), bw, pb - Y(a.cv), "none", `stroke="${c}" stroke-width="${r1(Math.max(2, w * 0.003))}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"`) +
      rect(cx - bw / 2, Y(hv), bw, pb - Y(hv), c, `opacity="0.92"`);
    out += txa(vs(hv), cx, Y(Math.max(hv, 0)) - fsV * 0.75, fsV, INK, 800);
    if (p.tags !== false && !unw) { const t = "×" + fmt(a.wt * 100, 1) + "%", f = fitT(t, slot * 0.9, fs); out += pill(t, cx, top + head + f * 0.9, f, i < applied ? shade(c, 0.8) : "#9aa5b1"); }
    out += txa(a.l, cx, pb + fs * 0.9, fitT(a.l, slot * 0.95, fs), INK, 700);
  });
  if (stack) {
    const cx = R + colW / 2, cw = colW * 0.45; let acc = 0;
    shownV.forEach((v, i) => { out += rect(cx - cw / 2, Y(acc + v), cw, Y(acc) - Y(acc + v), PAL[i % PAL.length], `stroke="#ffffff" stroke-width="${r1(Math.max(2, w * 0.003))}"`); acc += v; });
    const t = (p.rwaLabel ?? "RWA") + " " + vs(rwa), f = fitT(t, colW * 0.98, fs);
    out += line(cx - colW * 0.42, pb, cx + colW * 0.42, pb, INK, Math.max(2, w * 0.003)) + pill(t, cx, Y(rwa) - f * 1.2, f, INK);
  }
  if (ratioOn) {
    const cap = num(p.capital, 0), thr = num(p.threshold, 10.5), base = unw ? as.reduce((s, a) => s + a.cv, 0) : rwa, ratio = base > 0 ? (cap / base) * 100 : 0;
    const maxR = Math.max(20, thr * 2, Math.ceil(ratio / 5) * 5), rl = -w * 0.42, rr = w * 0.42, ry = pb + fs * 4.7, RX = (v) => rl + (Math.min(maxR, Math.max(0, v)) / maxR) * (rr - rl);
    out += rect(rl, ry - fs * 0.35, RX(thr) - rl, fs * 0.7, DOWN, `opacity="0.35"`) + rect(RX(thr), ry - fs * 0.35, rr - RX(thr), fs * 0.7, UP, `opacity="0.35"`) +
      rect(rl, ry - fs * 0.35, rr - rl, fs * 0.7, "none", `stroke="#2d3748" stroke-width="${r1(Math.max(2, w * 0.003))}" rx="${r1(fs * 0.2)}"`);
    for (let v = 0; v <= maxR + 1e-9; v += maxR <= 20 ? 5 : 10) out += tx(fmt(v) + "%", RX(v), ry + fs * 1.2, fs, MUTED, 700);
    out += line(RX(thr), ry - fs * 0.8, RX(thr), ry + fs * 0.55, DOWN, Math.max(4, w * 0.005));
    const t = `${p.ratioLabel ?? (unw ? "" : "CAR")} ${fmt(ratio, 0.1)}%`.trim(), f = fitT(t, w * 0.3, fs), x = RX(ratio), ok = ratio >= thr;
    const tt = fmt(thr, thr) + "%", ft = fs, gap = Math.abs(x - RX(thr)) < (tw(t, f) + tw(tt, ft)) / 2 + fs;
    out += `<path d="M${r1(x)} ${r1(ry - fs * 0.4)} L${r1(x - fs * 0.45)} ${r1(ry - fs * 1.1)} L${r1(x + fs * 0.45)} ${r1(ry - fs * 1.1)} Z" fill="${ok ? UP : DOWN}"/>` + pill(t, Math.max(rl, Math.min(rr, x)), ry - fs * 1.9, f, ok ? shade(UP, 0.8) : DOWN);
    if (!gap) out += tx(tt, RX(thr), ry - fs * 1.4, ft, DOWN, 800);
  }
  return out;
}

// ---------------------------------------------------------------- pumpJack (bottom)
// A nodding-donkey pump for crude oil: still, or running (the beam nods and the crank turns as the video plays).
function pumpJack(p) {
  const w = Math.max(60, num(p.w, 420)), run = p.running === true, rate = Math.max(0, Math.min(3, num(p.rate, 0.5))), t = sinceStart(p);
  const ph = run && Number.isFinite(t) ? 2 * Math.PI * rate * t : 0, c = okColor(p.color, "#e07b24"), d = shade(c, 0.65);
  const px = 0, py = -w * 0.62, ang = run ? 0.2 * Math.sin(ph) : 0, bl = w * 0.42, br = w * 0.3;
  const hx = px - Math.cos(ang) * bl, hy = py + Math.sin(ang) * bl, ex = px + Math.cos(ang) * br, ey = py - Math.sin(ang) * br;
  const cx = w * 0.3, cy = -w * 0.2, cr = w * 0.08, kx = cx + Math.cos(ph) * cr, ky = cy + Math.sin(ph) * cr;
  const sw = r1(Math.max(2, w * 0.012));
  let out = rect(-w * 0.5, -w * 0.05, w, w * 0.05, "#8a94a3", `rx="${r1(w * 0.01)}"`) +
    `<path d="M${r1(-w * 0.12)} ${r1(-w * 0.05)} L${r1(px)} ${r1(py)} L${r1(w * 0.12)} ${r1(-w * 0.05)}" fill="none" stroke="${d}" stroke-width="${r1(w * 0.03)}" stroke-linejoin="round"/>` +
    rect(cx - w * 0.08, -w * 0.12, w * 0.16, w * 0.07, "#6b7280") +
    rect(hx - w * 0.012, hy, w * 0.024, -w * 0.05 - hy, "#4a5568") +
    rect(-w * 0.48, -w * 0.11, w * 0.13, w * 0.06, "#4a5568", `rx="${r1(w * 0.01)}"`);
  out += `<path d="M${r1(kx)} ${r1(ky)} L${r1(ex)} ${r1(ey)}" stroke="#4a5568" stroke-width="${r1(w * 0.022)}" stroke-linecap="round"/>` +
    `<circle cx="${r1(cx)}" cy="${r1(cy)}" r="${r1(cr * 1.5)}" fill="${shade(c, 0.85)}" stroke="${d}" stroke-width="${sw}"/><circle cx="${r1(kx)}" cy="${r1(ky)}" r="${r1(w * 0.02)}" fill="${INK}"/>` +
    `<g transform="translate(${r1(px)},${r1(py)}) rotate(${r1((-ang * 180) / Math.PI)})">` +
    rect(-bl, -w * 0.03, bl + br, w * 0.06, c, `stroke="${d}" stroke-width="${sw}" rx="${r1(w * 0.01)}"`) +
    `<path d="M${r1(-bl)} ${r1(-w * 0.07)} Q${r1(-bl - w * 0.1)} 0 ${r1(-bl)} ${r1(w * 0.09)} L${r1(-bl + w * 0.03)} ${r1(w * 0.09)} L${r1(-bl + w * 0.03)} ${r1(-w * 0.07)} Z" fill="${c}" stroke="${d}" stroke-width="${sw}"/></g>` +
    `<circle cx="${r1(px)}" cy="${r1(py)}" r="${r1(w * 0.025)}" fill="${INK}"/>`;
  if (run && Number.isFinite(t)) {               // a drop of oil now and then at the wellhead
    const q = (t * rate) % 1;
    out += `<circle cx="${r1(-w * 0.415)}" cy="${r1(-w * 0.12 - q * w * 0.08)}" r="${r1(w * 0.016 * (1 - q))}" fill="#1f1a17" opacity="${r1(1 - q)}"/>`;
  }
  return out + (p.label ? tx(p.label, 0, w * 0.1, fitT(p.label, w * 1.1, w * 0.1), INK, 800) : "");
}

// ---------------------------------------------------------------- bargainTable
// A bargaining table seen from above: one side (the union) and the other (management), offer and threat cards that
// slide across on their words, a card torn (rejected) or stamped (agreed), a mediator who can join, and the tension.
function bargainTable(p) {
  const w = Math.max(300, num(p.w, 1300)), tw0 = w * 0.74, th = w * 0.36, fs = w * 0.03;
  const cards = parts(p.cards ?? "L:हड़ताल;R:बोनस").filter(Boolean).slice(0, 8).map((c) => { const b = c.split(":"); return { side: (b[0] || "").trim().toUpperCase() === "R" ? "R" : "L", t: (b[1] || "").trim(), st: (b[2] || "").trim() }; });
  const upto = Math.max(0, Math.round(num(p.upto, 0))), shown = upto > 0 ? Math.min(cards.length, upto) : cards.length;
  const k = easeIO(prog(sinceStep(p), num(p.glide, 1))), mood = clamp01(num(p.mood, 0)), t = sinceStart(p);
  const top = -th / 2, cTop = -th / 2 - fs * 2.2;
  let out = "";
  if (p.title) out += tx(p.title, 0, cTop - fs * (p.mediator === true ? 4.6 : 1.6), fitT(p.title, w * 0.95, w * 0.04), INK, 800);
  // the people around the table, seen from above: heads and shoulders
  const seat = (x, y, c) => `<g transform="translate(${r1(x)},${r1(y)})">${iconSvg("person", w * 0.07, c)}</g>`;
  for (let i = 0; i < 3; i++) {
    const y = top + th * (0.22 + i * 0.28);
    out += seat(-tw0 / 2 - w * 0.045, y, "#e5484d") + seat(tw0 / 2 + w * 0.045, y, "#2459a6");
  }
  if (p.mediator === true) out += seat(0, top - w * 0.045, "#7b61ff");
  out += `<rect x="${r1(-tw0 / 2)}" y="${r1(top)}" width="${r1(tw0)}" height="${r1(th)}" rx="${r1(th * 0.12)}" fill="#b98a5a" stroke="#7a5532" stroke-width="${r1(Math.max(3, w * 0.004))}"/>` +
    `<rect x="${r1(-tw0 / 2 + w * 0.012)}" y="${r1(top + w * 0.012)}" width="${r1(tw0 - w * 0.024)}" height="${r1(th - w * 0.024)}" rx="${r1(th * 0.1)}" fill="none" stroke="#d6ae80" stroke-width="${r1(Math.max(2, w * 0.002))}"/>`;
  if (mood > 0) {
    const fl = Number.isFinite(t) ? 0.6 + 0.4 * Math.sin(t * 7) : 1, zz = Array.from({ length: 9 }, (_, i) => `${i ? "L" : "M"}${r1((i % 2 ? 1 : -1) * w * 0.012)} ${r1(top + (th * i) / 8)}`).join(" ");
    out += `<path d="${zz}" fill="none" stroke="${DOWN}" stroke-width="${r1(Math.max(3, w * 0.005))}" opacity="${r1(mood * fl * 100) / 100}" stroke-linejoin="round"/>`;
  }
  // name plates over each side and the mediator
  const plate = (txt, x, y, c) => (txt ? pill(txt, x, y, fitT(txt, w * 0.3, fs * 1.1), c) : "");
  out += plate(p.left ?? "", -tw0 * 0.3, cTop, "#c0392b") + plate(p.right ?? "", tw0 * 0.3, cTop, "#2459a6") +
    (p.mediator === true ? plate(p.mediatorLabel ?? "", 0, top - w * 0.045 - w * 0.032 - fs * 1.05, "#7b61ff") : "");
  // the cards: each lands in the other side's half, one row per card from that side
  const rowsMax = 4, cw = tw0 * 0.36, chh = Math.min((th * 0.84) / rowsMax * 0.78, w * 0.06), seen = { L: 0, R: 0 };
  cards.forEach((c, i) => {
    const row = seen[c.side]++; if (i >= shown) return;
    const dir = c.side === "L" ? 1 : -1, x1 = dir * tw0 * 0.24, x0 = -dir * tw0 * 0.3, y = top + th * 0.08 + (Math.min(row, rowsMax - 1) + 0.5) * ((th * 0.84) / rowsMax);
    const kk = upto > 0 && i === shown - 1 ? k : 1, x = x0 + (x1 - x0) * kk, col = c.side === "L" ? "#c0392b" : "#2459a6";
    const torn = /torn|reject|फटा/i.test(c.st) && kk >= 1, ok = /agree|ok|मंज़ूर|हाँ/i.test(c.st) && kk >= 1;
    const f = fitT(c.t || " ", cw * 0.86, Math.min(fs * 1.15, chh * 0.55));
    const card = (dx, rot, op, clip) => `<g transform="translate(${r1(x + dx)},${r1(y)}) rotate(${rot})" opacity="${op}">` +
      `<rect x="${r1(-cw / 2)}" y="${r1(-chh / 2)}" width="${r1(cw)}" height="${r1(chh)}" rx="${r1(chh * 0.15)}" fill="#ffffff" stroke="${ok ? UP : col}" stroke-width="${r1(Math.max(3, w * (ok ? 0.006 : 0.003)))}"${clip}/>` +
      tx(c.t, 0, 0, f, INK, 800) + `</g>`;
    if (torn) {
      out += card(-cw * 0.03, -2, 0.75, "") + `<path d="M${r1(x - cw * 0.04)} ${r1(y - chh / 2 - 4)} l${r1(cw * 0.03)} ${r1(chh * 0.25)} l${r1(-cw * 0.04)} ${r1(chh * 0.25)} l${r1(cw * 0.04)} ${r1(chh * 0.25)} l${r1(-cw * 0.03)} ${r1(chh * 0.25 + 8)}" fill="none" stroke="#b98a5a" stroke-width="${r1(Math.max(6, w * 0.008))}"/>` +
        line(x - cw * 0.4, y - chh * 0.3, x + cw * 0.36, y + chh * 0.3, DOWN, Math.max(4, w * 0.004), `stroke-linecap="round" opacity="0.8"`);
    } else out += card(0, 0, 1, "");
    if (ok) out += tick(x + cw / 2 - chh * 0.1, y - chh / 2 + chh * 0.1, chh * 0.55);
  });
  return out;
}

export const DRAWS = {
  barChart: { fn: barChart, anchor: "center" },
  marginalBars: { fn: marginalBars, anchor: "bottom" },
  waterfall: { fn: waterfall, anchor: "center" },
  pieChart: { fn: pieChart, anchor: "center" },
  shareBar: { fn: shareBar, anchor: "center" },
  pictogram: { fn: pictogram, anchor: "center" },
  iconArray: { fn: iconArray, anchor: "center" },
  timeSeries: { fn: timeSeries, anchor: "center" },
  scatterFit: { fn: scatterFit, anchor: "center" },
  cycleWave: { fn: cycleWave, anchor: "center" },
  dayHours: { fn: dayHours, anchor: "center" },
  roundBars: { fn: roundBars, anchor: "bottom" },
  weightBars: { fn: weightBars, anchor: "center" },
  pumpJack: { fn: pumpJack, anchor: "bottom" },
  bargainTable: { fn: bargainTable, anchor: "center" },
};

export const PICTOGRAM_ICONS = PICTO_ICONS;
