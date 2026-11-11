// 3D models of economic ideas where depth teaches (Sloman ch. 4 and 6): the utility hill whose horizontal slices fall
// to the floor as the indifference map (a contour map), and the container cube (volume grows with the cube of the side,
// the surface with its square). Pure functions of parameters and time, like every kind (kinds_place.mjs).
import { PAL, clamp, clamp01, ease, num, mix, box, cyl, cone, sphere, tube } from "./parts3d.mjs";

const RING_COLORS = ["#e5484d", "#f29f05", "#2fa35b", "#3a7bd5", "#7b61ff", "#e2558f", "#2a9d8f", "#8a5a2b"];

// ---------------------------------------------------------------- the utility hill -> the indifference map
// U = X^a Y^b over 0..10 x 0..10. X runs along +x, Y along -z (so the top view reads like the 2D graph: X to the right,
// Y up); height is U scaled so the far corner stands HMAX high. `flatten` squashes the hill into the floor, `drop`
// lowers the rings (the slices at chosen heights) to the floor, where they are the indifference curves.
const SIZE = 10, HMAX = 5;
function utilityHill(p) {
  const out = [], spots = {}, zones = {};
  const a = clamp(num(p.a, 0.5), 0.1, 1.5), b = clamp(num(p.b, 0.5), 0.1, 1.5);
  const flat = clamp01(num(p.flatten, 0)), drop = clamp01(num(p.drop, 0)), glow = clamp01(num(p.glow, 0.4));
  const R = Math.round(clamp(num(p.rings, 5), 0, 8)), show = Math.round(num(p.show, 0));
  const umax = Math.pow(SIZE, a + b), lift = 1 - flat;
  if (p.base !== false) {
    out.push(box(SIZE + 0.8, 0.08, SIZE + 0.8, [0.4 - 0.4, -0.04, -0.4 + 0.4], "#fbf7ee"));
    for (let k = 2; k < SIZE; k += 2) {
      out.push(box(0.025, 0.012, SIZE, [-SIZE / 2 + k, 0.005, 0], "#d9d2c3"), box(SIZE, 0.012, 0.025, [0, 0.005, SIZE / 2 - k], "#d9d2c3"));
    }
  }
  if (flat < 0.995) {
    out.push({ g: "surface", a: { fn: "cobb", a: Math.round(a * 1000) / 1000, b: Math.round(b * 1000) / 1000, n: 40, size: SIZE, h: HMAX },
      p: [-SIZE / 2, 0.01, SIZE / 2], s: [1, Math.max(0.002, lift), 1], c: "#9fd38a", m: "vcol",
      // see-through when asked, while the rings fall under it, and as it flattens away
      o: Math.max(0.15, Math.min(p.solid === false ? 0.55 : 1, 1 - 0.6 * drop, flat > 0.3 ? 1.3 - flat : 1)) });
  }
  for (let k = 1; k <= R; k++) {
    const U = (umax * k) / (R + 1), H = (HMAX * k) / (R + 1);
    const xmin = Math.pow(U / Math.pow(SIZE, b), 1 / a), pts = [];
    for (let i = 0; i < 48; i++) {
      const X = xmin * Math.pow(SIZE / xmin, i / 47), Y = Math.min(SIZE, Math.pow(U / Math.pow(X, a), 1 / b));
      pts.push([X - SIZE / 2, 0, SIZE / 2 - Y]);
    }
    const y = H * lift * (1 - ease(drop)) + 0.05, hot = show === k;
    const c = RING_COLORS[(k - 1) % RING_COLORS.length];
    out.push({ ...tube(pts, hot ? 0.11 : 0.065, c, { e: 0.25 + glow * (hot ? 1.6 : 0.9) }), p: [0, Math.round(y * 1000) / 1000, 0] });
    if (p.planes && drop < 0.98 && lift > 0.05) out.push(box(SIZE, 0.02, SIZE, [0, H * lift, 0], c, { o: 0.16 * (1 - drop), m: "basic" }));
    const d = Math.pow(U, 1 / (a + b));                          // where the ring crosses X = Y (the label's place)
    const dx = Math.min(d, SIZE - 0.2), dy = Math.min(SIZE, Math.pow(U / Math.pow(dx, a), 1 / b));
    spots[`ring${k}`] = [dx - SIZE / 2 + 0.55, y, SIZE / 2 - dy - 0.55];
  }
  if (p.axes !== false) {
    const ink = PAL.ink, U = 6.2 * lift;
    out.push(box(SIZE + 1, 0.07, 0.07, [0.5, 0.04, SIZE / 2], ink), cone(0.16, 0.42, [SIZE / 2 + 1.1, 0.04, SIZE / 2], ink, { r: [0, 0, -Math.PI / 2] }));
    out.push(box(0.07, 0.07, SIZE + 1, [-SIZE / 2, 0.04, -0.5], ink), cone(0.16, 0.42, [-SIZE / 2, 0.04, -SIZE / 2 - 1.1], ink, { r: [-Math.PI / 2, 0, 0] }));
    if (U > 0.2) out.push(box(0.07, U, 0.07, [-SIZE / 2, U / 2, SIZE / 2], ink), cone(0.16, 0.42, [-SIZE / 2, U + 0.2, SIZE / 2], ink));
    spots.uaxis = [-SIZE / 2, U + 0.7, SIZE / 2];
  }
  spots.peak = [SIZE / 2, HMAX * lift + 0.4, -SIZE / 2]; spots.origin = [-SIZE / 2, 0, SIZE / 2];
  spots.xaxis = [SIZE / 2 + 1.6, 0, SIZE / 2]; spots.yaxis = [-SIZE / 2, 0, -SIZE / 2 - 1.6]; spots.floor = [0, 0, 0];
  spots.hill = [1.5, HMAX * lift * 0.55, -1.5];
  return { nodes: out, spots, zones, env: { sky: "#f7f1e5", hemi: ["#ffffff", "#c8bfae", 2.2], sun: ["#ffffff", 1.5, [0.4, 1, 0.6]] } };
}

// ---------------------------------------------------------------- the container cube
// A glass cube of side `side` (1..2 m, it grows on a step); `units` unit cubes fill it one by one (bottom layer first);
// `faces` lights its six faces, `explode` pulls them apart to count the surface; `grid` draws the 1 m squares on each face;
// `compare` keeps a 1 m cube beside it.
function cubeAt(side, cx, { faces = 0, explode = 0, grid = false, units = 0, glassC = "#9fd3f0" } = {}) {
  const out = [], s = side, h = s / 2, ex = explode * 0.42 * s;
  const fc = mix(glassC, "#f2c14e", faces), fo = 0.24 + 0.3 * faces, fe = faces * 0.35, t = 0.035;
  const FACES = [[[0, h, h + ex], [s, s, 0.02], "z"], [[0, h, -h - ex], [s, s, 0.02], "z"], [[h + ex, h, 0], [0.02, s, s], "x"],
    [[-h - ex, h, 0], [0.02, s, s], "x"], [[0, s + ex, 0], [s, 0.02, s], "y"], [[0, -ex * 0.15, 0], [s, 0.02, s], "y"]];
  for (const [[x, y, z], [w, hh, d], ax] of FACES) {
    out.push(box(w, hh, d, [cx + x, y, z], fc, { o: fo, e: fe }));
    // the face's frame, so a pulled-apart face is still a square
    const e = (W, H, D, X, Y, Z) => out.push(box(W, H, D, [cx + x + X, y + Y, z + Z], PAL.ink));
    if (ax === "z") { e(s, t, t, 0, h, 0); e(s, t, t, 0, -h, 0); e(t, s, t, h, 0, 0); e(t, s, t, -h, 0, 0); }
    if (ax === "x") { e(t, s, t, 0, 0, h); e(t, s, t, 0, 0, -h); e(t, t, s, 0, h, 0); e(t, t, s, 0, -h, 0); }
    if (ax === "y") { e(s, t, t, 0, 0, h); e(s, t, t, 0, 0, -h); e(t, t, s, h, 0, 0); e(t, t, s, -h, 0, 0); }
    if (grid) for (let k = 1; k < s - 0.02; k++) {
      const o = -h + k, g = 0.02;
      if (ax === "z") { out.push(box(s, g, g, [cx + x, y + o, z], PAL.ink, { o: 0.7 }), box(g, s, g, [cx + x + o, y, z], PAL.ink, { o: 0.7 })); }
      if (ax === "x") { out.push(box(g, g, s, [cx + x, y + o, z], PAL.ink, { o: 0.7 }), box(g, s, g, [cx + x, y, z + o], PAL.ink, { o: 0.7 })); }
      if (ax === "y") { out.push(box(s, g, g, [cx + x, y, z + o], PAL.ink, { o: 0.7 }), box(g, g, s, [cx + x + o, y, z], PAL.ink, { o: 0.7 })); }
    }
  }
  const m = Math.max(1, Math.floor(s + 1e-6)), cap = m * m * m, n = clamp(units, 0, cap), whole = Math.floor(n), part = n - whole;
  for (let i = 0; i < whole + (part > 0.02 ? 1 : 0); i++) {
    const iy = Math.floor(i / (m * m)), j = i % (m * m), ix = j % m, iz = Math.floor(j / m), g = i < whole ? 1 : ease(part);
    out.push(box(0.9, 0.9, 0.9, [cx - h + 0.5 + ix, 0.5 + iy + (1 - g) * 0.8, -h + 0.5 + iz], mix("#f29f05", "#e5484d", (i % 4) / 6), { s: [g, g, g] }));
  }
  return out;
}
function containerCube(p) {
  const side = clamp(num(p.side, 1), 0.5, 3), spots = {};
  const cx = p.compare ? 1.2 : 0;
  const out = [...cubeAt(side, cx, { faces: clamp01(num(p.faces, 0)), explode: clamp01(num(p.explode, 0)), grid: !!p.grid, units: num(p.units, 0) })];
  out.push(cyl(side * 0.9, side * 0.9, 0.02, [cx, 0.005, 0], "#2b2017", { o: 0.12, m: "basic", seg: 24 }));
  if (p.compare) {
    out.push(...cubeAt(1, -1.6, { units: 1, glassC: "#c9e6c0" }));
    spots.small = [-1.6, 1.35, 0]; spots.small_front = [-1.6, 0.5, 0.75];
  }
  const h = side / 2;
  spots.cube = [cx, side + 0.45, 0]; spots.top = [cx, side + 0.05, 0]; spots.front = [cx, h, h + 0.05];
  spots.side = [cx + h + 0.05, h, 0]; spots.base = [cx, 0, h + 0.5]; spots.right = [cx + h + 0.9, h, 0];
  return { nodes: out, spots, zones: {}, env: { sky: "#f7f1e5", hemi: ["#ffffff", "#c8bfae", 2.2], sun: ["#ffffff", 1.4, [0.5, 1, 0.7]] } };
}

export const KINDS = {
  utilityHill: { fn: utilityHill, camera: { angle: 35, height: 10, dist: 17, tx: 0, ty: 1.2, tz: 0, fov: 40 } },
  containerCube: { fn: containerCube, camera: { angle: 32, height: 3, dist: 7.4, tx: 0, ty: 1.05, tz: 0, fov: 40 } },
};
