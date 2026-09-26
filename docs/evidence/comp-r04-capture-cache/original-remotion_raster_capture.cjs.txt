'use strict';
// H8 actual renderer. No diagnostic bridge and no caller-provided PASS receipts.
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
 const frames=[],rasterFrames=[],errors=[];
 try{
  const composition=await selectComposition({serveUrl,id:req.composition_id,puppeteerInstance:browser});
  if(composition.width!==req.width||composition.height!==req.height||composition.fps!==req.fps||composition.durationInFrames!==req.frame_count)throw new Error('CAPTURE_COMPOSITION_MISMATCH');
  for(let frame=0;frame<req.frame_count;frame++){
   async function shot(kind,index){
    const mode=(kind==='full'||kind==='repeat')?{kind:'full'}:{kind,target_id:req.rasterTargets[index].target_id};
    const measurements=[];
    const onBrowserLog=log=>{
     if(log.text.startsWith('BIE_PAINT_V1:')){
      const value=JSON.parse(log.text.slice(13));
      if(value.nonce===req.nonce&&value.frame===frame&&JSON.stringify(value.raster.mode)===JSON.stringify(mode))measurements.push(value);
     }else if(log.type==='error')errors.push(log.text);
    };
    const name=`frame-${String(frame).padStart(6,'0')}`+((kind==='full'||kind==='repeat')?`-${kind}`:`-target-${String(index).padStart(3,'0')}-${kind}`)+'.png';
    const output=path.join(out,name);
    await renderStill({composition,serveUrl,frame,output,imageFormat:'png',puppeteerInstance:browser,onBrowserLog,
      inputProps:{__bieRasterMode:mode},timeoutInMilliseconds:30000});
    if(!measurements.length)throw new Error('CAPTURE_DOM_MEASUREMENT_MISSING:'+frame+':'+kind);
    const unique=[...new Set(measurements.map(m=>JSON.stringify(m)))];
    if(unique.length!==1)throw new Error('CAPTURE_DOM_NONDETERMINISM:'+frame+':'+kind);
    const m=measurements[0];
    if(m.raster.fonts_ready!==true||m.raster.image_errors.length)throw new Error('CAPTURE_ASSET_READINESS');
    return {file:{file:name,sha256:hash(output)},measurement:m};
   }
   const full=await shot('full');const targets=[];
   for(let i=0;i<req.rasterTargets.length;i++){
    const row={target_id:req.rasterTargets[i].target_id};
    for(const kind of ['baseline','isolated','muted']){
     const value=await shot(kind,i);
     if(JSON.stringify(value.measurement.raster.inventory)!==JSON.stringify(full.measurement.raster.inventory))throw new Error('CAPTURE_DOM_MODE_DRIFT');
     row[kind]=value.file;
    }
    targets.push(row);
   }
   const repeat=await shot('repeat');
   if(JSON.stringify(repeat.measurement.raster.inventory)!==JSON.stringify(full.measurement.raster.inventory))throw new Error('CAPTURE_DOM_RESTORE_DRIFT');
   frames.push({frame,image:full.file.file,image_sha256:full.file.sha256,measurement:full.measurement});
   rasterFrames.push({frame,full:full.file,repeat:repeat.file,inventory:full.measurement.raster.inventory,targets});
  }
  const outputLocation=path.join(out,'captured.mp4');
  await renderMedia({composition,serveUrl,outputLocation,codec:'h264',pixelFormat:'yuv420p',concurrency:1,puppeteerInstance:browser,
    inputProps:{__bieRasterMode:{kind:'full'}}});
  const counterfactual={schema_version:'bie.counterfactual-capture.v1',scope:'REAL_REMOTION_COUNTERFACTUAL_PIXELS',
    scene_sha256:req.scene_sha256,manifest_sha256:req.manifest_sha256,width:req.width,height:req.height,fps:req.fps,
    frame_count:req.frame_count,targets:req.rasterTargets,frames:rasterFrames,browser_errors:errors};
  const result={schema_version:'bie.actual-remotion-paint.v1',nonce:req.nonce,frames,browser_errors:errors,counterfactual,
    scope:'REAL_REMOTION_INSTRUMENTED_UNCHANGED_SCENE',real_react:true,real_remotion:true,media_sha256:hash(outputLocation),accepted:false};
  fs.writeFileSync(path.join(out,'RESULT.json'),JSON.stringify(result,null,2));
 }finally{await browser.close({silent:true});}
}
main().catch(e=>{console.error(e.stack||String(e));process.exitCode=2;});
