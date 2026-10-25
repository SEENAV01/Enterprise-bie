// Bundles the preview harness with esbuild; "remotion" resolves to the small compatible shim.
//   node build.mjs <dist>             core blocks only (bundle.js + index.html), as before
//   node build.mjs <dist> --toolbox   also the toolbox bundle (toolbox.js + toolbox.css + toolbox.html, Task 046a):
//                                     the core blocks plus three.js, KaTeX, D3, 3Dmol.js, Mol*, matter.js, cannon-es
//                                     blocks; "@remotion/three" resolves to three-lite.tsx (ThreeCanvas shim).
// Packages come from NODE_PATH (the CI lane installs them pinned, as of tools/npm_before.txt).
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = process.argv[2] && !process.argv[2].startsWith("--") ? process.argv[2] : join(here, "dist");
const toolbox = process.argv.includes("--toolbox");
const nodePath = process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim();
const candidates = [process.env.ESBUILD, join(nodePath, "esbuild/bin/esbuild"), "/opt/npm-tools/node_modules/esbuild/bin/esbuild"].filter(Boolean);
const esbuild = candidates.find((c) => existsSync(c)) || "esbuild";
mkdirSync(out, { recursive: true });
const common = ["--bundle", "--format=iife", "--jsx=automatic", "--minify", `--alias:remotion=${join(here, "remotion-lite.tsx")}`,
  "--define:process.env.NODE_ENV=\"production\"", "--define:global=globalThis"];
const env = { ...process.env, NODE_PATH: nodePath };
execFileSync(esbuild, [join(here, "main.tsx"), ...common, `--outfile=${join(out, "bundle.js")}`], { stdio: "inherit", env });
const page = (script, css) => `<!doctype html><html><head><meta charset="utf-8">${css ? `<link rel="stylesheet" href="${css}">` : ""}
<style>html,body{margin:0;padding:0;background:#06121c;width:1920px;height:1080px;overflow:hidden}#root{position:relative;width:1920px;height:1080px}</style>
</head><body><div id="root"></div><script src="${script}"></script></body></html>`;
writeFileSync(join(out, "index.html"), page("bundle.js"));
if (toolbox) {
  execFileSync(esbuild, [join(here, "main-toolbox.tsx"), ...common, `--alias:@remotion/three=${join(here, "three-lite.tsx")}`,
    "--loader:.woff2=dataurl", "--loader:.woff=dataurl", "--loader:.ttf=dataurl", "--log-level=error",
    `--outfile=${join(out, "toolbox.js")}`], { stdio: "inherit", env });
  writeFileSync(join(out, "toolbox.html"), page("toolbox.js", existsSync(join(out, "toolbox.css")) ? "toolbox.css" : ""));
}
console.log("built " + out + (toolbox ? " (with toolbox)" : ""));
