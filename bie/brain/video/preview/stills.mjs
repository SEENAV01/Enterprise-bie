// Stills (PNG) of chosen frames, or a quick MP4 preview through ffmpeg.
//   node stills.mjs --dist <dir> --spec video_spec.json --frames 0,45,120 --out <dir> [--page toolbox.html]
//   node stills.mjs --dist <dir> --spec video_spec.json --mp4 out.mp4 [--audio narration.wav] [--assets <dir>] [--page toolbox.html] [--from f --to g]
// Frames are captured straight from Chromium's compositor (CDP Page.captureScreenshot) once setFrame has painted them:
// Playwright's page.screenshot costs about 0.4 s more per frame for the same pixels (measured, Task 046 Part C, PR 4);
// --capture playwright keeps the old path for a comparison.
// The dist folder is served over http://127.0.0.1 (Task 046a: glTF models, PDB files and fonts load with fetch, which
// file:// pages cannot do). WebGL runs on SwiftShader, so three.js, 3Dmol.js and Mol* draw without a GPU.
import { createRequire } from "node:module";
import { execFileSync, spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync, existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]?.startsWith("--") || a[i + 1] === undefined ? "1" : a[i + 1]]] : acc), []));
const require = createRequire(join(process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim(), "_"));
const { chromium } = require("playwright");
const spec = JSON.parse(readFileSync(resolve(args.spec), "utf8"));
const dist = resolve(args.dist);
if (args.assets) execFileSync("cp", ["-R", resolve(args.assets) + "/.", dist]);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png",
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp", ".glb": "model/gltf-binary",
  ".gltf": "model/gltf+json", ".pdb": "chemical/x-pdb", ".sdf": "chemical/x-mdl-sdfile", ".woff2": "font/woff2", ".bin": "application/octet-stream" };
const server = createServer((req, res) => {
  const path = normalize(join(dist, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!(path === dist || path.startsWith(dist + sep)) || !existsSync(path) || !statSync(path).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYPES[extname(path).toLowerCase()] || "application/octet-stream" });
  res.end(readFileSync(path));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}/`;
// WebGL (three.js, 3Dmol.js, Mol*) runs on SwiftShader in the GPU process; the page itself is composited in software
// (--disable-gpu-compositing): compositing through the emulated GPU cost about 0.25 s a frame on a plain 2D scene and
// made every capture slower (measured, Task 046 Part C, PR 4). The frames are the same pixels either way.
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist",
  "--enable-webgl", "--disable-gpu-sandbox", "--disable-gpu-compositing"] });
const page = await browser.newPage({ viewport: { width: spec.width, height: spec.height } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
const cdp = args.capture === "playwright" ? null : await page.context().newCDPSession(page);
// setFrame resolves after the frame is painted (two animation frames after React committed, every block's own canvas
// drawn, every image loaded), so the compositor's current frame is the one asked for.
const capture = async (format, quality) => {
  if (!cdp) return page.screenshot(format === "png" ? { type: "png" } : { type: "jpeg", quality });
  const { data } = await cdp.send("Page.captureScreenshot", format === "png" ? { format: "png" } : { format: "jpeg", quality });
  return Buffer.from(data, "base64");
};
try {
  await page.goto(base + (args.page || "index.html"));
  await page.waitForFunction(() => window.ready === true);
  await page.evaluate((s) => { window.__VIDEO__ = s; }, spec);
  if (args.frames) {
    const out = resolve(args.out); mkdirSync(out, { recursive: true });
    for (const f of args.frames.split(",").map(Number)) {
      await page.evaluate((n) => window.setFrame(n), f);
      writeFileSync(join(out, `frame-${String(f).padStart(6, "0")}.png`), await capture("png"));
    }
  } else if (args.mp4) {
    const total = await page.evaluate(() => window.totalFrames());
    const first = args.from ? Math.max(0, Number(args.from)) : 0;        // Task 046: a chunk of a long video
    const last = args.to ? Math.min(total, Number(args.to)) : total;
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(spec.fps), "-c:v", "mjpeg", "-i", "-",
      ...(args.audio ? ["-i", resolve(args.audio)] : []), "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
      ...(args.audio ? ["-c:a", "aac", "-b:a", "160k", "-shortest"] : []), resolve(args.mp4)], { stdio: ["pipe", "inherit", "inherit"] });
    for (let f = first; f < last; f++) {
      await page.evaluate((n) => window.setFrame(n), f);
      const buf = await capture("jpeg", 92);
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    }
    ff.stdin.end();
    await new Promise((r, j) => ff.on("close", (c) => (c === 0 ? r() : j(new Error("ffmpeg " + c)))));
  }
} catch (e) {
  errors.push(String(e && e.message ? e.message : e));
}
console.log(JSON.stringify({ errors }));
await browser.close();
server.close();
if (errors.length) process.exit(1);
