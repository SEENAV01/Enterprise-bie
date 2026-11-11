// The 3D places of economics (the Sloman book's places, where depth teaches): a factory floor, a port, a city, a farm, a
// bank vault and a stock-exchange floor, plus a globe with trade routes. Each kind is a pure function of its parameters
// and of time (ctx.t: seconds since it appeared; ctx.s: since its last step): the same values give the same nodes, so a
// process (a belt, a crane, traffic, smoke) moves without any state. Each names its spots (3D points the plan can put
// people and words beside, projected through the camera by scene3d.mjs) and its zones (parts words must stay off).
// Generic places only: no logo, landmark, flag or real person; words come from the plan, never from the model.
import {
  PAL, clamp, clamp01, ease, lerp, num, frac, listOf, rng, mix, shade, box, cyl, cone, sphere, ico, prism, torus, tube, group, place,
  shadow, person, tree, pile, envOf,
} from "./parts3d.mjs";

const Z3 = (x0, y0, z0, x1, y1, z1) => [[x0, y0, z0], [x1, y1, z1]];
const ground = (w, d, c, y = -0.1) => box(w, 0.2, d, [0, y, 0], c, { bg: true });

// ---------------------------------------------------------------- factory floor
function factory(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {};
  const night = p.light === "night", lit = night || p.overtime;
  const M = Math.round(clamp(num(p.machines, 4), 1, 8)), run = clamp(num(p.running, M), 0, M);
  const W = clamp(num(p.workers, 4), 0, 16), rate = clamp(num(p.rate, 1), 0, 3), pace = p.overtime ? 1.7 : 1;
  out.push(ground(60, 44, "#c9ccd1"));
  out.push(box(26, 0.02, 1.2, [0, 0.01, 3.6], "#f2c14e", { bg: true }), box(26, 0.02, 0.12, [0, 0.02, -0.4], "#f2c14e", { bg: true }));
  // walls: the back wall with windows, the left wall, a sawtooth roof line, the chimney behind
  const wall = night ? "#a9a397" : "#e9e2d4";
  out.push(box(26, 7, 0.4, [0, 3.5, -6.2], wall), box(0.4, 7, 13, [-13, 3.5, 0.3], shade(wall, 0.92)));
  for (let i = 0; i < 8; i++) out.push(box(1.8, 1.5, 0.08, [-10.5 + i * 3, 5.1, -5.98], lit ? "#ffe08a" : "#bcd9ee", { e: lit ? 0.9 : 0.15 }));
  for (let i = 0; i < 6; i++) out.push(prism(1.25, 26 / 6 * 0.98, [-13 + 26 / 12 + i * 26 / 6, 7.6, -6.5], "#a39a88", { r: [-Math.PI / 2, Math.PI / 2, 0], s: [1.4, 1, 1] }));
  out.push(cyl(0.55, 0.75, 9.6, [8.5, 4.8, -8.4], "#b5523b", { seg: 10 }), cyl(0.58, 0.58, 0.6, [8.5, 8.4, -8.4], "#f2f2f2", { seg: 10 }));
  const smoke = clamp01(num(p.smoke, 0.6));
  const puffs = Math.round(smoke * 7);
  for (let i = 0; i < puffs; i++) {
    const ph = frac(t * 0.22 + i / Math.max(1, puffs));
    out.push(ico(0.5 + ph * 1.3, [8.5 + ph * 5.5, 9.8 + ph * 3.2, -8.4 - ph * 0.8], mix("#e6e6e6", "#7d7d7d", smoke * 0.7), { o: (1 - ph) * 0.85, detail: 1, m: "smooth" }));
  }
  // the conveyor belt: boxes ride along at `rate`
  const bz = 1.6, bx0 = -7, bx1 = 7;
  out.push(box(bx1 - bx0, 0.18, 1.3, [0, 0.95, bz], "#3b4252"), box(bx1 - bx0 + 0.4, 0.3, 1.5, [0, 0.72, bz], "#5b6474"));
  for (const x of [bx0, bx1]) out.push(cyl(0.22, 0.22, 1.5, [x, 0.9, bz], "#9aa5b1", { r: [Math.PI / 2, 0, 0] }));
  for (let x = bx0 + 0.6; x < bx1; x += 2.2) out.push(box(0.14, 0.6, 1.1, [x, 0.3, bz], "#5b6474"));
  const gap = 1.7, shift = frac((t * rate * 0.9) / gap) * gap;
  for (let x = bx0 + 0.2 + shift; x < bx1 - 0.3; x += gap) out.push(box(0.7, 0.55, 0.7, [x, 1.32, bz], "#c8955a"));
  spots.belt = [0, 1.6, bz]; spots.belt_start = [bx0, 1.6, bz]; spots.belt_end = [bx1, 1.6, bz];
  zones.belt = { keep: "text", box: Z3(bx0, 0.6, bz - 0.7, bx1, 1.7, bz + 0.7) };
  // machines in a row behind the belt: the first `running` press and glow green, the rest stand idle
  const span = 12.5, mx = (i) => -span / 2 + (M === 1 ? span / 2 : (i * span) / (M - 1));
  for (let i = 0; i < M; i++) {
    const x = mx(i), on = i < Math.floor(run) || (i === Math.floor(run) && run - Math.floor(run) > 0.5);
    const body = on ? PAL.blue : "#9aa5b1", press = on ? Math.abs(Math.sin(t * 3.2 * pace + i * 1.3)) : 0.8;
    out.push(shadow(x, -2, 1.3, 0.12), box(1.7, 1.5, 1.5, [x, 0.75, -2], body), box(1.9, 0.25, 1.7, [x, 1.6, -2], shade(body, 0.8)));
    out.push(box(0.3, 1.3, 0.3, [x - 0.6, 2.35, -2], "#4a5568"), box(0.3, 1.3, 0.3, [x + 0.6, 2.35, -2], "#4a5568"), box(1.5, 0.3, 0.6, [x, 3.05, -2], "#4a5568"));
    out.push(box(0.8, 0.45, 0.8, [x, 2.05 + 0.65 * press, -2], on ? "#f29f05" : "#c7ccd3"));
    out.push(sphere(0.17, [x + 0.7, 3.35, -1.7], on ? "#3ddc84" : "#e5484d", { e: 1.1, seg: 10 }));
    out.push(box(0.5, 0.12, 1.6, [x, 1.05, -0.4], "#7a8494", { r: [-0.25, 0, 0] }));          // a chute to the belt
    spots[`machine${i + 1}`] = [x, 3.5, -2];
  }
  zones.machines = { keep: "text", box: Z3(mx(0) - 1, 0, -2.9, mx(M - 1) + 1, 3.5, -1.1) };
  // workers stand at the machines; more workers than machines crowd the same stations
  const whole = Math.floor(W), part = W - whole;
  for (let j = 0; j < whole + (part > 0.05 ? 1 : 0); j++) {
    const m = j % M, row = Math.floor(j / M), x = mx(m) + (row ? (row % 2 ? 0.75 : -0.75) * Math.ceil(row / 2) : 0);
    const on = m < Math.round(run), g = j < whole ? 1 : ease(part);
    const nd = person(x, -0.55 + row * 0.12, Math.PI, t, { shirt: PAL.shirts[j % PAL.shirts.length], skin: PAL.skin[j % 4], act: on ? 1 : 0.1, speed: pace, seed: j });
    out.push(...(g < 1 ? nd.map((n) => ({ ...n, s: (n.s || [1, 1, 1]).map((v) => v * g) })) : nd));
    spots[`worker${j + 1}`] = [x, 2, -0.55];
  }
  // the output stack at the belt's end and the godown rack
  const outN = clamp(num(p.output, 6), 0, 45);
  const st = pile(outN, { x: 9.2, z: bz, cols: 3, rows: 3, size: 0.62, colors: ["#c8955a", "#b9844b"] });
  out.push(shadow(9.2, bz, 1.4, 0.12), ...st.nodes);
  spots.output = [9.2, st.top + 0.4, bz];
  const stock = clamp01(num(p.stock, 0.3));
  out.push(box(0.12, 4.2, 0.12, [-11.6, 2.1, -3.4], "#4a5568"), box(0.12, 4.2, 0.12, [-8, 2.1, -3.4], "#4a5568"),
    box(0.12, 4.2, 0.12, [-11.6, 2.1, -1.8], "#4a5568"), box(0.12, 4.2, 0.12, [-8, 2.1, -1.8], "#4a5568"));
  for (let k = 0; k < 4; k++) out.push(box(3.8, 0.1, 1.8, [-9.8, 0.3 + k * 1.25, -2.6], "#9aa5b1"));
  const slots = 15, full = stock * slots;
  for (let i = 0; i < Math.ceil(full - 0.02); i++) {
    const g = i < Math.floor(full) ? 1 : ease(full - Math.floor(full)), lvl = Math.floor(i / 5), c = i % 5;
    out.push(box(0.62, 0.62, 0.9, [-11.1 + c * 0.66, 0.67 + lvl * 1.25, -2.6], PAL.boxes[(i + lvl) % 6], { s: [g, g, g] }));
  }
  spots.godown = [-9.8, 4.6, -2.6];
  zones.godown = { keep: "text", box: Z3(-11.7, 0, -3.5, -7.9, 4.3, -1.7) };
  // the wall board: a target bar beside an output bar (the plan writes the words next to it)
  const target = clamp(num(p.target, 0), 0, 45);
  out.push(box(4.6, 2.4, 0.12, [-4, 4.3, -5.95], "#2d3748"));
  if (target > 0) {
    const sc = 1.8 / Math.max(target, outN, 1);
    out.push(box(0.8, Math.max(0.05, target * sc), 0.1, [-5, 3.2 + target * sc / 2, -5.85], "#f29f05"),
      box(0.8, Math.max(0.05, outN * sc), 0.1, [-3.4, 3.2 + outN * sc / 2, -5.85], outN >= target ? "#3ddc84" : "#e5484d", { e: 0.3 }));
  }
  spots.board = [-4, 4.3, -5.9]; spots.chimney = [8.5, 9.8, -8.4]; spots.smoke = [12, 12, -9]; spots.floor = [0, 0, 5];
  zones.chimney = { keep: "text", box: Z3(7.8, 0, -9.1, 9.2, 9.6, -7.7) };
  const env = envOf(p.light || "day");
  if (lit && night) env.hemi = ["#ffe9c4", "#6b6458", 1.9];       // the hall's own lamps
  return { nodes: out, spots, zones, env };
}

// ---------------------------------------------------------------- port
function port(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {};
  out.push(box(120, 0.2, 90, [0, -0.5, -30], PAL.sea, { bg: true }));
  for (let i = 0; i < 14; i++) {
    const r = rng(i + 3), x = -40 + frac(r() + t * 0.02) * 80, z = -4 - r() * 40;
    out.push(box(2 + r() * 2, 0.02, 0.12, [x, -0.38, z], "#8fc1e3", { bg: true }));
  }
  out.push(box(60, 1.2, 18, [0, -0.1, 8], "#b8afa2"), box(60, 0.3, 0.5, [0, 0.6, -0.8], "#8a8172"));
  out.push(box(60, 0.02, 2.4, [0, 0.51, 13], "#6b7280", { bg: true }));
  for (let x = -26; x < 30; x += 4) out.push(box(1.6, 0.02, 0.2, [x, 0.53, 13], "#f2f2f2", { bg: true }));
  const flowIn = p.flow === "import", working = p.working !== false;
  // ships come in along the sea lane as `arrive` goes 0 -> 1, and bob on the water
  const S = Math.round(clamp(num(p.ships, 1), 0, 3)), arrive = clamp01(num(p.arrive, 1)), cargo = clamp01(num(p.cargo, 0.6));
  for (let i = 0; i < S; i++) {
    const berth = -9 + i * 15, x = berth - (1 - arrive) * (45 + i * 6), bob = Math.sin(t * 1.3 + i) * 0.08, z = -4.6;
    const hull = [box(12, 1.8, 3.4, [0, 0, 0], i % 2 ? "#2459a6" : "#c0392b"), prism(1.7, 3.4, [6.85, 0, 0], i % 2 ? "#2459a6" : "#c0392b", { r: [0, Math.PI / 2, Math.PI / 2], s: [0.62, 1, 1] }),
      box(12.6, 0.25, 3.6, [0.2, 0.95, 0], "#2d3748"), box(2.2, 2.6, 3, [-4.8, 2.3, 0], "#f2f2f2"), box(2.3, 0.5, 3.1, [-4.8, 3.4, 0], "#4a5568"),
      cyl(0.35, 0.35, 1.4, [-4.8, 4.2, 0], "#e5484d", { seg: 8 })];
    const slots = 24, full = Math.round(cargo * slots);
    for (let k = 0; k < full; k++) {
      const lay = Math.floor(k / 12), j = k % 12, cx = -2.4 + (j % 4) * 2.05, cz = -0.8 + Math.floor(j / 4) * 0.8;
      hull.push(box(1.95, 0.75, 0.75, [cx + 0.6, 1.5 + lay * 0.78, cz], PAL.boxes[(k * 7 + i) % 6]));
    }
    out.push(...group(hull, { p: [x, 0.5 + bob, z] }));
    spots[`ship${i + 1}`] = [x, 3.6 + bob, z];
    if (i === 0) { spots.ship = spots.ship1; zones.ship = { keep: "text", box: Z3(x - 6, -0.5, z - 1.8, x + 8, 4.6, z + 1.8) }; }
  }
  // gantry cranes along the quay: the trolley carries a box between the ship and the quay on a loop
  const C = Math.round(clamp(num(p.cranes, 2), 1, 3));
  for (let i = 0; i < C; i++) {
    const x = -10 + i * 9, Y = "#f2c14e";
    out.push(box(0.35, 9, 0.35, [x - 1.6, 4.5, 1.2], Y), box(0.35, 9, 0.35, [x + 1.6, 4.5, 1.2], Y), box(0.35, 9, 0.35, [x - 1.6, 4.5, 4.2], Y),
      box(0.35, 9, 0.35, [x + 1.6, 4.5, 4.2], Y), box(3.6, 0.4, 0.4, [x, 7.4, 1.2], Y), box(3.6, 0.4, 0.4, [x, 7.4, 4.2], Y),
      box(0.6, 0.6, 15, [x, 9.2, -1.5], Y), box(1.4, 1.2, 1.6, [x, 9.6, 3.6], "#e07b24"), box(0.2, 2.4, 0.2, [x, 10.6, 4.4], Y));
    const ph = working ? frac(t * 0.13 + i * 0.37) : 0.25;
    // 0..0.25 over the ship lowering, 0.25..0.5 lift and travel, 0.5..0.75 lower on the quay, 0.75..1 back empty
    const zShip = -4.6, zQuay = 3.2, k = ph < 0.25 ? 0 : ph < 0.5 ? ease((ph - 0.25) / 0.25) : ph < 0.75 ? 1 : 1 - ease((ph - 0.75) / 0.25);
    const drop = ph < 0.25 ? Math.sin((ph / 0.25) * Math.PI) : ph >= 0.5 && ph < 0.75 ? Math.sin(((ph - 0.5) / 0.25) * Math.PI) : 0;
    const from = flowIn ? zShip : zQuay, to = flowIn ? zQuay : zShip, tz = lerp(from, to, k), hy = 7.6 - drop * 4.2;
    out.push(box(1, 0.4, 1, [x, 8.75, tz], "#4a5568"), box(0.06, 8.6 - hy, 0.06, [x, (8.6 + hy) / 2, tz], "#2b2b33"));
    if (ph >= 0.25 && ph < 0.75) out.push(box(1.95, 0.8, 0.8, [x, hy - 0.5, tz], PAL.boxes[(i + 2) % 6], { r: [0, Math.PI / 2, 0] }));
    spots[`crane${i + 1}`] = [x, 10.4, 1.5];
    if (i === 0) spots.crane = spots.crane1;
  }
  zones.cranes = { keep: "text", box: Z3(-12, 0.5, -0.5, -10 + (C - 1) * 9 + 2, 10.5, 4.6) };
  // container yards: exports waiting to sail (left), imports landed (right)
  const yard = (n, x0, colors) => {
    const nodes = [], whole = Math.floor(n), part = n - whole;
    let top = 0.5;
    for (let k = 0; k < whole + (part > 0.02 ? 1 : 0); k++) {
      const lay = Math.floor(k / 12), j = k % 12, g = k < whole ? 1 : ease(part);
      const y = 0.5 + 0.42 + lay * 0.86;
      nodes.push(box(2.3, 0.82, 0.95, [x0 + (j % 3) * 2.45, y + (1 - g) * 0.8, 6 + Math.floor(j / 3) * 1.05], colors[(k * 5 + lay) % colors.length], { s: [g, g, g] }));
      top = Math.max(top, y + 0.43);
    }
    return { nodes, top };
  };
  const ex = yard(clamp(num(p.exports, 10), 0, 48), -15, ["#f29f05", "#2a9d8f", "#e5484d"]);
  const im = yard(clamp(num(p.imports, 10), 0, 48), 5, ["#3a7bd5", "#7b61ff", "#2fa35b"]);
  out.push(...ex.nodes, ...im.nodes);
  spots.exports = [-12.5, ex.top + 0.5, 7.6]; spots.imports = [7.5, im.top + 0.5, 7.6];
  const T = Math.round(clamp(num(p.trucks, 1), 0, 4));
  for (let i = 0; i < T; i++) {
    const x = -32 + frac(t * 0.05 + i / Math.max(1, T)) * 64, c = PAL.boxes[(i * 2 + 1) % 6];
    out.push(...group([box(1.6, 1.4, 1.4, [1.6, 0.9, 0], "#4a5568"), box(3.2, 1, 1.4, [-0.8, 1.1, 0], c), box(4.4, 0.25, 1.3, [0, 0.35, 0], "#2d3748"),
      cyl(0.3, 0.3, 1.5, [-1.6, 0.3, 0], "#2b2b33", { r: [Math.PI / 2, 0, 0], seg: 10 }), cyl(0.3, 0.3, 1.5, [1.6, 0.3, 0], "#2b2b33", { r: [Math.PI / 2, 0, 0], seg: 10 })],
    { p: [x, 0.5, 12.6] }));
  }
  spots.dock = [0, 0.5, 11]; spots.sea = [-18, 0, -14];
  return { nodes: out, spots, zones, env: envOf(p.light || "day") };
}

// ---------------------------------------------------------------- city
function city(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {};
  const size = clamp01(num(p.size, 0.6)), lights = clamp01(num(p.lights, p.light === "night" ? 0.7 : 0)), traffic = clamp01(num(p.traffic, 0.4));
  const smog = clamp01(num(p.smog, 0)), night = p.light === "night";
  out.push(ground(140, 140, night ? "#4f5f4a" : PAL.grass));
  const N = 7, cell = 5, road = 1.6, half = (N * cell) / 2;
  for (let i = 0; i <= N; i++) {
    const c = -half + i * cell;
    out.push(box(N * cell + road, 0.04, road, [0, 0.02, c], "#5b6170", { bg: true }), box(road, 0.045, N * cell + road, [c, 0.02, 0], "#5b6170", { bg: true }));
  }
  // lots grow outward from the centre with `size`: buildings appear and rise
  const lots = [];
  const r = rng(num(p.seed, 7));
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    const x = -half + (i + 0.5) * cell, z = -half + (j + 0.5) * cell, d = Math.hypot(x, z) / (half * 1.42);
    lots.push({ x, z, d, h0: 0.35 + r() * 0.65, w: 2.4 + r() * 1.3, c: ["#e8d8c4", "#c7d3e3", "#f2c6a0", "#b9d7c1", "#d9c2e3", "#f1e3a6", "#cfd8dc"][Math.floor(r() * 7)], lit: r(), park: r() < 0.12 });
  }
  lots.sort((a, b) => a.d - b.d || a.x - b.x || a.z - b.z);
  const shown = size * lots.length;
  let tallest = null;
  lots.forEach((L, k) => {
    if (L.park) { out.push(...tree(L.x - 0.8, L.z - 0.6, 2.2), ...tree(L.x + 0.9, L.z + 0.7, 2.6)); spots.park = spots.park || [L.x, 2, L.z]; return; }
    if (k >= shown) return;
    const g = ease(clamp01(shown - k));
    const h = Math.max(0.4, (1.2 + 13 * L.h0 * (1 - L.d * 0.75)) * (0.35 + 0.65 * size)) * g;
    out.push(box(L.w, h, L.w, [L.x, h / 2, L.z], night ? shade(L.c, 0.55) : L.c), box(L.w * 1.04, 0.18, L.w * 1.04, [L.x, h + 0.09, L.z], shade(L.c, 0.8)));
    const floors = Math.floor(h / 0.9);
    for (let f = 0; f < floors; f++) {
      const y = 0.55 + f * 0.9;
      if (y > h - 0.3) break;
      for (let w = 0; w < 3; w++) {
        const on = frac(L.lit * 97 + f * 0.37 + w * 0.61) < lights;
        const col = on ? "#ffd86b" : night ? "#2c3a52" : "#8fb3cf", e = on ? 1.1 : 0;
        const off = (w - 1) * L.w * 0.3;
        out.push(box(L.w * 0.2, 0.42, 0.04, [L.x + off, y, L.z + L.w / 2 + 0.02], col, { e }), box(0.04, 0.42, L.w * 0.2, [L.x + L.w / 2 + 0.02, y, L.z + off], col, { e }));
      }
    }
    if (!tallest || h > tallest.h) tallest = { x: L.x, z: L.z, h };
    spots.edge = [L.x, h + 0.6, L.z];
  });
  // traffic: cars along the roads; a crowded road moves slower (the jam)
  const cars = Math.round(traffic * 30), speed = 3.2 * (1 - 0.75 * traffic);
  for (let i = 0; i < cars; i++) {
    const rr = rng(i * 13 + 5), along = rr() < 0.5, lane = Math.floor(rr() * (N + 1)), dir = rr() < 0.5 ? 1 : -1;
    const L = N * cell + road, s = frac(rr() + (dir * t * speed) / L) * L - L / 2, c = -half + lane * cell + dir * 0.35;
    const x = along ? s : c, z = along ? c : s, col = PAL.boxes[i % 6];
    out.push(...group([box(1, 0.4, 0.55, [0, 0.32, 0], col), box(0.55, 0.3, 0.5, [-0.05, 0.65, 0], shade(col, 0.85))], { p: [x, 0, z], ry: along ? 0 : Math.PI / 2 }));
    if (night) out.push(sphere(0.08, [x + (along ? dir * 0.55 : 0), 0.35, z + (along ? 0 : dir * 0.55)], "#fff4c2", { e: 2, seg: 6 }));
  }
  if (tallest) spots.tallest = [tallest.x, tallest.h + 0.8, tallest.z];
  else spots.tallest = [0, 1, 0];
  spots.centre = [0, 0, 0]; spots.road = [0, 0.1, half]; spots.sky = [0, 18, -half];
  spots.edge = spots.edge || [half * 0.8, 1, half * 0.5]; spots.park = spots.park || [-half - 2, 1, half];
  const smogC = mix("#cfd8e3", "#9b8a6e", smog);
  const env = envOf(p.light || "day");
  if (smog > 0.02) {
    env.sky = mix(env.sky, "#b9a98c", smog * 0.8);
    env.fog = { c: night ? mix(env.sky, "#3a3328", smog) : smogC, near: lerp(60, 6, smog), far: lerp(160, 48, smog) };
  }
  return { nodes: out, spots, zones, env };
}

// ---------------------------------------------------------------- farm
function farm(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {};
  const harvest = clamp01(num(p.harvest, 0.5)), drought = clamp01(num(p.drought, 0)), rain = clamp01(num(p.rain, 0));
  const soil = mix("#8a5a2b", "#c9a46a", drought);
  out.push(ground(140, 100, mix(PAL.grass, "#d9c58f", drought)));
  // the stony hillside behind the valley
  out.push(box(60, 0.4, 16, [0, 2.3, -16], mix("#a9b38a", "#c2b49a", drought), { r: [0.32, 0, 0] }), box(60, 6, 8, [0, 1, -24], mix("#a9b38a", "#c2b49a", drought)));
  const rr = rng(11);
  for (let i = 0; i < 22; i++) out.push(ico(0.3 + rr() * 0.5, [-26 + rr() * 52, 1.4 + rr() * 4.5, -10 - rr() * 12], "#9a958c", { detail: 0 }));
  const P = Math.round(clamp(num(p.plots, 3), 1, 6)), crops = listOf(p.crops || "wheat"), hill = Math.round(clamp(num(p.hillPlots, 0), 0, P));
  const pw = 6.2, pd = 5.2, valley = P - hill;
  const plotAt = (i) => i < valley ? [(-(valley - 1) / 2 + i) * (pw + 1), 0, 1] : [(-(hill - 1) / 2 + (i - valley)) * (pw + 1.4), 3.5, -12.5];
  for (let i = 0; i < P; i++) {
    const [x, y, z] = plotAt(i), onHill = i >= valley, crop = crops[i % crops.length] || "wheat";
    if (onHill) out.push(box(pw + 0.8, y, pd + 0.8, [x, y / 2, z], "#b8ae98"));             // a stony terrace on the hillside
    const plot = [box(pw, 0.25, pd, [0, 0.12, 0], onHill ? mix(soil, "#9a958c", 0.45) : soil)];
    if (crop === "rice" && harvest < 0.9) plot.push(box(pw * 0.96, 0.03, pd * 0.96, [0, 0.27, 0], "#8fc1e3", { o: 0.8 }));
    if (crop !== "none") {
      const rows = 9, cols = 14, sparse = onHill ? 0.5 : 1;
      const hgt = (0.1 + 0.75 * Math.min(1, harvest * 1.4)) * (1 - drought * 0.55) * (onHill ? 0.6 : 1) * (crop === "rice" ? 0.7 : 1);
      const green = harvest < 0.7 ? mix("#7cc47f", "#2fa35b", harvest / 0.7) : mix("#2fa35b", "#e8b93c", (harvest - 0.7) / 0.3);
      const col = mix(green, "#b59a5a", drought * 0.8);
      for (let a = 0; a < rows; a++) for (let b = 0; b < cols; b++) {
        if (frac(Math.sin((a * 31 + b * 17 + i * 7) * 12.9898) * 43758.5453) > sparse) continue;
        const sway = Math.sin(t * 1.6 + a + b * 0.7) * 0.06;
        const cx = -pw / 2 + 0.35 + b * (pw - 0.7) / (cols - 1), cz = -pd / 2 + 0.35 + a * (pd - 0.7) / (rows - 1);
        plot.push(cone(0.1, hgt, [cx, 0.25 + hgt / 2, cz], col, { r: [0, 0, sway], seg: 4 }));
        if (harvest > 0.75 && crop !== "rice") plot.push(ico(0.075, [cx + sway * hgt * 0.5, 0.25 + hgt, cz], mix("#e8b93c", "#c99a2e", 0.3), { detail: 0 }));
      }
    }
    out.push(...group(plot, { p: [x, y, z] }));
    spots[`plot${i + 1}`] = [x, y + 1.6, z];
    zones[`plot${i + 1}`] = { keep: "text", box: Z3(x - pw / 2, y, z - pd / 2, x + pw / 2, y + 1.2, z + pd / 2) };
  }
  // workers: on plot `workplot` (the fixed plot that crowds), or spread over the plots (0)
  const W = clamp(num(p.workers, 2), 0, 24), wp = Math.round(clamp(num(p.workplot, 1), 0, P));
  const whole = Math.floor(W), part = W - whole;
  for (let j = 0; j < whole + (part > 0.05 ? 1 : 0); j++) {
    const k = wp ? wp - 1 : j % P, [x, y, z] = plotAt(k), n = wp ? whole + 1 : Math.ceil(W / P), idx = wp ? j : Math.floor(j / P);
    const cols = Math.ceil(Math.sqrt(n * 1.4)), cx = (idx % cols) - (cols - 1) / 2, cz = Math.floor(idx / cols) - (Math.ceil(n / cols) - 1) / 2;
    const g = j < whole ? 1 : ease(part);
    const nd = person(x + cx * (pw / (cols + 0.5)), z + cz * 1.2, (j % 2 ? 0.6 : -0.6) + Math.PI * 0.1, t, { shirt: PAL.shirts[j % 7], skin: PAL.skin[j % 4], act: 0.7, bend: 0.6, seed: j });
    out.push(...nd.map((q) => ({ ...q, p: [q.p[0], q.p[1] + y + 0.25, q.p[2]], ...(g < 1 ? { s: (q.s || [1, 1, 1]).map((v) => v * g) } : {}) })));
  }
  // the harvest: sacks piling up at the field's edge
  const sacks = clamp(num(p.sacks, 0), 0, 40), sw = Math.floor(sacks), sp = sacks - sw;
  let top = 0;
  for (let i = 0; i < sw + (sp > 0.02 ? 1 : 0); i++) {
    const lay = Math.floor(i / 8), j = i % 8, g = i < sw ? 1 : ease(sp), y = 0.4 + lay * 0.62;
    out.push(cyl(0.38, 0.45, 0.75, [valley * (pw + 1) / 2 - 3.6 + (j % 4) * 0.85, y, 5.2 + Math.floor(j / 4) * 0.95], "#d9c08a", { s: [g, g * 0.8, g], seg: 8 }));
    top = Math.max(top, y + 0.4);
  }
  spots.sacks = [valley * (pw + 1) / 2 - 2.3, top + 0.6, 5.7];
  if (p.tractor) {
    const [x, , z] = plotAt(0), ph = (Math.sin(t * 0.35) + 1) / 2, tx = x - pw / 2 + 0.8 + ph * (pw - 1.6), dir = Math.cos(t * 0.35) >= 0 ? 0 : Math.PI;
    out.push(...group([box(1.6, 0.8, 1.1, [0, 0.8, 0], "#e5484d"), box(0.8, 0.9, 1, [-0.4, 1.6, 0], "#e5484d"), cyl(0.55, 0.55, 0.3, [-0.5, 0.55, 0.62], "#2b2b33", { r: [Math.PI / 2, 0, 0] }),
      cyl(0.55, 0.55, 0.3, [-0.5, 0.55, -0.62], "#2b2b33", { r: [Math.PI / 2, 0, 0] }), cyl(0.32, 0.32, 0.25, [0.6, 0.32, 0.6], "#2b2b33", { r: [Math.PI / 2, 0, 0] }),
      cyl(0.32, 0.32, 0.25, [0.6, 0.32, -0.6], "#2b2b33", { r: [Math.PI / 2, 0, 0] })], { p: [tx, 0.25, z + pd / 2 + 1.2], ry: dir }));
    spots.tractor = [tx, 2.6, z + pd / 2 + 1.2];
  }
  // a hut, a well and trees around the fields
  out.push(...group([box(3, 2, 2.6, [0, 1, 0], "#e9d8b4"), prism(2, 3.3, [0, 2.5, 0], "#b5523b", { r: [-Math.PI / 2, Math.PI / 2, 0], s: [1.0, 1, 0.75] }), box(0.8, 1.3, 0.05, [0, 0.65, 1.31], "#7a4e22")],
    { p: [-(valley * (pw + 1)) / 2 - 4.2, 0, -2] }));
  spots.hut = [-(valley * (pw + 1)) / 2 - 4.2, 3.6, -2];
  out.push(...tree(-(valley * (pw + 1)) / 2 - 7, 3, 3.4), ...tree(valley * (pw + 1) / 2 + 5, -3, 3.8), ...tree(valley * (pw + 1) / 2 + 7.5, 1, 2.8));
  // rain: streaks falling from a cloud bank; drought: a hard sun
  if (rain > 0.02) {
    for (let i = 0; i < 5; i++) out.push(ico(3 + (i % 2), [-12 + i * 6, 12 + (i % 2), -4], mix("#ffffff", "#7d8794", rain), { detail: 1, s: [1.4, 0.6, 1], m: "smooth" }));
    const n = Math.round(rain * 140);
    for (let i = 0; i < n; i++) {
      const q = rng(i * 7 + 1), y = 11 - frac(q() + t * 0.9) * 11;
      out.push(box(0.04, 0.6, 0.04, [-16 + q() * 32, y, -6 + q() * 14], "#9cc3e6", { o: 0.8, m: "basic" }));
    }
  }
  spots.hill = [0, 5.5, -13]; spots.valley = [0, 0.4, 1]; spots.field = spots.valley;
  const env = envOf(p.light || "day");
  if (rain > 0.02) env.sky = mix(env.sky, "#9aa7b4", rain * 0.7);
  if (drought > 0.3) { env.sky = mix(env.sky, "#f2dcae", drought * 0.6); env.sun = [env.sun[0], env.sun[1] * (1 + drought * 0.3), env.sun[2]]; }
  return { nodes: out, spots, zones, env };
}

// ---------------------------------------------------------------- bank vault / central bank
function vault(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {};
  out.push(ground(40, 30, "#e7e2d9"));
  for (let i = -6; i <= 6; i++) for (let j = -2; j <= 5; j++) if ((i + j) % 2 === 0) out.push(box(1.6, 0.02, 1.6, [i * 1.6, 0.01, j * 1.6], "#d5cec2", { bg: true }));
  const HR = 2.4, HY = 3.6;                                       // the round opening in the back wall
  for (let y = 0.225; y < 9; y += 0.45) {
    const dy = Math.max(0, Math.abs(y - HY) - 0.225), gap = dy < HR ? Math.sqrt(HR * HR - dy * dy) : 0;
    if (!gap) { out.push(box(22, 0.46, 0.6, [0, y, -4], "#efe8da")); continue; }
    out.push(box(11 - gap, 0.46, 0.6, [-(11 + gap) / 2, y, -4], "#efe8da"), box(11 - gap, 0.46, 0.6, [(11 + gap) / 2, y, -4], "#efe8da"));
  }
  out.push(box(22, 0.6, 1, [0, 9, -3.8], "#d9cfbd"));
  for (const x of [-9, -6, 6, 9]) out.push(cyl(0.45, 0.5, 8.2, [x, 4.1, -3.2], "#f5f0e6", { seg: 12 }), box(1.2, 0.35, 1.2, [x, 0.17, -3.2], "#d9cfbd"), box(1.2, 0.35, 1.2, [x, 8.3, -3.2], "#d9cfbd"));
  // the vault chamber behind the round door: reserve stacks fill to `level`
  out.push(box(6.6, 6.2, 0.2, [0, 3.6, -9.6], "#8a7a5c"), box(0.2, 6.2, 5.6, [-3.3, 3.6, -6.9], "#7a6b50"), box(0.2, 6.2, 5.6, [3.3, 3.6, -6.9], "#7a6b50"),
    box(6.6, 0.2, 5.6, [0, 6.7, -6.9], "#6b5d45"), box(6.6, 1.2, 5.6, [0, 0.6, -6.9], "#9a8a6a"));
  const notes = p.reserve === "notes", S = Math.round(clamp(num(p.stacks, 6), 1, 9)), level = clamp01(num(p.level, 0.7));
  const glow = p.glow ? 0.25 + 0.25 * Math.sin(t * 3) : 0;
  const per = 10, full = level * S * per;
  for (let s = 0; s < S; s++) {
    const cx = -2.2 + (s % 3) * 2.2, cz = -8.6 + Math.floor(s / 3) * 1.25;
    for (let k = 0; k < per; k++) {
      const idx = s * per + k;
      if (idx >= Math.ceil(full - 0.02)) break;
      const g = idx < Math.floor(full) ? 1 : ease(full - Math.floor(full)), lay = Math.floor(k / 2), side = k % 2;
      out.push(box(notes ? 0.8 : 0.85, 0.26, 0.42, [cx + (side - 0.5) * 0.9, 1.33 + lay * 0.28, cz], notes ? (s % 2 ? "#2fa35b" : "#7b61ff") : "#f3cf6a", { s: [g, g, g], e: notes ? 0 : 0.15 + glow }));
    }
  }
  spots.reserves = [0, 4.2, -7.4];
  // the round door on its hinge (left edge), turned open by `open`
  const open = clamp01(num(p.open, 0)), ang = -1.9 * ease(open), hx = -2.6, hz = -3.6;
  const door = [cyl(2.6, 2.6, 0.7, [2.6, 3.6, 0], "#c7ccd3", { r: [Math.PI / 2, 0, 0], seg: 28 }), cyl(2.1, 2.1, 0.75, [2.6, 3.6, 0], "#b3b9c2", { r: [Math.PI / 2, 0, 0], seg: 28 }),
    cyl(0.35, 0.35, 0.5, [2.6, 3.6, 0.5], "#4a5568", { r: [Math.PI / 2, 0, 0] })];
  for (let k = 0; k < 3; k++) door.push(box(2.4, 0.16, 0.16, [2.6, 3.6, 0.72], "#4a5568", { r: [0, 0, k * Math.PI / 3 + t * 0 + open * 2] }));
  for (let k = 0; k < 8; k++) door.push(cyl(0.12, 0.12, 0.3, [2.6 + Math.cos(k * Math.PI / 4) * 2.35, 3.6 + Math.sin(k * Math.PI / 4) * 2.35, 0.4], "#8a95a3", { r: [Math.PI / 2, 0, 0], seg: 6 }));
  out.push(torus(HR + 0.2, 0.32, [0, HY, -3.62], "#6b7280", { seg: 8, tseg: 40 }));
  out.push(...group(door, { p: [hx, 0, hz], ry: ang }), box(0.4, 1.4, 0.4, [hx, 3.6, hz], "#4a5568"));
  spots.door = place([2.6, 3.6, 0.6], { p: [hx, 0, hz], ry: ang });
  zones.door = { keep: "text", box: Z3(-3, 0.8, -4, 3, 6.4, -3.2) };
  // a counter and a sign board above the door (the plan writes the name beside it)
  out.push(box(4.4, 1.1, 1.2, [6.6, 0.55, 0.4], "#8a5a2b"), box(4.6, 0.12, 1.4, [6.6, 1.16, 0.4], "#a8763f"), box(7, 1.2, 0.12, [0, 7.4, -3.65], "#2d3748"));
  spots.counter = [6.6, 2.2, 0.4]; spots.sign = [0, 7.4, -3.55]; spots.floor = [0, 0, 3];
  return { nodes: out, spots, zones, env: envOf(p.light || "day", { sky: "#e9e2d4" }) };
}

// ---------------------------------------------------------------- stock-exchange floor
function exchange(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {};
  const trend = clamp(num(p.trend, 0.5), -1, 1), up = trend >= 0, col = up ? "#2fb463" : "#e5484d";
  out.push(ground(40, 30, "#d8dbe2"), box(26, 10, 0.5, [0, 5, -6], "#2d3748"), box(0.5, 10, 14, [-13, 5, 1], "#3b4252"));
  // the big board: bars of a random walk with drift `trend`; the newest bar grows on the step
  const B = 14, r = rng(num(p.seed, 3)), hs = [];
  let v = 0.5 - trend * 0.3;                                      // a falling market starts high, a rising one low
  for (let i = 0; i < B; i++) { v = clamp(v + (r() - 0.5) * 0.14 + trend * 0.045, 0.08, 1); hs.push(v); }
  const level = clamp(num(p.level, 1), 0.2, 1.6);
  out.push(box(15, 6.4, 0.2, [0, 5.4, -5.65], "#111827"));
  const pts = [];
  hs.forEach((h, i) => {
    const grow = i === B - 1 ? ease(clamp01(ctx.s / 1.2)) : 1;          // the newest bar grows from the one before it
    const H = Math.max(0.08, lerp(i ? hs[i - 1] : h, h, grow) * 4.6 * level);
    const x = -6.6 + i * (13.2 / (B - 1)), c = i === 0 || h >= hs[i - 1] ? "#2fb463" : "#e5484d";
    out.push(box(0.62, H, 0.25, [x, 2.5 + H / 2, -5.45], c, { e: 0.35 }));
    pts.push([x, 2.5 + H + 0.3, -5.3]);
  });
  out.push(tube(pts, 0.07, "#ffffff", { e: 0.9, m: "basic" }));
  spots.board = [0, 5.4, -5.4]; spots.board_top = [0, 9, -5.4]; spots.latest = pts[pts.length - 1];
  zones.board = { keep: "all", box: Z3(-7.5, 2.2, -5.8, 7.5, 8.6, -5.2) };
  // the ticker band: coloured cells sliding along
  if (p.ticker !== false) {
    out.push(box(24, 0.9, 0.2, [0, 1.3, -5.6], "#0b1220"));
    const L = 24, n = 16, sh = frac(t * 0.08) * (L / n);
    for (let i = 0; i < n + 1; i++) {
      const x = -L / 2 + i * (L / n) - sh;
      if (x < -L / 2 + 0.4 || x > L / 2 - 0.4) continue;
      const rr = rng((i + Math.floor(t * 0.08)) * 5 + 1);          // a cell keeps its colour as it slides
      out.push(box(0.9, 0.38, 0.05, [x, 1.3, -5.45], rr() < 0.5 + trend * 0.35 ? "#2fb463" : "#e5484d", { e: 0.8 }));
    }
    spots.ticker = [0, 1.3, -5.4];
  }
  // desks with screens and the traders on the floor
  const D = 4;
  for (let i = 0; i < D; i++) {
    const x = -7.5 + i * 5;
    out.push(box(3.6, 1, 1.4, [x, 0.5, 0.6], "#8a5a2b"), box(3.8, 0.1, 1.6, [x, 1.05, 0.6], "#a8763f"));
    for (const dx of [-1, 0, 1]) out.push(box(0.9, 0.6, 0.06, [x + dx * 1.05, 1.5, 0.2], col, { e: 0.6 }), box(0.1, 0.3, 0.1, [x + dx * 1.05, 1.15, 0.25], "#2b2b33"));
    spots[`desk${i + 1}`] = [x, 2.4, 0.6];
  }
  const crowd = clamp01(num(p.crowd, 0.5)), n = Math.round(crowd * 18);
  for (let j = 0; j < n; j++) {
    const q = rng(j * 3 + 2), x = -10 + q() * 20, z = 2.4 + q() * 4.5;
    out.push(...person(x, z, Math.PI + (q() - 0.5) * 0.8, t, { shirt: ["#f7f4ee", "#3a7bd5", "#e5484d", "#f2c14e"][j % 4], skin: PAL.skin[j % 4], act: 0.5 + Math.abs(trend) * 0.8, speed: 1 + Math.abs(trend), seed: j }));
  }
  spots.floor = [0, 0, 5];
  return { nodes: out, spots, zones, env: envOf("day", { sky: "#c9cfd9", hemi: ["#ffffff", "#9aa5b1", 2.0] }) };
}

// ---------------------------------------------------------------- globe with trade routes
export const REGIONS = {
  india: [22, 79], china: [35, 104], japan: [36, 138], southeastAsia: [5, 108], gulf: [25, 50], europe: [50, 10], uk: [54, -2],
  russia: [60, 90], africa: [5, 20], southAfrica: [-29, 24], usa: [39, -98], canada: [57, -100], mexico: [23, -102],
  brazil: [-10, -53], argentina: [-35, -65], australia: [-25, 134], centralAsia: [45, 68], egypt: [26, 30],
};
function latlon([lat, lon], R) {
  const ph = ((lon + 180) * Math.PI) / 180, la = (lat * Math.PI) / 180;
  return [-Math.cos(ph) * Math.cos(la) * R, Math.sin(la) * R, Math.sin(ph) * Math.cos(la) * R];
}
const rotY = ([x, y, z], a) => [x * Math.cos(a) + z * Math.sin(a), y, -x * Math.sin(a) + z * Math.cos(a)];
const norm = (v) => { const l = Math.hypot(...v) || 1; return v.map((c) => c / l); };
function routesOf(p) {
  return listOf(p.routes).map((r) => r.split(/\s*[-–>]+\s*/).map((s) => s.trim()).filter(Boolean));
}
function globeCheck(p) {
  const bad = [];
  for (const pair of routesOf(p)) {
    if (pair.length !== 2) bad.push(`globe.routes: '${pair.join("-")}' needs two regions joined by '-' (like india-europe)`);
    for (const r of pair) if (!REGIONS[r]) bad.push(`globe: no region '${r}' (regions: ${Object.keys(REGIONS).join(", ")})`);
  }
  for (const r of listOf(p.highlight)) if (!REGIONS[r]) bad.push(`globe.highlight: no region '${r}'`);
  if (p.face && !REGIONS[p.face]) bad.push(`globe.face: no region '${p.face}'`);
  return bad;
}
function globe(p, ctx) {
  const t = ctx.t, out = [], spots = {}, zones = {}, R = 3;
  const routes = routesOf(p).filter((r) => r.length === 2 && REGIONS[r[0]] && REGIONS[r[1]]);
  const vols = listOf(p.volumes).map(Number);
  let face = p.face && REGIONS[p.face] ? latlon(REGIONS[p.face], 1) : null;
  if (!face && routes.length) face = norm(latlon(REGIONS[routes[0][0]], 1).map((c, i) => c + latlon(REGIONS[routes[0][1]], 1)[i]));
  if (!face) face = latlon(REGIONS.india, 1);
  const a = -Math.atan2(face[0], face[2]) + (num(p.turn, 0) * Math.PI) / 180 + (num(p.spin, 0) * Math.PI / 180) * t;
  out.push({ ...node3("globe", [R], [0, 0, 0], "#4f8fc0"), r: [0, round3(a), 0] });
  out.push(sphere(R * 1.06, [0, 0, 0], "#bfe3ff", { o: 0.16, seg: 32, m: "basic" }));
  if (ctx.place) {
    const q = rng(5);
    for (let i = 0; i < 120; i++) { const d = norm([q() - 0.5, q() - 0.5, q() - 0.5]); out.push(sphere(0.06 + q() * 0.06, d.map((c) => c * 60), "#ffffff", { m: "basic", seg: 4, bg: true })); }
  }
  const hl = new Set(listOf(p.highlight));
  const used = new Set([...hl, ...routes.flat()]);
  for (const name of used) {
    const v = rotY(latlon(REGIONS[name], R * 1.01), a), pulse = hl.has(name) ? 1 + 0.25 * Math.sin(t * 4) : 1;
    out.push(sphere(0.11 * pulse, v, hl.has(name) ? "#f29f05" : "#ffffff", { e: hl.has(name) ? 1.2 : 0.4, seg: 10 }));
    spots[name] = { p: rotY(latlon(REGIONS[name], R * 1.08), a), n: norm(v) };
  }
  const speed = num(p.speed, 1);
  routes.forEach(([A, B], k) => {
    const va = norm(latlon(REGIONS[A], 1)), vb = norm(latlon(REGIONS[B], 1));
    const ang = Math.acos(clamp(va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2], -1, 1)), lift = 0.08 + 0.32 * ang / Math.PI;
    const vol = clamp(Number.isFinite(vols[k]) ? vols[k] : 1, 0.2, 5), pts = [];
    for (let i = 0; i <= 40; i++) {
      const u = i / 40, s = Math.sin(ang) || 1;
      const w1 = Math.sin((1 - u) * ang) / s, w2 = Math.sin(u * ang) / s, d = norm(va.map((c, j) => c * w1 + vb[j] * w2));
      pts.push(rotY(d.map((c) => c * R * (1.01 + lift * Math.sin(Math.PI * u))), a));
    }
    const c = ["#f29f05", "#e5484d", "#2fa35b", "#7b61ff", "#e2558f", "#2a9d8f"][k % 6];
    out.push(tube(pts, 0.025 + 0.022 * vol, c, { e: 0.4 }));
    if (p.tokens !== false) {
      const n = 1 + Math.round(vol);
      for (let j = 0; j < n; j++) {
        const u = frac(t * 0.18 * speed + j / n), f = u * 40, i0 = Math.floor(f), i1 = Math.min(40, i0 + 1), m = f - i0;
        out.push(box(0.16, 0.16, 0.16, pts[i0].map((cc, jj) => cc + (pts[i1][jj] - cc) * m), "#ffffff", { e: 1.4 }));
      }
    }
    spots[`route${k + 1}`] = { p: pts[20], n: norm(pts[20]) };
  });
  spots.globe = [0, R * 1.15, 0]; spots.north = [0, R * 1.05, 0];
  return { nodes: out, spots, zones, env: envOf("day", ctx.place ? { sky: "#0e1a2b", hemi: ["#ffffff", "#334466", 2.2] } : {}) };
}
const round3 = (v) => Math.round(v * 1000) / 1000;
const node3 = (g, a, p, c) => ({ g, a, p, c });

export const KINDS = {
  factory: { fn: factory, camera: { angle: 18, height: 8, dist: 20, tx: 0, ty: 3.2, tz: -1, fov: 44 } },
  port: { fn: port, camera: { angle: 24, height: 11, dist: 24, tx: -1, ty: 1.5, tz: 2, fov: 44 } },
  city: { fn: city, camera: { angle: 35, height: 20, dist: 30, tx: 0, ty: 1, tz: 0, fov: 42 } },
  farm: { fn: farm, camera: { angle: 16, height: 9, dist: 20, tx: 0, ty: 0.8, tz: -2, fov: 42 } },
  vault: { fn: vault, camera: { angle: 16, height: 4.2, dist: 19, tx: 0.5, ty: 3.6, tz: -3, fov: 44 } },
  exchange: { fn: exchange, camera: { angle: 12, height: 5, dist: 17, tx: 0, ty: 3.6, tz: -1, fov: 44 } },
  globe: { fn: globe, check: globeCheck, camera: { angle: 0, height: 3.2, dist: 11.5, tx: 0, ty: 0.3, tz: 0, fov: 40 } },
};
