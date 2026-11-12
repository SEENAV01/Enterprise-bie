// The econ_finance family of saanche (Sloman, Economics: the finance and macro needs of chapters 1-20, 5 November 2026):
// money and stock processes that run while the voice speaks. A circular flow with its two loops or its withdrawals and
// injections, a round-by-round chain (multiplier, credit creation, cash leakage) whose amounts the drawing computes, one
// amount splitting into parts that fly to their places, a stock-flow tank, a T-account balance sheet with its capital
// cushion, value through time, a gamble tree, an insurance pool, a queue served while stock lasts, contagion between
// institutions, a securitisation chain, a layer stack (Basel III capital, a liquidity ladder), an interest-rate
// corridor, a price path with its events, a two-way trade with running ledgers, a road whose traffic thickens, a crowd
// of agents (merging, believing, herding), a chance picture (coin, spinner, fog) and an account balance with its
// overdraft. Every word comes from a parameter; a process is a pure function of _t (seconds since the item appeared)
// and _s (seconds since its last step), and without times (a measurement) it shows its end state.

import { FONT, INK, esc, clamp01, parts, idxSet, isNum, easeIO, shade, rnd, drawSaancha } from "../draw.mjs";
import { textWidth } from "../boxes.mjs";

// ---------------------------------------------------------------- helpers (used inside the drawings only)
const r1 = (v) => (Number.isFinite(v) ? Math.round(v * 10) / 10 : 0);
const num = (v, d) => (isNum(v) ? Number(v) : d);
const tnum = (v) => (v === null || v === undefined || v === "" ? NaN : Number(v));
const since = (p) => { const s = tnum(p._s); return Number.isFinite(s) ? s : tnum(p._t); };
const prog = (s, dur) => (Number.isFinite(s) ? clamp01(s / Math.max(0.05, dur)) : 1);
const clampInt = (v, lo, hi) => Math.max(lo, Math.min(hi, Math.round(v)));
const lerp = (a, b, k) => a + (b - a) * k;
const tw = (t, fs) => textWidth(String(t), fs);
const list = (v) => parts(v).filter(Boolean);
const C = { money: "#2fa35b", real: "#d9822b", dim: "#c3cad3", keep: "#f2c14e", leak: "#9b6bd6", red: "#e5484d", blue: "#2459a6",
  teal: "#2a9d8f", ink2: "#4a5568", paper: "#ffffff", soft: "#f1f4f8" };

function T(text, x, y, size, fill = INK, weight = 700, anchor = "middle") {
  if (text === "" || text == null) return "";
  return `<text x="${r1(x)}" y="${r1(y + size * 0.35)}" font-family=${JSON.stringify(FONT)} font-size="${r1(size)}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}">${esc(text)}</text>`;
}
const pillW = (text, fs, pad = 0.9) => tw(text, fs) + fs * pad;
function pill(text, x, y, fs, o = {}) {
  if (text === "" || text == null) return "";
  const w = Math.max(o.minW || 0, pillW(text, fs, o.pad)), h = fs * 1.45;
  const cx = o.anchor === "start" ? x + w / 2 : o.anchor === "end" ? x - w / 2 : x;
  return `<rect x="${r1(cx - w / 2)}" y="${r1(y - h / 2)}" width="${r1(w)}" height="${r1(h)}" rx="${r1(h * 0.3)}" fill="${o.fill || C.paper}"` +
    (o.stroke ? ` stroke="${o.stroke}" stroke-width="${r1(o.sw || fs * 0.07)}"` : "") + `/>` + T(text, cx, y, fs, o.color || INK, o.weight || 800);
}
function tri(x, y, ang, L, color) {              // a filled arrow head with its tip at (x, y)
  const a1 = ang + Math.PI * 0.84, a2 = ang - Math.PI * 0.84;
  return `<path d="M${r1(x)} ${r1(y)} L${r1(x + L * Math.cos(a1))} ${r1(y + L * Math.sin(a1))} L${r1(x + L * Math.cos(a2))} ${r1(y + L * Math.sin(a2))} Z" fill="${color}"/>`;
}
const qpt = (a, c, b, u) => [(1 - u) ** 2 * a[0] + 2 * (1 - u) * u * c[0] + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * c[1] + u * u * b[1]];
const qang = (a, c, b, u) => Math.atan2(2 * (1 - u) * (c[1] - a[1]) + 2 * u * (b[1] - c[1]), 2 * (1 - u) * (c[0] - a[0]) + 2 * u * (b[0] - c[0]));
const qpath = (a, c, b) => `M${r1(a[0])} ${r1(a[1])} Q${r1(c[0])} ${r1(c[1])} ${r1(b[0])} ${r1(b[1])}`;
const quadPts = (a, c, b, n = 36) => Array.from({ length: n + 1 }, (_, i) => qpt(a, c, b, i / n));
const cubicPts = (a, c1, c2, b, n = 40) => Array.from({ length: n + 1 }, (_, i) => { const u = i / n, v = 1 - u;
  return [v ** 3 * a[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u ** 3 * b[0], v ** 3 * a[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u ** 3 * b[1]]; });
const ptsPath = (q) => q.map((pt, i) => `${i ? "L" : "M"}${r1(pt[0])} ${r1(pt[1])}`).join(" ");
function alongPts(q, u) {                          // the point and heading at a share u of a polyline's length
  const seg = []; let L = 0;
  for (let i = 1; i < q.length; i++) { const d = Math.hypot(q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]); seg.push(d); L += d; }
  let need = clamp01(u) * L;
  for (let i = 0; i < seg.length; i++) {
    if (need <= seg[i] || i === seg.length - 1) { const f = seg[i] ? Math.min(1, need / seg[i]) : 0, a = q[i], b = q[i + 1];
      return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, Math.atan2(b[1] - a[1], b[0] - a[0])]; }
    need -= seg[i];
  }
  return [q[0][0], q[0][1], 0];
}

function group(intStr) {                            // Indian grouping: 12,34,567
  return intStr.length > 3 ? intStr.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + intStr.slice(-3) : intStr;
}
function fmt(v, dp) {
  if (!Number.isFinite(v)) return "";
  if (dp === undefined) dp = Math.abs(v) < 10 ? 2 : 1;
  const r = Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10 ** dp) / 10 ** dp, a = Math.abs(r), [i, d] = String(a).split(".");
  return (r < 0 ? "−" : "") + group(i) + (d ? "." + d : "");
}
function unitOf(u) {
  u = String(u ?? "").trim();
  if (!u) return ["", ""];
  const m = u.match(/^([₹$€£¥])\s*(.*)$/);
  return m ? [m[1], m[2] ? " " + m[2] : ""] : ["", u === "%" ? "%" : " " + u];
}
const money = (v, u, dp) => { const [a, b] = unitOf(u); return a + fmt(v, dp) + b; };
// decimals as the plan wrote them (Sloman ch12/13: ₹100.50, ₹1.50, ₹16.20 were drawn as ₹101, ₹1.5, ₹16.2): decOf counts
// the given decimals, fmtKeep / moneyKeep show exactly that many (with Indian grouping); dp 0 falls back to fmt / money.
const decOf = (v) => { const m = String(v ?? "").replace(/,/g, "").match(/[-−]?\d*\.(\d+)/); return m ? Math.min(4, m[1].length) : 0; };
function fmtKeep(v, dp) {
  if (!Number.isFinite(v)) return "";
  if (!dp) return fmt(v);
  const [i, d] = Math.abs(v).toFixed(dp).split(".");
  return (v < 0 && Number(Math.abs(v).toFixed(dp)) !== 0 ? "−" : "") + group(i) + "." + d;
}
const moneyKeep = (v, u, dp) => { if (!dp) return money(v, u); const [a, b] = unitOf(u); return a + fmtKeep(v, dp) + b; };
const numIn = (v, d) => { const n = Number(String(v ?? "").replace(/[₹$€£¥,\s]/g, "").replace("−", "-")); return String(v ?? "").trim() !== "" && Number.isFinite(n) ? n : d; };
// "label:value" items; the value may glide from an old one: "label:70<80"
function items(v, max = 8) {
  return list(v).slice(0, max).map((s) => {
    const i = s.lastIndexOf(":");
    const label = (i >= 0 ? s.slice(0, i) : s).trim(), rest = i >= 0 ? s.slice(i + 1).trim() : "";
    const [now, old] = rest.split("<").map((x) => x.trim());
    return { label, value: isNum(now) ? Number(now) : null, old: isNum(old) ? Number(old) : null, raw: rest };
  });
}

// small pictures for the places of a process, centred on (0,0) and about s wide; the engine's own saanche where it has them
const PLACE = {
  house: ["building", { kind: "house" }, 0.92, 0.5], firm: ["building", { kind: "factory" }, 0.88, 0.42], factory: ["building", { kind: "factory" }, 0.88, 0.42],
  government: ["building", { kind: "government" }, 0.9, 0.55], office: ["building", { kind: "office" }, 0.8, 0.5],
  shop: ["building", { kind: "shop" }, 0.9, 0.35], warehouse: ["building", { kind: "warehouse" }, 0.9, 0.4], tower: ["building", { kind: "tower" }, 0.6, 0.68],
  exchange: ["building", { kind: "exchange" }, 0.85, 0.5], bank: ["bank", {}, 0.95, 0.42], centralBank: ["centralBank", {}, 0.85, 0.42],
};
function place(kind, s, opt = {}) {
  if (kind === "people") return `<g transform="translate(0,${r1(s * 0.45)})">${drawSaancha("crowd", { w: s * 0.95, n: 6, cols: 3 })}</g>`;
  if (kind === "person") return person(0, s * 0.45, s * 0.9, opt.i || 0, opt.dim);
  if (kind === "globe") return `<circle r="${r1(s * 0.42)}" fill="#9fd0f0" stroke="${C.blue}" stroke-width="${r1(s * 0.03)}"/>` +
    `<ellipse rx="${r1(s * 0.18)}" ry="${r1(s * 0.42)}" fill="none" stroke="${C.blue}" stroke-width="${r1(s * 0.02)}"/>` +
    `<path d="M${r1(-s * 0.42)} 0 L${r1(s * 0.42)} 0 M${r1(-s * 0.36)} ${r1(-s * 0.2)} L${r1(s * 0.36)} ${r1(-s * 0.2)} M${r1(-s * 0.36)} ${r1(s * 0.2)} L${r1(s * 0.36)} ${r1(s * 0.2)}" stroke="${C.blue}" stroke-width="${r1(s * 0.02)}"/>` +
    `<path d="M${r1(-s * 0.2)} ${r1(-s * 0.1)} q${r1(s * 0.1)} ${r1(-s * 0.15)} ${r1(s * 0.22)} ${r1(-s * 0.05)} q${r1(s * 0.05)} ${r1(s * 0.15)} ${r1(-s * 0.1)} ${r1(s * 0.2)} Z" fill="#7cc47a"/>`;
  if (kind === "vault") return `<g transform="translate(0,${r1(s * 0.45)})">${drawSaancha("vault", { w: s * 0.8, fill: opt.fill ?? 0.6 })}</g>`;
  if (kind === "pool") return `<ellipse cy="${r1(s * 0.12)}" rx="${r1(s * 0.48)}" ry="${r1(s * 0.3)}" fill="#dbe7f5" stroke="${C.blue}" stroke-width="${r1(s * 0.03)}"/>`;
  const k = PLACE[kind];
  if (k) return `<g transform="translate(0,${r1(s * k[3])}) scale(${r1(k[2] * 100) / 100})">${drawSaancha(k[0], { ...k[1], w: s })}</g>`;
  return `<rect x="${r1(-s * 0.45)}" y="${r1(-s * 0.32)}" width="${r1(s * 0.9)}" height="${r1(s * 0.64)}" rx="${r1(s * 0.1)}" fill="#eef3fb" stroke="#5b7fb8" stroke-width="${r1(s * 0.03)}"/>`;
}
const SKIN = ["#c68a5c", "#d39a6a", "#b97c50", "#a8714a", "#d8a274", "#c98c5e"];
const SHIRT = ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f", "#2a9d8f", "#9b6b43"];
function person(x, y, s, i, dim, shirt) {            // a small standing person, feet at (x, y), s tall
  const sk = SKIN[(i * 7) % SKIN.length], sh = shirt || SHIRT[(i * 5 + 3) % SHIRT.length];
  return `<g transform="translate(${r1(x)},${r1(y)})"${dim ? ` opacity="${dim}"` : ""}><path d="M${r1(-s * 0.24)} 0 L${r1(-s * 0.24)} ${r1(-s * 0.48)} Q${r1(-s * 0.24)} ${r1(-s * 0.7)} 0 ${r1(-s * 0.7)} Q${r1(s * 0.24)} ${r1(-s * 0.7)} ${r1(s * 0.24)} ${r1(-s * 0.48)} L${r1(s * 0.24)} 0 Z" fill="${sh}" stroke="${shade(sh)}" stroke-width="${r1(s * 0.025)}"/>` +
    `<circle cy="${r1(-s * 0.84)}" r="${r1(s * 0.16)}" fill="${sk}" stroke="${shade(sk)}" stroke-width="${r1(s * 0.02)}"/>` +
    `<path d="M${r1(-s * 0.16)} ${r1(-s * 0.87)} Q0 ${r1(-s * 1.08)} ${r1(s * 0.16)} ${r1(-s * 0.87)} Q0 ${r1(-s * 0.94)} ${r1(-s * 0.16)} ${r1(-s * 0.87)} Z" fill="#1f1a17"/></g>`;
}
function token(kind, r, col) {
  if (kind === "note") return `<rect x="${r1(-r * 1.4)}" y="${r1(-r * 0.75)}" width="${r1(r * 2.8)}" height="${r1(r * 1.5)}" rx="${r1(r * 0.2)}" fill="#6cbf7f" stroke="#2f7a45" stroke-width="${r1(r * 0.16)}"/><circle r="${r1(r * 0.4)}" fill="#e8f5ea"/>`;
  if (kind === "goods") return `<rect x="${r1(-r)}" y="${r1(-r)}" width="${r1(2 * r)}" height="${r1(2 * r)}" rx="${r1(r * 0.15)}" fill="#c8a06a" stroke="#8a6d3b" stroke-width="${r1(r * 0.16)}"/><path d="M${r1(-r)} ${r1(-r * 0.25)} L${r1(r)} ${r1(-r * 0.25)} M0 ${r1(-r)} L0 ${r1(-r * 0.25)}" stroke="#8a6d3b" stroke-width="${r1(r * 0.14)}"/>`;
  if (kind === "labour") return person(0, r * 1.1, r * 2.2, 2, 0, "#2459a6");
  if (kind === "slip") return `<rect x="${r1(-r * 0.8)}" y="${r1(-r * 1.1)}" width="${r1(r * 1.6)}" height="${r1(r * 2.2)}" rx="${r1(r * 0.15)}" fill="#fdf3e7" stroke="#d9822b" stroke-width="${r1(r * 0.16)}"/><path d="M${r1(-r * 0.45)} ${r1(-r * 0.4)} L${r1(r * 0.45)} ${r1(-r * 0.4)} M${r1(-r * 0.45)} ${r1(r * 0.1)} L${r1(r * 0.45)} ${r1(r * 0.1)}" stroke="#d9822b" stroke-width="${r1(r * 0.14)}"/>`;
  if (kind === "dot") return `<circle r="${r1(r * 0.75)}" fill="${col || C.red}"/>`;
  return `<circle r="${r1(r)}" fill="#f2c14e" stroke="#c99a2e" stroke-width="${r1(r * 0.18)}"/><circle r="${r1(r * 0.55)}" fill="none" stroke="#c99a2e" stroke-width="${r1(r * 0.1)}"/>`;
}
const at = (x, y, svg, sc) => `<g transform="translate(${r1(x)},${r1(y)})${sc && sc !== 1 ? ` scale(${r1(sc * 100) / 100})` : ""}">${svg}</g>`;
function plate(text, x, y, fs, col = INK) {          // a dark name plate
  return pill(text, x, y, fs, { fill: col, color: "#ffffff" });
}
const tickMark = (x, y, r, col = C.money) => `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(r)}" fill="${col}"/><path d="M${r1(x - r * 0.45)} ${r1(y + r * 0.02)} L${r1(x - r * 0.1)} ${r1(y + r * 0.38)} L${r1(x + r * 0.5)} ${r1(y - r * 0.35)}" fill="none" stroke="#ffffff" stroke-width="${r1(r * 0.24)}" stroke-linecap="round" stroke-linejoin="round"/>`;
const crossMark = (x, y, r, col = C.red) => `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(r)}" fill="${col}"/><path d="M${r1(x - r * 0.4)} ${r1(y - r * 0.4)} L${r1(x + r * 0.4)} ${r1(y + r * 0.4)} M${r1(x + r * 0.4)} ${r1(y - r * 0.4)} L${r1(x - r * 0.4)} ${r1(y + r * 0.4)}" stroke="#ffffff" stroke-width="${r1(r * 0.24)}" stroke-linecap="round"/>`;

// ---------------------------------------------------------------- circular flow
// Households and firms. mode "goods": an outer money loop one way, an inner real loop (goods, labour) the other, the
// goods market on top and the factor market below. mode "income": the money ring with withdrawals (S, T, M) leaving the
// households for their sectors and injections (I, G, X) joining the firms, each as thick as its amount; W and J totals.
function circularFlow(p) {
  const w = num(p.w, 1500), h = w * 0.6, fs = w * 0.027, t = tnum(p._t), s = since(p);
  const mode = p.mode === "income" ? "income" : "goods", size = Math.max(0.2, num(p.size, 1)), sp = Math.max(0, num(p.speed, 0.25));
  const hx = -w * 0.37, fx = w * 0.37, ns = w * 0.12, base = w * 0.0075 * size, tr = w * 0.013 * Math.sqrt(size);
  const labs = parts(p.arrows), act = String(p.active || "all");
  let back = "", lines = "", toks = "", words = "";
  const flowOn = (key) => act === "all" || act === key || (act === "money" && key.startsWith("m")) || (act === "real" && key.startsWith("r")) ||
    (act === "top" && key.endsWith("T")) || (act === "bottom" && key.endsWith("B"));
  const run = (q, sw, col, on, tok, n = 4, ph = 0) => {
    const [hx2, hy2, ang] = alongPts(q, 1);
    lines += `<path d="${ptsPath(alongTrim(q))}" fill="none" stroke="${on ? col : C.dim}" stroke-width="${r1(sw)}" stroke-linecap="round" stroke-linejoin="round"${on ? "" : ` stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.01)}"`}/>` +
      tri(hx2, hy2, ang, Math.max(sw * 2.2, w * 0.022), on ? col : C.dim);
    if (!on) return;
    for (let k = 0; k < n; k++) {
      const u = Number.isFinite(t) ? (((t * sp + ph + k / n) % 1) + 1) % 1 : (k + 0.5) / n;
      const [x, y] = alongPts(q, 0.05 + u * 0.85);
      toks += at(x, y, token(tok, tr));
    }
  };
  const alongTrim = (q) => { const [x, y] = alongPts(q, 0.97); return [...q.filter((pt, i) => i < q.length * 0.97), [x, y]]; };
  const income = num(p.income, NaN), incomeFrom = num(p.incomeFrom, NaN), unit = p.unit ?? "";
  const g = Math.max(0.1, num(p.glide, 2)), kk = easeIO(prog(s, g));
  const Y = Number.isFinite(income) ? (Number.isFinite(incomeFrom) ? lerp(incomeFrom, income, kk) : income) : NaN;
  if (mode === "goods") {
    const mt = p.moneyToken === "note" ? "note" : "coin", rt = p.realToken === "labour" ? "labour" : "goods";
    const oT = [[hx + ns * 0.15, -ns * 0.62], [0, -h * 0.76], [fx - ns * 0.15, -ns * 0.62]];
    const iT = [[fx - ns * 0.5, -ns * 0.3], [0, -h * 0.38], [hx + ns * 0.5, -ns * 0.3]];
    const oB = oT.map(([x, y]) => [-x, -y]), iB = iT.map(([x, y]) => [-x, -y]);
    run(quadPts(...oT), base, C.money, flowOn("mT"), mt, 4, 0);
    run(quadPts(...iT), base, C.real, flowOn("rT"), "goods", 3, 0.1);
    run(quadPts(...oB), base, C.money, flowOn("mB"), mt, 4, 0.5);
    run(quadPts(...iB), base, C.real, flowOn("rB"), rt === "labour" ? "labour" : "goods", 3, 0.6);
    const oPk = 0.5 * oT[0][1] + 0.5 * oT[1][1], iPk = 0.5 * iT[0][1] + 0.5 * iT[1][1];
    words += pill(labs[0], 0, oPk - fs * 1.15, fs, { stroke: C.money, color: shade(C.money, 0.7) }) +
      pill(labs[1], 0, iPk + fs * 1.15, fs, { stroke: C.real, color: shade(C.real, 0.7) }) +
      pill(labs[2], 0, -oPk + fs * 1.15, fs, { stroke: C.money, color: shade(C.money, 0.7) }) +
      pill(labs[3], 0, -iPk - fs * 1.15, fs, { stroke: C.real, color: shade(C.real, 0.7) });
    if (p.top) words += pill(p.top, 0, (oPk + iPk) / 2, fs * 1.05, { fill: "#2d3748", color: "#ffffff" });
    if (p.bottom) words += pill(p.bottom, 0, -(oPk + iPk) / 2, fs * 1.05, { fill: "#2d3748", color: "#ffffff" });
  } else {
    const leaks = items(p.leaks, 3), injs = items(p.injections, 3), secs = parts(p.sectors), n = Math.max(leaks.length, injs.length);
    const lit = new Set(list(p.lit).map((x) => x.toUpperCase())), litOn = (nm) => !lit.size || lit.has(String(nm).toUpperCase());
    const amts = [...leaks, ...injs].map((x) => x.value).filter((v) => v != null && v >= 0), top = Math.max(1e-9, ...amts);
    const thick = (v) => (v == null ? base : base * Math.max(0.35, (v / top) * 1.6));
    const W = leaks.reduce((a, x) => a + (x.value || 0), 0), J = injs.reduce((a, x) => a + (x.value || 0), 0);
    const oT = [[hx + ns * 0.1, -ns * 0.62], [hx + ns * 0.1, -h * 0.58], [fx - ns * 0.1, -h * 0.58], [fx - ns * 0.1, -ns * 0.62]];
    const oB = oT.map(([x, y]) => [-x, -y]), pk = 0.75 * oT[1][1] + 0.25 * oT[0][1];
    run(cubicPts(...oT), base * 1.6, C.money, flowOn("mT"), "coin", 6, 0);
    run(cubicPts(...oB), base * 1.6, C.money, flowOn("mB"), "coin", 6, 0.5);
    const topText = [labs[0], Number.isFinite(Y) && amts.length ? money(Y - W, unit) : ""].filter(Boolean).join(" ");
    const botText = [labs[1], Number.isFinite(Y) ? money(Y, unit) : ""].filter(Boolean).join(" ");
    words += pill(topText, 0, pk, fs * 1.05, { stroke: C.money, color: shade(C.money, 0.6), sw: w * 0.003 }) +
      pill(botText, 0, -pk, fs * 1.05, { stroke: C.money, color: shade(C.money, 0.6), sw: w * 0.003 });
    const ys = n === 1 ? [0] : n === 2 ? [-h * 0.14, h * 0.14] : [-h * 0.24, 0, h * 0.24];
    for (let k = 0; k < n; k++) {
      const y = ys[k], name = secs[k] || "", bw = Math.max(w * 0.15, pillW(name, fs)), bh = fs * 1.6;
      if (secs.some(Boolean)) back += `<rect x="${r1(-bw / 2)}" y="${r1(y - bh / 2)}" width="${r1(bw)}" height="${r1(bh)}" rx="${r1(bh * 0.25)}" fill="#eef3fb" stroke="#5b7fb8" stroke-width="${r1(w * 0.002)}"/>` + T(name, 0, y, fs, INK, 800);
      const lk = leaks[k], ij = injs[k];
      if (lk) {
        const a = [hx + ns * 0.5, y * 0.4], b = [-bw / 2 - w * 0.012, y], on = litOn(lk.label), q = cubicPts(a, [lerp(a[0], b[0], 0.45), a[1]], [lerp(a[0], b[0], 0.55), b[1]], b);
        run(q, thick(lk.value), C.red, on, "coin", 3, 0.2 * k);
        const [mx, my] = alongPts(q, 0.62);
        words += pill([lk.label, lk.value != null ? money(lk.value, unit) : lk.raw].filter(Boolean).join(" "), mx, my - fs * 1.0 - thick(lk.value) / 2, fs, { stroke: on ? C.red : C.dim, color: on ? shade(C.red, 0.7) : C.ink2 });
      }
      if (ij) {
        const a = [bw / 2 + w * 0.012, y], b = [fx - ns * 0.5, y * 0.4], on = litOn(ij.label), q = cubicPts(a, [lerp(a[0], b[0], 0.45), a[1]], [lerp(a[0], b[0], 0.55), b[1]], b);
        run(q, thick(ij.value), C.blue, on, "coin", 3, 0.2 * k + 0.1);
        const [mx, my] = alongPts(q, 0.38);
        words += pill([ij.label, ij.value != null ? money(ij.value, unit) : ij.raw].filter(Boolean).join(" "), mx, my - fs * 1.0 - thick(ij.value) / 2, fs, { stroke: on ? C.blue : C.dim, color: on ? shade(C.blue, 0.7) : C.ink2 });
      }
    }
    if (p.brackets && n) {
      const eq = Math.abs(W - J) < 1e-9, by = h * 0.305, bc = eq ? C.money : "#d9822b";
      words += pill(`${p.wLabel ?? "W"} = ${money(W, unit)}`, -w * 0.22, by, fs, { fill: bc, color: "#ffffff" }) +
        pill(`${p.jLabel ?? "J"} = ${money(J, unit)}`, w * 0.22, by, fs, { fill: bc, color: "#ffffff" });
    }
  }
  // the economy inside its environment: an enclosing ring with resources in and wastes out
  if (p.outer) {
    back = `<ellipse rx="${r1(w * 0.5)}" ry="${r1(h * 0.56)}" fill="#eef8ef" stroke="#2f8f4e" stroke-width="${r1(w * 0.005)}" stroke-dasharray="${r1(w * 0.016)} ${r1(w * 0.01)}"/>` + back;
    words += pill(p.outer, 0, -h * 0.56, fs * 1.05, { fill: "#2f8f4e", color: "#ffffff" });
    const ia = [w * 0.44, -h * 0.3], ib = [fx + ns * 0.18, -ns * 0.5], oa = [hx - ns * 0.18, ns * 0.5], ob = [-w * 0.44, h * 0.3];
    lines += `<path d="M${r1(ia[0])} ${r1(ia[1])} L${r1(ib[0])} ${r1(ib[1])}" stroke="#2f8f4e" stroke-width="${r1(w * 0.008)}" stroke-linecap="round"/>` +
      tri(ib[0], ib[1], Math.atan2(ib[1] - ia[1], ib[0] - ia[0]), w * 0.024, "#2f8f4e") +
      `<path d="M${r1(oa[0])} ${r1(oa[1])} L${r1(ob[0])} ${r1(ob[1])}" stroke="#8a6d3b" stroke-width="${r1(w * 0.008)}" stroke-linecap="round"/>` +
      tri(ob[0], ob[1], Math.atan2(ob[1] - oa[1], ob[0] - oa[0]), w * 0.024, "#8a6d3b");
    if (p.inputs) words += pill(p.inputs, w * 0.36, -h * 0.4, fs, { stroke: "#2f8f4e", color: "#2f8f4e" });
    if (p.outputs) words += pill(p.outputs, -w * 0.36, h * 0.4, fs, { stroke: "#8a6d3b", color: "#8a6d3b" });
  }
  const node = (x, kind, name) => at(x, 0, place(kind, ns)) + (name ? plate(name, x, ns * 0.62, fs * 1.05) : "");
  return back + lines + node(hx, "house", p.households) + node(fx, "firm", p.firms) + toks + words;
}

// ---------------------------------------------------------------- round-by-round chain
// One amount travels through a chain of stops (banks, shops, people): at each stop a share is kept (reserves), a share
// leaks (cash held, saving, imports) and the rest moves on; a total bar grows round by round towards its limit
// start / (keep + leak). Round n lights on its step and plays over glide seconds: the amount travels in, the kept and
// leaked slices drop, the total adds its block. view "bars" draws the rounds as shrinking bars instead of stops.
function chainRounds(p) {
  const w = num(p.w, 1600), h = w * 0.5, fs = w * 0.025, view = p.view === "bars" ? "bars" : "row";
  const start = Math.max(0, num(p.start, 100)), keep = clamp01(num(p.keep, 0.1)), leak = Math.min(1 - keep, clamp01(num(p.leak, 0)));
  const pass = Math.max(0, 1 - keep - leak), R = clampInt(num(p.rounds, 4), 1, 6), unit = p.unit ?? "";
  const A = Array.from({ length: R }, (_, i) => start * pass ** i), limit = keep + leak > 0 ? start / (keep + leak) : NaN;
  const upto = p.upto ? clampInt(num(p.upto, R), 0, R) : R, fin = p.final === true, s = since(p), g = Math.max(0.2, num(p.glide, 1.6));
  const k = prog(s, g), kNew = fin ? 1 : k, names = parts(p.names), kind = p.node || "bank";
  const totalSoFar = A.slice(0, upto).reduce((a, v) => a + v, 0) - (upto && !fin ? A[upto - 1] * (1 - easeIO(clamp01((k - 0.5) * 2))) : 0);
  const shownTotal = fin && Number.isFinite(limit) ? lerp(A.slice(0, upto).reduce((a, v) => a + v, 0), limit, easeIO(k)) : totalSoFar;
  let out = "";
  const x0 = -w * 0.43, x1 = w * 0.17, slot = R > 1 ? (x1 - x0) / (R - 1) : 0, xs = A.map((_, i) => (R > 1 ? x0 + i * slot : (x0 + x1) / 2));
  const gs = Math.min(R > 1 ? slot * 0.55 : w * 0.12, w * 0.1);
  const newest = upto - 1, phase1 = easeIO(clamp01(kNew * 2)), phase2 = easeIO(clamp01(kNew * 2 - 1));
  if (view === "row") {
    for (let i = 0; i < R; i++) {
      const x = xs[i], on = i < upto, isNew = i === newest;
      // the arrow in (from the left for round 1)
      const ax = i === 0 ? x - Math.max(slot, w * 0.1) * 0.55 : xs[i - 1] + gs * 0.55, bx = x - gs * 0.55;
      out += `<path d="M${r1(ax)} 0 L${r1(bx - w * 0.008)} 0" stroke="${on ? C.money : C.dim}" stroke-width="${r1(w * 0.006)}" stroke-linecap="round"${on ? "" : ` stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.008)}"`}/>` +
        tri(bx, 0, 0, w * 0.018, on ? C.money : C.dim);
      out += `<g opacity="${on ? 1 : 0.35}">${at(x, 0, place(kind, gs))}</g>`;
      if (names[i]) out += T(names[i], x, gs * 0.62 + fs * 0.6, fs, on ? INK : "#8a94a3", 800);
      if (!on) continue;
      if (isNew && phase1 < 1) out += at(lerp(ax, bx, phase1), 0, token("note", w * 0.012));
      if (!isNew || phase1 >= 1) {
        out += pill(money(A[i], unit), x, -gs * 0.62 - fs * 0.95, fs * 1.05, { fill: "#e9f6ee", stroke: C.money, color: shade(C.money, 0.6) });
        const d = isNew ? phase2 : 1, yk = gs * 0.62 + fs * (names[i] ? 2.1 : 1.0), drop = (y) => lerp(0, y, d);
        if (d > 0) {
          const two = leak > 0 && keep > 0, kx = two ? x - slot * 0.22 : x, lx = two ? x + slot * 0.22 : x;
          if (keep > 0) out += `<g opacity="${r1(Math.min(1, d * 2) * 100) / 100}">` + pill(money(A[i] * keep, unit), kx, drop(yk), fs, { fill: C.keep, color: "#5a4300" }) + `</g>`;
          if (leak > 0) out += `<g opacity="${r1(Math.min(1, d * 2) * 100) / 100}">` + pill(money(A[i] * leak, unit), lx, drop(yk), fs, { fill: C.leak, color: "#ffffff" }) + `</g>`;
        }
      }
    }
  } else {
    const top = A[0] || 1, bw = Math.min(slot * 0.5, w * 0.08), H = h * 0.62, yb = h * 0.3;
    for (let i = 0; i < R; i++) {
      const x = xs[i], on = i < upto, isNew = i === newest, grow = isNew ? phase1 : 1, bh = (A[i] / top) * H * grow;
      const hp = bh * pass, hk = bh * keep, hl = bh * leak;
      if (!on) { out += `<rect x="${r1(x - bw / 2)}" y="${r1(yb - (A[i] / top) * H)}" width="${r1(bw)}" height="${r1((A[i] / top) * H)}" fill="none" stroke="${C.dim}" stroke-width="${r1(w * 0.002)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"/>`; continue; }
      out += `<rect x="${r1(x - bw / 2)}" y="${r1(yb - hp)}" width="${r1(bw)}" height="${r1(hp)}" fill="${C.money}"/>` +
        `<rect x="${r1(x - bw / 2)}" y="${r1(yb - hp - hk)}" width="${r1(bw)}" height="${r1(hk)}" fill="${C.keep}"/>` +
        `<rect x="${r1(x - bw / 2)}" y="${r1(yb - bh)}" width="${r1(bw)}" height="${r1(hl)}" fill="${C.leak}"/>`;
      if (i + 1 < R && (i + 1 < upto)) out += `<path d="M${r1(x + bw / 2)} ${r1(yb - hp)} L${r1(xs[i + 1] - bw / 2)} ${r1(yb - hp)}" stroke="${shade(C.money, 0.7)}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"/>`;
      if (grow >= 1) out += T(money(A[i], unit), x, yb - bh - fs * 0.9, fs, INK, 800);
      out += T(names[i] || String(i + 1), x, yb + fs * 0.95, fs, C.ink2, 800);
    }
  }
  // the dots after the last round
  for (let j = 0; j < 3; j++) out += `<circle cx="${r1(x1 + w * 0.06 + j * w * 0.018)}" cy="${view === "row" ? 0 : r1(h * 0.24)}" r="${r1(w * 0.005)}" fill="${upto >= R ? INK : C.dim}"/>`;
  // the running total bar and its limit
  if (p.total !== false) {
    const bx = w * 0.39, bw = w * 0.075, yb = h * 0.34, H = h * 0.62, cap = Number.isFinite(limit) ? limit : A.reduce((a, v) => a + v, 0);
    out += `<rect x="${r1(bx - bw / 2)}" y="${r1(yb - H)}" width="${r1(bw)}" height="${r1(H)}" fill="${C.soft}" stroke="#9aa5b1" stroke-width="${r1(w * 0.002)}"/>`;
    let acc = 0;
    A.slice(0, upto).forEach((v, i) => {
      const part = i === newest && !fin ? v * easeIO(clamp01((k - 0.5) * 2)) : v, hh = (part / cap) * H;
      out += `<rect x="${r1(bx - bw / 2)}" y="${r1(yb - acc - hh)}" width="${r1(bw)}" height="${r1(hh)}" fill="${i % 2 ? shade(C.money, 1.25) : C.money}"/>`;
      acc += hh;
    });
    if (fin && Number.isFinite(limit)) { const extra = ((shownTotal - totalSoFar) / cap) * H; out += `<rect x="${r1(bx - bw / 2)}" y="${r1(yb - acc - extra)}" width="${r1(bw)}" height="${r1(Math.max(0, extra))}" fill="${shade(C.money, 1.45)}"/>`; acc += extra; }
    if (Number.isFinite(limit)) out += `<path d="M${r1(bx - bw * 0.9)} ${r1(yb - H)} L${r1(bx + bw * 0.9)} ${r1(yb - H)}" stroke="${C.red}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.005)}"/>` +
      (p.limit === false ? "" : T(money(limit, unit), bx, yb - H - fs * 0.85, fs, C.red, 800));
    out += pill(money(shownTotal, unit), bx, Math.max(yb - acc - fs * 0.9, yb - H + fs * 1.0), fs * 1.05, { fill: INK, color: "#ffffff" });
    if (p.totalLabel) out += T(p.totalLabel, bx, yb + fs * 0.95, fs, INK, 800);
  }
  // the legend: what the kept and leaked slices are called
  const legend = [[keep > 0 && p.keepLabel, C.keep], [leak > 0 && p.leakLabel, C.leak], [view === "bars" && p.passLabel, C.money]].filter(([l]) => l);
  if (legend.length) {
    let lx = -w * 0.47, y = h * 0.5;
    legend.forEach(([l, c]) => { out += `<rect x="${r1(lx)}" y="${r1(y - fs * 0.45)}" width="${r1(fs * 0.9)}" height="${r1(fs * 0.9)}" rx="${r1(fs * 0.2)}" fill="${c}"/>` + T(l, lx + fs * 1.2, y, fs, INK, 700, "start"); lx += fs * 2 + tw(l, fs) + fs; });
  }
  return out;
}

// ---------------------------------------------------------------- stock-flow tank
// A tank whose water is a stock: taps pour flows in (ins), spouts let flows out (outs), each as wide as its rate. The level
// glides from where it was (from) to where it goes (level) after the step, or settles like a leaky tank (settle: the
// outflow grows with the level). Marks name levels (Y1, Y2); a clock beside it stands still for a stock, runs for a flow.
function tank(p) {
  const w = num(p.w, 800), fs = w * 0.05, t = tnum(p._t), s = since(p), g = Math.max(0.1, num(p.glide, 2.5));
  const TW = w * 0.46, x0 = -TW / 2 - w * 0.04, x1 = TW / 2 - w * 0.04, yb = -w * 0.2, yt = -w * 0.84, H = yb - yt, inset = w * 0.012;
  const L1 = clamp01(num(p.level, 0.5)), L0 = isNum(p.from) ? clamp01(+p.from) : L1;
  const L = p.settle ? L1 + (L0 - L1) * Math.exp((-4 * (Number.isFinite(s) ? s : 99)) / g) : lerp(L0, L1, easeIO(prog(s, g)));
  const ws = yb - L * (H - inset * 2) - inset, ins = items(p.ins, 3), outs = items(p.outs, 3), col = p.color || "#5aa9e6";
  const moving = Number.isFinite(t) ? t : 0;
  let out = "";
  // stand and its plate
  out += `<rect x="${r1(x0 + TW * 0.08)}" y="${r1(yb)}" width="${r1(w * 0.03)}" height="${r1(-yb)}" fill="#8a94a3"/><rect x="${r1(x1 - TW * 0.08 - w * 0.03)}" y="${r1(yb)}" width="${r1(w * 0.03)}" height="${r1(-yb)}" fill="#8a94a3"/>` +
    `<path d="M${r1(x0 + TW * 0.1)} ${r1(yb * 0.15)} L${r1(x1 - TW * 0.1)} ${r1(yb * 0.85)} M${r1(x1 - TW * 0.1)} ${r1(yb * 0.15)} L${r1(x0 + TW * 0.1)} ${r1(yb * 0.85)}" stroke="#a7b0bc" stroke-width="${r1(w * 0.008)}"/>`;
  // water
  out += `<rect x="${r1(x0)}" y="${r1(yt)}" width="${r1(TW)}" height="${r1(H)}" rx="${r1(w * 0.02)}" fill="#f4f8fb"/>`;
  if (L > 0.003) {
    let wave = `M${r1(x0 + inset)} ${r1(yb - inset)} L${r1(x0 + inset)} ${r1(ws)}`;
    for (let j = 0; j <= 12; j++) { const xx = x0 + inset + ((TW - inset * 2) * j) / 12; wave += ` L${r1(xx)} ${r1(ws + Math.sin(j * 1.3 + moving * 3) * w * 0.004)}`; }
    out += `<path d="${wave} L${r1(x1 - inset)} ${r1(yb - inset)} Z" fill="${col}" opacity="0.85"/>`;
  }
  out += `<rect x="${r1(x0)}" y="${r1(yt)}" width="${r1(TW)}" height="${r1(H)}" rx="${r1(w * 0.02)}" fill="none" stroke="#5b6b7d" stroke-width="${r1(w * 0.012)}"/>`;
  // level marks
  list(p.marks).slice(0, 3).forEach((m) => {
    const [v, nm] = m.split(":"); if (!isNum(v)) return;
    const y = yb - clamp01(+v) * (H - inset * 2) - inset;
    out += `<path d="M${r1(x0 - w * 0.02)} ${r1(y)} L${r1(x1)} ${r1(y)}" stroke="${INK}" stroke-width="${r1(w * 0.004)}" stroke-dasharray="${r1(w * 0.014)} ${r1(w * 0.01)}"/>` +
      (nm ? T(nm.trim(), x0 - w * 0.035, y, fs, INK, 800, "end") : "");
  });
  // taps in: pipes from the left, each tap pouring as wide as its rate
  const drops = (xa, ya, xb, yb2, sw, c) => `<path d="M${r1(xa)} ${r1(ya)} L${r1(xb)} ${r1(yb2)}" stroke="${c}" stroke-width="${r1(sw)}" stroke-linecap="round" stroke-dasharray="${r1(w * 0.03)} ${r1(w * 0.012)}" stroke-dashoffset="${r1(-moving * w * 0.25)}" opacity="0.9"/>`;
  ins.forEach((it, k) => {
    const rate = clamp01(it.value ?? 0.5), py = yt - w * 0.09 - k * w * 0.12, tx2 = x0 + TW * (0.22 + 0.28 * k), lx = -w * 0.5;
    out += `<path d="M${r1(lx)} ${r1(py)} L${r1(tx2)} ${r1(py)} L${r1(tx2)} ${r1(py + w * 0.04)}" fill="none" stroke="#6b7a8c" stroke-width="${r1(w * 0.03)}" stroke-linejoin="round"/>` +
      `<rect x="${r1(tx2 - w * 0.03)}" y="${r1(py + w * 0.035)}" width="${r1(w * 0.06)}" height="${r1(w * 0.025)}" rx="${r1(w * 0.008)}" fill="#4a5568"/>` +
      `<circle cx="${r1(tx2)}" cy="${r1(py - w * 0.028)}" r="${r1(w * 0.02)}" fill="${C.red}"/>`;
    if (rate > 0) out += drops(tx2, py + w * 0.06, tx2, ws, Math.max(w * 0.006, rate * w * 0.05), col);
    if (it.label) out += T(it.label, lx, py - fs * 0.95, fs, shade(C.blue, 0.8), 800, "start");
  });
  // spouts out: low on the right wall, jets as wide as their rate (and the level, if settle)
  outs.forEach((it, k) => {
    const rate = clamp01(it.value ?? 0.4) * (p.settle || p.grows ? Math.max(0.15, L / Math.max(0.05, L1 || 0.05)) : 1), y = yb - w * 0.05 - k * w * 0.08;
    out += `<rect x="${r1(x1 - w * 0.005)}" y="${r1(y - w * 0.018)}" width="${r1(w * 0.06)}" height="${r1(w * 0.036)}" rx="${r1(w * 0.008)}" fill="#6b7a8c"/>`;
    const wet = L * (H - inset * 2) + inset > yb - y;
    if (rate > 0 && wet) {
      const a = [x1 + w * 0.055, y], c = [x1 + w * 0.2, y - w * 0.02], b = [x1 + w * 0.27, -w * 0.005];
      out += `<path d="${qpath(a, c, b)}" fill="none" stroke="${col}" stroke-width="${r1(Math.max(w * 0.006, Math.min(1.4, rate) * w * 0.045))}" stroke-linecap="round" stroke-dasharray="${r1(w * 0.03)} ${r1(w * 0.012)}" stroke-dashoffset="${r1(-moving * w * 0.25)}" opacity="0.9"/>`;
    }
    if (it.label) out += T(it.label, x1 + w * 0.09, y - fs * 0.62, fs, shade(C.red, 0.75), 800, "start");
  });
  if (p.value) out += pill(p.value, (x0 + x1) / 2, yt + H * 0.5, fs, { stroke: "#5b6b7d" });
  if (p.label) out += plate(p.label, (x0 + x1) / 2, yb * 0.5, fs);
  if (p.clock === "stock" || p.clock === "flow") {
    const cx = x0 - w * 0.13, cy = yb * 0.55, r = w * 0.055, a = p.clock === "flow" ? moving * 2.4 : 0.9;
    out += `<circle cx="${r1(cx)}" cy="${r1(cy)}" r="${r1(r)}" fill="#ffffff" stroke="${INK}" stroke-width="${r1(w * 0.008)}"/>` +
      `<path d="M${r1(cx)} ${r1(cy)} L${r1(cx + Math.sin(a) * r * 0.75)} ${r1(cy - Math.cos(a) * r * 0.75)} M${r1(cx)} ${r1(cy)} L${r1(cx + Math.sin(a / 12 + 2) * r * 0.5)} ${r1(cy - Math.cos(a / 12 + 2) * r * 0.5)}" stroke="${INK}" stroke-width="${r1(w * 0.007)}" stroke-linecap="round"/>` +
      (p.clock === "stock" ? `<rect x="${r1(cx + r * 0.7)}" y="${r1(cy - r * 1.1)}" width="${r1(r * 0.18)}" height="${r1(r * 0.55)}" fill="${C.red}"/><rect x="${r1(cx + r * 0.95)}" y="${r1(cy - r * 1.1)}" width="${r1(r * 0.18)}" height="${r1(r * 0.55)}" fill="${C.red}"/>` : "");
  }
  return out;
}

// ---------------------------------------------------------------- balance sheet (T-account)
// Assets on the left, liabilities and capital on the right; rows enter on cue (upto), a value can glide from its old
// amount ("Loans:70<80"), the totals stay balanced (a tick) or not (a cross), the capital row is a cushion. view
// "blocks" stacks both sides as blocks whose heights follow the amounts; a loss eats the top asset and the capital
// cushion with it, and a loss bigger than the capital leaves the bank insolvent (red).
function balanceSheet(p) {
  const w = num(p.w, 1200), fs = w * 0.034, unit = p.unit ?? "", s = since(p), g = Math.max(0.1, num(p.glide, 1.5)), k = easeIO(prog(s, g));
  const A = items(p.assets, 6), Lb = items(p.liabilities, 6), n = Math.max(A.length, Lb.length, 1);
  const val = (r) => (r.value == null ? 0 : r.old != null ? lerp(r.old, r.value, k) : r.value);
  const capIdx = p.cushion === false ? -1 : num(p.capital, Lb.length) - 1, glow = new Set(list(p.glow).map((x) => x.toLowerCase()));
  const upto = p.upto ? clampInt(num(p.upto, n), 0, n) : n;
  let out = "";
  const head = (txt, x, c) => pill(txt, x, 0, fs * 1.05, { fill: c, color: "#ffffff", minW: w * 0.3 });
  if ((p.view || "table") === "table") {
    const rh = fs * 1.85, top = -((n + 2) * rh) / 2 - (p.title ? rh * 0.5 : 0), hy = top + (p.title ? rh * 1.1 : 0) + rh * 0.5;
    if (p.title) out += T(p.title, 0, top + rh * 0.3, fs * 1.15, INK, 800);
    out += at(0, hy, head(p.leftHead ?? "", -w * 0.25, C.blue)) + at(0, hy, head(p.rightHead ?? "", w * 0.25, "#d9822b"));
    const ty = hy + rh * 0.62, yEnd = ty + (n + 1) * rh + rh * 0.2;
    out += `<path d="M${r1(-w * 0.49)} ${r1(ty)} L${r1(w * 0.49)} ${r1(ty)} M0 ${r1(ty)} L0 ${r1(yEnd)}" stroke="${INK}" stroke-width="${r1(w * 0.006)}" stroke-linecap="round"/>`;
    const side = (rows, sgn, key) => rows.forEach((r, i) => {
      if (i >= upto) return;
      const y = ty + (i + 0.55) * rh, xl = sgn < 0 ? -w * 0.47 : w * 0.03, xr = sgn < 0 ? -w * 0.03 : w * 0.47, cap = key === "l" && i === capIdx;
      const changing = r.old != null && Number.isFinite(s) && prog(s, g) < 1, lit = glow.has(key + (i + 1));
      if (cap) out += `<rect x="${r1(xl - w * 0.005)}" y="${r1(y - rh * 0.42)}" width="${r1(xr - xl + w * 0.01)}" height="${r1(rh * 0.84)}" rx="${r1(rh * 0.42)}" fill="#fff1c7" stroke="${C.keep}" stroke-width="${r1(w * 0.004)}"/>`;
      if (lit || changing) out += `<rect x="${r1(xl - w * 0.008)}" y="${r1(y - rh * 0.46)}" width="${r1(xr - xl + w * 0.016)}" height="${r1(rh * 0.92)}" rx="${r1(rh * 0.2)}" fill="none" stroke="#f29f05" stroke-width="${r1(w * 0.005)}"/>`;
      out += T(r.label, xl + w * 0.012, y, fs, INK, 700, "start") + T(r.value == null ? r.raw : money(val(r), unit), xr - w * 0.012, y, fs, r.old != null && r.value < r.old ? shade(C.red, 0.8) : INK, 800, "end");
    });
    side(A, -1, "a"); side(Lb, 1, "l");
    if (p.totals !== false && upto >= n) {
      const y = ty + (n + 0.55) * rh, SA = A.reduce((a, r) => a + val(r), 0), SL = Lb.reduce((a, r) => a + val(r), 0), ok = Math.abs(SA - SL) < 1e-6;
      out += `<path d="M${r1(-w * 0.47)} ${r1(y - rh * 0.5)} L${r1(-w * 0.03)} ${r1(y - rh * 0.5)} M${r1(w * 0.03)} ${r1(y - rh * 0.5)} L${r1(w * 0.47)} ${r1(y - rh * 0.5)}" stroke="#9aa5b1" stroke-width="${r1(w * 0.003)}"/>` +
        T(p.totalLabel ?? "", -w * 0.455, y, fs, INK, 800, "start") + T(money(SA, unit), -w * 0.042, y, fs * 1.05, INK, 800, "end") +
        T(p.totalLabel ?? "", w * 0.045, y, fs, INK, 800, "start") + T(money(SL, unit), w * 0.458, y, fs * 1.05, INK, 800, "end") +
        (ok ? tickMark(0, y, fs * 0.62) : crossMark(0, y, fs * 0.62));
    }
    return out;
  }
  // blocks
  const loss = Math.max(0, num(p.loss, 0)) * k, H = w * 0.55, cw = w * 0.24, xa = -w * 0.2, xl = w * 0.2, yb = H * 0.5;
  const av = A.map(val), lv = Lb.map(val), SA = av.reduce((a, v) => a + v, 0), SL = lv.reduce((a, v) => a + v, 0), scale = H / Math.max(1e-9, SA, SL);
  const capV = capIdx >= 0 && capIdx < lv.length ? lv[capIdx] : 0, eaten = Math.min(loss, SA), capLeft = capV - eaten;
  const cols = ["#3a7bd5", "#2a9d8f", "#7b61ff", "#2fa35b", "#c0563f", "#9b6b43"], lcols = ["#d9822b", "#e2558f", "#c0563f", "#8a6d3b", "#4a5568", "#2a9d8f"];
  const block = (x, y, hh, c, label, v, sgn, hatch) => {
    let b = `<rect x="${r1(x - cw / 2)}" y="${r1(y - hh)}" width="${r1(cw)}" height="${r1(Math.max(0, hh))}" fill="${c}" stroke="#ffffff" stroke-width="${r1(w * 0.003)}"${hatch ? ` opacity="0.9"` : ""}/>`;
    const txt = [label, v].filter((z) => z !== "" && z != null).join(" ");
    if (hh >= fs * 1.35) b += T(txt, x, y - hh / 2, fs, "#ffffff", 800);
    else if (txt) b += T(txt, x + sgn * (cw / 2 + w * 0.02), y - hh / 2, fs, INK, 800, sgn < 0 ? "end" : "start");
    return b;
  };
  let y = yb;
  A.forEach((r, i) => {
    if (i >= upto) return;
    let v = av[i];
    if (i === A.length - 1 || i === upto - 1) v = Math.max(0, v - eaten);
    out += block(xa, y, v * scale, cols[i % cols.length], r.label, money(v, unit), -1);
    y -= v * scale;
  });
  const aTop = y;
  if (eaten > 0) out += `<rect x="${r1(xa - cw / 2)}" y="${r1(y - eaten * scale)}" width="${r1(cw)}" height="${r1(eaten * scale)}" fill="none" stroke="${C.red}" stroke-width="${r1(w * 0.004)}" stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.007)}"/>` +
    (p.lossLabel ? T(`${p.lossLabel} ${money(eaten, unit)}`, xa - cw / 2 - w * 0.02, y - (eaten * scale) / 2, fs, C.red, 800, "end") : "");
  if (capLeft < 0) out += `<rect x="${r1(xa - cw / 2)}" y="${r1(aTop + capLeft * scale)}" width="${r1(cw)}" height="${r1(-capLeft * scale)}" fill="${C.red}" opacity="0.35"/>`;
  y = yb;
  Lb.forEach((r, i) => {
    if (i >= upto) return;
    const cap = i === capIdx, v = cap ? Math.max(0, capLeft) : lv[i];
    if (cap && v > 0) out += `<rect x="${r1(xl - cw / 2 - w * 0.008)}" y="${r1(y - v * scale - w * 0.008)}" width="${r1(cw + w * 0.016)}" height="${r1(v * scale + w * 0.016)}" rx="${r1(w * 0.02)}" fill="#fff1c7" stroke="${C.keep}" stroke-width="${r1(w * 0.005)}"/>`;
    out += block(xl, y, v * scale, cap ? "#e0a100" : lcols[i % lcols.length], r.label, money(cap ? capLeft : v, unit), 1);
    y -= v * scale;
  });
  if (capLeft < 0 && p.brokeLabel) out += pill(p.brokeLabel, xl, y - fs * 1.3, fs, { fill: C.red, color: "#ffffff" });
  out += `<path d="M${r1(-w * 0.4)} ${r1(yb)} L${r1(w * 0.4)} ${r1(yb)}" stroke="${INK}" stroke-width="${r1(w * 0.005)}"/>`;
  if (p.leftHead) out += T(p.leftHead, xa, yb + fs * 1.0, fs, C.blue, 800);
  if (p.rightHead) out += T(p.rightHead, xl, yb + fs * 1.0, fs, "#b0611f", 800);
  if (p.title) out += T(p.title, 0, yb - H - fs * 1.4, fs * 1.1, INK, 800);
  return out;
}

// ---------------------------------------------------------------- value through time
// A time axis (today, year 1, year 2 ... or hours of a day) with amounts at their slots. On a step, travel = n sends the
// first n amounts to "now" (dir back: they shrink by the discount factor d = 1/(1+r) per period, and by the present-bias
// factor b if not immediate) or to the last slot (dir forward: they grow by (1+r) per period), moving and changing size
// over glide seconds; their values sum at the end, and a cost paid today can be judged against the sum. Several rates
// draw one lane each (the same amount, two discount rates). "now" can move: a slot already passed is greyed.
function timeValue(p) {
  const w = num(p.w, 1500), fs = w * 0.026, unit = p.unit ?? "", s = since(p), g = Math.max(0.2, num(p.glide, 2));
  const P = clampInt(num(p.periods, 3), 1, 60), slots = parts(p.slots), now = clampInt(num(p.now, 0), 0, P), fwd = p.dir === "forward";
  const rates = list(p.rate).map(Number).filter(Number.isFinite).slice(0, 3);
  if (!rates.length) rates.push(0.1);
  // d: one discount factor, or one per lane (0.9;0.8): a lane per factor, its label d = 0.9 unless laneLabels names it
  const dList = list(p.d).map((x) => Number(x)).filter(Number.isFinite).map(clamp01).slice(0, 3);
  while (dList.length > 1 && rates.length < dList.length) rates.push(rates[rates.length - 1]);
  const dGiven = dList.length ? dList[0] : null, dLane = (li) => (dList.length ? dList[Math.min(li, dList.length - 1)] : null), b = isNum(p.b) ? clamp01(+p.b) : 1;
  const amts = list(p.amounts).slice(0, 6).map((a) => { const i = a.lastIndexOf(":"), lab = i >= 0 ? a.slice(0, i).trim() : "", body = i >= 0 ? a.slice(i + 1) : a;
    const [v, at2] = body.split("@").map((x) => x.trim()); return { lab, v: numIn(v, 0), dp: decOf(v), at: clampInt(num(at2, fwd ? 0 : P), 0, P) }; });
  const dpAll = Math.max(0, ...amts.map((a) => a.dp), decOf(p.cost)), mk = (v, dp) => moneyKeep(v, unit, dp);
  const travel = clampInt(num(p.travel, 0), 0, amts.length), newest = travel - 1, e = easeIO(prog(s, g));
  const x0 = -w * 0.36, x1 = w * 0.42, X = (i) => x0 + (i * (x1 - x0)) / P, nl = rates.length, laneH = nl > 1 ? w * 0.13 : w * 0.17;
  const axisY = (nl * laneH) / 2 + fs * 0.4, top = Math.max(1e-9, ...amts.map((a) => Math.abs(a.v))), target = fwd ? P : now;
  let out = "";
  // the axis, its slots and the "now" flag
  out += `<path d="M${r1(x0 - w * 0.03)} ${r1(axisY)} L${r1(x1 + w * 0.04)} ${r1(axisY)}" stroke="${INK}" stroke-width="${r1(w * 0.004)}"/>` +
    tri(x1 + w * 0.05, axisY, 0, w * 0.018, INK);
  const every = P <= 8 ? 1 : Math.ceil(P / 6);
  for (let i = 0; i <= P; i++) {
    const explicit = slots.some(Boolean), past = i < now && !fwd, lab = explicit ? (slots[i] ?? "") : P <= 8 || i % every === 0 || i === P ? String(i) : "";
    out += `<path d="M${r1(X(i))} ${r1(axisY - w * 0.008)} L${r1(X(i))} ${r1(axisY + w * 0.008)}" stroke="${past ? C.dim : INK}" stroke-width="${r1(w * 0.003)}"/>`;
    if (lab) out += T(lab, X(i), axisY + fs * 1.05, fs, past ? "#9aa5b1" : INK, i === now ? 800 : 700);
  }
  out += `<path d="M${r1(X(now))} ${r1(axisY)} L${r1(X(now))} ${r1(-axisY + fs * 0.2)}" stroke="${C.teal}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}"/>` +
    `<path d="M${r1(X(now))} ${r1(-axisY + fs * 0.2)} l${r1(w * 0.03)} ${r1(w * 0.012)} l${r1(-w * 0.03)} ${r1(w * 0.012)} Z" fill="${C.teal}"/>`;
  // the factor between slots (×d each period, or ×(1+r)), under the axis between the slot names
  if (p.showFactor && p.showFactor !== "none" && nl === 1 && P <= 8) for (let i = 0; i < P; i++) {
    if (!fwd && i < now) continue;
    const d = dGiven ?? 1 / (1 + rates[0]), f = fwd ? 1 + rates[0] : d, txt = p.showFactor === "symbol" ? (fwd ? "×(1+r)" : "×d") : "×" + fmt(f, 3);
    out += T(txt, (X(i) + X(i + 1)) / 2, axisY + fs * 1.05, fs, C.teal, 800);
  }
  let total = 0;
  rates.forEach((r, li) => {
    const d = dLane(li) ?? 1 / (1 + r), laneY = -axisY + fs * 0.6 + (li + 0.5) * laneH + (nl > 1 ? 0 : laneH * 0.1), coinY = laneY + laneH * 0.22;
    if (nl > 1) out += `<path d="M${r1(x0)} ${r1(coinY)} L${r1(x1)} ${r1(coinY)}" stroke="${C.dim}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.008)}"/>` +
      T(list(p.laneLabels)[li] || (dList.length > 1 ? `d = ${fmt(d, 3)}` : `${fmt(r * 100, 2)}%`), x0 - w * 0.05, coinY, fs, C.blue, 800, "end");
    const factor = (dist, part) => (fwd ? (1 + r) ** (dist * part) : d ** (dist * part) * (dist > 0 ? b ** part : 1));
    let arrived = 0, row = 0;
    amts.forEach((a, k) => {
      const dist = Math.abs(target - a.at), moving = k === newest ? e : k < travel ? 1 : 0, x = lerp(X(a.at), X(target), moving);
      const v = a.v * factor(dist, moving), neg = v < 0, txt = [a.lab, mk(v, a.dp)].filter(Boolean).join(" ");
      let rad = Math.max(w * 0.008, Math.sqrt(Math.abs(v) / top) * laneH * 0.26), y = coinY;
      if (moving >= 1) arrived += v;
      // the amount that left stays as a faded ghost at its own slot (ch12: "₹100 in 30 years" vanished once it travelled,
      // so the picture showed only ₹41 / ₹6 with nothing to compare them to); ghost: false turns it off
      if (moving > 0 && dist > 1 && p.ghost !== false && li === 0 && amts.length === 1) {   // one amount: its ghost has room
        const g0 = a.v, gt = [a.lab, mk(g0, a.dp)].filter(Boolean).join(" "), gr = Math.max(w * 0.008, Math.min(Math.sqrt(Math.abs(g0) / top) * laneH * 0.26, fs * 0.8));
        out += `<g opacity="0.5"><circle cx="${r1(X(a.at))}" cy="${r1(coinY)}" r="${r1(gr)}" fill="none" stroke="#c99a2e" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.006)} ${r1(w * 0.004)}"/>` +
          pill(gt, X(a.at), coinY - gr - fs * 0.95, fs, { stroke: "#c99a2e", color: INK }) + `</g>`;
      }
      if (moving >= 1 && nl === 1 && travel > 1) {           // arrived amounts stack up at their end slot, one row each
        rad = Math.min(rad, fs * 0.7); y = coinY - row * fs * 1.65; row++;
        out += `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(rad)}" fill="${neg ? "#f6b5b7" : "#f2c14e"}" stroke="${neg ? C.red : "#c99a2e"}" stroke-width="${r1(w * 0.003)}"/>` +
          pill(txt, x + (fwd ? -1 : 1) * (fs * 0.9), y, fs, { anchor: fwd ? "end" : "start", stroke: neg ? C.red : "#c99a2e", color: neg ? shade(C.red, 0.7) : INK });
        return;
      }
      out += `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(rad)}" fill="${neg ? "#f6b5b7" : "#f2c14e"}" stroke="${neg ? C.red : "#c99a2e"}" stroke-width="${r1(w * 0.003)}"/>` +
        pill(txt, x, y - rad - fs * 0.95, fs, { stroke: neg ? C.red : "#c99a2e", color: neg ? shade(C.red, 0.7) : INK });
    });
    total += arrived;
  });
  // under the end slot: the cost paid today and the sum (or the net), judged
  const cost = isNum(String(p.cost ?? "").replace(/,/g, "")) ? Math.abs(numIn(p.cost, 0)) : null, ux = X(target);
  if (cost != null && !fwd) out += pill(`${p.costLabel ? p.costLabel + " " : ""}${mk(-cost, dpAll)}`, ux, axisY + fs * 2.65, fs, { fill: "#fdeeee", stroke: C.red, color: shade(C.red, 0.7) });
  if (p.sum && travel && nl === 1) {
    const net = p.net && cost != null, val = net ? total - cost : total, txt = `${p.sumLabel ? p.sumLabel + " " : "Σ "}${mk(val, dpAll)}`, sy = axisY + fs * (cost != null && !fwd ? 4.4 : 2.65);
    out += pill(txt, ux, sy, fs * 1.05, { fill: net && val < 0 ? C.red : C.teal, color: "#ffffff" });
    if (cost != null && p.judge !== false && travel >= amts.length && e >= 1) out += ((net ? val >= 0 : total >= cost) ? tickMark : crossMark)(ux + pillW(txt, fs * 1.05) / 2 + fs * 0.9, sy, fs * 0.6);
  }
  if (p.title) out += T(p.title, 0, -axisY - fs * 0.9, fs * 1.1, INK, 800);
  return out;
}

// ---------------------------------------------------------------- gamble tree
// A gamble as branches from a chance point: each branch carries its probability and outcome; terms (p × outcome) appear at
// the branch ends and, with fly, slide into one expected-value pill over glide seconds after the step; a sure path can sit
// beside the gamble. A step that changes a probability recomputes the terms and the expected value.
function gambleTree(p) {
  const w = num(p.w, 1400), h = w * 0.55, fs = w * 0.026, unit = p.unit ?? "", s = since(p), g = Math.max(0.2, num(p.glide, 1.5)), e = easeIO(prog(s, g));
  const parseP = (v) => { v = String(v ?? "").trim(); const m = v.match(/^(-?[\d.]+)\s*\/\s*([\d.]+)$/); if (m) return +m[1] / (+m[2] || 1);
    if (v.endsWith("%")) return num(v.slice(0, -1), 0) / 100; return num(v, 0); };
  const br = list(p.branches).slice(0, 4).map((b) => { const [l, pp, o] = b.split(":").map((x) => (x ?? "").trim()); return { l, ptxt: pp, p: parseP(pp), o: numIn(o, 0), dp: decOf(o) }; });
  if (!br.length) br.push({ l: "", ptxt: "1/2", p: 0.5, o: 100 }, { l: "", ptxt: "1/2", p: 0.5, o: 0 });
  const sure = String(p.sure ?? "").trim(), [sl, sv] = sure.includes(":") ? sure.split(":").map((x) => x.trim()) : ["", sure];
  const glow = num(p.glow, 0), n = br.length, ev = br.reduce((a, b) => a + b.p * b.o, 0);
  const dp = Math.max(0, ...br.map((b) => b.dp || 0), decOf(sv)), mk = (v) => moneyKeep(v, unit, dp), fk = (v) => (dp ? fmtKeep(v, dp) : fmt(v));
  const rx = -w * 0.38, ex = -w * 0.06, ys = br.map((_, i) => (n === 1 ? 0 : -h * 0.4 + (i * h * 0.8) / (n - 1)) - (sure ? h * 0.08 : 0));
  const outTxt = br.map((b) => [b.l, moneyKeep(b.o, unit, b.dp)].filter(Boolean).join(" ")), ox = ex + fs * 0.4;
  const termX = ox + Math.max(...outTxt.map((t2) => pillW(t2, fs * 1.05))) + fs * 1.2;
  const termTxt = br.map((b) => `${fmt(b.p, 3)} × ${b.dp ? fmtKeep(b.o, b.dp) : fmt(b.o)} = ${fk(b.p * b.o)}`), termW = Math.max(...termTxt.map((t2) => tw(t2, fs)));
  const evTxt = `${p.evLabel ? p.evLabel + " " : "EV "}${mk(ev)}`, evX = Math.max(w * 0.4, termX + termW + fs * 1.5 + pillW(evTxt, fs * 1.15) / 2);
  let out = "";
  if (sure) {
    const y = h * 0.47;
    out += `<rect x="${r1(rx - w * 0.1)}" y="${r1(-w * 0.025)}" width="${r1(w * 0.05)}" height="${r1(w * 0.05)}" fill="#2d3748"/>` +
      `<path d="M${r1(rx - w * 0.075)} ${r1(w * 0.025)} L${r1(rx - w * 0.075)} ${r1(y)} L${r1(ex)} ${r1(y)}" fill="none" stroke="${C.money}" stroke-width="${r1(w * 0.006)}" stroke-dasharray="${r1(w * 0.014)} ${r1(w * 0.008)}"/>` +
      `<path d="M${r1(rx - w * 0.05)} 0 L${r1(rx)} 0" stroke="${C.blue}" stroke-width="${r1(w * 0.006)}"/>` +
      pill([sl, isNum(String(sv).replace(/,/g, "")) ? mk(numIn(sv, 0)) : sv].filter(Boolean).join(" "), ox, y, fs * 1.05, { anchor: "start", fill: "#e9f6ee", stroke: C.money, color: shade(C.money, 0.6) });
  }
  out += `<circle cx="${r1(rx)}" cy="0" r="${r1(w * 0.022)}" fill="${C.blue}"/>`;
  br.forEach((b, i) => {
    const y = ys[i], lit = !glow || glow === i + 1, col = lit ? C.blue : C.dim;
    const a = [rx + w * 0.02, 0], c = [rx + w * 0.12, y], d = [ex, y];
    out += `<path d="${qpath(a, c, d)}" fill="none" stroke="${col}" stroke-width="${r1(w * (glow === i + 1 ? 0.009 : 0.006))}" stroke-linecap="round"/>`;
    const [mx, my] = qpt(a, c, d, 0.6);
    out += pill(b.ptxt || fmt(b.p, 2), mx, my, fs, { fill: lit ? "#eef3fb" : "#f4f5f7", stroke: col, color: lit ? C.blue : "#8a94a3" });
    out += pill(outTxt[i], ox, y, fs * 1.05, { anchor: "start", fill: lit ? "#ffffff" : "#f4f5f7", stroke: lit ? INK : C.dim, color: lit ? INK : "#8a94a3" });
    if (p.terms !== false) {
      const k = p.fly ? e : 0, tx2 = lerp(termX, evX - tw(termTxt[i], fs) / 2, k), ty = lerp(y, 0, k);
      if (k < 1) out += `<g opacity="${r1((1 - k * 0.7) * 100) / 100}">` + T(termTxt[i], tx2, ty, fs, lit ? shade(C.teal, 0.7) : "#8a94a3", 800, "start") + `</g>`;
    }
  });
  if (p.ev !== false && (!p.fly || e >= 1 || !Number.isFinite(s))) out += pill(evTxt, evX, 0, fs * 1.15, { fill: C.teal, color: "#ffffff" });
  if (p.title) out += T(p.title, 0, -h * 0.58, fs * 1.1, INK, 800);
  return out;
}

// ---------------------------------------------------------------- insurance pool
// Many members pay a premium into one pot; each year a share of them has an accident and is paid a claim. phase
// "premium" sends a coin from every member into the pot, "claim" turns the hit members red and sends claim notes out,
// over glide seconds after the step. Two risk groups can be drawn (types) and one of them can walk out (leave: adverse
// selection). The ledger beside it computes premiums in, claims out, admin cost and the margin.
function insurancePool(p) {
  const w = num(p.w, 1500), h = w * 0.5, fs = w * 0.025, unit = p.unit ?? "", s = since(p), g = Math.max(0.3, num(p.glide, 2)), e = prog(s, g);
  const n = clampInt(num(p.n, 40), 1, 100), premium = num(p.premium, 0), claim = num(p.claim, 0), admin = num(p.admin, 0);
  const types = items(p.types, 2), leave = num(p.leave, 0), seed = clampInt(num(p.year, 1), 0, 9999) + 7;
  const cols = Math.ceil(Math.sqrt(n * 1.4)), rows = Math.ceil(n / cols), gw = w * 0.42, cell = Math.min(gw / cols, (h * 0.85) / rows), ps = cell * 0.82;
  const gx0 = -w * 0.48, gy0 = -(rows * cell) / 2;
  // which group each member is in, who has left, who is hit (seeded: the same year gives the same members)
  const grp = Array.from({ length: n }, (_, i) => (types.length === 2 ? ((i % cols) < cols / 2 ? 0 : 1) : 0));
  const share = (gi) => (types.length ? clamp01(types[gi]?.value ?? 0) : clamp01(num(p.share, 0.05)));
  const gone = (i) => types.length === 2 && leave === grp[i] + 1;
  const r = rnd(seed), order = Array.from({ length: n }, (_, i) => [r(), i]).sort((a, b) => a[0] - b[0]).map((x) => x[1]);
  const hit = new Set();
  [0, 1].forEach((gi) => { const mem = order.filter((i) => grp[i] === gi && !gone(i)); const k = Math.round(mem.length * share(gi)); mem.slice(0, k).forEach((i) => hit.add(i)); });
  const stay = Array.from({ length: n }, (_, i) => i).filter((i) => !gone(i)), N = stay.length, H = hit.size;
  const potX = w * 0.02, potY = 0, phase = p.phase || "none";
  const gc = ["#3a7bd5", "#e07b24"];
  let out = "";
  // the pot
  out += `<g transform="translate(${r1(potX)},${r1(h * 0.28)})">${drawSaancha("coinJar", { w: w * 0.13, fill: phase === "claim" ? lerp(0.8, 0.45, e) : phase === "premium" ? lerp(0.2, 0.8, e) : 0.6 })}</g>`;
  if (p.pot) out += plate(p.pot, potX, h * 0.36, fs);
  for (let i = 0; i < n; i++) {
    const c = i % cols, rr = Math.floor(i / cols), x = gx0 + (c + 0.5) * cell, y = gy0 + (rr + 1) * cell - cell * 0.08;
    const left = gone(i), walk = left ? (Number.isFinite(s) ? clamp01(s / g) : 1) : 0, isHit = hit.has(i) && phase === "claim";
    const shirt = types.length === 2 ? gc[grp[i]] : isHit ? C.red : "#3a7bd5";
    out += person(x - walk * w * 0.25, y, ps, i, left ? r1((1 - walk * 0.85) * 100) / 100 : 0, isHit ? C.red : shirt);
    if (isHit && e > 0) out += at(lerp(potX, x, e), lerp(-h * 0.05, y - ps * 0.5, e), token("note", fs * 0.42));
    if (phase === "premium" && !left) { const k = clamp01(e * 1.4 - (i / n) * 0.4); if (k > 0 && k < 1) out += at(lerp(x, potX, k), lerp(y - ps * 0.5, -h * 0.05, k), token("coin", fs * 0.32)); }
  }
  if (types.length === 2) types.forEach((t2, gi) => {
    const y = gy0 - fs * 1.2, x = gx0 + (gi ? Math.ceil(cols / 2) + (cols - Math.ceil(cols / 2)) / 2 : Math.ceil(cols / 2) / 2) * cell, lab = [t2.label, t2.value != null ? `${fmt(t2.value * 100, 1)}%` : ""].filter(Boolean).join(" ");
    out += pill(lab, x, y - fs * 0.2, fs, { fill: gc[gi], color: "#ffffff", opacity: leave === gi + 1 ? 0.4 : 1 });
  });
  if (p.totals !== false) {
    const lab = parts(p.labels), lx = w * 0.17, rx2 = w * 0.49, rh = fs * 1.7, rowsL = [
      [lab[0] ?? "", N * premium, C.money], [lab[1] ?? "", -H * claim, C.red], [lab[2] ?? "", -N * admin, "#8a6d3b"]];
    const margin = N * premium - H * claim - N * admin;
    let y = -rh * 1.6;
    if (p.title) out += T(p.title, (lx + rx2) / 2, y - rh, fs * 1.05, INK, 800);
    rowsL.forEach(([l, v, c]) => { if (!l && !v) return; out += T(l, lx, y, fs, INK, 700, "start") + T(money(v, unit), rx2, y, fs, c, 800, "end"); y += rh; });
    out += `<path d="M${r1(lx)} ${r1(y - rh * 0.5)} L${r1(rx2)} ${r1(y - rh * 0.5)}" stroke="${INK}" stroke-width="${r1(w * 0.003)}"/>` +
      T(lab[3] ?? "", lx, y, fs, INK, 800, "start") + T(money(margin, unit), rx2, y, fs * 1.05, margin >= 0 ? shade(C.money, 0.7) : C.red, 800, "end");
    if (p.countLabel) out += T(`${p.countLabel} ${H} / ${N}`, (lx + rx2) / 2, y + rh * 1.3, fs, C.red, 800);
  }
  return out;
}

// ---------------------------------------------------------------- queue served while stock lasts
// A line of people (or trucks) before a counter, gate, ticket window, operation theatre or bank counter. The counter
// serves rate people per second from the step on (served counts up, the line advances), the stock on the counter falls
// with each one; at stock 0 a bar drops and the rest turn away (sad) or move to a waiting list whose board counts them.
// urgent members jump to the front; joinRate adds people at the back; a bank counter's vault drains with the stock.
function queueLine(p) {
  const w = num(p.w, 1600), fs = w * 0.024, t = tnum(p._t), s = since(p), S = Number.isFinite(s) ? s : 999;
  const n0 = clampInt(num(p.n, 10), 0, 40), stock0 = Math.max(0, num(p.stock, 5)), served0 = Math.max(0, num(p.served, 0)), rate = Math.max(0, num(p.rate, 0));
  const join = Math.max(0, num(p.joinRate, 0)), n = Math.min(60, n0 + Math.floor(join * (Number.isFinite(s) ? s : 0)));
  const cap = served0 + stock0, q = Math.min(cap, served0 + rate * S, served0 + n), stock = Math.max(0, cap - q);
  const out0 = stock <= 1e-9 && n > q, tEnd = rate > 0 ? (cap - served0) / rate : 0, sinceEnd = Math.max(0, S - tEnd);
  const kind = p.place || "counter", cx = w * 0.3, gap = Math.min(w * 0.055, (w * 0.7) / Math.max(1, n - q + 1)), ps = Math.min(w * 0.085, gap * 1.7);
  const urgent = idxSet(p.urgent), order = [...Array(n).keys()].sort((a, b) => (urgent.has(b + 1) ? 1 : 0) - (urgent.has(a + 1) ? 1 : 0) || a - b);
  let out = `<path d="M${r1(-w * 0.5)} 0 L${r1(w * 0.5)} 0" stroke="#c9c3b6" stroke-width="${r1(w * 0.004)}"/><!--behind-->`, behind = "";
  // the counter
  const ch = w * 0.11, cw2 = w * 0.12, cols = { counter: "#a0703d", gate: "#6b7a8c", theatre: "#2a9d8f", bank: "#3a7bd5", office: "#5b7fb8", ration: "#c0563f" };
  const cc = cols[kind] || cols.counter;
  if (kind === "gate") out += `<rect x="${r1(cx - w * 0.01)}" y="${r1(-ch * 1.6)}" width="${r1(w * 0.02)}" height="${r1(ch * 1.6)}" fill="${cc}"/><rect x="${r1(cx + cw2 * 0.8)}" y="${r1(-ch * 1.6)}" width="${r1(w * 0.02)}" height="${r1(ch * 1.6)}" fill="${cc}"/>` +
    `<rect x="${r1(cx - w * 0.01)}" y="${r1(-ch * 1.7)}" width="${r1(cw2 * 0.8 + w * 0.03)}" height="${r1(w * 0.02)}" fill="${cc}"/>`;
  else if (kind === "theatre") out += `<rect x="${r1(cx)}" y="${r1(-ch * 1.5)}" width="${r1(cw2)}" height="${r1(ch * 1.5)}" rx="${r1(w * 0.008)}" fill="#e8f4f2" stroke="${cc}" stroke-width="${r1(w * 0.004)}"/>` +
    `<rect x="${r1(cx + cw2 * 0.42)}" y="${r1(-ch * 1.35)}" width="${r1(cw2 * 0.16)}" height="${r1(ch * 0.4)}" fill="${C.red}"/><rect x="${r1(cx + cw2 * 0.3)}" y="${r1(-ch * 1.22)}" width="${r1(cw2 * 0.4)}" height="${r1(ch * 0.14)}" fill="${C.red}"/>`;
  else out += `<rect x="${r1(cx)}" y="${r1(-ch)}" width="${r1(cw2)}" height="${r1(ch)}" rx="${r1(w * 0.006)}" fill="${cc}" stroke="${shade(cc)}" stroke-width="${r1(w * 0.003)}"/>` +
    `<rect x="${r1(cx - w * 0.008)}" y="${r1(-ch - w * 0.012)}" width="${r1(cw2 + w * 0.016)}" height="${r1(w * 0.016)}" fill="${shade(cc, 0.8)}"/>` +
    `<path d="M${r1(cx + w * 0.01)} ${r1(-ch - w * 0.012)} L${r1(cx + w * 0.01)} ${r1(-ch * 2)} M${r1(cx + cw2 - w * 0.01)} ${r1(-ch - w * 0.012)} L${r1(cx + cw2 - w * 0.01)} ${r1(-ch * 2)}" stroke="${shade(cc, 0.8)}" stroke-width="${r1(w * 0.006)}"/>` +
    `<rect x="${r1(cx - w * 0.01)}" y="${r1(-ch * 2.1)}" width="${r1(cw2 + w * 0.02)}" height="${r1(ch * 0.18)}" rx="${r1(w * 0.006)}" fill="${shade(cc, 0.8)}"/>`;
  if (kind === "bank" && p.vault !== false) out += at(cx + cw2 + w * 0.09, 0, drawSaancha("vault", { w: w * 0.08, door: 1, fill: cap ? stock / Math.max(1e-9, num(p.vaultFull, cap)) : 0 }));
  // the stock on the counter: a small pile that shrinks, and its number
  const pile = Math.min(12, Math.ceil(stock));
  for (let k = 0; k < pile; k++) out += `<rect x="${r1(cx + cw2 * 0.12 + (k % 4) * cw2 * 0.2)}" y="${r1(-ch - w * 0.012 - (Math.floor(k / 4) + 1) * w * 0.016)}" width="${r1(cw2 * 0.17)}" height="${r1(w * 0.014)}" rx="${r1(w * 0.003)}" fill="#f2c14e" stroke="#c99a2e" stroke-width="${r1(w * 0.0015)}"/>`;
  if (p.label) out += plate(p.label, cx + cw2 / 2, -ch * (kind === "theatre" ? 1.5 : 2.1) - fs * 1.2, fs);
  if (p.showStock !== false) out += pill(`${p.stockLabel ? p.stockLabel + " " : ""}${money(Math.ceil(stock - 1e-9), p.unit ?? "", 0)}`, cx + cw2 / 2, -ch * 0.5, fs, { fill: "#ffffff", color: stock > 0 ? INK : C.red });
  // the bar that drops when the stock runs out
  if (out0 && p.cut !== false) {
    const k = easeIO(clamp01(sinceEnd / 0.6)), by = lerp(-ch * 2.4, -ch * 0.9, k);
    out += `<rect x="${r1(cx - w * 0.07)}" y="${r1(by)}" width="${r1(w * 0.06)}" height="${r1(w * 0.014)}" fill="${C.red}" stroke="#ffffff" stroke-width="${r1(w * 0.002)}"/>` +
      `<rect x="${r1(cx - w * 0.075)}" y="${r1(by - w * 0.01)}" width="${r1(w * 0.01)}" height="${r1(-by + w * 0.01)}" fill="#4a5568"/>`;
    if (p.cutLabel) out += pill(p.cutLabel, cx - w * 0.04, by - fs * 1.1, fs, { fill: C.red, color: "#ffffff" });
  }
  // the people: served ones walk past the counter, the line advances, after the cut the rest turn away
  const away = p.turnAway === "wait" ? "wait" : "leave", trucks = p.who === "trucks";
  order.forEach((idx, pos) => {
    const slot = pos - q, served = pos < q;
    let x = cx - gap * 0.9 - slot * gap, y = 0, op = 0;
    if (served) { const k = clamp01(-slot); x = cx - gap * 0.9 + k * (cw2 + gap * 0.9 + w * 0.12); op = 1 - clamp01(-slot * 1.2 - 0.1); if (op <= 0.02) return; }
    if (!served && out0 && p.cut !== false) {
      const k = easeIO(clamp01((sinceEnd - 0.6 - pos * 0.05) / 1.2));
      if (away === "leave") { x -= k * w * 0.3; op = 1 - k * 0.8; }
      else { const bx = -w * 0.46 + (pos - Math.ceil(q)) * gap * 0.6; x = lerp(x, bx, k); y = lerp(0, -w * 0.2, k) * 0; }
    }
    const u = urgent.has(idx + 1), dst = served ? "behind" : "out";
    const svg = trucks ? at(x, y, `<g opacity="${r1((op || 1) * 100) / 100}"><rect x="${r1(-ps * 0.35)}" y="${r1(-ps * 0.42)}" width="${r1(ps * 0.48)}" height="${r1(ps * 0.32)}" fill="#c8a06a" stroke="#8a6d3b" stroke-width="${r1(ps * 0.02)}"/>` +
      `<rect x="${r1(ps * 0.13)}" y="${r1(-ps * 0.32)}" width="${r1(ps * 0.22)}" height="${r1(ps * 0.22)}" rx="${r1(ps * 0.03)}" fill="${C.blue}"/><circle cx="${r1(-ps * 0.2)}" cy="${r1(-ps * 0.07)}" r="${r1(ps * 0.07)}" fill="#2d3748"/><circle cx="${r1(ps * 0.22)}" cy="${r1(-ps * 0.07)}" r="${r1(ps * 0.07)}" fill="#2d3748"/></g>`)
      : person(x, y, ps, idx, op ? r1(op * 100) / 100 : 0, u ? C.red : undefined);
    if (dst === "behind") behind += svg; else out += svg;
    if (u && !served) out += `<circle cx="${r1(x)}" cy="${r1(-ps * 1.12)}" r="${r1(ps * 0.08)}" fill="${C.red}"/>`;
  });
  if (p.waiting != null && p.waiting !== "" || p.waitLabel) {
    const wn = Math.round(num(p.waiting, 0) + (out0 && away === "wait" ? Math.max(0, n - q) * clamp01((sinceEnd - 0.6) / 1.2) : 0));
    out += pill(`${p.waitLabel ? p.waitLabel + " " : ""}${wn}`, -w * 0.4, -w * 0.22, fs, { fill: "#2d3748", color: "#ffffff" });
  }
  return out.replace("<!--behind-->", behind);
}

// ---------------------------------------------------------------- contagion between institutions
// Banks (or domino tiles, or named discs) in a row or a ring, joined by lending links along which money keeps moving.
// fail gives the order of the falls; upto = n on a step makes the n-th fall over glide seconds (a bank cracks and tilts,
// a tile tips onto the next); every link touching a fallen one freezes (grey, dashed, no money). A stopped one (a
// firewall, a thick capital buffer) shakes and stands; rescued ones get a lifeline from the rescuer above.
function contagion(p) {
  const w = num(p.w, 1500), fs = w * 0.026, s = since(p), g = Math.max(0.2, num(p.glide, 1.2)), t = tnum(p._t);
  const names = parts(p.names), n = clampInt(num(p.n, names.filter(Boolean).length || 5), 2, 8), layout = p.layout === "ring" ? "ring" : "row";
  const style = ["domino", "disc"].includes(p.style) ? p.style : "bank", sizes = String(p.sizes ?? "").split(/[,;\s]+/).filter(Boolean).map(Number);
  const failOrder = String(p.fail ?? "").split(/[,;\s]+/).filter(Boolean).map((x) => parseInt(x, 10) - 1).filter((i) => i >= 0 && i < n);
  const order = failOrder.length ? failOrder : [...Array(n).keys()], stop = idxSet(p.stop), rescued = idxSet(p.rescued);
  const upto = clampInt(num(p.upto, 0), 0, order.length), e = easeIO(prog(s, g));
  const fallen = new Map();                                  // node -> fall progress 0..1
  order.slice(0, upto).forEach((i, k) => { if (!stop.has(i + 1)) fallen.set(i, k === upto - 1 ? e : 1); });
  const hitStop = upto > 0 && stop.has(order[upto - 1] + 1) ? order[upto - 1] : -1;
  const size = (i) => Math.sqrt(Math.max(0.5, Math.min(3, sizes[i] || 1)));
  const slot = layout === "row" ? (w * 0.84) / Math.max(1, n - 1) : (w * 0.6) / n;
  const base = Math.min(slot * (style === "domino" ? 0.5 : 0.62), w * 0.12), top = rescued.size ? -w * 0.12 : 0;
  const pos = [...Array(n).keys()].map((i) => layout === "row" ? [n === 1 ? 0 : -w * 0.42 + i * slot, w * 0.06]
    : [Math.cos(-Math.PI / 2 + (2 * Math.PI * i) / n) * w * 0.34, Math.sin(-Math.PI / 2 + (2 * Math.PI * i) / n) * w * 0.2 + w * 0.06]);
  let links = list(p.links).map((l) => l.split(">").map((x) => parseInt(x, 10) - 1)).filter(([a, b]) => a >= 0 && b >= 0 && a < n && b < n && a !== b);
  if (!links.length) links = [...Array(layout === "ring" ? n : n - 1).keys()].map((i) => [i, (i + 1) % n]);
  let out = "", lab = "";
  links.forEach(([a, b], k) => {
    const frozen = fallen.has(a) || fallen.has(b), [ax, ay] = pos[a], [bx, by] = pos[b], dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy) || 1;
    const ux = dx / L, uy = dy / L, ga = base * 0.55 * size(a), gb = base * 0.55 * size(b);
    const A = [ax + ux * ga, ay - base * 0.35 + uy * ga], B = [bx - ux * gb, by - base * 0.35 - uy * gb], mid = [(A[0] + B[0]) / 2 - uy * L * 0.12, (A[1] + B[1]) / 2 + ux * L * 0.12 - (layout === "row" ? L * 0.12 : 0)];
    out += `<path d="${qpath(A, mid, B)}" fill="none" stroke="${frozen ? C.dim : C.money}" stroke-width="${r1(w * 0.005)}" stroke-linecap="round"${frozen ? ` stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.008)}"` : ""}/>`;
    if (!frozen) {
      out += tri(...qpt(A, mid, B, 1), qang(A, mid, B, 0.98), w * 0.018, C.money);
      const u = Number.isFinite(t) ? ((t * 0.4 + k * 0.37) % 1) : 0.5;
      out += at(...qpt(A, mid, B, 0.1 + u * 0.8), token("coin", w * 0.009));
    } else out += at(...qpt(A, mid, B, 0.5), `<path d="M${r1(-w * 0.008)} ${r1(-w * 0.008)} L${r1(w * 0.008)} ${r1(w * 0.008)} M${r1(w * 0.008)} ${r1(-w * 0.008)} L${r1(-w * 0.008)} ${r1(w * 0.008)}" stroke="${C.red}" stroke-width="${r1(w * 0.004)}" stroke-linecap="round"/>`);
  });
  if (rescued.size) {
    const rx = 0, ry = top - w * 0.06;
    out += at(rx, ry, place("centralBank", w * 0.1)) + (p.rescuer ? plate(p.rescuer, rx, ry - w * 0.085, fs) : "");
    rescued.forEach((ri) => { const i = ri - 1; if (i < 0 || i >= n) return; const [x, y] = pos[i], yy = y - base * 0.95 * size(i);
      out += `<path d="M${r1(rx)} ${r1(ry + w * 0.05)} Q${r1((rx + x) / 2)} ${r1(ry + w * 0.12)} ${r1(x)} ${r1(yy)}" fill="none" stroke="#a0703d" stroke-width="${r1(w * 0.005)}" stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.006)}"/>` +
        `<circle cx="${r1(x)}" cy="${r1(yy)}" r="${r1(w * 0.014)}" fill="none" stroke="${C.red}" stroke-width="${r1(w * 0.007)}"/>`; });
  }
  for (let i = 0; i < n; i++) {
    const [x, y] = pos[i], sz = base * size(i), f = fallen.get(i) ?? 0, saved = rescued.has(i + 1);
    const shake = i === hitStop && Number.isFinite(s) ? Math.sin(s * 28) * Math.exp(-s * 2.5) * w * 0.006 : 0;
    let body;
    if (style === "domino") {
      const tw2 = sz * 0.34, th = sz * 1.15, col = f > 0 ? "#c0392b" : "#2d3748";
      body = `<g transform="translate(${r1(x + shake)},${r1(y)}) rotate(${r1(f * 72)} ${r1(tw2 / 2)} 0)"><rect x="${r1(-tw2 / 2)}" y="${r1(-th)}" width="${r1(tw2)}" height="${r1(th)}" rx="${r1(tw2 * 0.12)}" fill="${col}"/>` +
        `<circle cy="${r1(-th * 0.72)}" r="${r1(tw2 * 0.13)}" fill="#ffffff"/><circle cy="${r1(-th * 0.3)}" r="${r1(tw2 * 0.13)}" fill="#ffffff"/><path d="M${r1(-tw2 * 0.4)} ${r1(-th * 0.5)} L${r1(tw2 * 0.4)} ${r1(-th * 0.5)}" stroke="#ffffff" stroke-width="${r1(tw2 * 0.05)}"/></g>`;
    } else if (style === "disc") {
      const r = sz * 0.42, col = f > 0 ? "#c0392b" : DIAG_ALT[i % DIAG_ALT.length];
      body = `<g transform="translate(${r1(x + shake)},${r1(y - r)})" opacity="${r1((1 - f * 0.45) * 100) / 100}"><circle r="${r1(r)}" fill="${col}" stroke="#ffffff" stroke-width="${r1(w * 0.003)}"/>` +
        (names[i] ? T(names[i], 0, 0, Math.max(fs, Math.min(r * 0.55, fs * 1.2)), "#ffffff", 800) : "") + `</g>`;
    } else {
      body = `<g transform="translate(${r1(x + shake)},${r1(y)}) rotate(${r1(-f * 12)} 0 0)" opacity="${r1((1 - f * 0.4) * 100) / 100}"><g transform="translate(0,${r1(-sz * 0.45)})">${place("bank", sz)}</g>` +
        (f > 0 ? `<path d="M${r1(-sz * 0.1)} ${r1(-sz * 0.85)} L${r1(sz * 0.05)} ${r1(-sz * 0.6)} L${r1(-sz * 0.08)} ${r1(-sz * 0.42)} L${r1(sz * 0.08)} ${r1(-sz * 0.18)} L${r1(-sz * 0.02)} 0" fill="none" stroke="#5a1f1f" stroke-width="${r1(sz * 0.035)}" stroke-linejoin="round" opacity="${r1(f * 100) / 100}"/>` +
          crossMark(sz * 0.32, -sz * 0.95, sz * 0.12 * f) : "") + `</g>`;
    }
    out += body;
    if (stop.has(i + 1)) out += `<rect x="${r1(x - sz * 0.62)}" y="${r1(y - sz * 1.05)}" width="${r1(w * 0.012)}" height="${r1(sz * 1.05)}" rx="${r1(w * 0.004)}" fill="#8a6d3b"/>` +
      `<path d="M${r1(x - sz * 0.62 + w * 0.006)} ${r1(y - sz * 1.15)} l${r1(w * 0.016)} ${r1(w * 0.008)} l0 ${r1(w * 0.02)} q${r1(-w * 0.016)} ${r1(w * 0.016)} ${r1(-w * 0.016)} ${r1(w * 0.016)} q${r1(-w * 0.016)} 0 ${r1(-w * 0.016)} ${r1(-w * 0.016)} l0 ${r1(-w * 0.02)} Z" fill="${C.money}"/>` +
      (p.stopLabel ? T(p.stopLabel, x - sz * 0.62, y - sz * 1.15 - fs * 1.4, fs * 0.95, shade(C.money, 0.7), 800) : "");
    if (names[i] && style !== "disc") lab += T(names[i], x, y + fs * 0.95, fs, f > 0 ? C.red : saved ? shade(C.money, 0.7) : INK, 800);
  }
  out += `<path d="M${r1(-w * 0.49)} ${r1(w * 0.06)} L${r1(w * 0.49)} ${r1(w * 0.06)}" stroke="#c9c3b6" stroke-width="${r1(w * 0.003)}" opacity="${layout === "row" ? 1 : 0}"/>`;
  if (p.title) lab += T(p.title, 0, (rescued.size ? top - w * 0.2 : -w * 0.2) - fs, fs * 1.1, INK, 800);
  return out + lab;
}
const DIAG_ALT = ["#2459a6", "#2a9d8f", "#7b61ff", "#d9822b", "#2fa35b", "#c2447a", "#4a5568", "#9b6b43"];

// ---------------------------------------------------------------- securitisation chain
// Loans travel from the lender into a pool owned by an SPV, the pool is cut into tranches (CDO papers) that go to the
// noteholders, and cash comes back along dotted arrows (stage 0..4, each stage playing over glide seconds after its
// step). default turns that share of the loans red: losses fill the tranches from the bottom (equity first) and the
// holders of a hit tranche turn red; a RISK disc travels with the loans.
function securitisation(p) {
  const w = num(p.w, 1600), h = w * 0.5, fs = w * 0.024, s = since(p), g = Math.max(0.3, num(p.glide, 1.6)), e = easeIO(prog(s, g)), t = tnum(p._t);
  const stage = clampInt(num(p.stage, 4), 0, 4), m = clampInt(num(p.loans, 16), 4, 24), def = clamp01(num(p.default, 0));
  const tr = items(p.tranches || "Senior:70;Mezzanine:20;Equity:10", 4), holders = parts(p.holders).filter(Boolean).slice(0, 3);
  const nH = Math.max(1, holders.length || 3), ox = -w * 0.42, poolX = -w * 0.17, trX = w * 0.07, hx = w * 0.32, cashY = h * 0.44;
  const k = (st) => (stage > st ? 1 : stage === st ? e : 0);
  let out = "";
  const arrow = (x1, x2, y, on, col) => `<path d="M${r1(x1)} ${r1(y)} L${r1(x2 - w * 0.01)} ${r1(y)}" stroke="${on ? col : C.dim}" stroke-width="${r1(w * 0.004)}"/>` + tri(x2, y, 0, w * 0.014, on ? col : C.dim);
  // places
  out += at(ox, 0, place("bank", w * 0.12)) + (p.originator ? plate(p.originator, ox, w * 0.085, fs) : "");
  const pw = w * 0.17, ph = w * 0.13, TH = h * 0.5, tw2 = w * 0.12;
  out += arrow(ox + w * 0.07, poolX - pw / 2 - w * 0.006, 0, stage >= 1, "#4a5568") + arrow(poolX + pw / 2 + w * 0.006, trX - tw2 / 2 - w * 0.006, 0, stage >= 2, "#4a5568");
  out += `<rect x="${r1(poolX - pw / 2)}" y="${r1(-ph / 2)}" width="${r1(pw)}" height="${r1(ph)}" rx="${r1(w * 0.012)}" fill="#f4f1fb" stroke="#7b61ff" stroke-width="${r1(w * 0.004)}" stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.006)}"/>`;
  if (p.spv) out += plate(p.spv, poolX, -ph / 2 - fs * 1.1, fs, "#7b61ff");
  // loans: at the lender (stage 0), flying into the pool (stage 1), then sitting in it
  const cols = 6, rows = Math.ceil(m / cols), cw = pw / (cols + 0.5), lw = cw * 0.72, lh = lw * 1.25, red = Math.round(m * def), gy = (ph - rows * lh * 1.12) / 2;
  for (let i = 0; i < m; i++) {
    const c = i % cols, r = Math.floor(i / cols), px = poolX - pw / 2 + cw * (c + 0.75), py = -ph / 2 + gy + r * lh * 1.12 + lh * 0.56;
    const sx = ox + w * 0.075 + (i % 3) * lw * 0.55, sy = -h * 0.06 - Math.floor(i / 3) * lw * 0.25;
    const ki = clamp01(k(1) * 1.6 - (i / m) * 0.6), x = lerp(sx, px, ki), y = lerp(sy, py, ki) - Math.sin(ki * Math.PI) * h * 0.12;
    const bad = i >= m - red && stage >= 1;
    out += `<rect x="${r1(x - lw / 2)}" y="${r1(y - lh / 2)}" width="${r1(lw)}" height="${r1(lh)}" rx="${r1(lw * 0.1)}" fill="${bad ? "#fdd" : "#ffffff"}" stroke="${bad ? C.red : "#8a94a3"}" stroke-width="${r1(w * 0.0018)}"/>` +
      `<path d="M${r1(x - lw * 0.28)} ${r1(y - lh * 0.15)} L${r1(x + lw * 0.28)} ${r1(y - lh * 0.15)} M${r1(x - lw * 0.28)} ${r1(y + lh * 0.12)} L${r1(x + lw * 0.2)} ${r1(y + lh * 0.12)}" stroke="${bad ? C.red : "#b8c0cc"}" stroke-width="${r1(w * 0.0018)}"/>`;
  }
  // tranches: the pool cut into a stack; losses fill from the bottom (equity first)
  const total = tr.reduce((a, x) => a + (x.value || 0), 0) || 1, kt = k(2), trc = ["#2459a6", "#2a9d8f", "#d9822b", "#c2447a"];
  let yb = TH / 2, lossLeft = def * total;
  const hurt = [];
  tr.slice().reverse().forEach((x, jr) => {
    const j = tr.length - 1 - jr, hh = ((x.value || 0) / total) * TH * kt, lossH = (Math.min(x.value || 0, lossLeft) / total) * TH * kt;
    lossLeft = Math.max(0, lossLeft - (x.value || 0)); hurt[j] = lossH > 0.5;
    if (hh > 0.5) out += `<rect x="${r1(trX - tw2 / 2)}" y="${r1(yb - hh)}" width="${r1(tw2)}" height="${r1(hh)}" fill="${trc[j % trc.length]}" stroke="#ffffff" stroke-width="${r1(w * 0.003)}"/>` +
      (lossH > 0.5 ? `<rect x="${r1(trX - tw2 / 2)}" y="${r1(yb - lossH)}" width="${r1(tw2)}" height="${r1(lossH)}" fill="${C.red}" opacity="0.8"/>` : "") +
      (kt >= 1 && x.label ? (hh >= fs * 1.35 ? T(x.label, trX, yb - hh / 2, fs, "#ffffff", 800) : T(x.label, trX - tw2 / 2 - w * 0.012, yb - hh / 2, fs, INK, 800, "end")) : "");
    yb -= hh;
  });
  // the noteholders: papers of their tranche fly to them (stage 3); cash returns along the bottom (stage 4)
  if (stage >= 4) {
    const kk = Number.isFinite(t) ? (t * 0.3) % 1 : 0.5;
    out += `<path d="M${r1(hx)} ${r1(cashY)} L${r1(ox)} ${r1(cashY)} L${r1(ox)} ${r1(w * 0.085 + fs * 0.9)}" fill="none" stroke="${C.money}" stroke-width="${r1(w * 0.004)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.008)}" opacity="${r1(e * 100) / 100}"/>` +
      tri(ox, w * 0.085 + fs * 0.9, -Math.PI / 2, w * 0.014, C.money) + at(lerp(hx, ox, kk), cashY, token("coin", w * 0.009)) + at(lerp(hx, ox, (kk + 0.5) % 1), cashY, token("coin", w * 0.009)) +
      (p.cashLabel ? pill(p.cashLabel, (hx + ox) / 2 + w * 0.12, cashY, fs, { stroke: C.money, color: shade(C.money, 0.6) }) : "");
  }
  for (let i = 0; i < nH; i++) {
    const y = nH === 1 ? 0 : -h * 0.3 + (i * h * 0.6) / (nH - 1), j = Math.min(tr.length - 1, Math.round((i * (tr.length - 1)) / Math.max(1, nH - 1)));
    const bad = def > 0 && hurt[j] && stage >= 3, kp = k(3), py = lerp(0, y - w * 0.01, kp);
    if (stage >= 4 && i === nH - 1) out += `<path d="M${r1(hx)} ${r1(y + w * 0.04)} L${r1(hx)} ${r1(cashY)}" stroke="${C.money}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.006)} ${r1(w * 0.008)}" opacity="${r1(e * 100) / 100}"/>`;
    out += at(hx, y, place(["office", "tower", "bank"][i % 3], w * 0.07)) + (holders[i] ? T(holders[i], hx + w * 0.045, y, fs, bad ? C.red : INK, 800, "start") : "");
    if (kp > 0) out += at(lerp(trX + tw2 / 2 + w * 0.02, hx - w * 0.06, kp), py, drawSaancha("paper", { kind: "bond", title: "", w: w * 0.03, lines: 2 })) +
      (bad && kp >= 1 ? crossMark(hx - w * 0.06 + w * 0.016, py - w * 0.022, w * 0.009) : "");
  }
  if (p.risk) {
    const rp = stage === 0 ? [ox, -w * 0.11] : stage < 3 ? [lerp(ox, poolX, k(1)), -ph / 2 - fs * 2.7] : [lerp(poolX, hx, k(3)), -h * 0.44];
    out += pill(p.riskLabel ?? "RISK", rp[0], rp[1], fs, { fill: C.red, color: "#ffffff" });
  }
  return out;
}

// ---------------------------------------------------------------- layer stack (Basel III capital) and liquidity ladder
// mode "stack": layers stacked like floors on a % axis, bottom first ("Tier 2:2;AT1:1.5;CET1:4.5"), each as tall as
// its value, with cumulative marks; upto builds them one per step (the newest rises over glide), and one buffer layer can
// be filled 0..1 (a counter-cyclical buffer filling in a boom). mode "ladder": assets on a ladder from the most liquid
// (top) to the least (bottom), each rung with its return tag; a cut line parts the liquid ones from the rest.
function layers(p) {
  const w = num(p.w, 900), fs = w * 0.042, s = since(p), g = Math.max(0.2, num(p.glide, 1.2)), e = easeIO(prog(s, g));
  const L = items(p.layers, 8), unit = p.unit ?? "%", glow = num(p.at, 0);
  const upto = p.upto ? clampInt(num(p.upto, L.length), 0, L.length) : L.length;
  const cols = ["#2459a6", "#3a7bd5", "#2a9d8f", "#2fa35b", "#8cc152", "#f2c14e", "#f08a3c", "#c2447a"];
  let out = "";
  if ((p.mode || "stack") === "ladder") {
    const n = Math.max(1, L.length), H = w * 0.9, rh = H / n, x0 = -w * 0.12, rw = w * 0.36, cut = num(p.cut, 0);
    out += `<rect x="${r1(x0 - rw / 2 - w * 0.02)}" y="${r1(-H - w * 0.04)}" width="${r1(w * 0.025)}" height="${r1(H + w * 0.04)}" rx="${r1(w * 0.008)}" fill="#a0703d"/>` +
      `<rect x="${r1(x0 + rw / 2 - w * 0.005)}" y="${r1(-H - w * 0.04)}" width="${r1(w * 0.025)}" height="${r1(H + w * 0.04)}" rx="${r1(w * 0.008)}" fill="#a0703d"/>`;
    L.forEach((it, i) => {
      if (i >= upto) return;
      const y = -H + (i + 0.5) * rh, k = i === upto - 1 && p.upto ? e : 1, lit = glow === i + 1;
      out += `<rect x="${r1(x0 - rw / 2)}" y="${r1(y - rh * 0.05 + fs * 0.74)}" width="${r1(rw)}" height="${r1(w * 0.02)}" fill="#8a5d2e"/>` +
        `<g opacity="${r1(k * 100) / 100}">` + pill(it.label, x0, y - rh * 0.05, fs, { fill: lit ? "#fff3c4" : "#ffffff", stroke: lit ? "#f29f05" : "#9aa5b1", minW: rw * 0.9, sw: lit ? w * 0.006 : w * 0.002 }) +
        (it.raw ? pill(it.value != null ? `${fmt(it.value)}${unit}` : it.raw, x0 + rw / 2 + w * 0.06 + fs * 0.4 * Math.min(4, i), y - rh * 0.05, fs * (1 + Math.min(0.4, i * 0.08)), { anchor: "start", fill: lerpColor(i, n), color: "#ffffff" }) : "") + `</g>`;
      if (cut === i + 1 && cut < n) {
        const cy = -H + (i + 1) * rh;
        out += `<path d="M${r1(-w * 0.48)} ${r1(cy)} L${r1(w * 0.48)} ${r1(cy)}" stroke="${C.red}" stroke-width="${r1(w * 0.006)}" stroke-dasharray="${r1(w * 0.02)} ${r1(w * 0.012)}"/>` +
          (p.cutLabel ? T(p.cutLabel, -w * 0.48, cy - fs * 0.75, fs, C.red, 800, "start") : "") + (p.cutBelow ? T(p.cutBelow, -w * 0.48, cy + fs * 0.85, fs, C.red, 800, "start") : "");
      }
    });
    if (p.title) out += T(p.title, 0, -H - w * 0.1, fs * 1.1, INK, 800);
    return out;
  }
  const total = L.reduce((a, x) => a + Math.max(0, x.value || 0), 0) || 1, H = w * 0.85, scale = H / Math.max(total, num(p.max, 0)), bw = w * 0.36, bx = -w * 0.06;
  const fillAt = num(p.fillLayer, 0), fill = clamp01(num(p.fill, 1));
  out += `<path d="M${r1(bx - bw / 2 - w * 0.04)} ${r1(-H - w * 0.03)} L${r1(bx - bw / 2 - w * 0.04)} 0 L${r1(bx + bw / 2 + w * 0.06)} 0" fill="none" stroke="${INK}" stroke-width="${r1(w * 0.005)}"/>`;
  let y = 0, acc = 0;
  L.forEach((it, i) => {
    if (i >= upto) return;
    const v = Math.max(0, it.value || 0), k = i === upto - 1 && p.upto ? e : 1, hh = v * scale * k, c = cols[i % cols.length], lit = glow === i + 1;
    const filled = fillAt === i + 1 ? fill : 1;
    out += `<rect x="${r1(bx - bw / 2)}" y="${r1(y - hh)}" width="${r1(bw)}" height="${r1(hh)}" fill="${c}" opacity="${filled < 1 ? 0.25 : 1}" stroke="#ffffff" stroke-width="${r1(w * 0.004)}"/>` +
      (filled < 1 ? `<rect x="${r1(bx - bw / 2)}" y="${r1(y - hh * filled)}" width="${r1(bw)}" height="${r1(hh * filled)}" fill="${c}"/>` +
        `<rect x="${r1(bx - bw / 2)}" y="${r1(y - hh)}" width="${r1(bw)}" height="${r1(hh)}" fill="none" stroke="${c}" stroke-width="${r1(w * 0.004)}" stroke-dasharray="${r1(w * 0.012)} ${r1(w * 0.008)}"/>` : "") +
      (lit ? `<rect x="${r1(bx - bw / 2 - w * 0.008)}" y="${r1(y - hh - w * 0.008)}" width="${r1(bw + w * 0.016)}" height="${r1(hh + w * 0.016)}" fill="none" stroke="#f29f05" stroke-width="${r1(w * 0.007)}"/>` : "");
    const txt = [it.label, it.value != null ? `${fmt(v)}${unit}` : ""].filter(Boolean).join(" ");
    if (k >= 1) out += hh >= fs * 1.3 && filled >= 1 ? T(txt, bx, y - hh / 2, fs, "#ffffff", 800) : T(txt, bx + bw / 2 + w * 0.03, y - hh / 2, fs, INK, 800, "start");
    y -= hh; acc += v * k;
  });
  list(p.marks).forEach((mk) => { const [v, nm] = mk.split(":"); if (!isNum(v) || +v > acc + 1e-9) return; const my = -(+v) * scale;
    out += `<path d="M${r1(bx - bw / 2 - w * 0.04)} ${r1(my)} L${r1(bx + bw / 2)} ${r1(my)}" stroke="${INK}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.007)}"/>` +
      T(nm ? nm.trim() : `${fmt(+v)}${unit}`, bx - bw / 2 - w * 0.06, my, fs, INK, 800, "end"); });
  if (p.title) out += T(p.title, bx, -H - w * 0.09, fs * 1.1, INK, 800);
  return out;
}
const lerpColor = (i, n) => ["#2fa35b", "#8cc152", "#f2c14e", "#f08a3c", "#e5484d", "#a3273a"][Math.round((n <= 1 ? 0 : i / (n - 1)) * 5)];

// ---------------------------------------------------------------- price path and interest-rate corridor (drawn by graph)
// A price over time (given points, or a seeded random walk with a drift and an optional bubble and burst) drawn by the
// engine's graph saancha: the path draws itself up to "now" at the voice's speed (drawIn seconds), the region above a
// reference price shades for one side and below for the other (futures, short selling), a second line (fundamental
// value) shades the bubble gap, events mark dates, a dot rides the head with its live value.
function walkPoints(p) {
  const pts = String(p.points ?? "").trim().split(/\s+/).map((q) => q.split(",").map(Number)).filter((q) => q.length === 2 && q.every(Number.isFinite));
  if (pts.length >= 2) return pts;
  const n = clampInt(num(p.steps, 40), 4, 200), r = rnd(clampInt(num(p.seed, 7), 1, 99999)), drift = num(p.drift, 0), vol = num(p.vol, 1), y0 = num(p.start, 50);
  const bub = String(p.bubble ?? "").split(/[,;\s]+/).filter(Boolean).map(Number), burst = num(p.burst, NaN);
  const out = [[0, y0]];
  let y = y0;
  for (let i = 1; i <= n; i++) {
    y += drift + (r() - 0.5) * 2 * vol;
    if (bub.length === 2 && i > bub[0] && i <= bub[1]) y += num(p.boom, 2);
    if (Number.isFinite(burst) && i === Math.round(burst)) y = out[0][1] + (y - out[0][1]) * 0.25;
    out.push([i, Math.round(y * 100) / 100]);
  }
  return out;
}
function cutAt(pts, x) { const out = []; for (let i = 0; i < pts.length; i++) { if (pts[i][0] <= x) out.push(pts[i]); else { const a = pts[i - 1]; if (a) { const f = (x - a[0]) / (pts[i][0] - a[0] || 1); out.push([x, a[1] + (pts[i][1] - a[1]) * f]); } break; } } return out; }
function bandAreas(pts, ref, label, col, above) {             // one polygon between a path and a level, on one side of it
  if (pts.length < 2) return [];
  const q = [];
  for (let i = 0; i < pts.length; i++) {
    const [x, y] = pts[i];
    if (i > 0) { const [px, py] = pts[i - 1]; if ((py - ref) * (y - ref) < 0) { const f = (ref - py) / (y - py); q.push([px + (x - px) * f, ref]); } }
    q.push([x, above ? Math.max(y, ref) : Math.min(y, ref)]);
  }
  if (!q.some(([, y]) => Math.abs(y - ref) > 1e-9)) return [];
  const poly = [...q, [q[q.length - 1][0], ref], [q[0][0], ref]].map((v) => `${r1(v[0] * 100) / 100},${r1(v[1] * 100) / 100}`).join(" ");
  return [`${label}:${poly}@${col}`];
}
function pricePath(p) {
  const w = num(p.w, 1400), pts = walkPoints(p), x0 = pts[0][0], x1 = pts[pts.length - 1][0], s = since(p), t = tnum(p._t);
  const drawIn = Math.max(0, num(p.drawIn, 0)), clock = p.fromStep ? s : t, k = drawIn && Number.isFinite(clock) ? clamp01(clock / drawIn) : 1;
  const xNow = isNum(p.upto) ? Math.min(x1, +p.upto) : x1, xEnd = lerp(x0, xNow, k), path = cutAt(pts, xEnd);
  const base = String(p.base ?? "").trim() ? walkPoints({ points: p.base }) : null, ref = isNum(p.ref) ? +p.ref : null;
  const ys = [...pts.map((q) => q[1]), ...(base || []).map((q) => q[1]), ...(ref != null ? [ref] : [])], lo = Math.min(...ys), hi = Math.max(...ys), pad = (hi - lo || 1) * 0.15;
  const ymin = isNum(p.ymin) ? +p.ymin : Math.floor(lo - pad), ymax = isNum(p.ymax) ? +p.ymax : Math.ceil(hi + pad);
  const lines = [`${p.name ?? ""}:${path.map((q) => `${q[0]},${q[1]}`).join(" ")}`], areas = [], colors = ["1:#2459a6"];
  if (base) { lines.push(`${p.baseName ?? ""}:${cutAt(base, xEnd).map((q) => `${q[0]},${q[1]}`).join(" ")}`); colors.push("2:#8a94a3"); }
  if (ref != null && p.shade !== false) { areas.push(...bandAreas(path, ref, p.aboveLabel ?? "", "#2fa35b", true), ...bandAreas(path, ref, p.belowLabel ?? "", "#e5484d", false)); }
  if (base && p.gap !== false && path.length > 1) {
    const bb = cutAt(base, xEnd), gapPts = path.map((q) => { const b = cutAt(base, q[0]); return [q, b[b.length - 1]]; }).filter(([q, b]) => b && q[1] > b[1]);
    if (gapPts.length >= 2) areas.push(`${p.gapLabel ?? ""}:${[...gapPts.map(([q]) => q), ...gapPts.reverse().map(([, b]) => b)].map((q) => `${r1(q[0] * 100) / 100},${r1(q[1] * 100) / 100}`).join(" ")}@#f29f05`);
    void bb;
  }
  const head = path[path.length - 1], dot = p.dot === false ? "" : `${head[0]},${head[1]}:${String(p.dotLabel ?? "").replace("{y}", fmt(head[1])).replace("{x}", fmt(head[0]))}`;
  const ev = list(p.events).filter((e2) => { const v = parseFloat(e2); return Number.isFinite(v) && v <= xEnd + 1e-9; }).join(";");
  return drawSaancha("graph", { w, xmin: x0, xmax: x1 + (x1 - x0) * 0.04, ymin, ymax, lines: lines.join(";"), colors: colors.join(";"), smooth: p.smooth === true,
    areas: areas.slice(0, 6).join(";"), hlines: ref != null ? `${ref}:${p.refLabel ?? ""}` : "", vlines: ev, dots: dot, drop: false, xLabel: p.xLabel ?? "", yLabel: p.yLabel ?? "",
    xTicks: p.xTicks ?? "", yTicks: p.yTicks ?? "", title: p.title ?? "" });
}
// The interest-rate corridor: a ceiling (the lending facility rate), the policy rate and a floor (the deposit rate) over
// time, the band between them shaded, and the overnight market rate as a dot that wanders inside (a deterministic
// wobble, or the given path) and draws its trail as the video plays. mode "floor": the ceiling fades and the rate sits on
// the floor; "broken": the given path may leave the band. omo pushes the dot back towards the policy rate.
function rateCorridor(p) {
  const w = num(p.w, 1400), t = tnum(p._t), s = since(p), cei = num(p.ceiling, 6), pol = num(p.policy, 5), flo = num(p.floor, 4), T0 = 0, T1 = num(p.span, 10);
  const mode = ["floor", "broken"].includes(p.mode) ? p.mode : "corridor", sp = Math.max(0.05, num(p.speed, 1));
  const given = String(p.path ?? "").trim().split(/[;\s]+/).map((q) => q.split(/[:,]/).map(Number)).filter((q) => q.length === 2 && q.every(Number.isFinite));
  const amp = Math.min(cei - pol, pol - flo) * clamp01(num(p.wander, 0.6));
  const at2 = (x) => {
    if (given.length >= 2) { const c = cutAt(given, x); return c.length ? c[c.length - 1][1] : given[0][1]; }
    if (mode === "floor") return flo + Math.abs(Math.sin(x * 2.1)) * (pol - flo) * 0.08;
    let y = pol + amp * (0.62 * Math.sin(x * 1.37 + 0.4) + 0.38 * Math.sin(x * 3.1 + 1.3));
    if (p.omo && Number.isFinite(s)) y = lerp(y, pol, clamp01(s / 1.5) * 0.8);
    return y;
  };
  const xEnd = Number.isFinite(t) ? Math.min(T1, T0 + t * sp) : T1, n = 60, trail = [];
  for (let i = 0; i <= n; i++) { const x = T0 + ((xEnd - T0) * i) / n; trail.push([Math.round(x * 100) / 100, Math.round(at2(x) * 1000) / 1000]); }
  const ys = [cei, flo, ...trail.map((q) => q[1])], lo = Math.min(...ys), hi = Math.max(...ys), pad = (cei - flo) * 0.35;
  const lab = parts(p.labels), fade = mode === "floor";
  const TL = T0 + (T1 - T0) * 1.38, lines = [`${lab[0] ?? ""}:${T0},${cei} ${TL},${cei}`, `${lab[1] ?? ""}:${T0},${pol} ${TL},${pol}`, `${lab[2] ?? ""}:${T0},${flo} ${TL},${flo}`, `:${trail.map((q) => `${q[0]},${q[1]}`).join(" ")}`];
  const head = trail[trail.length - 1];
  return drawSaancha("graph", { w, xmin: T0, xmax: T0 + (T1 - T0) * 1.45, ymin: Math.floor((lo - pad) * 2) / 2, ymax: Math.ceil((hi + pad) * 2) / 2, lines: lines.join(";"),
    colors: `1:${fade ? "#d5dbe1" : "#e5484d"};2:#2b2b33;3:#2459a6;4:#f29f05`, dashed: fade ? "1" : "", bold: "4", smooth: false,
    areas: `:${T0},${flo} ${TL},${flo} ${TL},${cei} ${T0},${cei}@${fade ? "#eef1f4" : "#8ecae6"}`, drop: false,
    dots: `${head[0]},${head[1]}:${String(p.dotLabel ?? "{y}%").replace("{y}", fmt(head[1], 2))}`,
    arrows: p.omo ? `${head[0] - (T1 - T0) * 0.16},${head[1] + (head[1] >= pol ? 0.6 : -0.6) * (cei - flo) * 0.5}>${head[0] - (T1 - T0) * 0.02},${head[1] + (head[1] >= pol ? 0.08 : -0.08) * (cei - flo) * 0.5}:${p.omoLabel ?? ""}` : "",
    yLabel: p.yLabel ?? "", xLabel: p.xLabel ?? "", xTicks: p.xTicks ?? "", title: p.title ?? "" });
}

// ---------------------------------------------------------------- one amount splitting into parts
// One amount (a bar of money) splits into labelled parts, each as big as its amount, and each part flies on its own step
// to its destination (upto = n sends the n-th over glide seconds): GST to the tax office, imports to the port, the rest
// to a factory. A destination may name its picture: "Cd:80:कारख़ाना@factory".
function moneySplit(p) {
  const w = num(p.w, 1500), h = w * 0.55, fs = w * 0.026, unit = p.unit ?? "", s = since(p), g = Math.max(0.2, num(p.glide, 1.4)), e = easeIO(prog(s, g));
  const P = list(p.parts).slice(0, 5).map((x) => { const [l, v, to] = x.split(":").map((z) => (z ?? "").trim()); const [dest, kind] = (to || "").split("@");
    return { l, v: Math.max(0, num(v, 0)), to: (dest || "").trim(), kind: (kind || "").trim() }; });
  if (!P.length) P.push({ l: "", v: 60, to: "", kind: "" }, { l: "", v: 40, to: "", kind: "" });
  const total = isNum(p.total) ? +p.total : P.reduce((a, x) => a + x.v, 0) || 1, split = p.split !== false, n = P.length;
  const upto = isNum(p.upto) ? clampInt(+p.upto, 0, n) : split ? n : 0, sx = -w * 0.36, bw = w * 0.11, H = h * 0.78, dx = w * 0.3;
  const cols = ["#2fa35b", "#3a7bd5", "#d9822b", "#7b61ff", "#c2447a"];
  let out = "", y = -H / 2;
  out += pill(`${p.label ? p.label + " " : ""}${money(total, unit)}`, sx, -H / 2 - fs * 1.2, fs * 1.1, { fill: INK, color: "#ffffff" });
  const ys = P.map((_, i) => (n === 1 ? 0 : -H / 2 + fs + (i * (H - fs * 2)) / (n - 1)));
  P.forEach((pt, i) => {
    const hh = (pt.v / total) * H, gap = split ? fs * 0.25 : 0, cy = y + hh / 2 + gap * i, c = cols[i % cols.length], txt = [pt.l, money(pt.v, unit)].filter(Boolean).join(" ");
    const flown = i < upto, k = i === upto - 1 && isNum(p.upto) ? e : flown ? 1 : 0, dy = ys[i];
    // the slice stays as a ghost once it has left
    out += `<rect x="${r1(sx - bw / 2)}" y="${r1(cy - hh / 2)}" width="${r1(bw)}" height="${r1(Math.max(1, hh))}" rx="${r1(Math.min(hh / 2, w * 0.006))}" fill="${split ? c : "#6cbf7f"}" opacity="${k >= 1 ? 0.25 : 1}"${k >= 1 ? ` stroke="${c}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.006)}" stroke-width="${r1(w * 0.002)}"` : ""}/>`;
    if (split && k < 1) out += k > 0 ? "" : T(txt, sx + bw / 2 + w * 0.015, cy, fs, shade(c, 0.7), 800, "start");
    // the destination
    const kx = dx + w * 0.12;
    out += at(kx, dy, place(pt.kind || "office", w * 0.08)) + (pt.to ? T(pt.to, kx + w * 0.055, dy, fs, INK, 800, "start") : "");
    if (k > 0) {
      const a = [sx + bw / 2, cy], b = [dx - w * 0.02, dy], c2 = [lerp(a[0], b[0], 0.5), lerp(a[1], b[1], 0.1) - h * 0.1], [x, yy] = qpt(a, c2, b, k);
      if (k < 1) out += `<path d="${qpath(a, c2, b)}" fill="none" stroke="${c}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.008)} ${r1(w * 0.008)}" opacity="0.6"/>`;
      out += pill(txt, x, yy, fs, { anchor: k >= 1 ? "end" : "middle", fill: c, color: "#ffffff" });
    }
    y += hh;
  });
  return out;
}

// ---------------------------------------------------------------- a two-way trade with running ledgers
// Two parties (firms, a firm and a household, two countries) and what crosses between them on the deal word: things
// (permits, goods, papers) go one way, money comes back, over glide seconds after the step (deal true). Each party keeps
// a ledger whose values can glide ("Permits:10000<20000") and whose total updates. A cap pile in the middle can shrink.
function tradeLedger(p) {
  const w = num(p.w, 1500), h = w * 0.5, fs = w * 0.026, unit = p.unit ?? "", s = since(p), g = Math.max(0.2, num(p.glide, 1.6)), e = easeIO(prog(s, g));
  const lx = -w * 0.33, rx = w * 0.33, dealt = p.deal === true, k = dealt ? e : 0, nItems = clampInt(num(p.items, 3), 0, 8), tok = ["slip", "goods", "coin", "note"].includes(p.itemKind) ? p.itemKind : "slip";
  let out = "";
  const party = (x, name, kind) => at(x, -h * 0.1, place(kind || "factory", w * 0.13)) + (name ? plate(name, x, -h * 0.1 + w * 0.09, fs) : "");
  out += party(lx, p.left, p.leftKind) + party(rx, p.right, p.rightKind);
  const yI = -h * 0.24, yM = h * 0.0;
  out += `<path d="M${r1(lx + w * 0.09)} ${r1(yI)} L${r1(rx - w * 0.1)} ${r1(yI)}" stroke="#d9822b" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.008)}"/>` + tri(rx - w * 0.09, yI, 0, w * 0.014, "#d9822b") +
    `<path d="M${r1(rx - w * 0.09)} ${r1(yM)} L${r1(lx + w * 0.1)} ${r1(yM)}" stroke="${C.money}" stroke-width="${r1(w * 0.003)}" stroke-dasharray="${r1(w * 0.01)} ${r1(w * 0.008)}"/>` + tri(lx + w * 0.09, yM, Math.PI, w * 0.014, C.money);
  for (let i = 0; i < nItems; i++) {
    const kk = clamp01(k * 1.4 - (i / Math.max(1, nItems)) * 0.4), x = lerp(lx + w * 0.11 + i * fs * 0.9, rx - w * 0.13 - (nItems - 1 - i) * fs * 0.9, kk);
    out += at(x, yI - (kk > 0 && kk < 1 ? Math.sin(kk * Math.PI) * h * 0.06 : 0) - fs * 0.6, token(tok, fs * 0.5));
  }
  const mk = clamp01(k * 1.3 - 0.1), mx = lerp(rx - w * 0.13, lx + w * 0.13, mk);
  if (p.payLabel || nItems) out += at(mx, yM + fs * 0.9, token("note", fs * 0.55));
  if (p.itemLabel) out += pill(p.itemLabel, 0, yI + fs * 1.15, fs, { stroke: "#d9822b", color: shade("#d9822b", 0.7) });
  if (p.payLabel) out += pill(p.payLabel, 0, yM + fs * 2.3, fs, { stroke: C.money, color: shade(C.money, 0.6) });
  if (isNum(p.cap)) {
    const capN = Math.max(0, num(p.cap, 0)), from = isNum(p.capFrom) ? +p.capFrom : capN, cn = Math.round(lerp(from, capN, e)), cx = 0, cyb = -h * 0.42;
    for (let i = 0; i < Math.min(30, cn); i++) out += `<rect x="${r1(cx - w * 0.03 + (i % 2) * w * 0.004)}" y="${r1(cyb - i * w * 0.006)}" width="${r1(w * 0.06)}" height="${r1(w * 0.008)}" rx="${r1(w * 0.002)}" fill="#fdf3e7" stroke="#d9822b" stroke-width="${r1(w * 0.0015)}"/>`;
    if (p.capLabel) out += T(`${p.capLabel} ${fmt(cn, 0)}`, cx + w * 0.05, cyb - Math.min(30, cn) * w * 0.003, fs, "#b0611f", 800, "start");
  }
  // the ledgers
  const ledger = (x, rows) => {
    const R = items(rows, 5); if (!R.length) return "";
    const rh = fs * 1.6, x0 = x - w * 0.15, x1 = x + w * 0.15; let y = h * 0.2, o = "", sum = 0;
    R.forEach((r) => { const v = r.value == null ? 0 : r.old != null ? lerp(r.old, r.value, e) : r.value; sum += v;
      o += T(r.label, x0, y, fs, INK, 700, "start") + T(r.value == null ? r.raw : money(v, unit), x1, y, fs, r.old != null && Number.isFinite(s) && prog(s, g) < 1 ? "#d9822b" : INK, 800, "end"); y += rh; });
    if (p.totals !== false && R.some((r) => r.value != null)) o += `<path d="M${r1(x0)} ${r1(y - rh * 0.5)} L${r1(x1)} ${r1(y - rh * 0.5)}" stroke="${INK}" stroke-width="${r1(w * 0.003)}"/>` +
      T(p.totalLabel ?? "", x0, y, fs, INK, 800, "start") + T(money(sum, unit), x1, y, fs * 1.05, INK, 800, "end");
    return `<rect x="${r1(x0 - fs * 0.6)}" y="${r1(h * 0.2 - rh * 0.6)}" width="${r1(x1 - x0 + fs * 1.2)}" height="${r1((R.length + (p.totals !== false ? 1 : 0)) * rh + rh * 0.2)}" rx="${r1(fs * 0.3)}" fill="#ffffff" stroke="#d5dbe1" stroke-width="${r1(w * 0.002)}"/>` + o;
  };
  return out + ledger(lx, p.leftRows) + ledger(rx, p.rightRows);
}

// ---------------------------------------------------------------- road corridor
// A city road seen from above: lanes each way, cars that stream at the given density and slow to a jam, a bus lane, a
// car-pool (2+) lane, a charging gantry with its display, side streets that take diverted cars (rat-runs), kerb parking
// (free, banned, paid), roadside houses with fumes, or a closed street full of walkers. Cars move with _t.
function road(p) {
  const w = num(p.w, 1600), fs = w * 0.024, t = tnum(p._t), tt = Number.isFinite(t) ? t : 0;
  const lanes = clampInt(num(p.lanes, 2), 1, 4), dens = clamp01(num(p.cars, 0.4)), speed = clamp01(num(p.speed, 0.7)), laneH = w * 0.045;
  const RH = lanes * 2 * laneH, y0 = -RH / 2, L = w, sides = clampInt(num(p.sideStreets, 0), 0, 3), walk = p.pedestrian === true;
  const carCols = ["#e5484d", "#3a7bd5", "#f2c14e", "#2fa35b", "#7b61ff", "#ffffff", "#4a5568", "#e2558f"];
  let out = "";
  // houses along the top with fumes
  const nh = clampInt(num(p.houses, 0), 0, 8);
  for (let i = 0; i < nh; i++) {
    const hx = -w * 0.44 + (i * w * 0.88) / Math.max(1, nh - 1 || 1), hy = y0 - fs * 1.9;
    out += at(hx, hy, drawSaancha("building", { kind: "house", w: w * 0.07 }));
    if (p.fumes) for (let j = 0; j < 3; j++) { const u = ((tt * 0.3 + j / 3 + i * 0.17) % 1); out += `<circle cx="${r1(hx + w * 0.03 + Math.sin(tt + i + j) * w * 0.008)}" cy="${r1(y0 - u * fs * 1.6)}" r="${r1(w * (0.007 + u * 0.008))}" fill="#9aa5b1" opacity="${r1((0.6 - u * 0.45) * 100) / 100}"/>`; }
  }
  // side streets going down from the road
  for (let k2 = 0; k2 < sides; k2++) {
    const sx = -w * 0.25 + k2 * w * 0.25;
    out += `<rect x="${r1(sx - laneH * 0.7)}" y="${r1(-y0)}" width="${r1(laneH * 1.4)}" height="${r1(w * 0.16)}" fill="#6b7280"/>`;
    const sd = clamp01(num(p.sideCars, 0.3)), nc = Math.round(sd * 4);
    for (let c = 0; c < nc; c++) { const u = (((tt * 0.12 * (0.4 + speed) + c / Math.max(1, nc)) % 1) + 1) % 1;
      out += `<rect x="${r1(sx - laneH * 0.25)}" y="${r1(-y0 + u * w * 0.15)}" width="${r1(laneH * 0.5)}" height="${r1(w * 0.03)}" rx="${r1(w * 0.005)}" fill="${carCols[(c + k2) % carCols.length]}" stroke="#2d3748" stroke-width="${r1(w * 0.001)}"/>`; }
  }
  // the road
  out += `<rect x="${r1(-L / 2)}" y="${r1(y0 - w * 0.008)}" width="${r1(L)}" height="${r1(RH + w * 0.016)}" fill="#c9c3b6"/><rect x="${r1(-L / 2)}" y="${r1(y0)}" width="${r1(L)}" height="${r1(RH)}" fill="#59606b"/>`;
  for (let i = 1; i < lanes * 2; i++) {
    const ly = y0 + i * laneH;
    out += i === lanes ? `<path d="M${r1(-L / 2)} ${r1(ly - w * 0.002)} L${r1(L / 2)} ${r1(ly - w * 0.002)} M${r1(-L / 2)} ${r1(ly + w * 0.002)} L${r1(L / 2)} ${r1(ly + w * 0.002)}" stroke="#f2c14e" stroke-width="${r1(w * 0.0018)}"/>`
      : `<path d="M${r1(-L / 2)} ${r1(ly)} L${r1(L / 2)} ${r1(ly)}" stroke="#ffffff" stroke-width="${r1(w * 0.002)}" stroke-dasharray="${r1(w * 0.02)} ${r1(w * 0.015)}" opacity="0.8"/>`;
  }
  const busLane = p.busLane === true, hov = p.hovLane === true;
  if (busLane) out += `<rect x="${r1(-L / 2)}" y="${r1(y0 + (2 * lanes - 1) * laneH)}" width="${r1(L)}" height="${r1(laneH)}" fill="#b23a3a" opacity="0.55"/>`;
  if (hov && lanes > 1) out += `<rect x="${r1(-L / 2)}" y="${r1(y0 + lanes * laneH)}" width="${r1(L)}" height="${r1(laneH)}" fill="#2a9d8f" opacity="0.4"/>` +
    `<path d="M${r1(-w * 0.3)} ${r1(y0 + lanes * laneH + laneH * 0.5)} l${r1(laneH * 0.3)} ${r1(-laneH * 0.3)} l${r1(laneH * 0.3)} ${r1(laneH * 0.3)} l${r1(-laneH * 0.3)} ${r1(laneH * 0.3)} Z" fill="#ffffff"/>`;
  if (walk) {
    for (let i = 0; i < 14; i++) { const r = rnd(i + 3), x = -L / 2 + ((r() * L + tt * w * 0.02 * (i % 2 ? 1 : -1)) % L + L) % L, yy = y0 + laneH * 0.4 + r() * (RH - laneH * 0.6);
      out += person(x, yy + laneH * 0.4, laneH * 0.9, i); }
    out += [-1, 1].map((sg) => `<rect x="${r1(sg * L * 0.47 - w * 0.008)}" y="${r1(y0)}" width="${r1(w * 0.016)}" height="${r1(RH)}" fill="#e5484d"/>`).join("");
  } else {
    // cars: each lane has a row of cars spaced by the density; slow speed bunches them (a jam)
    for (let ln = 0; ln < lanes * 2; ln++) {
      const dir = ln < lanes ? -1 : 1, ly = y0 + ln * laneH + laneH / 2, isBus = busLane && ln === lanes * 2 - 1;
      const nCars = isBus ? 2 : Math.max(0, Math.round(dens * 14 * (hov && ln === lanes ? 0.3 : 1))), v = (0.03 + speed * 0.12) * w;
      const r = rnd(ln * 17 + 5), cl = isBus ? w * 0.1 : w * 0.05, cw = laneH * 0.62;
      for (let c = 0; c < nCars; c++) {
        const base = (c / Math.max(1, nCars)) * L + r() * (L / Math.max(1, nCars)) * (0.6 - dens * 0.5), x = ((((base + dir * v * tt) % L) + L) % L) - L / 2;
        const col = isBus ? "#d1462f" : carCols[Math.floor(r() * carCols.length)];
        out += `<g transform="translate(${r1(x)},${r1(ly)})"><rect x="${r1(-cl / 2)}" y="${r1(-cw / 2)}" width="${r1(cl)}" height="${r1(cw)}" rx="${r1(cw * 0.3)}" fill="${col}" stroke="#2d3748" stroke-width="${r1(w * 0.0012)}"/>` +
          `<rect x="${r1(dir > 0 ? cl * 0.08 : -cl * 0.32)}" y="${r1(-cw * 0.36)}" width="${r1(cl * 0.24)}" height="${r1(cw * 0.72)}" rx="${r1(cw * 0.12)}" fill="#cfe3f5"/></g>`;
      }
    }
  }
  // kerb parking at the bottom edge
  const park = p.parking || "none";
  if (park !== "none") {
    const ky = -y0 + w * 0.014;
    if (park === "banned") out += `<path d="M${r1(-L / 2)} ${r1(ky - w * 0.004)} L${r1(L / 2)} ${r1(ky - w * 0.004)} M${r1(-L / 2)} ${r1(ky + w * 0.002)} L${r1(L / 2)} ${r1(ky + w * 0.002)}" stroke="#f2c14e" stroke-width="${r1(w * 0.003)}"/>`;
    else for (let c = 0; c < 8; c++) { const x = -L * 0.45 + c * L * 0.12; out += `<rect x="${r1(x)}" y="${r1(ky)}" width="${r1(w * 0.05)}" height="${r1(laneH * 0.55)}" rx="${r1(w * 0.008)}" fill="${carCols[(c * 3) % carCols.length]}" stroke="#2d3748" stroke-width="${r1(w * 0.0012)}"/>` +
      (park === "paid" && c % 2 === 0 ? `<rect x="${r1(x + w * 0.055)}" y="${r1(ky)}" width="${r1(w * 0.006)}" height="${r1(laneH * 0.55)}" fill="#4a5568"/><circle cx="${r1(x + w * 0.058)}" cy="${r1(ky)}" r="${r1(w * 0.007)}" fill="#2a9d8f"/>` : ""); }
  }
  // the gantry and its display
  if (p.gantry) {
    const gx = w * 0.22;
    out += `<rect x="${r1(gx - w * 0.006)}" y="${r1(y0 - w * 0.03)}" width="${r1(w * 0.012)}" height="${r1(RH + w * 0.06)}" fill="#4a5568"/>` +
      pill(p.gantry, gx, y0 - w * 0.03 - fs * 0.15, fs, { fill: "#1f2a33", color: "#f2c14e" });
  }
  if (p.label) out += plate(p.label, -w * 0.3, y0 - w * 0.03 - fs * 0.15, fs);
  return out;
}

// ---------------------------------------------------------------- agents: merging, believing, herding
// A crowd of identical agents. mode "merge": they slide together into one big representative agent (merge 0..1, gliding
// from "from" after the step); vary splits it back into different people who react differently. mode "belief": thought
// bubbles carrying the belief (price up, prices down, a growing factory, a rupee) pop up across a growing share of the
// crowd over spread seconds. mode "herd": people walk towards a stall and its price tag rises as the crowd there grows.
function agents(p) {
  // fs: the words keep the readable floor (36 px at s 1): on a notes picture the crowd came out with 28 px labels (ch20)
  const w = num(p.w, 1400), h = w * 0.55, fs = Math.max(36, w * 0.028), s = since(p), t = tnum(p._t), n = clampInt(num(p.n, 24), 1, 60), mode = ["belief", "herd"].includes(p.mode) ? p.mode : "merge";
  const cols = Math.ceil(Math.sqrt(n * 2)), rows = Math.ceil(n / cols), cell = Math.min((w * 0.8) / cols, (h * 0.75) / rows), ps = cell * 0.8, firms = p.kinds === "firms";
  let out = "";
  const grid = (i) => [-((cols - 1) * cell) / 2 + (i % cols) * cell, -((rows - 1) * cell) / 2 + Math.floor(i / cols) * cell + cell * 0.45];
  const one = (x, y, sz, i, shirt, dim) => firms ? at(x, y - sz * 0.45, place("factory", sz * 0.9)) : person(x, y, sz, i, dim, shirt);
  if (mode === "merge") {
    const m1 = clamp01(num(p.merge, 1)), m0 = isNum(p.from) ? clamp01(+p.from) : m1, m = lerp(m0, m1, easeIO(prog(s, num(p.glide, 1.5))));
    const vary = p.vary === true, bigS = h * 0.75;
    for (let i = 0; i < n; i++) {
      const [gx, gy] = grid(i), r = rnd(i + 11), sz = vary ? ps * (0.75 + r() * 0.5) : ps, shirt = vary ? undefined : "#3a7bd5";
      out += one(lerp(gx, 0, m), lerp(gy, bigS * 0.5, m), sz, vary ? i : 1, shirt, m > 0.85 ? r1((1 - (m - 0.85) / 0.15) * 100) / 100 || 0.01 : 0);
      if (vary && m < 0.05 && p.react) { const up = r() > 0.5; out += tri(gx + ps * 0.35, gy - ps * (up ? 1.05 : 0.6), up ? -Math.PI / 2 : Math.PI / 2, ps * 0.22, up ? C.money : C.red); }
    }
    if (m > 0.6) out += `<g opacity="${r1(clamp01((m - 0.6) / 0.3) * 100) / 100}">${one(0, bigS * 0.5, bigS, 1, "#3a7bd5")}</g>`;
    if (p.shock && m > 0.9) out += `<path d="M${r1(w * 0.18)} ${r1(-h * 0.45)} L${r1(w * 0.1)} ${r1(-h * 0.2)} L${r1(w * 0.14)} ${r1(-h * 0.2)} L${r1(w * 0.06)} ${r1(0)}" fill="none" stroke="#f2c14e" stroke-width="${r1(w * 0.012)}" stroke-linejoin="round"/>`;
    if (p.label && m > 0.9) out += plate(p.label, 0, bigS * 0.5 + fs * 1.2, fs);
    return out;
  }
  if (mode === "belief") {
    const sh1 = clamp01(num(p.share, 0.5)), sh0 = isNum(p.from) ? clamp01(+p.from) : 0, spread = Math.max(0.1, num(p.spread, 2)), sh = lerp(sh0, sh1, easeIO(prog(s, spread)));
    const order = Array.from({ length: n }, (_, i) => [rnd(i + 5)(), i]).sort((a, b) => a[0] - b[0]).map((x) => x[1]), k = Math.round(sh * n), has = new Set(order.slice(0, k));
    for (let i = 0; i < n; i++) { const [x, y] = grid(i); out += one(x, y, ps, i, undefined, has.has(i) ? 0 : 0.55); }
    for (let i = 0; i < n; i++) if (has.has(i)) {
      const [x, y] = grid(i), bx = x + ps * 0.28, by = y - ps * 1.25, br = ps * 0.26;
      out += `<circle cx="${r1(x + ps * 0.14)}" cy="${r1(y - ps * 0.98)}" r="${r1(br * 0.16)}" fill="#ffffff" stroke="#9aa5b1" stroke-width="${r1(w * 0.001)}"/>` +
        `<ellipse cx="${r1(bx)}" cy="${r1(by)}" rx="${r1(br * 1.3)}" ry="${r1(br)}" fill="#ffffff" stroke="#9aa5b1" stroke-width="${r1(w * 0.0015)}"/>` + at(bx, by, beliefGlyph(p.belief, br * 0.75));
    }
    if (p.label) out += pill(`${p.label} ${Math.round(sh * 100)}%`, 0, ((rows + 1) * cell) / 2 + fs * 0.6, fs, { fill: INK, color: "#ffffff" });
    return out;
  }
  // herd
  const rate = Math.max(0, num(p.rate, 2)), T = Number.isFinite(s) ? s : 99, sx = w * 0.32, price0 = num(p.price, 100), step = num(p.priceStep, 5);
  out += at(sx, h * 0.3, drawSaancha("building", { kind: p.target || "shop", w: w * 0.18 }));
  let arrived = 0;
  for (let i = 0; i < n; i++) {
    const st = i / Math.max(0.01, rate), k = clamp01((T - st) / 2.5), r = rnd(i + 2), x0 = -w * 0.46 + r() * w * 0.2, y0 = -h * 0.3 + r() * h * 0.6;
    const ax = sx - w * 0.12 - (i % 6) * ps * 0.45, ay = h * 0.3 - Math.floor(i / 6) * ps * 0.12;
    if (k >= 1) arrived++;
    out += person(lerp(x0, ax, easeIO(k)), lerp(y0, ay, easeIO(k)) + (k > 0 && k < 1 && Number.isFinite(t) ? -Math.abs(Math.sin(t * 9 + i)) * ps * 0.05 : 0), ps * 0.8, i);
  }
  out += pill(money(price0 + arrived * step, p.unit ?? "₹"), sx, h * 0.3 - w * 0.2, fs * 1.1, { fill: "#f2c14e", color: INK });
  if (p.label) out += plate(p.label, sx, h * 0.3 + fs * 1.1, fs);
  return out;
}
function beliefGlyph(kind, s) {
  if (kind === "down") return `<path d="M0 ${r1(s * 0.7)} L${r1(-s * 0.55)} ${r1(-s * 0.1)} L${r1(-s * 0.2)} ${r1(-s * 0.1)} L${r1(-s * 0.2)} ${r1(-s * 0.7)} L${r1(s * 0.2)} ${r1(-s * 0.7)} L${r1(s * 0.2)} ${r1(-s * 0.1)} L${r1(s * 0.55)} ${r1(-s * 0.1)} Z" fill="${C.red}"/>`;
  if (kind === "factory") return `<g transform="translate(0,${r1(s * 0.5)})">${drawSaancha("building", { kind: "factory", w: s * 1.3 })}</g>`;
  if (kind === "rupee") return token("coin", s * 0.7);
  if (kind === "house") return `<g transform="translate(0,${r1(s * 0.55)})">${drawSaancha("building", { kind: "house", w: s * 1.1 })}</g>`;
  return `<path d="M0 ${r1(-s * 0.7)} L${r1(s * 0.55)} ${r1(s * 0.1)} L${r1(s * 0.2)} ${r1(s * 0.1)} L${r1(s * 0.2)} ${r1(s * 0.7)} L${r1(-s * 0.2)} ${r1(s * 0.7)} L${r1(-s * 0.2)} ${r1(s * 0.1)} L${r1(-s * 0.55)} ${r1(s * 0.1)} Z" fill="${C.money}"/>`;
}

// ---------------------------------------------------------------- chance: a coin, a spinner, a fog
// Risk against uncertainty: a coin that flips and lands (heads or tails, after flip seconds from the step), a spinner
// whose wedge shows a known chance p and whose pointer spins and stops on the outcome, and a dial lost in fog with a
// question mark (the chance is not known). Each can carry a label underneath.
function chance(p) {
  const w = num(p.w, 1200), fs = w * 0.032, s = since(p), kinds = String(p.kind || "coin,spinner").split(/[,;\s]+/).filter((k) => ["coin", "spinner", "fog"].includes(k)).slice(0, 3);
  if (!kinds.length) kinds.push("coin");
  const labs = parts(p.labels), n = kinds.length, slot = w / n, R = Math.min(slot * 0.32, w * 0.16), heads = (p.outcome || "heads") !== "tails";
  let out = "";
  kinds.forEach((kd, i) => {
    const x = -w / 2 + (i + 0.5) * slot;
    if (kd === "coin") {
      const fl = Math.max(0.1, num(p.flip, 1.2)), k = prog(s, fl), sy = k < 1 ? Math.cos(k * Math.PI * 7) : 1, up = k < 1 ? -Math.sin(k * Math.PI) * R * 0.9 : 0, face = k < 1 ? (Math.cos(k * Math.PI * 7) > 0) : heads;
      out += `<g transform="translate(${r1(x)},${r1(up)}) scale(1,${r1(Math.max(0.06, Math.abs(sy)) * 100) / 100})"><circle r="${r1(R)}" fill="${face ? "#f2c14e" : "#d7dde4"}" stroke="${face ? "#b8860b" : "#8d99a6"}" stroke-width="${r1(R * 0.08)}"/>` +
        (face ? `<path d="M0 ${r1(-R * 0.5)} L${r1(R * 0.14)} ${r1(-R * 0.16)} L${r1(R * 0.5)} ${r1(-R * 0.14)} L${r1(R * 0.22)} ${r1(R * 0.1)} L${r1(R * 0.32)} ${r1(R * 0.48)} L0 ${r1(R * 0.28)} L${r1(-R * 0.32)} ${r1(R * 0.48)} L${r1(-R * 0.22)} ${r1(R * 0.1)} L${r1(-R * 0.5)} ${r1(-R * 0.14)} L${r1(-R * 0.14)} ${r1(-R * 0.16)} Z" fill="#b8860b"/>`
          : `<circle r="${r1(R * 0.42)}" fill="none" stroke="#8d99a6" stroke-width="${r1(R * 0.1)}"/>`) + `</g>`;
      if (k >= 1 && (heads ? p.headsLabel : p.tailsLabel)) out += pill(heads ? p.headsLabel : p.tailsLabel, x, -R - fs * 1.2, fs, { fill: INK, color: "#ffffff" });
    } else if (kd === "spinner") {
      const pr = clamp01(num(p.p, 0.5)), a1 = -Math.PI / 2 + pr * 2 * Math.PI, large = pr > 0.5 ? 1 : 0;
      out += `<circle cx="${r1(x)}" r="${r1(R)}" fill="#e3ecf7" stroke="${C.blue}" stroke-width="${r1(R * 0.05)}"/>` +
        (pr > 0 && pr < 1 ? `<path d="M${r1(x)} 0 L${r1(x)} ${r1(-R)} A${r1(R)} ${r1(R)} 0 ${large} 1 ${r1(x + Math.cos(a1) * R)} ${r1(Math.sin(a1) * R)} Z" fill="${C.money}"/>` : pr >= 1 ? `<circle cx="${r1(x)}" r="${r1(R)}" fill="${C.money}"/>` : "");
      const sp = Math.max(0.1, num(p.spin, 2)), k = prog(s, sp), win = p.win !== false, target = win ? -Math.PI / 2 + pr * Math.PI : -Math.PI / 2 + (pr + (1 - pr) / 2) * 2 * Math.PI;
      const ang = target + (1 - easeIO(k)) * Math.PI * 6;
      out += `<path d="M${r1(x)} 0 L${r1(x + Math.cos(ang) * R * 0.85)} ${r1(Math.sin(ang) * R * 0.85)}" stroke="${INK}" stroke-width="${r1(R * 0.07)}" stroke-linecap="round"/><circle cx="${r1(x)}" r="${r1(R * 0.08)}" fill="${INK}"/>`;
      if (p.pText !== false) out += pill(p.pText || `${fmt(pr * 100, 0)}%`, x, -R - fs * 1.2, fs, { fill: C.money, color: "#ffffff" });
    } else {
      out += `<circle cx="${r1(x)}" r="${r1(R)}" fill="#e3ecf7" stroke="#9aa5b1" stroke-width="${r1(R * 0.05)}"/>`;
      for (let j = 0; j < 7; j++) { const r = rnd(j + 4); out += `<ellipse cx="${r1(x + (r() - 0.5) * R * 1.4)}" cy="${r1((r() - 0.5) * R * 1.4)}" rx="${r1(R * (0.4 + r() * 0.3))}" ry="${r1(R * (0.22 + r() * 0.15))}" fill="#ffffff" opacity="0.8"/>`; }
      out += T("?", x, 0, R * 1.1, "#6b7280", 800);
    }
    if (labs[i]) out += T(labs[i], x, R + fs * 1.1, fs, INK, 800);
  });
  return out;
}

// ---------------------------------------------------------------- account balance with its overdraft
// A balance bar with zero marked: above zero it is green, below it a red overdraft zone down to the limit. The balance
// glides from "from" to "balance" after the step, falling through zero into red on the word.
function accountBar(p) {
  const w = num(p.w, 1100), fs = w * 0.036, unit = p.unit ?? "₹", s = since(p), g = Math.max(0.1, num(p.glide, 1.5));
  const lim = Math.abs(num(p.limit, 500)), top = Math.max(1, num(p.max, 1000)), b1 = num(p.balance, 300), b0 = isNum(p.from) ? +p.from : b1, b = lerp(b0, b1, easeIO(prog(s, g)));
  const x0 = -w * 0.42, x1 = w * 0.42, X = (v) => x0 + ((Math.max(-lim, Math.min(top, v)) + lim) / (top + lim)) * (x1 - x0), bh = w * 0.09, zx = X(0);
  let out = `<rect x="${r1(x0)}" y="${r1(-bh / 2)}" width="${r1(x1 - x0)}" height="${r1(bh)}" rx="${r1(bh * 0.2)}" fill="#eef1f4" stroke="#9aa5b1" stroke-width="${r1(w * 0.003)}"/>` +
    `<rect x="${r1(x0)}" y="${r1(-bh / 2)}" width="${r1(zx - x0)}" height="${r1(bh)}" fill="#fdeeee"/>` +
``;
  const bx = X(b), neg = b < 0;
  out += `<rect x="${r1(Math.min(zx, bx))}" y="${r1(-bh * 0.32)}" width="${r1(Math.abs(bx - zx))}" height="${r1(bh * 0.64)}" rx="${r1(bh * 0.1)}" fill="${neg ? C.red : C.money}"/>` +
    `<path d="M${r1(zx)} ${r1(-bh * 0.85)} L${r1(zx)} ${r1(bh * 0.85)}" stroke="${INK}" stroke-width="${r1(w * 0.005)}"/>` + T(p.zeroLabel ?? "0", zx, bh * 0.85 + fs * 0.8, fs, INK, 800) +
    (lim > 0 ? T(money(-lim, unit), x0, bh * 0.85 + fs * 0.8, fs, C.red, 800, "start") : "") +
    `<path d="M${r1(bx)} ${r1(-bh * 0.6)} l${r1(-w * 0.014)} ${r1(-w * 0.022)} l${r1(w * 0.028)} 0 Z" fill="${INK}"/>` + pill(money(b, unit), bx, -bh * 0.6 - w * 0.022 - fs * 0.9, fs * 1.05, { fill: neg ? C.red : C.money, color: "#ffffff" });
  if (p.limitLabel) out += T(p.limitLabel, (x0 + zx) / 2, 0, fs, shade(C.red, 0.7), 800);
  if (p.label) out += T(p.label, 0, bh * 0.85 + fs * 2.3, fs * 1.05, INK, 800);
  return out;
}

// ---------------------------------------------------------------- things of the stories: appliances, vehicles, papers
// An appliance (a pedestal fan that turns when on, a fridge whose door opens, a water tanker with its fill, a TV, a
// washing machine) with an optional price tag; a vehicle (small car, sedan, SUV, luxury car, bus, truck) with a damage
// state (dents, a cracked window, smoke), a lemon sticker and wheels that turn when it moves; a paper of the insurance
// and lemons stories (a policy with its rows, a form whose ticks fill in, a degree with its seal, a medical certificate)
// on which a stamp lands after the step.
function appliance(p) {
  const w = num(p.w, 300), fs = Math.max(w * 0.13, 36), kind = p.kind || "fan", t = tnum(p._t), c = p.color || "#3a7bd5";
  let out = "";
  if (kind === "fan") {
    const r = w * 0.32, cy = -w * 0.95, a = p.on === false || !Number.isFinite(t) ? 20 : (t * 720) % 360;
    out += `<rect x="${r1(-w * 0.025)}" y="${r1(cy)}" width="${r1(w * 0.05)}" height="${r1(-cy - w * 0.06)}" fill="#8a94a3"/><ellipse cy="${r1(-w * 0.04)}" rx="${r1(w * 0.22)}" ry="${r1(w * 0.05)}" fill="#6b7280"/>` +
      `<circle cy="${r1(cy)}" r="${r1(r)}" fill="#eef3fb" stroke="#9aa5b1" stroke-width="${r1(w * 0.012)}"/>` +
      `<g transform="translate(0,${r1(cy)}) rotate(${r1(a)})">${[0, 120, 240].map((d) => `<ellipse cx="0" cy="${r1(-r * 0.48)}" rx="${r1(r * 0.2)}" ry="${r1(r * 0.42)}" fill="${c}" opacity="0.85" transform="rotate(${d})"/>`).join("")}</g>` +
      `<circle cy="${r1(cy)}" r="${r1(r * 0.13)}" fill="#4a5568"/>` + [0.33, 0.66, 1].map((k) => `<circle cy="${r1(cy)}" r="${r1(r * k)}" fill="none" stroke="#c3cad3" stroke-width="${r1(w * 0.004)}"/>`).join("");
  } else if (kind === "fridge") {
    const fw = w * 0.5, fh = w * 1.0, open = clamp01(num(p.open, 0));
    out += `<rect x="${r1(-fw / 2)}" y="${r1(-fh)}" width="${r1(fw)}" height="${r1(fh)}" rx="${r1(w * 0.03)}" fill="#e8eef5" stroke="#9aa5b1" stroke-width="${r1(w * 0.01)}"/>` +
      (open > 0 ? `<rect x="${r1(-fw / 2 + w * 0.02)}" y="${r1(-fh + w * 0.02)}" width="${r1(fw - w * 0.04)}" height="${r1(fh * 0.62)}" fill="#fdfdf8"/>` +
        [0.2, 0.4].map((k) => `<rect x="${r1(-fw / 2 + w * 0.02)}" y="${r1(-fh + fh * k)}" width="${r1(fw - w * 0.04)}" height="${r1(w * 0.01)}" fill="#c3cad3"/>`).join("") +
        `<circle cx="${r1(-fw * 0.15)}" cy="${r1(-fh * 0.86)}" r="${r1(w * 0.04)}" fill="#e5484d"/><rect x="${r1(fw * 0.05)}" y="${r1(-fh * 0.72)}" width="${r1(w * 0.08)}" height="${r1(w * 0.1)}" fill="#2fa35b"/>` : "") +
      `<g transform="translate(${r1(-fw / 2)},0) scale(${r1((1 - open * 1.6) * 100) / 100},1)"><rect x="0" y="${r1(-fh)}" width="${r1(fw)}" height="${r1(fh * 0.64)}" rx="${r1(w * 0.03)}" fill="${shade(c, 1.5)}" stroke="#9aa5b1" stroke-width="${r1(w * 0.008)}"/>` +
      `<rect x="${r1(fw * 0.82)}" y="${r1(-fh * 0.9)}" width="${r1(w * 0.025)}" height="${r1(fh * 0.2)}" rx="${r1(w * 0.01)}" fill="#6b7280"/></g>` +
      `<rect x="${r1(-fw / 2)}" y="${r1(-fh * 0.35)}" width="${r1(fw)}" height="${r1(fh * 0.35)}" rx="${r1(w * 0.03)}" fill="${shade(c, 1.5)}" stroke="#9aa5b1" stroke-width="${r1(w * 0.008)}"/>` +
      `<rect x="${r1(fw * 0.32)}" y="${r1(-fh * 0.3)}" width="${r1(w * 0.025)}" height="${r1(fh * 0.14)}" rx="${r1(w * 0.01)}" fill="#6b7280"/>`;
  } else if (kind === "tanker") {
    const lvl = clamp01(num(p.level, 0.7)), tl = w * 0.62, th = w * 0.26, tx0 = -w * 0.48, ty = -w * 0.1 - th;
    out += `<rect x="${r1(tx0)}" y="${r1(-w * 0.14)}" width="${r1(w * 0.96)}" height="${r1(w * 0.06)}" fill="#4a5568"/>` +
      `<rect x="${r1(tx0 + w * 0.02)}" y="${r1(ty)}" width="${r1(tl)}" height="${r1(th)}" rx="${r1(th / 2)}" fill="#dfe7ef" stroke="#6b7a8c" stroke-width="${r1(w * 0.01)}"/>` +
      `<rect x="${r1(tx0 + w * 0.03)}" y="${r1(ty + th * (1 - lvl))}" width="${r1(tl - w * 0.02)}" height="${r1(th * lvl - w * 0.01)}" rx="${r1(th * 0.3)}" fill="#5aa9e6" opacity="0.85"/>` +
      `<path d="M${r1(tx0 + tl + w * 0.04)} ${r1(-w * 0.14)} L${r1(tx0 + tl + w * 0.04)} ${r1(-w * 0.38)} L${r1(w * 0.4)} ${r1(-w * 0.38)} L${r1(w * 0.48)} ${r1(-w * 0.26)} L${r1(w * 0.48)} ${r1(-w * 0.14)} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${r1(w * 0.008)}"/>` +
      `<rect x="${r1(tx0 + tl + w * 0.08)}" y="${r1(-w * 0.34)}" width="${r1(w * 0.14)}" height="${r1(w * 0.09)}" rx="${r1(w * 0.015)}" fill="#cfe3f5"/>` +
      [tx0 + w * 0.16, tx0 + w * 0.5, w * 0.36].map((x) => `<circle cx="${r1(x)}" cy="${r1(-w * 0.07)}" r="${r1(w * 0.07)}" fill="#2d3748"/><circle cx="${r1(x)}" cy="${r1(-w * 0.07)}" r="${r1(w * 0.03)}" fill="#9aa5b1"/>`).join("");
  } else if (kind === "tv") {
    out += `<rect x="${r1(-w * 0.45)}" y="${r1(-w * 0.7)}" width="${r1(w * 0.9)}" height="${r1(w * 0.55)}" rx="${r1(w * 0.03)}" fill="#2d3748"/><rect x="${r1(-w * 0.41)}" y="${r1(-w * 0.66)}" width="${r1(w * 0.82)}" height="${r1(w * 0.47)}" fill="${shade(c, 1.3)}"/>` +
      `<path d="M${r1(-w * 0.15)} 0 L0 ${r1(-w * 0.15)} L${r1(w * 0.15)} 0 Z" fill="#4a5568"/>`;
  } else {
    out += `<rect x="${r1(-w * 0.3)}" y="${r1(-w * 0.75)}" width="${r1(w * 0.6)}" height="${r1(w * 0.75)}" rx="${r1(w * 0.03)}" fill="#f4f6f8" stroke="#9aa5b1" stroke-width="${r1(w * 0.01)}"/>` +
      `<circle cy="${r1(-w * 0.33)}" r="${r1(w * 0.2)}" fill="#cfe3f5" stroke="#6b7a8c" stroke-width="${r1(w * 0.02)}"/><rect x="${r1(-w * 0.26)}" y="${r1(-w * 0.71)}" width="${r1(w * 0.52)}" height="${r1(w * 0.1)}" fill="#e3e8ee"/>`;
  }
  if (p.label) out += pill(p.label, kind === "tanker" ? -w * 0.17 : 0, kind === "fan" ? -w * 1.38 : kind === "tanker" ? -w * 0.5 : kind === "fridge" ? -w * 1.12 : -w * 0.88, fs, { fill: "#f2c14e", color: INK });
  return out;
}
function vehicle(p) {
  const w = num(p.w, 420), fs = Math.max(w * 0.1, 36), kind = p.kind || "sedan", t = tnum(p._t), c = p.color || "#3a7bd5", dmg = clamp01(num(p.damage, 0)), moving = p.moving === true && Number.isFinite(t);
  const L = kind === "bus" || kind === "truck" ? w : kind === "small" ? w * 0.7 : w * 0.88, H = kind === "bus" ? w * 0.36 : kind === "truck" ? w * 0.32 : kind === "suv" ? w * 0.26 : w * 0.2;
  const R = w * (kind === "small" ? 0.065 : 0.08), ws = moving ? t * 600 : 0;
  let body = "";
  if (kind === "bus") body = `<rect x="${r1(-L / 2)}" y="${r1(-H - R)}" width="${r1(L)}" height="${r1(H)}" rx="${r1(w * 0.03)}" fill="${c}" stroke="${shade(c)}" stroke-width="${r1(w * 0.008)}"/>` +
    [0, 1, 2, 3, 4].map((k) => `<rect x="${r1(-L / 2 + w * 0.06 + k * L * 0.17)}" y="${r1(-H - R + H * 0.12)}" width="${r1(L * 0.13)}" height="${r1(H * 0.36)}" rx="${r1(w * 0.01)}" fill="#cfe3f5"/>`).join("");
  else if (kind === "truck") body = `<rect x="${r1(-L / 2)}" y="${r1(-H - R)}" width="${r1(L * 0.66)}" height="${r1(H)}" rx="${r1(w * 0.01)}" fill="#c8a06a" stroke="#8a6d3b" stroke-width="${r1(w * 0.008)}"/>` +
    `<path d="M${r1(L * 0.18)} ${r1(-R)} L${r1(L * 0.18)} ${r1(-H * 0.85 - R)} L${r1(L * 0.38)} ${r1(-H * 0.85 - R)} L${r1(L / 2)} ${r1(-H * 0.45 - R)} L${r1(L / 2)} ${r1(-R)} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${r1(w * 0.008)}"/>` +
    `<rect x="${r1(L * 0.24)}" y="${r1(-H * 0.75 - R)}" width="${r1(L * 0.12)}" height="${r1(H * 0.28)}" rx="${r1(w * 0.008)}" fill="#cfe3f5"/>`;
  else {
    const roofH = kind === "suv" ? H * 0.9 : kind === "luxury" ? H * 0.62 : H * 0.75, bl = -L / 2, by = -R - H * 0.55;
    body = `<path d="M${r1(bl)} ${r1(-R)} L${r1(bl)} ${r1(by)} Q${r1(bl)} ${r1(by - H * 0.1)} ${r1(bl + L * 0.1)} ${r1(by - H * 0.12)} L${r1(bl + L * 0.24)} ${r1(by - H * 0.12)} L${r1(bl + L * 0.34)} ${r1(by - roofH)} L${r1(bl + L * 0.7)} ${r1(by - roofH)} L${r1(bl + L * 0.82)} ${r1(by - H * 0.12)} L${r1(-bl - L * 0.04)} ${r1(by - H * 0.02)} Q${r1(-bl)} ${r1(by)} ${r1(-bl)} ${r1(by + H * 0.2)} L${r1(-bl)} ${r1(-R)} Z" fill="${c}" stroke="${shade(c)}" stroke-width="${r1(w * 0.008)}"/>` +
      `<path d="M${r1(bl + L * 0.29)} ${r1(by - H * 0.14)} L${r1(bl + L * 0.36)} ${r1(by - roofH + H * 0.1)} L${r1(bl + L * 0.5)} ${r1(by - roofH + H * 0.1)} L${r1(bl + L * 0.5)} ${r1(by - H * 0.14)} Z M${r1(bl + L * 0.54)} ${r1(by - H * 0.14)} L${r1(bl + L * 0.54)} ${r1(by - roofH + H * 0.1)} L${r1(bl + L * 0.68)} ${r1(by - roofH + H * 0.1)} L${r1(bl + L * 0.77)} ${r1(by - H * 0.14)} Z" fill="#cfe3f5"/>` +
      (kind === "luxury" ? `<path d="M${r1(bl + L * 0.05)} ${r1(by + H * 0.15)} L${r1(-bl - L * 0.05)} ${r1(by + H * 0.15)}" stroke="#f2c14e" stroke-width="${r1(w * 0.008)}"/>` : "") +
      `<circle cx="${r1(-bl - L * 0.03)}" cy="${r1(by + H * 0.12)}" r="${r1(w * 0.015)}" fill="#f2c14e"/>`;
  }
  const wheel = (x) => `<g transform="translate(${r1(x)},${r1(-R)}) rotate(${r1(ws % 360)})"><circle r="${r1(R)}" fill="#2d3748"/><circle r="${r1(R * 0.45)}" fill="#c3cad3"/><path d="M${r1(-R * 0.45)} 0 L${r1(R * 0.45)} 0" stroke="#6b7280" stroke-width="${r1(R * 0.12)}"/></g>`;
  let out = body + wheel(-L * 0.3) + wheel(L * 0.3);
  if (dmg > 0) {
    out += `<path d="M${r1(-L * 0.05)} ${r1(-R - H * 0.4)} l${r1(w * 0.03)} ${r1(w * 0.02)} l${r1(-w * 0.02)} ${r1(w * 0.025)} l${r1(w * 0.035)} ${r1(w * 0.02)}" fill="none" stroke="#2d3748" stroke-width="${r1(w * 0.006)}" opacity="${r1(Math.min(1, dmg * 2) * 100) / 100}"/>`;
    if (dmg > 0.4) out += `<path d="M${r1(L * 0.1)} ${r1(-R - H * 0.95)} l${r1(w * 0.02)} ${r1(w * 0.04)} m${r1(-w * 0.01)} ${r1(-w * 0.02)} l${r1(w * 0.03)} ${r1(-w * 0.01)}" stroke="#4a5568" stroke-width="${r1(w * 0.004)}"/>`;
    if (dmg > 0.7) for (let j = 0; j < 3; j++) { const u = Number.isFinite(t) ? (t * 0.5 + j / 3) % 1 : j / 3; out += `<circle cx="${r1(L * 0.42 + u * w * 0.05)}" cy="${r1(-R - H - u * w * 0.2)}" r="${r1(w * (0.03 + u * 0.03))}" fill="#6b7280" opacity="${r1((0.7 - u * 0.6) * 100) / 100}"/>`; }
  }
  if (p.lemon) out += `<ellipse cx="${r1(-L * 0.1)}" cy="${r1(-R - H * 0.35)}" rx="${r1(w * 0.045)}" ry="${r1(w * 0.032)}" fill="#f7e04a" stroke="#c9a400" stroke-width="${r1(w * 0.005)}"/><path d="M${r1(-L * 0.1 + w * 0.04)} ${r1(-R - H * 0.37)} l${r1(w * 0.02)} ${r1(-w * 0.015)}" stroke="#4f9a4a" stroke-width="${r1(w * 0.008)}"/>`;
  if (moving) out += [0, 1, 2].map((k) => `<path d="M${r1(-L / 2 - w * 0.04 - k * w * 0.02)} ${r1(-R - H * (0.2 + k * 0.25))} l${r1(-w * 0.08)} 0" stroke="#9aa5b1" stroke-width="${r1(w * 0.008)}" stroke-linecap="round"/>`).join("");
  const topY = kind === "bus" || kind === "truck" ? -R - H : -R - H * 0.55 - (kind === "suv" ? H * 0.9 : kind === "luxury" ? H * 0.62 : H * 0.75);
  if (p.label) out += pill(p.label, 0, topY - fs * 0.95, fs, { fill: "#f2c14e", color: INK });
  return out;
}
function certificate(p) {
  const w = num(p.w, 520), h = w * 1.25, fs = Math.max(w * 0.075, 36), kind = p.kind || "policy", s = since(p), band = { policy: "#2a9d8f", form: "#3a7bd5", degree: "#7a4e22", medical: "#d6454f" }[kind] || "#2a9d8f";
  const x0 = -w / 2, y0 = -h / 2;
  let out = `<rect x="${r1(x0)}" y="${r1(y0)}" width="${r1(w)}" height="${r1(h)}" rx="${r1(w * 0.03)}" fill="${kind === "degree" ? "#fbf3e2" : "#ffffff"}" stroke="${shade(band, 1.2)}" stroke-width="${r1(w * 0.012)}"/>` +
    `<rect x="${r1(x0)}" y="${r1(y0)}" width="${r1(w)}" height="${r1(h * 0.15)}" rx="${r1(w * 0.03)}" fill="${band}"/>`;
  if (p.title) out += T(p.title, 0, y0 + h * 0.075, Math.min(fs, (w * 0.86) / Math.max(1, tw(p.title, 1))), "#ffffff", 800);
  const rows = items(p.rows, 4), ry = y0 + h * 0.25, rh = fs * 1.6;
  if (kind === "form") {
    const n = Math.max(rows.length, clampInt(num(p.boxes, 4), 1, 5)), ticked = clampInt(num(p.ticked, 0), 0, n);
    for (let i = 0; i < n; i++) { const y = ry + i * rh, on = i < ticked;
      out += `<rect x="${r1(x0 + w * 0.08)}" y="${r1(y - fs * 0.45)}" width="${r1(fs * 0.9)}" height="${r1(fs * 0.9)}" rx="${r1(fs * 0.15)}" fill="#ffffff" stroke="${band}" stroke-width="${r1(w * 0.008)}"/>` +
        (on ? `<path d="M${r1(x0 + w * 0.08 + fs * 0.18)} ${r1(y)} L${r1(x0 + w * 0.08 + fs * 0.4)} ${r1(y + fs * 0.25)} L${r1(x0 + w * 0.08 + fs * 0.78)} ${r1(y - fs * 0.3)}" fill="none" stroke="${C.money}" stroke-width="${r1(fs * 0.14)}" stroke-linecap="round" stroke-linejoin="round"/>` : "") +
        (rows[i] ? T(rows[i].label, x0 + w * 0.08 + fs * 1.3, y, fs, INK, 700, "start") : `<rect x="${r1(x0 + w * 0.08 + fs * 1.3)}" y="${r1(y - w * 0.012)}" width="${r1(w * 0.55)}" height="${r1(w * 0.024)}" rx="${r1(w * 0.012)}" fill="#d5dbe1"/>`); }
  } else {
    rows.forEach((r, i) => { const y = ry + i * rh; out += T(r.label, x0 + w * 0.08, y, fs, "#4a5568", 700, "start") + T(r.raw, -x0 - w * 0.08, y, fs, INK, 800, "end"); });
    const used = rows.length * rh;
    for (let i = 0; i < Math.max(0, 3 - rows.length); i++) out += `<rect x="${r1(x0 + w * 0.08)}" y="${r1(ry + used + i * w * 0.07)}" width="${r1(w * (i === 2 ? 0.5 : 0.84))}" height="${r1(w * 0.022)}" rx="${r1(w * 0.011)}" fill="#d5dbe1"/>`;
    const gy = -y0 - h * 0.17;
    if (kind === "policy") out += `<path d="M${r1(x0 + w * 0.2)} ${r1(gy - w * 0.09)} l${r1(w * 0.08)} ${r1(w * 0.03)} l0 ${r1(w * 0.06)} q0 ${r1(w * 0.06)} ${r1(-w * 0.08)} ${r1(w * 0.09)} q${r1(-w * 0.08)} ${r1(-w * 0.03)} ${r1(-w * 0.08)} ${r1(-w * 0.09)} l0 ${r1(-w * 0.06)} Z" fill="${band}"/>`;
    if (kind === "degree") out += `<circle cx="${r1(x0 + w * 0.2)}" cy="${r1(gy)}" r="${r1(w * 0.07)}" fill="#c0392b"/><path d="M${r1(x0 + w * 0.17)} ${r1(gy + w * 0.06)} l${r1(-w * 0.03)} ${r1(w * 0.09)} l${r1(w * 0.04)} ${r1(-w * 0.02)} M${r1(x0 + w * 0.23)} ${r1(gy + w * 0.06)} l${r1(w * 0.03)} ${r1(w * 0.09)} l${r1(-w * 0.04)} ${r1(-w * 0.02)}" fill="#c0392b" stroke="#c0392b" stroke-width="${r1(w * 0.01)}"/>`;
    if (kind === "medical") out += `<rect x="${r1(x0 + w * 0.17)}" y="${r1(gy - w * 0.08)}" width="${r1(w * 0.06)}" height="${r1(w * 0.16)}" fill="${band}"/><rect x="${r1(x0 + w * 0.12)}" y="${r1(gy - w * 0.03)}" width="${r1(w * 0.16)}" height="${r1(w * 0.06)}" fill="${band}"/>`;
    out += `<path d="M${r1(w * 0.05)} ${r1(gy + w * 0.03)} q${r1(w * 0.06)} ${r1(-w * 0.07)} ${r1(w * 0.12)} 0 t${r1(w * 0.14)} 0" fill="none" stroke="#2d3748" stroke-width="${r1(w * 0.008)}"/>`;
  }
  if (p.stamp) {
    const k = easeIO(prog(s, 0.5)), sc = 1.6 - 0.6 * k, sc2 = r1(sc * 100) / 100, sw = Math.max(pillW(p.stamp, fs), w * 0.5);
    out += `<g transform="translate(${r1(w * 0.08)},${r1(h * 0.18)}) rotate(-14) scale(${sc2})" opacity="${r1(Math.min(1, k * 1.5) * 100) / 100}"><rect x="${r1(-sw / 2)}" y="${r1(-fs * 0.8)}" width="${r1(sw)}" height="${r1(fs * 1.6)}" rx="${r1(fs * 0.25)}" fill="none" stroke="${p.stampColor || C.red}" stroke-width="${r1(w * 0.014)}"/>` +
      T(p.stamp, 0, 0, fs, p.stampColor || C.red, 800) + `</g>`;
  }
  return out;
}

export const DRAWS = {
  circularFlow: { fn: circularFlow, anchor: "center" },
  chainRounds: { fn: chainRounds, anchor: "center" },
  tank: { fn: tank, anchor: "bottom" },
  balanceSheet: { fn: balanceSheet, anchor: "center" },
  timeValue: { fn: timeValue, anchor: "center" },
  gambleTree: { fn: gambleTree, anchor: "center" },
  insurancePool: { fn: insurancePool, anchor: "center" },
  queueLine: { fn: queueLine, anchor: "bottom" },
  contagion: { fn: contagion, anchor: "center" },
  securitisation: { fn: securitisation, anchor: "center" },
  layers: { fn: layers, anchor: "bottom" },
  pricePath: { fn: pricePath, anchor: "center" },
  rateCorridor: { fn: rateCorridor, anchor: "center" },
  moneySplit: { fn: moneySplit, anchor: "center" },
  tradeLedger: { fn: tradeLedger, anchor: "center" },
  road: { fn: road, anchor: "center" },
  agents: { fn: agents, anchor: "center" },
  riskDial: { fn: chance, anchor: "center" },
  accountBar: { fn: accountBar, anchor: "center" },
  appliance: { fn: appliance, anchor: "bottom" },
  usedCar: { fn: vehicle, anchor: "bottom" },
  certificate: { fn: certificate, anchor: "center" },
};
export const _test = { fmt, money, items };
