// Stills of saanche: each cell draws one BIEDraw function with its params, caption below.
//   node stills.mjs --dist DIR --cells cells.json --out sheet.png [--cols 4] [--w 1920]
// cells.json: [{"draw": "centralBank", "params": {...}, "caption": "..."}, ...]
// DIR must hold draw.js, people.js, econ_saanche.js and fonts/ (served over a local http server).
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFileSync, existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]]] : acc), []));
const require = createRequire("/opt/node22/lib/node_modules/_");
const { chromium } = require("playwright");
const dist = resolve(args.dist);
const cells = JSON.parse(readFileSync(resolve(args.cells), "utf8"));
const cols = Number(args.cols || 4), W = Number(args.w || 1920), cw = W / cols, ch = cw * 0.82;
const rows = Math.ceil(cells.length / cols), H = Math.ceil(rows * ch);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".ttf": "font/ttf", ".svg": "image/svg+xml" };
const page = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face { font-family: "Baloo 2"; src: url("fonts/Baloo2.ttf"); font-weight: 400 800; }
@font-face { font-family: "Hind"; src: url("fonts/Hind-SemiBold.ttf"); font-weight: 600; }
@font-face { font-family: "Hind"; src: url("fonts/Hind-Bold.ttf"); font-weight: 700; }
html,body{margin:0;background:#f6f1e7} svg{display:block}</style></head><body>
<svg id="s" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"></svg>
<script src="draw.js"></script><script src="people.js"></script><script src="econ_saanche.js"></script>
<script>window.drawCells = (cells) => { const D = window.BIEDraw; let out = "";
  cells.forEach((c, i) => { const x = (i % ${cols}) * ${cw} + ${cw} / 2, y = Math.floor(i / ${cols}) * ${ch};
    const sc = c.scale || 1; let body = "";
    try { body = D[c.draw](c.params || {}); } catch (e) { body = D.text("ERROR " + c.draw + ": " + e.message, 0, 0, 18, { fill: "#c00" }); }
    out += '<g transform="translate(' + x + ' ' + (y + ${ch} * (c.base || 0.72)) + ') scale(' + sc + ')">' + body + '</g>';
    out += D.text(c.caption || c.draw, x, y + ${ch} - 26, 22, { fill: "#3b3b46", weight: 600 });
    out += '<rect x="' + (x - ${cw} / 2 + 6) + '" y="' + (y + 6) + '" width="' + (${cw} - 12) + '" height="' + (${ch} - 12) + '" rx="14" fill="none" stroke="#e2d8c6"/>'; });
  document.getElementById("s").innerHTML = out; return true; };</script></body></html>`;
const server = createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (u === "/" || u === "/index.html") { res.writeHead(200, { "content-type": "text/html" }); res.end(page); return; }
  const p = normalize(join(dist, u));
  if (!(p.startsWith(dist + sep)) || !existsSync(p) || !statSync(p).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[extname(p)] || "application/octet-stream" }); res.end(readFileSync(p));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: Number(args.scale || 1) });
pg.on("pageerror", (e) => console.error("pageerror", e.message));
await pg.goto(`http://127.0.0.1:${server.address().port}/index.html`);
await pg.evaluate(() => document.fonts.ready);
await pg.evaluate((c) => window.drawCells(c), cells);
await pg.evaluate(() => document.fonts.ready);
await pg.screenshot({ path: resolve(args.out) });
await b.close(); server.close();
console.log("wrote", args.out, cells.length, "cells");
