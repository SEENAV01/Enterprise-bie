// Bundles the preview harness with esbuild; "remotion" resolves to the small compatible shim.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = process.argv[2] || join(here, "dist");
const nodePath = process.env.NODE_PATH || execFileSync("npm", ["root", "-g"]).toString().trim();
import { existsSync } from "node:fs";
const candidates = [process.env.ESBUILD, join(nodePath, "esbuild/bin/esbuild"), "/opt/npm-tools/node_modules/esbuild/bin/esbuild"].filter(Boolean);
const esbuild = candidates.find((c) => existsSync(c)) || "esbuild";
mkdirSync(out, { recursive: true });
execFileSync(esbuild, [join(here, "main.tsx"), "--bundle", "--format=iife", "--jsx=automatic", "--minify",
  `--alias:remotion=${join(here, "remotion-lite.tsx")}`, "--define:process.env.NODE_ENV=\"production\"",
  `--outfile=${join(out, "bundle.js")}`], { stdio: "inherit", env: { ...process.env, NODE_PATH: nodePath } });
writeFileSync(join(out, "index.html"), `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#06121c;width:1920px;height:1080px;overflow:hidden}#root{position:relative;width:1920px;height:1080px}</style>
</head><body><div id="root"></div><script src="bundle.js"></script></body></html>`);
console.log("built " + out);
