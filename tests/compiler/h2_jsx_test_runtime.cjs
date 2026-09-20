// H2 TEST ONLY: actual TypeScript compiler, explicit React/Remotion hook doubles.
// This is neither a Remotion render nor a multi-tenant execution sandbox.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process');
const tsc=fs.realpathSync(cp.execFileSync('which',['tsc'],{encoding:'utf8'}).trim());
const ts=require(path.resolve(tsc,'../../lib/typescript.js'));
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const createElement=(tag,props,...children)=>typeof tag==='function'?tag({...props,children}):({tag,props:props||{},children:children.flat(Infinity).filter(x=>x!==null&&x!==undefined&&x!==false)});
const react={createElement}; let frame=0, fps=req.fps||24;
const interpolate=(v,input,output,opts={})=>{
 let i=0; while(i<input.length-2 && v>input[i+1])i++;
 let u=(v-input[i])/(input[i+1]-input[i]);
 if(opts.extrapolateLeft==='clamp' || opts.extrapolateRight==='clamp')u=Math.min(1,Math.max(0,u));
 return output[i]+(output[i+1]-output[i])*u;
};
const transpiled=ts.transpileModule(req.source,{compilerOptions:{jsx:ts.JsxEmit.React,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true},reportDiagnostics:true});
if(transpiled.diagnostics.some(x=>x.category===ts.DiagnosticCategory.Error))throw Error('transpile diagnostics');
const safeMath=Object.create(Math);safeMath.random=()=>{throw Error('TEST: random prohibited')};
const scope={exports:{},Math:safeMath,require:(name)=>{
 if(name==='react')return {__esModule:true,default:react,...react};
 if(name==='remotion')return {Interactive:{Div:'div'},useCurrentFrame:()=>frame,useVideoConfig:()=>({fps}),interpolate};
 throw Error('TEST: unapproved import '+name);
}};
vm.createContext(scope);vm.runInContext(transpiled.outputText,scope,{timeout:3000});
const trees=[];
for(const f of req.frames||[0]){
 frame=f; scope.callProps=req.props||{children:createElement('span',{},'Visible technical fixture')};
 vm.runInContext('result=exports['+JSON.stringify(req.component)+'](callProps)',scope,{timeout:3000});
 trees.push({frame:f,tree:scope.result});
}
const calls=[];
for(const call of req.calls||[]){
 scope.callArgs=call.args;
 vm.runInContext('callResult=exports['+JSON.stringify(call.name)+'](...callArgs)',scope,{timeout:3000});
 calls.push(scope.callResult);
}
process.stdout.write(JSON.stringify({execution_kind:'REAL_TS_EXECUTION_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES',typescript_version:ts.version,trees,calls,accepted:false}));
