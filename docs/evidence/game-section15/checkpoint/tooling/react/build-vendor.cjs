const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const esbuild = require('esbuild');
const root = __dirname;
const out = path.resolve(root, '../../bie/game_engine/react_runtime_engine/vendor');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const versions = {react: '19.3.0', 'react-dom': '19.3.0', esbuild: '0.28.2'};
async function main() {
for (const [name, version] of Object.entries(versions)) {
  const installed = require(name + '/package.json').version;
  if (installed !== version) throw new Error('BIE_VENDOR_VERSION_MISMATCH:' + name);
}
fs.mkdirSync(out, {recursive:true});
const confinedResolver = {name:'bie-pinned-local-dependencies', setup(build) {
  build.onResolve({filter:/.*/}, args => {
    const from = args.importer ? path.dirname(path.join(root,args.importer)) : root;
    const resolved = args.kind === 'entry-point' ? path.join(root,'vendor-entry.js') : require.resolve(args.path,{paths:[from]});
    const relative = path.relative(root,resolved);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('BIE_VENDOR_RESOLUTION_ESCAPE');
    return {path:relative.replaceAll('\\','/'),namespace:'pinned'};
  });
  build.onLoad({filter:/.*/,namespace:'pinned'}, args => ({contents:fs.readFileSync(path.join(root,args.path),'utf8'),loader:'js'}));
}};
const result = await esbuild.build({absWorkingDir:root, entryPoints:['./vendor-entry.js'],plugins:[confinedResolver],
  outfile:path.join(out, 'react-vendor.js'), bundle:true, write:false, metafile:true,
  platform:'browser', target:'es2020', format:'iife', globalName:'BIEReactVendor',
  preserveSymlinks:true, tsconfigRaw:{compilerOptions:{}},
  minify:true, legalComments:'external', charset:'utf8',
  define:{'process.env.NODE_ENV':'"production"'}});
for (const info of Object.values(result.metafile.outputs)) {
  if (info.imports.some(x => x.external)) throw new Error('BIE_VENDOR_EXTERNAL_IMPORT');
}
const exportSource = '\nexport const React = BIEReactVendor.React;\nexport const createRoot = BIEReactVendor.createRoot;\nexport const flushSync = BIEReactVendor.flushSync;\nexport const reactDomVersion = BIEReactVendor.reactDomVersion;\n';
for (const file of result.outputFiles) {
  fs.writeFileSync(file.path, file.path.endsWith('.js') ? file.text + exportSource : file.contents);
}
for (const name of ['react','react-dom','scheduler']) {
  fs.copyFileSync(path.join(root,'node_modules',name,'LICENSE'),path.join(out,name+'-LICENSE.txt'));
}
const sources = Object.keys(result.metafile.inputs).sort().map(name => {
  const relative = name.replace(/^pinned:/,'');
  return {path:relative.replaceAll('\\','/'),sha256:sha(fs.readFileSync(path.resolve(root,relative)))};
});
const files = fs.readdirSync(out).filter(n => n !== 'vendor-manifest.json').sort().map(name => {
  const data = fs.readFileSync(path.join(out,name)); return {path:name,sha256:sha(data),size_bytes:data.length};
});
const manifest = {schema_version:'bie.game.react-vendor/1',versions,
  package_lock_sha256:sha(fs.readFileSync(path.join(root,'package-lock.json'))),
  build_script_sha256:sha(fs.readFileSync(__filename)), sources, files,
  network_at_runtime:false, product_accepted:false};
const bytes = JSON.stringify(manifest,null,2)+'\n';
fs.writeFileSync(path.join(out,'vendor-manifest.json'),bytes);
fs.writeFileSync(path.join(out,'../pins.py'),
  '# Generated from the reviewed pinned vendor build.\nVENDOR_MANIFEST_SHA256 = '+JSON.stringify(sha(bytes))+'\n');
console.log(JSON.stringify({versions,manifest_sha256:sha(bytes),files},null,2));
}
main().catch(error => { console.error(error); process.exitCode=1; });
