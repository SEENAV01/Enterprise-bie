// Render a VideoSpec with real Remotion (Task 046a bridge proof).
//   node render.mjs --spec spec.json --public <assets parent> --out out.mp4 [--frames 0,40,90 --stills <dir>] [--browser <chrome>]
// Packages (@remotion/bundler, @remotion/renderer, remotion, @remotion/three, three, the React Three Fiber stack, KaTeX,
// D3, 3Dmol.js, Mol*, Matter.js, cannon-es) come from NODE_PATH, pinned by bie/toolbox/web_packages.json.
import { createRequire } from "node:module";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]]] : acc), []));
const here = dirname(fileURLToPath(import.meta.url));
const modules = process.env.NODE_PATH;
const require = createRequire(join(modules, "_"));
const { bundle } = require("@remotion/bundler");
const { renderMedia, renderStill, selectComposition } = require("@remotion/renderer");
const spec = JSON.parse(readFileSync(resolve(args.spec), "utf8"));
const inputProps = { spec };
const serveUrl = await bundle({
  entryPoint: join(here, "Root.tsx"),
  publicDir: resolve(args.public),
  enableCaching: false,               // no webpack cache folder in the working directory (it is half a gigabyte)
  webpackOverride: (config) => ({ ...config, resolve: { ...config.resolve, modules: [modules, "node_modules"] },
    resolveLoader: { ...(config.resolveLoader || {}), modules: [modules, "node_modules"] } }),
});
const chromiumOptions = { gl: process.env.BIE_REMOTION_GL || "swangle", enableMultiProcessOnLinux: true };
const browserExecutable = args.browser || null;
const onBrowserLog = (log) => { if (log.type === "error" || log.type === "warning" || process.env.BIE_REMOTION_LOG) console.error(`[browser ${log.type}] ${log.text}`.slice(0, 500)); };
const composition = await selectComposition({ serveUrl, id: "BieVideo", inputProps, chromiumOptions, browserExecutable });
if (args.frames) {
  const out = resolve(args.stills);
  mkdirSync(out, { recursive: true });
  for (const f of args.frames.split(",").map(Number)) {
    await renderStill({ composition, serveUrl, inputProps, frame: f, output: join(out, `frame-${String(f).padStart(6, "0")}.png`),
      chromiumOptions, browserExecutable, onBrowserLog });
  }
}
if (args.out) {
  await renderMedia({ composition, serveUrl, codec: "h264", outputLocation: resolve(args.out), inputProps, chromiumOptions,
    browserExecutable, concurrency: 1, muted: true, onBrowserLog });
}
console.log(JSON.stringify({ ok: true, durationInFrames: composition.durationInFrames }));
