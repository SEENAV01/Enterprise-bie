// The box rule (dabba-niyam, Navin 5 November 2026): every thing the engine draws knows its own box and the boxes of
// the words inside it, measured from the very SVG it draws — one truth, so a saancha added tomorrow is measured the
// same way without anyone writing its box by hand. Pure string work (no DOM): the scene-plan compiler asks Node for
// these boxes (tools/saancha_boxes.mjs) and refuses a plan whose things sit on texts, faces or reserved places.
//
// svgBounds(svg) -> { box: [x0, y0, x1, y1] | null, texts: [{ t, px, box }] } in the SVG's own coordinates. Paths count
// their control points (a box never smaller than the drawing), strokes add half their width, a text's width is
// estimated per letter (Latin, digits, Devanagari with its vowel signs) like the compiler's own text box.

const NUM = /-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi;
const ID = [1, 0, 0, 1, 0, 0];

function mul(m, n) {
  return [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
    m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
}

export function parseTransform(s) {
  let m = ID;
  for (const f of String(s || "").matchAll(/([a-zA-Z]+)\s*\(([^)]*)\)/g)) {
    const a = (f[2].match(NUM) || []).map(Number);
    let n = ID;
    if (f[1] === "translate") n = [1, 0, 0, 1, a[0] || 0, a[1] || 0];
    else if (f[1] === "scale") n = [a[0] ?? 1, 0, 0, a[1] ?? a[0] ?? 1, 0, 0];
    else if (f[1] === "rotate") {
      const r = ((a[0] || 0) * Math.PI) / 180, c = Math.cos(r), sn = Math.sin(r), cx = a[1] || 0, cy = a[2] || 0;
      n = mul(mul([1, 0, 0, 1, cx, cy], [c, sn, -sn, c, 0, 0]), [1, 0, 0, 1, -cx, -cy]);
    } else if (f[1] === "matrix" && a.length === 6) n = a;
    m = mul(m, n);
  }
  return m;
}

const apply = (m, x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
const scaleOf = (m) => Math.sqrt(Math.abs(m[0] * m[3] - m[1] * m[2])) || 1;

function attrs(s) {
  const out = {};
  for (const a of s.matchAll(/([a-zA-Z_:-]+)\s*=\s*("([^"]*)"|'([^']*)')/g)) out[a[1]] = a[3] ?? a[4];
  return out;
}

// Path points (absolute), control points included: every command of the SVG path grammar.
export function pathPoints(d) {
  const pts = [], toks = String(d || "").match(/[a-zA-Z]|-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi) || [];
  let i = 0, cmd = "", x = 0, y = 0, sx = 0, sy = 0;
  const num = () => Number(toks[i++]);
  const more = () => i < toks.length && !/^[a-zA-Z]$/.test(toks[i]);
  while (i < toks.length) {
    if (/^[a-zA-Z]$/.test(toks[i])) cmd = toks[i++];
    else if (!cmd) { i++; continue; }
    const rel = cmd === cmd.toLowerCase(), C = cmd.toUpperCase();
    if (C === "Z") { x = sx; y = sy; pts.push([x, y]); if (!more()) continue; }
    const bx = rel ? x : 0, by = rel ? y : 0;
    if (C === "M" || C === "L" || C === "T") {
      if (!more()) continue;
      x = bx + num(); y = by + num(); pts.push([x, y]);
      if (C === "M") { sx = x; sy = y; cmd = rel ? "l" : "L"; }
    } else if (C === "H") { if (!more()) continue; x = bx + num(); pts.push([x, y]); }
    else if (C === "V") { if (!more()) continue; y = by + num(); pts.push([x, y]); }
    else if (C === "Q" || C === "S") {
      if (!more()) continue;
      pts.push([bx + num(), by + num()]); x = bx + num(); y = by + num(); pts.push([x, y]);
    } else if (C === "C") {
      if (!more()) continue;
      pts.push([bx + num(), by + num()]); pts.push([bx + num(), by + num()]); x = bx + num(); y = by + num(); pts.push([x, y]);
    } else if (C === "A") {
      if (!more()) continue;
      const rx = Math.abs(num()), ry = Math.abs(num()); num(); num(); num();
      const nx = bx + num(), ny = by + num(), mx = (x + nx) / 2, my = (y + ny) / 2;
      pts.push([x, y], [nx, ny], [mx - rx, my - ry], [mx + rx, my + ry]);   // the whole ellipse: never too small
      x = nx; y = ny;
    } else i++;
  }
  return pts;
}

// One letter's advance as a share of the font size (bold Noto Sans / Noto Sans Devanagari, the engine's faces).
export function letterWidth(ch) {
  const c = ch.codePointAt(0);
  if (c >= 0x0900 && c <= 0x097f) {
    if ((c >= 0x0900 && c <= 0x0903) || (c >= 0x093a && c <= 0x094f) || (c >= 0x0951 && c <= 0x0957) || c === 0x0962 || c === 0x0963)
      return c === 0x093e || c === 0x0940 || c === 0x0949 || c === 0x094a || c === 0x094b || c === 0x094c ? 0.28 : 0.04;  // vowel signs
    return 0.66;
  }
  if (ch === " ") return 0.27;
  if (/[0-9]/.test(ch)) return 0.6;
  if (/[A-Z]/.test(ch)) return 0.7;
  if (/[a-z]/.test(ch)) return "iljft".includes(ch) ? 0.32 : "mw".includes(ch) ? 0.92 : 0.58;
  if ("₹$€£¥".includes(ch)) return 0.6;
  return 0.42;
}

export function textWidth(t, px) {
  let w = 0;
  for (const ch of String(t)) w += letterWidth(ch);
  return w * px;
}

const unesc = (s) => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, "&");

export function svgBounds(svg) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const texts = [];
  const add = (m, x, y, pad = 0) => {
    const [px, py] = apply(m, x, y), p = pad * scaleOf(m);
    x0 = Math.min(x0, px - p); y0 = Math.min(y0, py - p); x1 = Math.max(x1, px + p); y1 = Math.max(y1, py + p);
  };
  const addBox = (m, bx0, by0, bx1, by1, pad = 0) => { add(m, bx0, by0, pad); add(m, bx1, by0, pad); add(m, bx0, by1, pad); add(m, bx1, by1, pad); };
  const stack = [ID];
  const re = /<(\/?)([a-zA-Z][\w:-]*)((?:[^>"']|"[^"]*"|'[^']*')*?)(\/?)>|([^<]+)/g;
  let inDefs = 0, openText = null;
  for (const m of String(svg).matchAll(re)) {
    if (m[5] != null) { if (openText) openText.t += m[5]; continue; }
    const closing = m[1] === "/", tag = m[2], a = attrs(m[3] || ""), selfClose = m[4] === "/";
    if (tag === "defs" || tag === "linearGradient" || tag === "radialGradient" || tag === "clipPath" || tag === "mask") {
      if (closing) inDefs = Math.max(0, inDefs - 1); else if (!selfClose) inDefs++;
      continue;
    }
    if (closing) {
      if (tag === "g" || tag === "svg") stack.pop();
      if (tag === "text" && openText) {
        const { m: tm, x, y, px, anchor } = openText, t = unesc(openText.t).replace(/\s+/g, " ").trim();
        if (t) {
          const w = textWidth(t, px), lx = anchor === "middle" ? x - w / 2 : anchor === "end" ? x - w : x;
          const c = [apply(tm, lx, y - px * 0.8), apply(tm, lx + w, y - px * 0.8), apply(tm, lx, y + px * 0.25), apply(tm, lx + w, y + px * 0.25)];
          const bx = c.map((p) => p[0]), by = c.map((p) => p[1]);
          const box = [Math.min(...bx), Math.min(...by), Math.max(...bx), Math.max(...by)];
          texts.push({ t, px: +(px * scaleOf(tm)).toFixed(2), box });
          x0 = Math.min(x0, box[0]); y0 = Math.min(y0, box[1]); x1 = Math.max(x1, box[2]); y1 = Math.max(y1, box[3]);
        }
        openText = null;
      }
      continue;
    }
    const top = stack[stack.length - 1], cur = a.transform ? mul(top, parseTransform(a.transform)) : top;
    if (tag === "g" || tag === "svg") { if (!selfClose) stack.push(cur); continue; }
    if (inDefs || a.opacity === "0" || a.display === "none" || a.visibility === "hidden") continue;
    const n = (k, d = 0) => (a[k] != null && a[k] !== "" ? Number(a[k]) : d);
    const sw = a.stroke && a.stroke !== "none" ? n("stroke-width", 1) / 2 : 0;
    if (tag === "rect") addBox(cur, n("x"), n("y"), n("x") + n("width"), n("y") + n("height"), sw);
    else if (tag === "circle") addBox(cur, n("cx") - n("r"), n("cy") - n("r"), n("cx") + n("r"), n("cy") + n("r"), sw);
    else if (tag === "ellipse") addBox(cur, n("cx") - n("rx"), n("cy") - n("ry"), n("cx") + n("rx"), n("cy") + n("ry"), sw);
    else if (tag === "line") { add(cur, n("x1"), n("y1"), sw); add(cur, n("x2"), n("y2"), sw); }
    else if (tag === "image") addBox(cur, n("x"), n("y"), n("x") + n("width"), n("y") + n("height"));
    else if (tag === "path") for (const [px, py] of pathPoints(a.d)) add(cur, px, py, sw);
    else if (tag === "polygon" || tag === "polyline") {
      const v = (a.points || "").match(NUM) || [];
      for (let k = 0; k + 1 < v.length; k += 2) add(cur, Number(v[k]), Number(v[k + 1]), sw);
    } else if (tag === "text" && !selfClose)
      openText = { m: cur, x: n("x"), y: n("y"), px: n("font-size", 16), anchor: a["text-anchor"] || "start", t: "" };
  }
  const box = Number.isFinite(x0) ? [x0, y0, x1, y1].map((v) => +v.toFixed(2)) : null;
  return { box, texts: texts.map((r) => ({ ...r, box: r.box.map((v) => +v.toFixed(2)) })) };
}
