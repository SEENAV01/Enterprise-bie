// The text audit of a video (Task 048 frame checks; Navin, 3 November 2026: "minimum on-screen text size readable on a phone",
// "label overlap in every mode"): the same page the renderer draws (setFrame), and for every sampled frame each visible text's
// size ON SCREEN (its font size times every camera and scale above it) and the boxes it covers, so tools/text_audit.py can
// count the texts under the floor and the texts that cover each other.
//   node audit.mjs --dist <dir> --spec video_spec.json --out audit.jsonl [--every 30] [--from f --to g] [--page toolbox.html]
// One JSON line per sampled frame: {"frame", "texts": [{"t", "px", "box": [x, y, w, h], "boxes": [[x, y, w, h], ...], "caption"?}]}
// ("caption": the text is the caption strip under the scene, index.tsx Captions; "plan": words the scene plan wrote, the
// show engine's texts and kicker, as against the words inside a saancha).
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { createServer } from "node:http";
import { readFileSync, writeFileSync, existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]?.startsWith("--") || a[i + 1] === undefined ? "1" : a[i + 1]]] : acc), []));
const require = createRequire(join(process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim(), "_"));
const { chromium } = require("playwright");
const spec = JSON.parse(readFileSync(resolve(args.spec), "utf8"));
const dist = resolve(args.dist);
if (args.assets) execFileSync("cp", ["-R", resolve(args.assets) + "/.", dist]);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png",
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp", ".glb": "model/gltf-binary",
  ".gltf": "model/gltf+json", ".woff2": "font/woff2", ".bin": "application/octet-stream" };
const server = createServer((req, res) => {
  const path = normalize(join(dist, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!(path === dist || path.startsWith(dist + sep)) || !existsSync(path) || !statSync(path).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[extname(path).toLowerCase()] || "application/octet-stream" });
  res.end(readFileSync(path));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}/`;
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist",
  "--enable-webgl", "--disable-gpu-sandbox", "--disable-gpu-compositing"] });
const page = await browser.newPage({ viewport: { width: spec.width, height: spec.height } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));

// Runs in the page: every visible text node, its size on screen and its line boxes (frame pixels).
function measure() {
  const root = document.getElementById("root");
  const W = root.clientWidth, H = root.clientHeight;
  const out = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  const opacityOf = (el) => { let o = 1; for (let a = el; a && a !== root; a = a.parentElement) { const cs = getComputedStyle(a); if (cs.display === "none" || cs.visibility === "hidden") return 0; o *= parseFloat(cs.opacity || "1"); } return o; };
  while ((node = walker.nextNode())) {
    const text = (node.textContent || "").replace(/\s+/g, " ").trim();
    if (!text) continue;
    const el = node.parentElement;
    if (!el || el.closest("style,script,defs,clipPath,marker")) continue;
    if (opacityOf(el) < 0.35) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const boxes = Array.from(range.getClientRects()).filter((r) => r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 && r.left < W && r.top < H)
      .map((r) => [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]);
    if (!boxes.length) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize) || 0;
    let scale = 1;
    if (el instanceof SVGGraphicsElement) {
      const bb = el.getBBox(), rr = el.getBoundingClientRect();
      scale = bb.height > 0 ? rr.height / bb.height : 1;
    } else {
      const rr = el.getBoundingClientRect();
      scale = el.offsetHeight > 0 ? rr.height / el.offsetHeight : 1;
    }
    const xs = boxes.map((b) => b[0]), ys = boxes.map((b) => b[1]);
    const x1 = Math.max(...boxes.map((b) => b[0] + b[2])), y1 = Math.max(...boxes.map((b) => b[1] + b[3]));
    const row = { t: text.slice(0, 80), px: Math.round(fs * scale * 10) / 10, box: [Math.min(...xs), Math.min(...ys), x1 - Math.min(...xs), y1 - Math.min(...ys)], boxes };
    if (el.closest(".bie-caption")) row.caption = true;
    if (el.closest(".bie-plan")) row.plan = true;           // words the scene plan wrote (engine textSvg, the kicker)
    out.push(row);
  }
  return out;
}

try {
  await page.goto(base + (args.page || "index.html"));
  await page.waitForFunction(() => window.ready === true);
  await page.evaluate((s) => { window.__VIDEO__ = s; }, spec);
  const total = await page.evaluate(() => window.totalFrames());
  const every = Math.max(1, Number(args.every || 30));
  const first = args.from ? Math.max(0, Number(args.from)) : 0, last = args.to ? Math.min(total, Number(args.to)) : total;
  const lines = [];
  for (let f = first; f < last; f += every) {
    await page.evaluate((n) => window.setFrame(n), f);
    lines.push(JSON.stringify({ frame: f, texts: await page.evaluate(measure) }));
  }
  writeFileSync(resolve(args.out), lines.join("\n") + "\n");
} catch (e) {
  errors.push(String(e && e.message ? e.message : e));
}
console.log(JSON.stringify({ errors }));
await browser.close();
server.close();
if (errors.length) process.exit(1);
