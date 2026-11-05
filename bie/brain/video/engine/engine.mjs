// BIE's showing engine (Phase 1, agreement of 3 November 2026 §2.3): renders any frame of a show-spec
// (bie.show-spec/1, the v2 demo's spec.json format) in a plain browser page, on the same window API as the preview
// harness (window.__VIDEO__, setFrame, totalFrames, ready), so BIE's stills, MP4, chunked CI render and text audit
// all work unchanged. The engine owns: scenes, camera, element timelines (keys), enter/leave, persons with poses,
// holds, walks, shakes and nods, items (saanche, assets, groups), text styles with steps, arrows, marks, bubbles,
// panels, glows, the map, the kicker and the subtitles. Stage space is 1920×1080, scaled to the spec's width.
import { DRAWS, drawSaancha, markSvg } from "./draw.mjs";
import { POSES, LOOKS, drawPerson, handAtAngles } from "./people.mjs";
import { background, foreground } from "./backgrounds.mjs";
import MAP_LAND from "./map_land.json";

const FONT = "'Noto Sans', 'Noto Sans Devanagari', sans-serif";
const INK = "#2b2b33";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const ease = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };

// ---------------------------------------------------------------- timeline math (identical to the v2 builder's x_at)
function propAt(el, t, fields) {
  const st = {};
  for (const f of fields) st[f] = el[f] ?? (f === "s" ? (el.s ?? 1) : 0);
  for (const k of el.keys || []) {
    if (t <= k.t) break;
    const p = ease((t - k.t) / (k.d ?? 0.6));
    for (const f of fields) if (k[f] != null) st[f] += (k[f] - st[f]) * p;
  }
  return st;
}

function camAt(cam, t) {
  const st = { x: 960, y: 540, z: 1 };
  for (const k of cam || []) {
    if (t <= k.t) break;
    const p = ease((t - k.t) / (k.d ?? 1.0));
    for (const f of ["x", "y", "z"]) if (k[f] != null) st[f] += (k[f] - st[f]) * p;
  }
  return st;
}

function enterAlphaScale(el, t, sceneT0) {
  const t0 = el.t0 ?? sceneT0, mode = el.enter ?? "pop";
  let a = 1, s = 1;
  if (mode === "pop") {
    const k = Math.min(1, (t - t0) / 0.3);
    a = Math.min(1, k * 2.5);
    s = ease(k) * (1 + 0.16 * Math.sin(Math.min(1, k) * Math.PI));
  } else if (mode === "fade") a = Math.min(1, (t - t0) / 0.4);
  if (el.t1 != null && t > el.t1) a *= Math.max(0, 1 - (t - el.t1) / 0.25);
  if (el.alpha != null) a *= el.alpha;
  return [a, s];
}

const visible = (el, t, sceneT0) => t >= (el.t0 ?? sceneT0) && (el.t1 == null || t <= el.t1 + 0.25);

// ---------------------------------------------------------------- text
let ctx = null;
function measure(text, size, weight = 700) {
  if (!ctx) ctx = document.createElement("canvas").getContext("2d");
  ctx.font = `${weight} ${size}px ${FONT.replace(/'/g, "")}`;
  return ctx.measureText(text).width;
}

function wrap(text, size, weight, maxW) {
  if (!maxW) return [String(text)];
  const words = String(text).split(/\s+/), lines = [];
  let cur = "";
  for (const w of words) {
    const next = cur ? cur + " " + w : w;
    if (cur && measure(next, size, weight) > maxW) { lines.push(cur); cur = w; } else cur = next;
  }
  if (cur) lines.push(cur);
  return lines;
}

const TEXT_STYLES = {
  tag: { weight: 800, pad: [0.62, 0.42], bg: "#ffffff", stroke: INK, sw: 3, radius: 0.35, fill: INK },
  pill: { weight: 800, pad: [0.72, 0.42], bg: INK, radius: 999, fill: "#ffffff" },
  plain: { weight: 700, fill: INK },
  title: { weight: 800, fill: INK, halo: "#f7f1e5" },
};

function textSvg(el, t) {
  let text = el.text;
  let stepT = null;
  for (const s of el.steps || []) if (t >= s.t) { text = s.text; stepT = s.t; }
  const style = TEXT_STYLES[el.style || "tag"] || TEXT_STYLES.plain;
  const size = el.size || 46, weight = style.weight;
  const lines = wrap(text, size, weight, el.w);
  const lineH = size * 1.28;
  const wMax = Math.max(...lines.map((l) => measure(l, size, weight)));
  let out = "";
  const fill = el.fill || style.fill;
  if (style.bg) {
    const bw = wMax + size * (style.pad?.[0] ?? 0.6) * 2, bh = lines.length * lineH + size * (style.pad?.[1] ?? 0.4) * 2;
    const r = style.radius === 999 ? bh / 2 : size * (style.radius ?? 0.3);
    out += `<rect x="${-bw / 2}" y="${-bh / 2}" width="${bw}" height="${bh}" rx="${r}" fill="${el.bg || style.bg}"` +
      (style.stroke ? ` stroke="${style.stroke}" stroke-width="${style.sw}"` : "") + `/>`;
  }
  const y0 = -((lines.length - 1) * lineH) / 2;
  const halo = style.halo ? ` paint-order="stroke" stroke="${style.halo}" stroke-width="${size * 0.22}" stroke-linejoin="round"` : "";
  lines.forEach((l, i) => {
    out += `<text x="0" y="${y0 + i * lineH + size * 0.34}" font-family=${JSON.stringify(FONT)} font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="middle"${halo}>${esc(l)}</text>`;
  });
  const popK = stepT != null ? Math.min(1, (t - stepT) / 0.25) : 1;
  const ps = 1 + 0.16 * Math.sin(popK * Math.PI);
  return `<g class="bie-plan" transform="scale(${ps.toFixed(3)})">${out}</g>`;   // bie-plan: words the plan wrote (the text audit gate)
}

// ---------------------------------------------------------------- items (saanche, assets, groups, mini persons)
function itemSvg(el, t, assets) {
  if (el.group) {
    return el.group.map((m) => {
      const inner = itemSvg(m, t, assets);
      return `<g transform="translate(${m.x || 0},${m.y || 0}) scale(${m.s ?? 1})">${inner}</g>`;
    }).join("");
  }
  if (el.asset) {
    const w = el.w || 160, href = (assets && assets[el.asset]) || `assets/${el.asset}.png`;
    return `<image href="${esc(href)}" x="${-w / 2}" y="${-w / 2}" width="${w}" height="${w}"/>`;
  }
  if (el.draw === "__person__")
    return `<g transform="translate(0,${(el.h || 200) / 2})">${drawPerson({ look: el.look, h: el.h || 200, facing: el.facing || 1, arms: el.pose || "stand", expr: el.expr || "smile" })}</g>`;
  if (el.draw === "mark") return markSvg(el.p?.kind || "tick", el.p?.w || 100, el.p?.color, 1);
  if (el.draw) {
    const d = DRAWS[el.draw];
    let p = el.p || {}, last = el.t0 ?? 0;
    for (const s of el.steps || []) if (t >= s.t && s.p) { p = { ...p, ...s.p }; last = s.t; }   // a content change on its cue word
    // _t: seconds since the thing appeared (a process keeps moving); _s: since its last step (a graph line drawn on the word)
    const svg = drawSaancha(el.draw, { ...p, _t: Math.max(0, t - (el.t0 ?? 0)), _s: Math.max(0, t - last) });
    if (d && d.anchor === "bottom") return svg;      // stands on its origin like a person
    return svg;
  }
  if (el.text != null) return textSvg(el, t);
  return "";
}

function itemAnim(el, t) {
  let extra = "", s = 1;
  if (el.anim === "t") extra = ` translate(${(Math.sin(t * 6.3) * 3).toFixed(1)},${(Math.cos(t * 7.1) * 2).toFixed(1)})`;
  if (el.anim === "p" && el.pt != null && t >= el.pt && t <= el.pt + (el.pd || 1)) {
    const k = (t - el.pt) / (el.pd || 1);
    s = 1 + 0.12 * Math.sin(k * Math.PI * 3) * (1 - k * 0.6);
  }
  return [extra, s];
}

// ---------------------------------------------------------------- persons
function blendPose(el, t) {
  const changes = [{ t: -1e9, pose: el.pose || "stand" }, ...(el.poses || [])].sort((a, b) => a.t - b.t);
  let cur = changes[0], prev = changes[0];
  for (const c of changes) if (t >= c.t) { prev = cur; cur = c; }
  const a = POSES[cur.pose] || POSES.stand, b = POSES[prev.pose] || POSES.stand;
  const k = ease((t - cur.t) / 0.28);
  return a.map((v, i) => b[i] + (v - b[i]) * k);
}

function lastAt(list, t, field) {
  let v = null;
  for (const e of list || []) if (t >= e.t) v = field ? e[field] : e;
  return v;
}

function personSvg(el, t, assets) {
  const H = el.h || 440;
  const pos = propAt(el, t, ["x", "y"]);
  let facing = el.facing ?? 1;
  for (const f of el.facings || []) if (t >= f.t) facing = f.s;
  const arms = blendPose(el, t);
  const expr = lastAt(el.exprs, t, "expr") || el.expr || "smile";
  let walkPhase = null;
  for (const w of el.walks || []) if (t >= w.t && t <= w.t + (w.d ?? 1.4)) walkPhase = ((t - w.t) / 0.45) % 1;
  let headDx = 0, headDy = 0;
  for (const sh of el.shakes || []) if (t >= sh.t && t <= sh.t + (sh.d ?? 1)) headDx = Math.sin((t - sh.t) * 22) * 0.045 * H * (1 - (t - sh.t) / ((sh.d ?? 1) * 1.3));
  for (const nd of el.nods || []) if (t >= nd.t && t <= nd.t + (nd.d ?? 1)) headDy = Math.abs(Math.sin((t - nd.t) * 14)) * 0.03 * H;
  const held = lastAt(el.holds, t);
  const body = drawPerson({ look: el.look, h: H, facing, arms, expr, walkPhase, headDx, headDy });
  let heldSvg = "";
  if (held && held.item) {
    const bob = walkPhase == null ? 0 : -Math.abs(Math.sin(walkPhase * Math.PI * 2)) * 0.018 * H;
    const [hx, hy] = handAtAngles(H, 1, arms[0], arms[1]);
    const spec = held.item;
    heldSvg = `<g transform="translate(${(hx * facing).toFixed(1)},${(hy + bob).toFixed(1)})"><g transform="translate(${spec.x || 0},${spec.y || 0}) scale(${spec.s ?? 1})">${itemSvg(spec, t, assets)}</g></g>`;
  }
  const shadow = `<ellipse cx="0" cy="0" rx="${0.22 * H}" ry="${0.034 * H}" fill="#2b2017" opacity="0.13"/>`;
  return { svg: `<g transform="translate(${pos.x.toFixed(1)},${pos.y.toFixed(1)})">${shadow}${body}${heldSvg}</g>`, pos, facing, H };
}

// ---------------------------------------------------------------- arrows, bubbles, map
function arrowSvg(el, t) {
  const { x1, y1, x2, y2 } = el, bend = el.bend || 0, w = el.width || 8, color = el.color || INK;
  const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1;
  const mx = (x1 + x2) / 2 - (dy / len) * bend * len, my = (y1 + y2) / 2 + (dx / len) * bend * len;
  const k = el.dashed ? 1 : Math.min(1, (t - (el.t0 ?? 0)) / 0.45);
  const tx = mx + (x2 - mx) * 0.96, ty = my + (y2 - my) * 0.96;
  const ang = Math.atan2(y2 - ty, x2 - tx) * 180 / Math.PI;
  const head = k > 0.92 ? `<g transform="translate(${x2},${y2}) rotate(${ang.toFixed(1)})"><path d="M0 0 L${-w * 2.6} ${-w * 1.5} L${-w * 2.6} ${w * 1.5} Z" fill="${color}"/></g>` : "";
  const dash = el.dashed ? ` stroke-dasharray="${w * 2.2} ${w * 1.8}"` : ` stroke-dasharray="${len * 1.25}" stroke-dashoffset="${(len * 1.25 * (1 - k)).toFixed(1)}"`;
  return `<path d="M${x1} ${y1} Q${mx.toFixed(1)} ${my.toFixed(1)} ${x2} ${y2}" stroke="${color}" stroke-width="${w}" fill="none" stroke-linecap="round"${dash}/>` + head;
}

function bubbleSvg(el, t, persons, assets) {
  const of = el.of != null ? persons[el.of] : null;
  const bx = (of ? of.pos.x : el.x || 0) + (el.dx ?? 200), by = (of ? of.pos.y : el.y || 0) + (el.dy ?? -560);
  const w = el.w || 260, h = w * 0.74;
  const tail = el.tail ?? -1;
  const k = Math.min(1, (t - (el.t0 ?? 0)) / 0.3);
  let shape;
  if ((el.kind2 || "think") === "think") {
    shape = `<ellipse rx="${w / 2}" ry="${h / 2}" fill="#ffffff" stroke="${INK}" stroke-width="4"/>` +
      `<circle cx="${tail * w * 0.34}" cy="${h * 0.62}" r="${w * 0.055}" fill="#ffffff" stroke="${INK}" stroke-width="3.4"/>` +
      `<circle cx="${tail * w * 0.46}" cy="${h * 0.82}" r="${w * 0.035}" fill="#ffffff" stroke="${INK}" stroke-width="3"/>`;
  } else {
    shape = `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${w * 0.1}" fill="#ffffff" stroke="${INK}" stroke-width="4"/>` +
      `<path d="M${tail * w * 0.2} ${h / 2 - 2} L${tail * w * 0.34} ${h * 0.82} L${tail * w * 0.34} ${h / 2 - 2} Z" fill="#ffffff" stroke="${INK}" stroke-width="4" stroke-linejoin="round"/>`;
  }
  const content = el.content ? `<g transform="translate(0,${h * 0.06})">${itemSvg(dictFit(el.content, w), t, assets)}</g>` : "";
  return `<g transform="translate(${bx.toFixed(1)},${by.toFixed(1)}) scale(${ease(k).toFixed(3)})">${shape}${content}</g>`;
}

function dictFit(spec, w) {
  if (spec.text != null && !spec.style) return { ...spec, style: "plain" };
  return spec;
}

function mapSvg() {
  const land = MAP_LAND.paths.map((d) => `<path d="${d}" fill="#e0d2a4" stroke="#bfa871" stroke-width="2.5"/>`).join("");
  return `<rect width="1920" height="1080" fill="#f3e7c9"/>` + land;
}

// ---------------------------------------------------------------- the frame
function sceneAt(spec, t) {
  const scenes = spec.scenes || [];
  for (const sc of scenes) if (t >= sc.t0 && t < sc.t1) return sc;
  return t >= (spec.duration || 0) ? scenes[scenes.length - 1] : scenes[0];
}

function renderFrame(spec, t) {
  const sc = sceneAt(spec, t);
  if (!sc) return "";
  const persons = {};
  const parts = [];
  const els = [...(sc.els || [])].map((el, i) => [el, i]).sort((a, b) => (a[0].z ?? 10) - (b[0].z ?? 10) || a[1] - b[1]);
  for (const [el] of els) {
    if (!visible(el, t, sc.t0)) continue;
    const [alpha, popS] = enterAlphaScale(el, t, sc.t0);
    if (alpha <= 0.004) continue;
    const kind = el.kind || (el.draw || el.asset || el.group ? "item" : el.text != null ? "text" : "");
    let svg = "";
    if (kind === "person") {
      const p = personSvg(el, t, spec.assets);
      if (el.id) persons[el.id] = p;
      svg = `<g opacity="${alpha.toFixed(3)}">${p.svg}</g>`;
    } else if (kind === "item" || kind === "text") {
      const pos = propAt(el, t, ["x", "y", "s", "r"]);
      const [jitter, pulse] = itemAnim(el, t);
      const d = el.draw ? DRAWS[el.draw] : null;
      const shW = el.p?.w || el.w || el.h || 120;
      const sh = el.draw === "__person__"
        ? `<ellipse cx="0" cy="${(el.h || 200) / 2}" rx="${(el.h || 200) * 0.22}" ry="${(el.h || 200) * 0.034}" fill="#2b2017" opacity="0.12"/>`
        : d && d.anchor === "bottom" ? `<ellipse cx="0" cy="0" rx="${shW * 0.42}" ry="${shW * 0.05}" fill="#2b2017" opacity="0.1"/>` : "";
      const inner = kind === "text" ? textSvg(el, t) : itemSvg(el, t, spec.assets);
      const scale = ((pos.s || 1) * popS * pulse).toFixed(3);
      svg = `<g transform="translate(${pos.x.toFixed(1)},${pos.y.toFixed(1)})${jitter} scale(${scale}) rotate(${(pos.r || 0).toFixed(1)})" opacity="${alpha.toFixed(3)}">${sh}${inner}</g>`;
    } else if (kind === "mark") {
      const k = Math.min(1, (t - (el.t0 ?? sc.t0)) / 0.45);
      svg = `<g transform="translate(${el.x},${el.y})" opacity="${alpha.toFixed(3)}">${markSvg(el.mark, el.w || 120, el.color, k)}</g>`;
    } else if (kind === "arrow") {
      svg = `<g opacity="${alpha.toFixed(3)}">${arrowSvg(el, t)}</g>`;
    } else if (kind === "bubble") {
      svg = `<g opacity="${alpha.toFixed(3)}">${bubbleSvg(el, t, persons, spec.assets)}</g>`;
    } else if (kind === "rect") {
      const shadow = el.shadow === false ? "" : `<rect x="${el.x - el.w / 2 + 6}" y="${el.y - el.h / 2 + 12}" width="${el.w}" height="${el.h}" rx="20" fill="#2b2017" opacity="0.1"/>`;
      svg = `<g opacity="${alpha.toFixed(3)}">${shadow}<rect x="${el.x - el.w / 2}" y="${el.y - el.h / 2}" width="${el.w}" height="${el.h}" rx="20" fill="${el.fill || "#ffffff"}"` +
        (el.stroke ? ` stroke="${el.stroke}" stroke-width="${el.sw || 4}"` : "") + `/></g>`;
    } else if (kind === "glow") {
      const pul = 1 + 0.1 * Math.sin(t * 3.4);
      svg = `<circle cx="${el.x}" cy="${el.y}" r="${(el.w / 2) * pul}" fill="${el.fill || "#ffd95a"}" opacity="${(0.3 * alpha).toFixed(3)}"/>` +
        `<circle cx="${el.x}" cy="${el.y}" r="${(el.w / 3.2) * pul}" fill="${el.fill || "#ffd95a"}" opacity="${(0.42 * alpha).toFixed(3)}"/>`;
    } else if (kind === "map") {
      svg = `<g opacity="${alpha.toFixed(3)}">${mapSvg()}</g>`;
    }
    parts.push(svg);
  }
  const cam = camAt(sc.cam, t);
  const world = `<g transform="translate(960,540) scale(${cam.z.toFixed(4)}) translate(${(-cam.x).toFixed(1)},${(-cam.y).toFixed(1)})">` +
    background(sc.bg || "paper") + parts.join("") + foreground(sc.fg) + `</g>`;
  // screen space: kicker + subtitles
  let hud = "";
  if (sc.kicker) {
    const kw = measure(sc.kicker, 36, 800) + 52;             // 36 px: the readable floor on the 1080p frame (CV-17)
    hud += `<g class="bie-plan" transform="translate(${46 + kw / 2},74)"><rect x="${-kw / 2}" y="-33" width="${kw}" height="66" rx="33" fill="${INK}" opacity="0.88"/>` +
      `<text y="13" font-family=${JSON.stringify(FONT)} font-size="36" font-weight="800" fill="#ffffff" text-anchor="middle">${esc(sc.kicker)}</text></g>`;
  }
  const sub = (spec.subs || []).find((s) => t >= s.t0 && t < s.t1);
  if (sub) {
    const size = 36, lines = wrap(sub.text, size, 700, 1660);
    const lh = size * 1.3, bh = lines.length * lh + 26, bw = Math.max(...lines.map((l) => measure(l, size, 700))) + 64;
    const by = 1080 - 28 - bh;
    hud += `<g class="bie-caption" transform="translate(960,${by + bh / 2})"><rect x="${-bw / 2}" y="${-bh / 2}" width="${bw}" height="${bh}" rx="16" fill="#12141c" opacity="0.86"/>` +
      lines.map((l, i) => `<text y="${-((lines.length - 1) * lh) / 2 + i * lh + size * 0.34}" font-family=${JSON.stringify(FONT)} font-size="${size}" font-weight="700" fill="#ffffff" text-anchor="middle">${esc(l)}</text>`).join("") + `</g>`;
  }
  return world + hud;
}

// ---------------------------------------------------------------- window API
const svgRoot = () => {
  const spec = window.__VIDEO__ || { width: 1280, height: 720 };
  let el = document.getElementById("stage");
  if (!el) {
    el = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    el.id = "stage";
    document.getElementById("root").appendChild(el);
  }
  el.setAttribute("width", spec.width);
  el.setAttribute("height", spec.height);
  el.setAttribute("viewBox", "0 0 1920 1080");
  document.body.style.cssText = `margin:0;width:${spec.width}px;height:${spec.height}px;overflow:hidden;background:#000`;
  const root = document.getElementById("root");
  root.style.cssText = `position:relative;width:${spec.width}px;height:${spec.height}px`;
  return el;
};

const raf = () => new Promise((r) => requestAnimationFrame(() => r()));
window.pendingRenders = () => [];
window.totalFrames = () => {
  const spec = window.__VIDEO__;
  return spec ? Math.round((spec.duration || 0) * (spec.fps || 30)) : 0;
};
let fontsReady = false;
window.setFrame = async (n) => {
  const spec = window.__VIDEO__;
  const el = svgRoot();
  if (!fontsReady) { try { await document.fonts.ready; } catch { } fontsReady = true; }
  el.innerHTML = renderFrame(spec, n / (spec.fps || 30));
  await raf(); await raf();
  const images = Array.from(el.querySelectorAll("image"));
  await Promise.all(images.map((img) => new Promise((r) => {
    const href = img.getAttribute("href");
    const probe = new Image();
    probe.onload = probe.onerror = r;
    probe.src = href;
  })));
  await raf();
};
window.ready = true;

export const _test = { propAt, camAt, wrap, renderFrame, sceneAt };
