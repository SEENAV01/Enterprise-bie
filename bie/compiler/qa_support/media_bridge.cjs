// H11 MEDIA DIAGNOSTIC ONLY: real TypeScript/JS execution, explicitly NOT React/Remotion.
// Lazy vnode traversal models Sequence local-frame scoping; no audio is played.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process');
const tsc=fs.realpathSync(cp.execFileSync('which',['tsc'],{encoding:'utf8'}).trim());
const ts=require(path.resolve(tsc,'../../lib/typescript.js'));
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
if(!Array.isArray(req.frames)||req.frames.length>2000)throw Error('FRAME_BUDGET');
const files=req.files,cache={}; let localFrame=0;const SEQ=Symbol('sequence'),AUDIO=Symbol('audio'),VIDEO=Symbol('video'),IMAGE=Symbol('image'),FRAG=Symbol('fragment');
function createElement(tag,props,...children){return {type:tag,props:props||{},children:children.flat(Infinity)};}
const react={createElement,Fragment:FRAG};
const fillStyle={position:'absolute',width:'100%',height:'100%',top:0,left:0};
const fill=p=>createElement('div',{...p,style:{...fillStyle,...(p.style||{})}},...(p.children||[]));
function interpolate(v,x,y,o={}){let i=0;while(i<x.length-2&&v>x[i+1])i++;let u=(v-x[i])/(x[i+1]-x[i]);if(o.extrapolateLeft==='clamp'||o.extrapolateRight==='clamp')u=Math.max(0,Math.min(1,u));return y[i]+(y[i+1]-y[i])*u;}
const remotion={CanvasImage:IMAGE,Interactive:{Div:'div'},AbsoluteFill:fill,Sequence:SEQ,
 useCurrentFrame:()=>localFrame,useVideoConfig:()=>({fps:req.fps,width:req.width,height:req.height}),interpolate,
 staticFile:p=>{if(typeof p!=='string'||p.includes('..')||p.includes('://'))throw Error('STATIC_PATH');return '/'+p;}};
function render(v,frame){
 if(v===null||v===undefined||v===false||v===true)return null;
 if(typeof v==='string'||typeof v==='number')return v;
 if(Array.isArray(v))return v.flatMap(x=>{const r=render(x,frame);return r==null?[]:Array.isArray(r)?r:[r];});
 const p={...v.props,children:v.children};
 if(v.type===FRAG)return render(v.children,frame);
 if(v.type===SEQ){
   if(!Number.isInteger(p.from)||!Number.isInteger(p.durationInFrames)||p.durationInFrames<1)throw Error('SEQUENCE_INTERVAL');
   if(frame<p.from||frame>=p.from+p.durationInFrames)return null;
   const child=render(v.children,frame-p.from);
   return p.layout==='none'?child:{tag:'div',props:{style:fillStyle},children:child};
 }
 if(v.type===IMAGE){
   return {tag:'img',props:{crossorigin:'anonymous',src:p.src,style:p.style,'data-bie-test-native-image':true},children:[]};
 }
 if(v.type===VIDEO){
   if(!Number.isInteger(p.trimBefore)||!Number.isInteger(p.trimAfter)||p.trimAfter<=p.trimBefore)throw Error('VIDEO_TRIM_CONTRACT');
   return {tag:'video',props:{crossorigin:'anonymous',src:p.src,style:p.style,muted:true,preload:'auto',playsinline:true,
       'data-bie-test-native-video':true,'data-bie-audio-played':false,
       'data-bie-source-time':(p.trimBefore+frame)/req.fps,
       'data-bie-declared-muted':p.muted},children:[]};
 }
 if(v.type===AUDIO){
   if(!Number.isInteger(p.trimBefore)||!Number.isInteger(p.trimAfter)||p.trimAfter<=p.trimBefore||p.volume<=0||p.volume>1)throw Error('AUDIO_CONTRACT');
   return {tag:'span',props:{'data-bie-test-audio':true,'data-src':p.src,'data-source-frame':p.trimBefore+frame,
      'data-trim-before':p.trimBefore,'data-trim-after':p.trimAfter,'data-volume':p.volume,
      'data-audio-played':false},children:[]};
 }
 if(typeof v.type==='function'){
   const old=localFrame;localFrame=frame;
   try{return render(v.type(p),frame);}finally{localFrame=old;}
 }
 if(typeof v.type!=='string')throw Error('UNSUPPORTED_VNODE');
 return {tag:v.type,props:v.props,children:render(v.children,frame)};
}
function load(id){
 if(cache[id])return cache[id]; if(!(id in files))throw Error('MISSING_FILE '+id);
 if(id.endsWith('.json'))return JSON.parse(files[id]);
 const out=ts.transpileModule(files[id],{compilerOptions:{jsx:ts.JsxEmit.React,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true},reportDiagnostics:true});
 if(out.diagnostics.some(d=>d.category===ts.DiagnosticCategory.Error))throw Error('TS_TRANSPILATION_FAILED');
 const safeMath=Object.create(Math);safeMath.random=()=>{throw Error('RANDOM_FORBIDDEN')};
 const scope={exports:{},Math:safeMath,require:name=>{
   if(name==='react')return {__esModule:true,default:react,...react};
   if(name==='remotion')return remotion;
   if(name==='@remotion/media')return {Audio:AUDIO,Video:VIDEO};
   if(!name.startsWith('.'))throw Error('UNMOCKED_IMPORT '+name);
   const base=path.posix.normalize(path.posix.join(path.posix.dirname(id),name));
   if(base.startsWith('../')||path.posix.isAbsolute(base))throw Error('IMPORT_ESCAPE');
   const resolved=[base,base+'.tsx',base+'.ts',base+'.json'].find(p=>p in files);
   if(!resolved)throw Error('IMPORT_UNRESOLVED '+base);return load(resolved);
 }};
 cache[id]=scope.exports;vm.createContext(scope);vm.runInContext(out.outputText,scope,{timeout:3000});return scope.exports;
}
const main=load('src/Scene.tsx');const runtime=files['src/runtime/frame-runtime.ts']?load('src/runtime/frame-runtime.ts'):{atFrame:()=>null};
const scope={main,render,createElement,runtime};vm.createContext(scope);const trees=[];
for(const f of req.frames){
 if(!Number.isInteger(f)||f<0)throw Error('FRAME_INVALID');scope.f=f;localFrame=f;
 vm.runInContext('tree=render(createElement(main.Scene,{}),f); state=runtime.atFrame(f)',scope,{timeout:3000});
 trees.push({frame:f,tree:scope.tree,state:scope.state});
}
const result=JSON.stringify({execution_kind:'REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES',
 runtime_bridge:'H11_LAZY_MEDIA_API_DOUBLE_NATIVE_BROWSER_DECODE_NO_AUDIO_PLAYBACK',typescript_version:ts.version,trees,real_react:false,real_remotion:false,audio_played:false,accepted:false});
if(Buffer.byteLength(result)>64*1024*1024)throw Error('OUTPUT_BUDGET');process.stdout.write(result);
