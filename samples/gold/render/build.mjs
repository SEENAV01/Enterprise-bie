// Bundles the renderer into dist/ (index.html + bundle.js) with esbuild.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const nodePath = execFileSync("npm", ["root", "-g"]).toString().trim();
const esbuild = process.env.ESBUILD || "/opt/npm-tools/node_modules/esbuild/bin/esbuild";
mkdirSync(join(here, "dist"), { recursive: true });
execFileSync(esbuild, [join(here, "src/main.tsx"), "--bundle", "--format=iife", "--jsx=automatic", "--minify",
  "--define:process.env.NODE_ENV=\"production\"", `--outfile=${join(here, "dist/bundle.js")}`],
  { stdio: "inherit", env: { ...process.env, NODE_PATH: nodePath } });
writeFileSync(join(here, "dist/index.html"), `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#071624;width:1920px;height:1080px;overflow:hidden}#root{position:relative;width:1920px;height:1080px}</style>
</head><body><div id="root"></div><script src="bundle.js"></script></body></html>`);
console.log("built dist/");
