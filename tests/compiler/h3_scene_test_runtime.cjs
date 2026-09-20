// H3 TEST BRIDGE ONLY. Real TS transpilation/execution, NOT React or Remotion.
// Eager evaluation is valid only for this QA assembler's all-scene from=0 layers.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process');
const tsc=fs.realpathSync(cp.execFileSync('which',['tsc'],{encoding:'utf8'}).trim());
const ts=require(path.resolve(tsc,'../../lib/typescript.js'));
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
if(!Array.isArray(req.frames)||req.frames.length>2000)throw Error('FRAME_BUDGET');
const files=req.files;let frame=0;const cache={};
function createElement(tag,props,...children){
 const p={...(props||{}),children:children.flat(Infinity).filter(x=>x!==null&&x!==undefined&&x!==false)};
 return typeof tag==='function'?tag(p):{tag,props:props||{},children:p.children};
}
const react={createElement};
function interpolate(v,x,y,options={}){let i=0;while(i<x.length-2&&v>x[i+1])i++;let u=(v-x[i])/(x[i+1]-x[i]);if(options.extrapolateLeft==='clamp'||options.extrapolateRight==='clamp')u=Math.max(0,Math.min(1,u));return y[i]+(y[i+1]-y[i])*u;}
const fill=(p)=>createElement('div',{...p,style:{position:'absolute',width:'100%',height:'100%',top:0,left:0,...(p.style||{})}},...(p.children||[]));
const remotion={Interactive:{Div:'div'},AbsoluteFill:fill,Sequence:(p)=>{
 if(p.from!==0)throw Error('TEST_BRIDGE_NONZERO_SEQUENCE_UNSUPPORTED');
 return frame>=p.durationInFrames?null:fill(p);
},useCurrentFrame:()=>frame,useVideoConfig:()=>({fps:req.fps,width:req.width,height:req.height}),interpolate};
function load(id){
 if(cache[id])return cache[id];
 if(!(id in files))throw Error('MISSING_FILE '+id);
 if(id.endsWith('.json'))return JSON.parse(files[id]);
 const out=ts.transpileModule(files[id],{compilerOptions:{jsx:ts.JsxEmit.React,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true},reportDiagnostics:true});
 if(out.diagnostics.some(d=>d.category===ts.DiagnosticCategory.Error))throw Error('TS_TRANSPILATION_FAILED');
 const safeMath=Object.create(Math);safeMath.random=()=>{throw Error('TEST_RANDOM_FORBIDDEN')};
 const scope={exports:{},Math:safeMath,require:(name)=>{
   if(name==='react')return {__esModule:true,default:react,...react};
   if(name==='remotion')return remotion;
   if(!name.startsWith('.'))throw Error('UNMOCKED_IMPORT '+name);
   const base=path.posix.normalize(path.posix.join(path.posix.dirname(id),name));
   if(base.startsWith('../')||path.posix.isAbsolute(base))throw Error('IMPORT_ESCAPE');
   const resolved=[base,base+'.tsx',base+'.ts',base+'.json'].find(p=>p in files);
   if(!resolved)throw Error('IMPORT_UNRESOLVED '+base);
   return load(resolved);
 }};
 cache[id]=scope.exports;vm.createContext(scope);vm.runInContext(out.outputText,scope,{timeout:3000});return scope.exports;
}
const main=load('src/Scene.tsx');const scope={main};vm.createContext(scope);
const trees=[];
for(const f of req.frames){
 if(!Number.isInteger(f)||f<0)throw Error('FRAME_INVALID');frame=f;
 vm.runInContext('tree=main.Scene({})',scope,{timeout:3000});trees.push({frame:f,tree:scope.tree});
}
const result=JSON.stringify({execution_kind:'REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES',typescript_version:ts.version,trees,accepted:false});
if(Buffer.byteLength(result)>64*1024*1024)throw Error('OUTPUT_BUDGET');process.stdout.write(result);
