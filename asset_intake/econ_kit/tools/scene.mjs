// One composed 1920x1080 still from saanche: items placed at (x, y) with scale, arrows with labels, free texts.
//   node scene.mjs --dist DIR --scene scene.json --out still.png
// scene.json: {"bg": "#f6f1e7", "title": "...", "items": [{"draw", "params", "x", "y", "s"}],
//              "arrows": [{"from": [x, y], "to": [x, y], "color", "label", "dashed", "bend", "w"}],
//              "texts": [{"text", "x", "y", "size", "color"}], "footer": "..."}
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFileSync, existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]]] : acc), []));
const require = createRequire("/opt/node22/lib/node_modules/_");
const { chromium } = require("playwright");
const dist = resolve(args.dist);
const scene = JSON.parse(readFileSync(resolve(args.scene), "utf8"));
const page = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: "Baloo 2"; src: url("fonts/Baloo2.ttf"); font-weight: 400 800; }
@font-face { font-family: "Hind"; src: url("fonts/Hind-SemiBold.ttf"); font-weight: 600; }
@font-face { font-family: "Hind"; src: url("fonts/Hind-Bold.ttf"); font-weight: 700; }
html,body{margin:0} svg{display:block}</style></head><body>
<svg id="s" width="1920" height="1080" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg"></svg>
<script src="draw.js"></script><script src="people.js"></script><script src="econ_saanche.js"></script>
<script>window.drawScene = (sc) => { const D = window.BIEDraw; let out = '<rect width="1920" height="1080" fill="' + (sc.bg || "#f6f1e7") + '"/>';
  out += '<defs><marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>';
  for (const a of sc.arrows || []) { const [x1, y1] = a.from, [x2, y2] = a.to, b = a.bend || 0;
    const mx = (x1 + x2) / 2 - (y2 - y1) * b, my = (y1 + y2) / 2 + (x2 - x1) * b, c = a.color || "#3b3b46";
    out += '<path d="M ' + x1 + ' ' + y1 + ' Q ' + mx + ' ' + my + ' ' + x2 + ' ' + y2 + '" fill="none" stroke="' + c + '" stroke-width="' + (a.w || 10) + '" stroke-linecap="round"' + (a.dashed ? ' stroke-dasharray="18 14"' : '') + ' marker-end="url(#ah)"/>';
    if (a.label) { const lx = (x1 + 2 * mx + x2) / 4, ly = (y1 + 2 * my + y2) / 4 + (a.dy || 0);
      out += '<g transform="translate(' + (lx + (a.dx || 0)) + ' ' + ly + ')"><rect x="' + (-a.label.length * 9 - 22) + '" y="-24" width="' + (a.label.length * 18 + 44) + '" height="48" rx="24" fill="' + c + '"/>' + D.text(a.label, 0, 0, 30, { fill: "#fff" }) + '</g>'; } }
  for (const it of sc.items || []) out += '<g transform="translate(' + it.x + ' ' + it.y + ') scale(' + (it.s || 1) + ')">' + D[it.draw](it.params || {}) + '</g>';
  for (const t of sc.texts || []) out += D.text(t.text, t.x, t.y, t.size || 36, { fill: t.color || "#2b2b33", weight: t.weight || 700 });
  if (sc.title) out += D.text(sc.title, 60, 62, 40, { fill: "#2b2b33", anchor: "start", weight: 800 });
  if (sc.footer) out += D.text(sc.footer, 1890, 1052, 22, { fill: "#8a8f98", anchor: "end", weight: 600 });
  document.getElementById("s").innerHTML = out; return true; };</script></body></html>`;
const TYPES = { ".js": "text/javascript", ".ttf": "font/ttf" };
const server = createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (u === "/" || u === "/index.html") { res.writeHead(200, { "content-type": "text/html" }); res.end(page); return; }
  const p = normalize(join(dist, u));
  if (!p.startsWith(dist + sep) || !existsSync(p) || !statSync(p).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[extname(p)] || "application/octet-stream" }); res.end(readFileSync(p));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
pg.on("pageerror", (e) => console.error("pageerror", e.message));
await pg.goto(`http://127.0.0.1:${server.address().port}/index.html`);
await pg.evaluate(() => document.fonts.ready);
await pg.evaluate((s) => window.drawScene(s), scene);
await pg.evaluate(() => document.fonts.ready);
await pg.screenshot({ path: resolve(args.out) });
await b.close(); server.close();
console.log("wrote", args.out);
