'use strict';
// H7 real Remotion producer. Never imports the legacy API-double bridges.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {createRequire}=require('node:module');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function main(){
 const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
 const fromProject=createRequire(path.join(req.workspace,'package.json'));
 const {bundle}=fromProject('@remotion/bundler');
 const {selectComposition,renderStill,renderMedia,openBrowser}=fromProject('@remotion/renderer');
 for(const name of ['remotion','@remotion/renderer','@remotion/bundler']){
  if(fromProject(name+'/package.json').version!==req.remotion_version)throw new Error('CAPTURE_PIN_MISMATCH:'+name);
 }
 const out=req.output;fs.mkdirSync(out,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(req.workspace,'qa-capture-entry.tsx'),outDir:path.join(out,'bundle'),publicDir:path.join(req.workspace,'public')});
 const browser=await openBrowser('chrome',{browserExecutable:req.browser,chromiumOptions:{enableMultiProcessOnLinux:true}});
 const frames=[],errors=[];
 try{
  const composition=await selectComposition({serveUrl,id:req.composition_id,puppeteerInstance:browser});
  if(composition.width!==req.width||composition.height!==req.height||composition.fps!==req.fps||composition.durationInFrames!==req.frame_count)throw new Error('CAPTURE_COMPOSITION_MISMATCH');
  for(let frame=0;frame<req.frame_count;frame++){
   const measurements=[];
   const onBrowserLog=log=>{
    if(log.text.startsWith('BIE_PAINT_V1:')){const value=JSON.parse(log.text.slice(13));if(value.nonce===req.nonce&&value.frame===frame)measurements.push(value);}
    else if(log.type==='error')errors.push(log.text);
   };
   const output=path.join(out,`frame-${String(frame).padStart(6,'0')}.png`);
   await renderStill({composition,serveUrl,frame,output,imageFormat:'png',puppeteerInstance:browser,onBrowserLog,timeoutInMilliseconds:30000});
   if(!measurements.length)throw new Error('CAPTURE_DOM_MEASUREMENT_MISSING:'+frame);
   const unique=[...new Set(measurements.map(m=>JSON.stringify(m)))];
   if(unique.length!==1)throw new Error('CAPTURE_DOM_NONDETERMINISM:'+frame);
   frames.push({frame,image:path.basename(output),image_sha256:hash(output),measurement:measurements[0]});
  }
  // This media uses the same original Scene plus a nonpainting observation component.
  const outputLocation=path.join(out,'captured.mp4');
  await renderMedia({composition,serveUrl,outputLocation,codec:'h264',pixelFormat:'yuv420p',concurrency:1,puppeteerInstance:browser});
  const result={schema_version:'bie.actual-remotion-paint.v1',nonce:req.nonce,frames,browser_errors:errors,
   scope:'REAL_REMOTION_INSTRUMENTED_UNCHANGED_SCENE',real_react:true,real_remotion:true,media_sha256:hash(outputLocation),accepted:false};
  fs.writeFileSync(path.join(out,'RESULT.json'),JSON.stringify(result,null,2));
 }finally{await browser.close({silent:true});}
}
main().catch(e=>{console.error(e.stack||String(e));process.exitCode=2;});
