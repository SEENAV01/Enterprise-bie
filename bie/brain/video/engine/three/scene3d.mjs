// The 3D layer's pure core (no three.js, no DOM): which kinds exist, a model element's parameters and camera at any
// time, the camera's projection, and where a model's spots, box and zones land on the 1920x1080 stage. The engine's
// layer (layer3d.mjs) draws exactly what frameModel describes; the scene-plan compiler asks tools/model3d_measure.mjs
// (this file in Node) for spots, boxes and zones, so the plan, the box rule and the frame never disagree.
//
// A model element of a show-spec (compiled by bie/brain/video/showplan.py):
//   { kind: "model3d", id, model: "factory", p: {...}, steps: [{t, p, d?}], cam3d: [{t, d?, angle?, height?, dist?,
//     tx?, ty?, tz?, fov?, spin?}], x, y, w, h, s, keys, z, t0, t1, enter, place: true for a scene's 3D world }
// A step's numbers glide over d seconds (default 0.8; 0 jumps), other values change on the word; camera keys glide
// over d seconds (default 1.2) like the 2D camera; spin turns the camera on, degrees per second, from its key.
import MANIFEST from "./models3d.json" with { type: "json" };
import { KINDS as PLACES } from "./kinds_place.mjs";
import { KINDS as MATHS } from "./kinds_math.mjs";

export const KINDS = { ...PLACES, ...MATHS };
export const STAGE_W = 1920, STAGE_H = 1080;
export const CAM_FIELDS = ["angle", "height", "dist", "tx", "ty", "tz", "fov"];
const ease = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
const R4 = (v) => Math.round(v * 10000) / 10000;

export function manifestEntry(kind) {
  return MANIFEST.saanche[kind] || null;
}

export function defaults(kind) {
  const e = manifestEntry(kind);
  return e ? Object.fromEntries(Object.entries(e.params).map(([k, v]) => [k, v.default])) : {};
}

/** The parameters at time ``t``: defaults, then p, then every step up to t (numbers glide over the step's d). */
export function paramsAt(el, t) {
  const cur = { ...defaults(el.model), ...(el.p || {}) };
  let last = el.t0 ?? 0;
  const steps = [...(el.steps || [])].filter((s) => s && s.t != null).sort((a, b) => a.t - b.t);
  for (const st of steps) {
    if (t < st.t) break;
    const d = st.d ?? 0.8, k = d > 0 ? ease((t - st.t) / d) : 1;
    for (const [key, v] of Object.entries(st.p || {})) {
      if (typeof v === "number" && typeof cur[key] === "number" && k < 1) cur[key] += (v - cur[key]) * k;
      else cur[key] = v;
    }
    last = st.t;
  }
  return { p: cur, last };
}

/** The 3D camera at ``t``: the kind's camera, the element's base camera, then its keys (eased), plus spin. */
export function camAt(el, t) {
  const K = KINDS[el.model];
  const st = { ...(K ? K.camera : { angle: 30, height: 6, dist: 12, tx: 0, ty: 0, tz: 0, fov: 40 }) };
  const keys = [...(el.cam3d || [])].filter((k) => k && k.t != null).sort((a, b) => a.t - b.t);
  let spin = 0, spinFrom = 0, turned = 0;
  for (const k of keys) {
    if (t <= k.t) break;
    const p = ease((t - k.t) / (k.d ?? 1.2));
    for (const f of CAM_FIELDS) if (k[f] != null) st[f] += (k[f] - st[f]) * p;
    if (k.spin != null) { turned += spin * (k.t - spinFrom); spin = k.spin; spinFrom = k.t; }
  }
  st.angle += turned + spin * Math.max(0, t - spinFrom);
  return st;
}

/** Eye, target, up and field of view of a camera state (the up vector never degenerates, even straight down). */
export function view(cam) {
  const a = (cam.angle * Math.PI) / 180, d = Math.max(0, cam.dist), h = cam.height;
  const target = [cam.tx, cam.ty, cam.tz];
  const eye = [cam.tx + Math.sin(a) * d, cam.ty + h, cam.tz + Math.cos(a) * d];
  const pitch = Math.atan2(h, d);
  const up = [-Math.sin(pitch) * Math.sin(a), Math.cos(pitch), -Math.sin(pitch) * Math.cos(a)];
  const r = Math.max(0.5, Math.hypot(d, h));
  return { eye, target, up, fov: Math.max(5, Math.min(120, cam.fov)), near: Math.max(0.05, r * 0.01), far: r * 30 + 300 };
}

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

/** A projector for one view onto a stage rect [x0, y0, w, h]: point -> {x, y, front} (three.js's lookAt and perspective). */
export function projector(v, rect) {
  const z = unit(sub(v.eye, v.target)), x = unit(cross(v.up, z)), y = cross(z, x);
  const f = 1 / Math.tan((v.fov * Math.PI) / 360), aspect = rect[2] / rect[3];
  return (pt) => {
    const d = sub(pt, v.eye), cx = dot(x, d), cy = dot(y, d), cz = dot(z, d);
    const depth = -cz, front = depth > v.near;
    const dd = Math.max(1e-6, Math.abs(depth));
    const nx = (f / aspect) * cx / dd, ny = f * cy / dd;
    return { x: rect[0] + ((nx + 1) / 2) * rect[2], y: rect[1] + ((1 - ny) / 2) * rect[3], front };
  };
}

/** Where an element sits on the stage at ``t`` (engine.mjs propAt for x, y, s), as [x0, y0, w, h]. */
export function rectAt(el, t) {
  const st = { x: el.x ?? 960, y: el.y ?? 540, s: el.s ?? 1 };
  for (const k of el.keys || []) {
    if (t <= k.t) break;
    const p = ease((t - k.t) / (k.d ?? 0.6));
    for (const f of ["x", "y", "s"]) if (k[f] != null) st[f] += (k[f] - st[f]) * p;
  }
  const w = (el.w ?? STAGE_W) * st.s, h = (el.h ?? STAGE_H) * st.s;
  return [st.x - w / 2, st.y - h / 2, w, h];
}

/** Everything the layer needs to draw one model element at show time ``t``. */
export function frameModel(el, t) {
  const K = KINDS[el.model];
  if (!K) throw new Error(`BIE_3D_KIND: no 3D model '${el.model}' (models: ${Object.keys(KINDS).join(", ")})`);
  const { p, last } = paramsAt(el, t);
  const t0 = el.t0 ?? 0;
  const ctx = { t: Math.max(0, t - t0), s: Math.max(0, t - last), place: !!el.place };
  const d = K.fn(p, ctx);
  const cam = camAt(el, t);
  return { nodes: d.nodes, spots: d.spots || {}, zones: d.zones || {}, env: d.env || {}, cam, view: view(cam), p, place: !!el.place };
}

// ---------------------------------------------------------------- bounds of a node (for the box rule)
function halfOf(nd) {
  const a = nd.a;
  switch (nd.g) {
    case "box": return [[-a[0] / 2, -a[1] / 2, -a[2] / 2], [a[0] / 2, a[1] / 2, a[2] / 2]];
    case "cyl": { const r = Math.max(a[0], a[1]); return [[-r, -a[2] / 2, -r], [r, a[2] / 2, r]]; }
    case "prism": return [[-a[0], -a[1] / 2, -a[0]], [a[0], a[1] / 2, a[0]]];
    case "cone": return [[-a[0], -a[1] / 2, -a[0]], [a[0], a[1] / 2, a[0]]];
    case "sphere": case "ico": case "globe": return [[-a[0], -a[0], -a[0]], [a[0], a[0], a[0]]];
    case "torus": { const r = a[0] + a[1]; return [[-r, -r, -a[1]], [r, r, a[1]]]; }
    case "surface": return [[0, 0, -a.size], [a.size, a.h, 0]];
    case "tube": {
      const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
      for (const q of a.pts) for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], q[i] - a.r); hi[i] = Math.max(hi[i], q[i] + a.r); }
      return [lo, hi];
    }
    default: return null;
  }
}

/** The 8 corners of a node's box in model space (scale, turn YXZ, move: three.js's order). */
export function corners(nd) {
  const hb = halfOf(nd);
  if (!hb) return [];
  const [lo, hi] = hb, s = nd.s || [1, 1, 1], r = nd.r || [0, 0, 0], p = nd.p || [0, 0, 0];
  const [cx, sx] = [Math.cos(r[0]), Math.sin(r[0])], [cy, sy] = [Math.cos(r[1]), Math.sin(r[1])], [cz, sz] = [Math.cos(r[2]), Math.sin(r[2])];
  const out = [];
  for (const X of [lo[0], hi[0]]) for (const Y of [lo[1], hi[1]]) for (const Z of [lo[2], hi[2]]) {
    let x = X * s[0], y = Y * s[1], z = Z * s[2];
    [x, y] = [x * cz - y * sz, x * sz + y * cz];                 // Rz
    [y, z] = [y * cx - z * sx, y * sx + z * cx];                 // Rx
    [x, z] = [x * cy + z * sy, -x * sy + z * cy];                // Ry (YXZ: R = Ry Rx Rz)
    out.push([x + p[0], y + p[1], z + p[2]]);
  }
  return out;
}

const spotPoint = (v) => (Array.isArray(v) ? { p: v } : v);

/** The stage positions of a model element at ``t``: spots {name: {x, y, front}}, its box [x0, y0, x1, y1] (the model's
 * drawn parts, not its ground or sky) and its zones [{name, keep, box}]. */
export function measure(el, t) {
  const fm = frameModel(el, t);
  const rect = rectAt(el, t), P = projector(fm.view, rect);
  const spots = {};
  for (const [name, raw] of Object.entries(fm.spots)) {
    const sp = spotPoint(raw), q = P(sp.p);
    let front = q.front;
    if (front && sp.n) front = dot(sp.n, unit(sub(fm.view.eye, sp.p))) > 0.08;
    spots[name] = { x: R4(q.x), y: R4(q.y), front };
  }
  const bbox = (pts) => {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, any = false;
    for (const pt of pts) {
      const q = P(pt);
      if (!q.front) continue;
      any = true;
      x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.x); y1 = Math.max(y1, q.y);
    }
    if (!any) return null;
    const cl = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
    return [cl(x0, rect[0], rect[0] + rect[2]), cl(y0, rect[1], rect[1] + rect[3]), cl(x1, rect[0], rect[0] + rect[2]), cl(y1, rect[1], rect[1] + rect[3])].map(R4);
  };
  const pts = [];
  for (const nd of fm.nodes) if (!nd.bg && (nd.o ?? 1) > 0.05) pts.push(...corners(nd));
  const zones = [];
  for (const [name, z] of Object.entries(fm.zones)) {
    const [[a, b, c], [d, e, f]] = z.box, zb = bbox([[a, b, c], [d, b, c], [a, e, c], [d, e, c], [a, b, f], [d, b, f], [a, e, f], [d, e, f]]);
    if (zb) zones.push({ name, keep: z.keep, box: zb });
  }
  return { spots, box: bbox(pts), zones, rect: rect.map(R4) };
}

/** The problems of a model's parameters that a manifest's types cannot see (a globe's region names). */
export function check(model, p) {
  const K = KINDS[model];
  if (!K) return [`no 3D model '${model}' (models: ${Object.keys(KINDS).join(", ")})`];
  return K.check ? K.check({ ...defaults(model), ...(p || {}) }) : [];
}
