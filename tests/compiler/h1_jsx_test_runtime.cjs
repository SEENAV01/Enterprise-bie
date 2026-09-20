// TEST ONLY. This is not React, Remotion, a browser, or a security sandbox.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const cp=require('node:child_process');
const tsc=fs.realpathSync(cp.execFileSync('which',['tsc'],{encoding:'utf8'}).trim());
const ts=require(path.resolve(tsc,'../../lib/typescript.js'));
const req=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const createElement=(tag,props,...children)=>typeof tag==='function'?tag({...props,children}):({tag,props:props||{},children:children.flat(Infinity).filter(x=>x!==null&&x!==undefined&&x!==false)});
const react={createElement};
const transpiled=ts.transpileModule(req.source,{compilerOptions:{jsx:ts.JsxEmit.React,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true},reportDiagnostics:true});
if(transpiled.diagnostics.some(x=>x.category===ts.DiagnosticCategory.Error))throw Error('transpile diagnostics');
const safeMath=Object.create(Math);safeMath.random=()=>{throw Error('TEST: unexpected random execution')};
const scope={exports:{},Math:safeMath,require:(name)=>{
 if(name==='react')return {__esModule:true,default:react,...react};
 if(name==='remotion')return {Interactive:{Div:'div'}};
 throw Error('TEST: forbidden import '+name);
}};
vm.createContext(scope);
vm.runInContext(transpiled.outputText,scope,{timeout:2000});
vm.runInContext('result=exports['+JSON.stringify(req.component)+']({})',scope,{timeout:2000});
process.stdout.write(JSON.stringify({execution_kind:'REAL_TS_TRANSPILATION_WITH_EXPLICIT_JSX_TEST_DOUBLE',tree:scope.result,accepted:false}));
