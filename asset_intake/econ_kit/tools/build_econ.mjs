// Bundle the economy kit preview (BIE core blocks + canvas_build + curve_story) with esbuild, like BIE's build.mjs.
//   node build_econ.mjs <dist>
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const kit = dirname(here);
const repo = join(kit, "..", "..");
const out = process.argv[2] || join(kit, "dist");
const nodePath = process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim();
const candidates = [process.env.ESBUILD, join(nodePath, "esbuild/bin/esbuild"), "/opt/npm-tools/node_modules/esbuild/bin/esbuild"].filter(Boolean);
const esbuild = candidates.find((c) => existsSync(c)) || "esbuild";
mkdirSync(out, { recursive: true });
execFileSync(esbuild, [join(kit, "preview", "main-econ.tsx"), "--bundle", "--format=iife", "--jsx=automatic", "--minify",
  `--alias:remotion=${join(repo, "bie/brain/video/preview/remotion-lite.tsx")}`, "--define:process.env.NODE_ENV=\"production\"",
  "--define:global=globalThis", `--outfile=${join(out, "econ.js")}`], { stdio: "inherit", env: { ...process.env, NODE_PATH: nodePath } });
writeFileSync(join(out, "econ.html"), `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#fbf8f1;width:1920px;height:1080px;overflow:hidden}#root{position:relative;width:1920px;height:1080px}</style>
</head><body><div id="root"></div><script src="econ.js"></script></body></html>`);
console.log("built " + out);
