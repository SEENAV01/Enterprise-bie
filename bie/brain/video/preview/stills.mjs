// Stills (PNG) of chosen frames, or a quick MP4 preview through ffmpeg.
//   node stills.mjs --dist <dir> --spec video_spec.json --frames 0,45,120 --out <dir>
//   node stills.mjs --dist <dir> --spec video_spec.json --mp4 out.mp4 [--audio narration.wav] [--assets <dir>]
import { createRequire } from "node:module";
import { execFileSync, spawn } from "node:child_process";
import { mkdirSync, readFileSync, copyFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]?.startsWith("--") || a[i + 1] === undefined ? "1" : a[i + 1]]] : acc), []));
const require = createRequire(join(process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim(), "_"));
const { chromium } = require("playwright");
const spec = JSON.parse(readFileSync(resolve(args.spec), "utf8"));
const dist = resolve(args.dist);
if (args.assets) execFileSync("cp", ["-R", resolve(args.assets) + "/.", dist]);
const browser = await chromium.launch({ args: ["--disable-gpu", "--allow-file-access-from-files"] });
const page = await browser.newPage({ viewport: { width: spec.width, height: spec.height } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(pathToFileURL(join(dist, "index.html")).href);
await page.waitForFunction(() => window.ready === true);
await page.evaluate((s) => { window.__VIDEO__ = s; }, spec);
if (args.frames) {
  const out = resolve(args.out); mkdirSync(out, { recursive: true });
  for (const f of args.frames.split(",").map(Number)) {
    await page.evaluate((n) => window.setFrame(n), f);
    await page.screenshot({ path: join(out, `frame-${String(f).padStart(6, "0")}.png`) });
  }
} else if (args.mp4) {
  const total = await page.evaluate(() => window.totalFrames());
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(spec.fps), "-c:v", "mjpeg", "-i", "-",
    ...(args.audio ? ["-i", resolve(args.audio)] : []), "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
    ...(args.audio ? ["-c:a", "aac", "-b:a", "160k", "-shortest"] : []), resolve(args.mp4)], { stdio: ["pipe", "inherit", "inherit"] });
  for (let f = 0; f < total; f++) {
    await page.evaluate((n) => window.setFrame(n), f);
    const buf = await page.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on("close", (c) => (c === 0 ? r() : j(new Error("ffmpeg " + c)))));
}
console.log(JSON.stringify({ errors }));
await browser.close();
if (errors.length) process.exit(1);
