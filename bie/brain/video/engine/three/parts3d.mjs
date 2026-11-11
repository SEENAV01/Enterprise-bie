// The 3D layer's building parts (Navin, 5 November 2026: "3d models objects duniya process bna sakte ho aise format mein
// jinme bie scene plan ke hisab se modify karke use kar sake"). Pure code, no three.js: a 3D model is described as a flat
// list of nodes, each a primitive with its place, turn, size and colour, so the same parameters and the same time always
// give the same description (tests read it in Node without WebGL), and layer3d.mjs turns it into three.js meshes.
//
// A node: { g, a, p: [x, y, z], r: [rx, ry, rz] (radians, Euler order YXZ), s: [sx, sy, sz], c: "#rrggbb",
//           e: glow 0..2, o: opacity 0..1, m: "flat" | "smooth" | "basic" | "vcol", bg: true (ground, sky: not part of
//           the model's box), n: name }
// g / a: box [w, h, d] | cyl [rTop, rBottom, h, segments] | cone [r, h, segments] | sphere [r, wSeg, hSeg] |
//        ico [r, detail] | torus [R, tube, radialSeg, tubularSeg] (in its XY plane) | tube {pts, r, seg} (a path) |
//        surface {fn, ...} (a height field) | globe [r] (the land map on a sphere) | prism [r, h] (a triangular prism)
// Units are metres; the ground is y = 0; +x right, +y up, +z toward the default camera.

export const PAL = {
  ink: "#2b2b33", paper: "#f7f1e5", red: "#e5484d", blue: "#3a7bd5", green: "#2fa35b", orange: "#f29f05",
  purple: "#7b61ff", pink: "#e2558f", teal: "#2a9d8f", yellow: "#f2c14e", gold: "#f3cf6a", brown: "#8a5a2b",
  slate: "#4a5568", grey: "#9aa5b1", light: "#c7ccd3", sky: "#cfe8f5", sea: "#4f8fc0", ground: "#b9b2a4",
  grass: "#9cc98a", soil: "#8a5a2b", skin: ["#c68a5c", "#d39a6a", "#b97c50", "#a8714a"],
  shirts: ["#3a7bd5", "#e5484d", "#2fa35b", "#f29f05", "#7b61ff", "#e2558f", "#2a9d8f"],
  boxes: ["#e5484d", "#3a7bd5", "#2fa35b", "#f29f05", "#7b61ff", "#2a9d8f"],
};

export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const clamp01 = (v) => clamp(v, 0, 1);
export const ease = (x) => { x = clamp01(x); return x * x * (3 - 2 * x); };
export const lerp = (a, b, k) => a + (b - a) * k;
export const num = (v, d) => (typeof v === "number" && Number.isFinite(v) ? v : d);
export const frac = (v) => v - Math.floor(v);
export const listOf = (s) => String(s ?? "").split(";").map((x) => x.trim()).filter(Boolean);

/** A seeded random stream (mulberry32): the same seed, the same numbers, on every machine. */
export function rng(seed = 1) {
  let a = (Math.floor(seed) * 2654435761) >>> 0 || 1;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mix(c1, c2, k) {
  const a = parseInt(c1.slice(1), 16), b = parseInt(c2.slice(1), 16);
  const ch = (sh) => Math.round(lerp((a >> sh) & 255, (b >> sh) & 255, clamp01(k)));
  return `#${((ch(16) << 16) | (ch(8) << 8) | ch(0)).toString(16).padStart(6, "0")}`;
}
export const shade = (c, f) => mix("#000000", c, f);

const R3 = (v) => Math.round(v * 1000) / 1000;
const vec = (v, d) => (Array.isArray(v) ? v.map(R3) : [R3(v ?? d), R3(v ?? d), R3(v ?? d)]);

/** One primitive node. ``o`` takes r (turn), s (scale), e (glow), o (opacity), m (material), bg, n. */
export function node(g, a, p, c, o = {}) {
  const out = { g, a, p: vec(p, 0), c };
  if (o.r) out.r = vec(o.r, 0);
  if (o.s != null) out.s = vec(o.s, 1);
  if (o.e) out.e = R3(o.e);
  if (o.o != null && o.o < 1) out.o = R3(Math.max(0, o.o));
  if (o.m) out.m = o.m;
  if (o.bg) out.bg = true;
  if (o.n) out.n = o.n;
  return out;
}
export const box = (w, h, d, p, c, o) => node("box", [R3(w), R3(h), R3(d)], p, c, o);
export const cyl = (rt, rb, h, p, c, o = {}) => node("cyl", [R3(rt), R3(rb), R3(h), o.seg || 12], p, c, o);
export const cone = (r, h, p, c, o = {}) => node("cone", [R3(r), R3(h), o.seg || 8], p, c, o);
export const sphere = (r, p, c, o = {}) => node("sphere", [R3(r), o.seg || 16, Math.max(6, Math.round((o.seg || 16) * 0.7))], p, c, { m: "smooth", ...o });
export const ico = (r, p, c, o = {}) => node("ico", [R3(r), o.detail ?? 0], p, c, o);
export const torus = (R, tube, p, c, o = {}) => node("torus", [R3(R), R3(tube), o.seg || 8, o.tseg || 32], p, c, o);
export const prism = (r, h, p, c, o) => node("prism", [R3(r), R3(h)], p, c, o);
export function tube(pts, r, c, o = {}) {
  return node("tube", { pts: pts.map((q) => q.map(R3)), r: R3(r), seg: o.seg || Math.min(160, pts.length * 2) }, [0, 0, 0], c, o);
}

/** Children placed as one unit: moved to ``p``, turned ``ry`` about the vertical, scaled ``s`` (uniform). */
export function group(nodes, { p = [0, 0, 0], ry = 0, s = 1 } = {}) {
  const c = Math.cos(ry), sn = Math.sin(ry);
  return nodes.map((nd) => {
    const [x, y, z] = nd.p;
    const out = { ...nd, p: [R3(p[0] + s * (x * c + z * sn)), R3(p[1] + s * y), R3(p[2] + s * (-x * sn + z * c))] };
    if (ry) out.r = [nd.r ? nd.r[0] : 0, R3((nd.r ? nd.r[1] : 0) + ry), nd.r ? nd.r[2] : 0];
    if (s !== 1) out.s = (nd.s || [1, 1, 1]).map((v) => R3(v * s));
    if (nd.g === "tube") out.a = { ...nd.a, pts: nd.a.pts.map(([px, py, pz]) => [R3(p[0] + s * (px * c + pz * sn)), R3(p[1] + s * py), R3(p[2] + s * (-px * sn + pz * c))]), r: R3(nd.a.r * s) };
    if (nd.g === "tube") out.p = [0, 0, 0];
    return out;
  });
}
/** A point moved like ``group`` moves its children. */
export function place(pt, { p = [0, 0, 0], ry = 0, s = 1 } = {}) {
  const c = Math.cos(ry), sn = Math.sin(ry), [x, y, z] = pt;
  return [p[0] + s * (x * c + z * sn), p[1] + s * y, p[2] + s * (-x * sn + z * c)];
}

/** A soft round shadow on the ground under a thing (the flat 2D saanche's shadow, in 3D). */
export const shadow = (x, z, r, o = 0.16) => cyl(r, r, 0.02, [x, 0.012, z], "#2b2017", { o, m: "basic", seg: 20 });

/** A low-poly person (about 1.7 m), turned ``ry``; ``act`` 0..1 how busy (arms move with time), ``bend`` a stoop. */
export function person(x, z, ry, t, { shirt = PAL.blue, skin = PAL.skin[0], act = 0, bend = 0, speed = 1, seed = 0, h = 1.7, pants = "#3d4451" } = {}) {
  const k = h / 1.7, ph = t * 4.2 * speed + seed * 1.7;
  const swing = act * Math.sin(ph) * 0.9, bob = act * Math.abs(Math.sin(ph)) * 0.03;
  const lean = bend * 0.5 + act * 0.06 * Math.sin(ph * 0.5);
  const parts = [
    box(0.16, 0.8, 0.18, [-0.11, 0.4, 0], pants), box(0.16, 0.8, 0.18, [0.11, 0.4, 0], pants),
    cyl(0.2, 0.26, 0.62, [0, 1.12 + bob, 0], shirt, { seg: 8, r: [lean, 0, 0] }),
    ico(0.17, [0, 1.6 + bob - lean * 0.18, lean * 0.3], skin, { detail: 1 }),
    box(0.11, 0.6, 0.11, [-0.33, 1.15 + bob, 0.06 + swing * 0.12], shirt, { r: [-0.4 - swing, 0, 0.12] }),
    box(0.11, 0.6, 0.11, [0.33, 1.15 + bob, 0.06 - swing * 0.12], shirt, { r: [-0.4 + swing, 0, -0.12] }),
  ];
  return [shadow(x, z, 0.32, 0.14), ...group(parts, { p: [x, 0, z], ry, s: k })];
}

/** A low-poly tree. */
export function tree(x, z, h = 3, c = "#5aa469") {
  return [cyl(0.12 * h / 3, 0.18 * h / 3, h * 0.45, [x, h * 0.22, z], "#7a4e22", { seg: 6 }),
    ico(h * 0.33, [x, h * 0.62, z], c, { detail: 0 }), ico(h * 0.24, [x + h * 0.12, h * 0.8, z - h * 0.05], mix(c, "#ffffff", 0.12), { detail: 0 })];
}

/** Boxes in a tidy pile: ``n`` (fractional: the next one is growing in) in rows x cols layers; returns nodes and top y. */
export function pile(n, { x = 0, z = 0, cols = 3, rows = 3, size = 0.7, gap = 0.06, colors = ["#c8955a"], y0 = 0, max = 99 } = {}) {
  const out = [], step = size + gap, whole = Math.floor(clamp(n, 0, max)), part = clamp(n, 0, max) - whole;
  let top = y0;
  for (let i = 0; i < Math.min(max, whole + (part > 0.02 ? 1 : 0)); i++) {
    const layer = Math.floor(i / (cols * rows)), j = i % (cols * rows), cx = (j % cols) - (cols - 1) / 2, cz = Math.floor(j / cols) - (rows - 1) / 2;
    const g = i < whole ? 1 : ease(part);
    const y = y0 + layer * step + size / 2;
    out.push(box(size, size, size, [x + cx * step, y + (1 - g) * 0.6, z + cz * step], colors[i % colors.length], { s: [g, g, g] }));
    top = Math.max(top, y0 + (layer + 1) * step);
  }
  return { nodes: out, top };
}

/** The light of a place: day, evening or night (the 2D worlds' light parameter, in 3D). */
export function envOf(light = "day", extra = {}) {
  const E = {
    day: { sky: "#cfe8f5", hemi: ["#ffffff", "#b9b2a4", 2.1], sun: ["#ffffff", 1.7, [0.45, 1, 0.55]] },
    evening: { sky: "#f4c49a", hemi: ["#fff0e0", "#9a8a7a", 1.9], sun: ["#ffc48a", 1.3, [-0.7, 0.55, 0.5]] },
    night: { sky: "#14233d", hemi: ["#93a8d6", "#2f3a4d", 1.35], sun: ["#b9ccff", 0.75, [0.3, 1, 0.4]] },
  };
  return { ...(E[light] || E.day), ...extra };
}
