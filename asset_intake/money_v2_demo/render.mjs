// Render a frame range of the demo to an MP4 (same page and window API as BIE's stills.mjs).
//   node render.mjs --dist dist --spec spec.json --from 0 --to 9000 --out part0.mp4
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { readFileSync, existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]]] : acc), []));
const require = createRequire("/opt/node22/lib/node_modules/_");
const { chromium } = require("playwright");
const spec = JSON.parse(readFileSync(resolve(args.spec), "utf8"));
const dist = resolve(args.dist);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml", ".ttf": "font/ttf" };
const server = createServer((req, res) => {
  const path = normalize(join(dist, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!(path === dist || path.startsWith(dist + sep)) || !existsSync(path) || !statSync(path).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[extname(path).toLowerCase()] || "application/octet-stream" });
  res.end(readFileSync(path));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: spec.width, height: spec.height } });
await page.goto(`http://127.0.0.1:${server.address().port}/index.html`);
await page.waitForFunction(() => window.ready === true);
await page.evaluate((s) => { window.__VIDEO__ = s; }, spec);
const total = await page.evaluate(() => window.totalFrames());
const from = Number(args.from || 0), to = Math.min(total, Number(args.to || total));
const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(spec.fps), "-c:v", "mjpeg", "-i", "-",
  "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", resolve(args.out)], { stdio: ["pipe", "inherit", "inherit"] });
const t0 = Date.now();
for (let f = from; f < to; f++) {
  await page.evaluate((n) => window.setFrame(n), f);
  const buf = await page.screenshot({ type: "jpeg", quality: 90 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  if ((f - from) % 900 === 0) console.log(`frame ${f} of ${to}, ${((f - from) / ((Date.now() - t0) / 1000 + 1e-9)).toFixed(1)} fps`);
}
ff.stdin.end();
await new Promise((r, j) => ff.on("close", (c) => (c === 0 ? r() : j(new Error("ffmpeg " + c)))));
await browser.close(); server.close();
console.log("done", from, to);
