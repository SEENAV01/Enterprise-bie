// Checks every economy saancha in saanche/manifest.json: it exists, renders with its defaults and with the still
// variants, gives well-formed SVG (parses as XML) and never prints NaN or undefined.
//   node tests/test_saanche.mjs [path/to/money_v2_demo/dist]
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
const here = dirname(fileURLToPath(import.meta.url)), kit = resolve(here, "..");
const v2 = resolve(process.argv[2] || join(kit, "..", "money_v2_demo", "dist"));
const ctx = { window: {} }; vm.createContext(ctx);
for (const f of [join(v2, "draw.js"), join(v2, "people.js"), join(kit, "saanche", "econ_saanche.js")]) vm.runInContext(readFileSync(f, "utf8"), ctx, { filename: f });
const D = ctx.window.BIEDraw, man = JSON.parse(readFileSync(join(kit, "saanche", "manifest.json"), "utf8"));
const cases = man.saanche.map((s) => ({ draw: s.name, params: {} }));
for (const c of ["stills_cells1.json", "stills_cells2.json", "stills_cells3.json"]) cases.push(...JSON.parse(readFileSync(join(kit, "saanche", c), "utf8")));
for (const it of JSON.parse(readFileSync(join(kit, "saanche", "demo_scene_crr.json"), "utf8")).items) cases.push(it);
for (const p of [0, 0.3, 1]) cases.push({ draw: "paper", params: { stamp: "FAIL", stampP: p, p } }, { draw: "crowd", params: { share: 0.5, p } }, { draw: "vault", params: { door: p, lockP: p } });
let fails = 0;
function wellFormed(svg) {
  // a tiny tag balance check (no XML parser in node core): every opened element is closed in order
  const stack = [];
  for (const m of svg.matchAll(/<(\/?)([a-zA-Z]+)([^>]*?)(\/?)>/g)) {
    if (m[1]) { if (stack.pop() !== m[2]) return false; } else if (!m[4]) stack.push(m[2]);
  }
  return stack.length === 0;
}
for (const c of cases) {
  const fn = D[c.draw];
  let out = "";
  try { out = fn(c.params || {}); } catch (e) { console.log("FAIL", c.draw, "threw", e.message); fails++; continue; }
  if (typeof out !== "string" || !out.length) { console.log("FAIL", c.draw, "empty"); fails++; continue; }
  if (/NaN|undefined/.test(out)) { console.log("FAIL", c.draw, JSON.stringify(c.params), "has NaN/undefined"); fails++; }
  if (!wellFormed(out)) { console.log("FAIL", c.draw, JSON.stringify(c.params), "unbalanced tags"); fails++; }
}
for (const s of man.saanche) if (typeof D[s.name] !== "function") { console.log("FAIL missing", s.name); fails++; }
console.log(`${cases.length} cases, ${fails} failures`);
process.exit(fails ? 1 : 0);
