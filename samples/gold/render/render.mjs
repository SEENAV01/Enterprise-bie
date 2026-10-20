// Renders a timeline frame by frame in Chromium and encodes it with ffmpeg.
//   node render.mjs --timeline t.json --stills 0,120,900 --out dir        (PNG stills for review)
//   node render.mjs --timeline t.json --out video.mp4 [--audio narration.wav] [--workers 2] [--from F --to F]
import { spawn, execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(join(execFileSync("npm", ["root", "-g"]).toString().trim(), "_"));
const { chromium } = require("playwright");

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]?.startsWith("--") || a[i + 1] === undefined ? "1" : a[i + 1]]] : acc), []));
const timeline = JSON.parse(readFileSync(resolve(args.timeline), "utf8"));
const page_url = pathToFileURL(join(here, "dist/index.html")).href;

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: timeline.width, height: timeline.height }, deviceScaleFactor: 1 });
  await page.goto(page_url);
  await page.waitForFunction(() => window.ready === true);
  await page.evaluate((t) => { window.__TIMELINE__ = t; }, timeline);
  return page;
}

async function stills(browser) {
  const out = resolve(args.out);
  mkdirSync(out, { recursive: true });
  const page = await openPage(browser);
  for (const f of args.stills.split(",").map(Number)) {
    await page.evaluate((n) => window.setFrame(n), f);
    await page.screenshot({ path: join(out, `frame-${String(f).padStart(5, "0")}.png`) });
  }
  console.log(`stills written to ${out}`);
}

async function segment(browser, from, to, file) {
  const page = await openPage(browser);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(timeline.fps), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", String(timeline.fps), file], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now();
  for (let f = from; f < to; f++) {
    await page.evaluate((n) => window.setFrame(n), f);
    const buf = await page.screenshot({ type: "jpeg", quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    if ((f - from) % 300 === 0) console.log(`[${from}-${to}] frame ${f} (${((Date.now() - t0) / Math.max(1, f - from)).toFixed(0)} ms/frame)`);
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on("close", (c) => (c === 0 ? r() : j(new Error("ffmpeg " + c)))));
  await page.close();
}

async function video(browser) {
  const out = resolve(args.out);
  const from = Number(args.from ?? 0), to = Number(args.to ?? timeline.frames);
  const workers = Number(args.workers ?? 2);
  const tmp = out + ".parts";
  rmSync(tmp, { recursive: true, force: true });
  mkdirSync(tmp, { recursive: true });
  const size = Math.ceil((to - from) / workers);
  const parts = [];
  for (let w = 0; w < workers; w++) {
    const a = from + w * size, b = Math.min(to, a + size);
    if (a < b) parts.push({ a, b, file: join(tmp, `part-${w}.mp4`) });
  }
  await Promise.all(parts.map((p) => segment(browser, p.a, p.b, p.file)));
  writeFileSync(join(tmp, "list.txt"), parts.map((p) => `file '${p.file}'`).join("\n"));
  const audio = args.audio ? ["-ss", String(from / timeline.fps), "-t", String((to - from) / timeline.fps), "-i", resolve(args.audio)] : [];
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", join(tmp, "list.txt"), ...audio,
    "-c:v", "copy", ...(args.audio ? ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-shortest"] : []), "-movflags", "+faststart", out], { stdio: "inherit" });
  rmSync(tmp, { recursive: true, force: true });
  console.log(`video written to ${out}`);
}

const browser = await chromium.launch({ args: ["--disable-gpu", "--font-render-hinting=none"] });
try {
  if (args.stills) await stills(browser); else await video(browser);
} finally {
  await browser.close();
}
