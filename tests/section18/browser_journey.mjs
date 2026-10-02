// Native Chromium/Edge regression, own isolated profile. No external dependency.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
const [browser,profile,debugPort,base,runId,mode,fixture,scenario]=process.argv.slice(2);
if(process.platform==='win32'){
 // The Python parent owns a private Job Object. Do not launch a browser before
 // assignment, including when job creation/assignment fails closed.
 const gate=await new Promise(resolve=>{process.stdin.once('data',data=>resolve(data));process.stdin.once('end',()=>resolve(null));process.stdin.resume();});
 if(!gate || !['GO\n','GO\r\n'].includes(gate.toString()))throw new Error('WINDOWS_BROWSER_OWNERSHIP_NOT_ESTABLISHED');
 process.stdin.pause();
}
const child=spawn(browser,['--headless=new','--no-first-run','--no-default-browser-check',
  '--remote-debugging-address=127.0.0.1','--remote-debugging-port='+debugPort,
  '--user-data-dir='+profile,'about:blank'],{stdio:'ignore',windowsHide:true});
let socket;const contexts=new Map(),sessions=new Map(),diagnostics=[];
let rootResponse=null,domReady=false,loadSeen=false;
const pending=new Map();let seq=0;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function call(method,params={},sessionId=null){
 // Never include params/expression: they can contain the operator credential.
 // Keep the original deadline; capture which real protocol call timed out.
 const id=++seq;return await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(new Error('CDP_TIMEOUT:'+method+':'+id));},10000);
 pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));});
}
async function evaluate(expression){
 const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails)throw new Error('BROWSER_EXPRESSION_FAILED');return r.result.value;
}
async function until(expression){for(let n=0;n<100;n++){if(await evaluate(expression))return;await sleep(100);}throw new Error('BROWSER_STATE_TIMEOUT:'+expression.slice(0,180));}
function assert(value,code){if(!value)throw new Error(code);}
try{
 let tabs;for(let n=0;n<300;n++){try{tabs=await (await fetch('http://127.0.0.1:'+debugPort+'/json/list')).json();break;}catch{}await sleep(100);}
 assert(tabs?.length,'BROWSER_START_FAILED');
 socket=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
 await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
 socket.onmessage=event=>{const row=JSON.parse(event.data),p=pending.get(row.id);if(p){clearTimeout(p.timer);pending.delete(row.id);row.error?p.reject(new Error('CDP_CALL_FAILED')):p.resolve(row.result);}
  if(row.method==='Page.domContentEventFired')domReady=true;
  if(row.method==='Page.loadEventFired')loadSeen=true;
  if(row.method==='Network.responseReceived'&&row.params.response.url===base)rootResponse=row.params.response.status;
  if(row.method==='Runtime.executionContextCreated'){const c=row.params.context;contexts.set((row.sessionId||'root')+':'+c.id,{...c,sessionId:row.sessionId||null});}
  if(row.method==='Target.attachedToTarget'){sessions.set(row.params.sessionId,row.params.targetInfo);for(const method of ['Runtime.enable','Log.enable','Network.enable'])call(method,{},row.params.sessionId).catch(()=>{});}
  if(row.method==='Runtime.exceptionThrown'){
   const d=row.params.exceptionDetails,description=d.exception?.description||d.text||'';
   diagnostics.push({kind:'exception',code:description.match(/GAME_[A-Z0-9_]+/)?.[0]||description.split(':')[0].slice(0,40)});
  }
  if(row.method==='Network.loadingFailed')diagnostics.push({kind:'loading_failed',code:row.params.errorText,reason:row.params.blockedReason,cors:row.params.corsErrorStatus?.corsError});
  if(row.method==='Network.responseReceived'&&row.params.response.url.includes('/_preview/'))diagnostics.push({kind:'resource',name:row.params.response.url.split('/').at(-1).replace(/[^A-Za-z0-9_.-]/g,''),status:row.params.response.status,mime:row.params.response.mimeType});
  if(row.method==='Log.entryAdded'&&row.params.entry.level==='error')diagnostics.push({kind:'browser_error',message:row.params.entry.text.replace(/https?:\/\/[^\s'"<>)]+/g,'<resource>').slice(0,240)});
 };
 await call('Page.enable');await call('Runtime.enable');
 await call('Network.enable');await call('Log.enable');
 await call('Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:false,flatten:true});
 const dimensions=mode==='phone'?{width:390,height:844,mobile:true}:mode==='tablet'?{width:820,height:1180,mobile:true}:{width:1440,height:1000,mobile:false};
 await call('Emulation.setDeviceMetricsOverride',{...dimensions,deviceScaleFactor:1});
 await call('Page.navigate',{url:base});await until("document.readyState==='complete' && typeof action==='function'");
 assert(await evaluate("document.querySelector('#create').disabled"),'INITIAL_STATE_NOT_FAIL_CLOSED');
 const credential=process.env.BIE_OPERATOR_TOKEN;
 await evaluate(`document.getElementById('token').value=${JSON.stringify(credential)}; document.getElementById('connect').click();`);
 await until("!document.getElementById('upload').disabled && document.body.getAttribute('aria-busy')==='false'");
 await evaluate(`document.getElementById('run-id').value=${JSON.stringify(runId)};document.getElementById('open-run').click();`);
 await until("document.getElementById('run-summary').textContent.includes('READY') && document.body.getAttribute('aria-busy')==='false'");
 if(mode==='desktop'){
   await evaluate("document.getElementById('pause').click()");await until("document.getElementById('run-summary').textContent.includes('PAUSED') && document.body.getAttribute('aria-busy')==='false'");
   await evaluate("document.getElementById('resume').click()");await until("!document.getElementById('pause').disabled && document.body.getAttribute('aria-busy')==='false'");
   // File input uses actual synthetic native PDF. It is never real-book evidence.
   const {root}=await call('DOM.getDocument');const {nodeId}=await call('DOM.querySelector',{nodeId:root.nodeId,selector:'#pdf'});
   await call('DOM.setFileInputFiles',{nodeId,files:[fixture]});await evaluate("document.getElementById('upload').click()");
   await until("document.getElementById('validation').textContent.includes('VALID') && !document.getElementById('create').disabled && document.body.getAttribute('aria-busy')==='false'");
   await evaluate("document.getElementById('create').click()");await until("document.getElementById('run-summary').textContent.includes('READY') && document.body.getAttribute('aria-busy')==='false'");
   await evaluate("document.getElementById('cancel').click()");await until("document.getElementById('run-summary').textContent.includes('CANCELLED') && document.body.getAttribute('aria-busy')==='false'");
   await evaluate(`document.getElementById('run-id').value=${JSON.stringify(runId)};document.getElementById('open-run').click();`);
   await until("!document.getElementById('pause').disabled && document.body.getAttribute('aria-busy')==='false'");
 }
 await evaluate("document.getElementById('concept').click()");await until("document.querySelector('#graph svg') && document.body.getAttribute('aria-busy')==='false'");
 assert(await evaluate("document.querySelectorAll('#graph svg circle').length===2 && document.querySelectorAll('#graph-fallback table tr').length===3"),'GRAPH_NOT_STRUCTURED');
 assert(await evaluate("document.querySelectorAll('#graph img,#graph script').length===0"),'GRAPH_SCRIPT_INJECTION');
 await evaluate("document.getElementById('prerequisite').click()");await until("document.getElementById('graph-fallback').textContent.includes('Teaching order:') && document.body.getAttribute('aria-busy')==='false'");
 assert(await evaluate("document.querySelector('#graph svg line').getAttribute('marker-end')==='url(#arrow)'"),'PREREQUISITE_DIRECTION_MISSING');
 if(scenario==='batch002'){
  for(const kind of ['reasoning','curriculum','lesson','director','scene_ir','game_plan']){
   await evaluate(`document.getElementById('view-${kind}').click()`);
   await until("document.getElementById('view-state').textContent.includes('SYNTHETIC_TEST') && document.body.getAttribute('aria-busy')==='false'");
   assert(await evaluate("document.querySelectorAll('#artifact-view table').length>=1"),'STRUCTURED_VIEW_MISSING:'+kind);
   assert(await evaluate("document.querySelectorAll('#artifact-view script,#artifact-view iframe,#artifact-view img').length===0"),'ARTIFACT_SCRIPT_INJECTION');
   assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"),'VIEW_HORIZONTAL_OVERFLOW:'+kind);
  }
  await evaluate("document.getElementById('browse-artifacts').click()");
  await until("document.getElementById('artifact-list').textContent.includes('operator.generated_code') && document.body.getAttribute('aria-busy')==='false'");
  await evaluate("[...document.querySelectorAll('#artifact-list button')].find(b=>b.textContent==='Open verified code').click()");
  await until("document.getElementById('code-view').textContent.includes('window.injected') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("window.injected===undefined && !document.querySelector('#code-view script')"),'CODE_EXECUTED');
  await evaluate("[...document.querySelectorAll('#artifact-list button')].find(b=>b.textContent==='Open artifact lineage').click()");
  await until("document.querySelector('#lineage-view svg') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('lineage-view').textContent.includes('Passed')"),'LINEAGE_NOT_VERIFIED');
  await evaluate("[...document.querySelectorAll('#artifact-list button')].find(b=>b.textContent==='Open evidence').click()");
  await until("document.getElementById('evidence-view').textContent.includes('SYNTHETIC_TEST') && document.body.getAttribute('aria-busy')==='false'");
 }
 if(scenario==='batch003'){
  await evaluate("document.getElementById('preview-render').click()");
  await until("document.querySelector('#preview-content video')?.readyState>=1 && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("(()=>{const v=document.querySelector('#preview-content video');return v.videoWidth===128&&v.videoHeight===96&&Math.abs(v.duration-2)<.1})()"),'ACTUAL_MP4_NOT_DECODED');
  let play=await call('Runtime.evaluate',{expression:"(()=>{const v=document.querySelector('#preview-content video');v.muted=true;return v.play().then(()=>true)})()",awaitPromise:true,returnByValue:true,userGesture:true});
  assert(!play.exceptionDetails,'MEDIA_PLAYBACK_FAILED');await until("document.querySelector('#preview-content video').currentTime>.1");
  await evaluate("document.getElementById('preview-game').click()");
  await until("document.querySelector('#preview-content iframe') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.querySelector('#preview-content iframe').getAttribute('sandbox')==='allow-scripts'"),'GAME_SANDBOX_WEAKENED');
  let gameContext=null;
  for(let n=0;n<100&&!gameContext;n++){
   const tree=await call('Page.getFrameTree');const frame=tree.frameTree.childFrames?.find(f=>f.frame.url.includes('/_preview/'))?.frame;
   for(const c of contexts.values())if(c.auxData?.isDefault&&(c.auxData.frameId===frame?.id||sessions.get(c.sessionId)?.type==='iframe')){
    const r=await call('Runtime.evaluate',{expression:'Boolean(globalThis.__BIE_GAME_RUNTIME__?.booted)',contextId:c.id,returnByValue:true},c.sessionId);
    if(r.result?.value===true){gameContext=c;break;}
   }if(!gameContext)await sleep(100);
  }
  if(!gameContext){
   const frameStates=[];for(const c of contexts.values())if(c.sessionId&&c.auxData?.isDefault){try{const r=await call('Runtime.evaluate',{expression:"({ready:document.readyState,scripts:document.scripts.length,body_length:document.body?.textContent.length,url_kind:document.URL.startsWith('chrome-error:')?'ERROR':document.URL.includes('/_preview/')?'PREVIEW':'OTHER',runtime_type:typeof globalThis.__BIE_GAME_RUNTIME__})",contextId:c.id,returnByValue:true},c.sessionId);frameStates.push(r.result?.value);}catch{}}
   console.error(JSON.stringify({code:'GAME_BOOT_DIAGNOSTICS',diagnostics,frameStates,contexts:[...contexts.values()].map(c=>({id:c.id,isDefault:c.auxData?.isDefault,hasFrame:Boolean(c.auxData?.frameId),session:Boolean(c.sessionId)})),sessions:[...sessions.values()].map(t=>({type:t.type}))}));
  }
  assert(gameContext,'CANONICAL_GAME_RUNTIME_NOT_BOOTED');
  const inGame=async expression=>{const r=await call('Runtime.evaluate',{expression,contextId:gameContext.id,returnByValue:true,awaitPromise:true},gameContext.sessionId);assert(!r.exceptionDetails,'GAME_CONTEXT_FAILED');return r.result.value;};
  assert(await inGame("(()=>{try{return parent.document===document}catch{return false}})()")===false,'OPAQUE_GAME_CAN_READ_OPERATOR');
  assert(await inGame("document.querySelectorAll('main[role=application]').length===1"),'NATIVE_GAME_DOM_MISSING');
  const before=await inGame('JSON.stringify(__BIE_GAME_RUNTIME__.getState())');
  const buttons=await inGame("[...document.querySelectorAll('[data-action-id]')].map(b=>({id:b.getAttribute('data-action-id'),kind:b.tagName}))");
  assert(buttons.length>0,'NATIVE_GAME_CONTROLS_MISSING');
  await inGame("document.querySelector('[data-action-id]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));true");
  const after=await inGame('JSON.stringify(__BIE_GAME_RUNTIME__.getState())');
  assert(before!==after,'NATIVE_GAME_INPUT_HAS_NO_EFFECT');
  assert(await inGame('__BIE_GAME_RUNTIME__.getTelemetry().length>0'),'NATIVE_GAME_TELEMETRY_MISSING');
  // The compiled package cannot call the privileged API from its sandbox.
  const network=await inGame("fetch('/operator/v1/runs').then(()=>false).catch(()=>true)");assert(network,'GAME_NETWORK_NOT_BLOCKED');
  await evaluate("document.getElementById('stop-preview').click()");await until("!document.querySelector('#preview-content iframe') && document.body.getAttribute('aria-busy')==='false'");
 }
 if(scenario==='batch004'){
  await evaluate("document.getElementById('governance-policy').click()");
  await until("document.getElementById('governance-content').textContent.includes('native-policy') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('governance-content').textContent.includes('EXPLICIT_POLICY_BOUND_NEW_INSPECTION_RUNS') && document.getElementById('governance-content').textContent.includes('NOT_RUN')"),'POLICY_EXECUTION_FABRICATED');
  await evaluate("[...document.querySelectorAll('#governance-content button')].find(b=>b.textContent==='Prepare next policy version').click();document.getElementById('policy-locale').value='hi';document.getElementById('policy-save').click()");
  await until("document.getElementById('governance-content').textContent.includes('revision 2') && document.body.getAttribute('aria-busy')==='false'");
  await evaluate("[...document.querySelectorAll('#governance-content button')].find(b=>b.textContent==='Activate pinned version').click()");
  await until("document.querySelector('#governance-content button')?.disabled===false && document.body.getAttribute('aria-busy')==='false'");
  await evaluate("[...document.querySelectorAll('#governance-content button')].find(b=>b.textContent==='Bind policy to next new run').click()");
  assert(await evaluate("selectedPolicy.revision===2 && document.getElementById('locale').value==='hi' && document.getElementById('policy-binding-state').textContent.includes('revision 2')"),'POLICY_BINDING_MISSING');
  await evaluate("[...document.querySelectorAll('#governance-content button')].find(b=>b.textContent==='Open immutable version history').click()");
  await until("document.querySelectorAll('#governance-detail tbody tr').length===2 && document.body.getAttribute('aria-busy')==='false'");
  await evaluate("[...document.querySelectorAll('#governance-detail button')].find(b=>b.textContent.includes('Compare revision')).click()");
  await until("document.getElementById('governance-detail').textContent.includes('/locale') && document.body.getAttribute('aria-busy')==='false'");
  if(mode==='desktop'){
   await evaluate("document.getElementById('create').click()");
   await until("document.getElementById('run-summary').textContent.includes('READY') && document.body.getAttribute('aria-busy')==='false'");
   assert(await evaluate("run.run_id!=="+JSON.stringify(runId)), 'POLICY_BOUND_RUN_NOT_CREATED');
  }
  await evaluate("document.getElementById('governance-benchmark').click()");
  await until("document.getElementById('governance-content').textContent.includes('native-benchmark') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.querySelectorAll('#governance-content table').length===5 && document.getElementById('governance-content').textContent.includes('AUTHORED_DIAGNOSTIC') && document.getElementById('governance-content').textContent.includes('NOT_RUN')"),'BENCHMARK_CONFIGURATION_MISLEADING');
  const {root:configurationRoot}=await call('DOM.getDocument');const {nodeId:configurationNode}=await call('DOM.querySelector',{nodeId:configurationRoot.nodeId,selector:'#benchmark-file'});
  await call('DOM.setFileInputFiles',{nodeId:configurationNode,files:[fixture.replace(/synthetic\.pdf$/,'invalid-benchmark.json')]});
  await evaluate("document.getElementById('benchmark-id').value='invalid-benchmark';document.getElementById('benchmark-save').click()");
  await until("document.getElementById('notice').textContent.includes('duplicate_json_key') && document.body.getAttribute('aria-busy')==='false'");
  await evaluate("document.getElementById('governance-audit').click()");
  await until("document.getElementById('governance-content').textContent.includes('CONFIG_ACTIVATED') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.querySelector('#governance-content table') && document.getElementById('governance-content').textContent.includes('EXPLICIT') && !document.querySelector('#governance-content script,#governance-content iframe,#governance-content img')"),'AUDIT_SAFE_PROJECTION_MISSING');
 }
 if(scenario==='batch003d'){
  await evaluate("document.getElementById('admin-providers').click()");
  await until("document.getElementById('admin-content').textContent.includes('registry-only') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('admin-content').textContent.includes('NOT_RUN') && document.getElementById('admin-content').textContent.includes('SYNTHETIC_TEST') && document.getElementById('admin-content').textContent.includes('adapter_not_bound_in_this_process')"),'PROVIDER_HEALTH_FABRICATED');
  await evaluate("[...document.querySelectorAll('#admin-content button')].find(b=>b.textContent==='Disable registered model').click()");
  await until("document.getElementById('admin-content').textContent.includes('Enable registered model') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("[...document.querySelectorAll('#admin-content button')].find(b=>b.textContent==='Enable registered model').disabled"),'UNBOUND_PROVIDER_ENABLED');
  await evaluate("[...document.querySelectorAll('#admin-content button')].find(b=>b.textContent==='Open immutable provider history').click()");
  await until("document.querySelector('#admin-detail table') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.querySelectorAll('#admin-detail tbody tr').length===2"),'PROVIDER_VERSIONS_NOT_PERSISTED');
  await evaluate("document.getElementById('admin-workers').click()");
  await until("document.getElementById('admin-content').textContent.includes('STOPPED') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('admin-content').textContent.includes('ACKED') && document.getElementById('admin-content').textContent.includes('FAILED') && document.getElementById('admin-content').textContent.includes('START_AND_COMPLETION_ONLY')"),'WORKER_ACTUAL_HISTORY_MISSING');
  await evaluate("document.getElementById('queue-state').value='ACKED';document.getElementById('admin-queue').click()");
  await until("document.getElementById('admin-content').textContent.includes('ACKED') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("!document.getElementById('admin-content').textContent.includes('Canonical queueREADY')"),'QUEUE_FILTER_IGNORED');
  await evaluate("document.getElementById('admin-dead-letters').click()");
  await until("document.getElementById('admin-content').textContent.includes('DEAD_LETTER') && document.body.getAttribute('aria-busy')==='false'");
  // Desktop also created a genuinely cancelled queued run above. It correctly
  // has a non-recoverable dead letter. Select the FAILED parent (READY admission),
  // not whichever hash-sorted run happens to be first in a fresh fixture.
  await evaluate("[...document.querySelectorAll('#admin-content article')].find(a=>a.textContent.includes('Executor admissionREADY')).querySelector('button').click()");
  await until("document.getElementById('admin-detail').textContent.includes('CREATE_GOVERNED_CHILD_RETRY') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.querySelectorAll('#admin-detail tbody tr').length===3"),'DEADLETTER_CANONICAL_EVENTS_MISSING');
  await evaluate("[...document.querySelectorAll('#admin-detail button')].find(b=>b.textContent==='Create governed child retry').click()");
  await until("document.getElementById('admin-detail').textContent.includes('Persisted child') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('admin-detail').textContent.includes('READY / READY') && document.getElementById('admin-detail').textContent.includes('Parent stays FAILED / DEAD_LETTER')"),'RECOVERY_PARENT_REWRITTEN');
  assert(await evaluate("!document.querySelector('#admin-content script,#admin-content iframe,#admin-content img,#admin-detail script')"),'ADMIN_SCRIPT_INJECTION');
 }
 if(scenario==='batch003c'){
  await evaluate("document.getElementById('assurance-gates').click()");
  await until("document.getElementById('assurance-state').textContent.includes('Verified historical gates') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.querySelectorAll('#assurance-content table').length===3 && document.getElementById('assurance-content').textContent.includes('BLOCKED') && document.getElementById('assurance-content').textContent.includes('MISSING_REQUIRED_EVIDENCE')"),'QA_GATE_FLOORS_MISSING');
  assert(await evaluate("document.getElementById('assurance-content').textContent.includes('SYNTHETIC_TEST') && document.getElementById('assurance-content').textContent.includes('Product acceptedNo')"),'QA_GATE_MISLEADING_AUTHORITY');
  assert(await evaluate("!document.querySelector('#assurance-content script,#assurance-content iframe,#assurance-content img')"),'ASSURANCE_INJECTION');
  await evaluate("document.querySelector('#assurance-content button').click()");await until("document.querySelector('#lineage-view svg') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"),'ASSURANCE_HORIZONTAL_OVERFLOW');
  await evaluate("document.getElementById('assurance-repairs').click()");
  await until("document.getElementById('assurance-state').textContent.includes('native_repair_journal_not_bound') && document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('assurance-content').textContent===''"),'SYNTHETIC_REPAIR_SUBSTITUTION');
 }
 if(scenario==='batch003b'){
  for(const kind of ['benchmark','release']){
   await evaluate(`document.getElementById('quality-${kind}').click()`);
   await until("document.getElementById('quality-state').textContent.includes('verified persisted historical') && document.body.getAttribute('aria-busy')==='false'");
   assert(await evaluate("document.querySelectorAll('#quality-content table').length>=1"),'QUALITY_NOT_STRUCTURED');
   assert(await evaluate("document.getElementById('quality-content').textContent.includes('SYNTHETIC_TEST') && document.getElementById('quality-content').textContent.includes('Product acceptedNo')"),'QUALITY_MISLEADING_ACCEPTANCE');
   assert(await evaluate("!document.querySelector('#quality-content script,#quality-content iframe,#quality-content img')"),'QUALITY_INJECTION');
   if(kind==='benchmark')assert(await evaluate("document.getElementById('quality-content').textContent.includes('case-2') && document.getElementById('quality-content').textContent.includes('1/2') && document.getElementById('quality-content').textContent.includes('FAIL')"),'BENCHMARK_MISSING_DENOMINATOR');
   else assert(await evaluate("document.getElementById('quality-content').textContent.includes('BLOCKED') && document.getElementById('quality-content').textContent.includes('Critical floors') && document.getElementById('quality-content').textContent.includes('CRITICAL_METRIC_NOT_MEASURED')"),'RELEASE_FLOOR_NOT_SHOWN');
   assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"),'QUALITY_HORIZONTAL_OVERFLOW');
  }
  await evaluate("document.querySelector('#quality-content button').click()");await until("document.querySelector('#lineage-view svg') && document.body.getAttribute('aria-busy')==='false'");
 }
 assert(await evaluate("document.documentElement.scrollWidth<=window.innerWidth"),'HORIZONTAL_OVERFLOW');
 assert(await evaluate("[...document.querySelectorAll('input,select')].every(e=>document.querySelector('label[for=\"'+e.id+'\"]'))"),'FORM_LABEL_MISSING');
 await evaluate("document.getElementById('token').focus()");await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
 assert(await evaluate("document.activeElement.id==='connect'"),'KEYBOARD_FOCUS_PATH_FAILED');
 const metrics=await call('Accessibility.getFullAXTree');
 assert(metrics.nodes.some(n=>n.role?.value==='heading'&&n.name?.value==='Source-linked graphs'),'AX_GRAPH_HEADING_MISSING');
 assert(metrics.nodes.some(n=>n.role?.value==='table'),'AX_TABLE_FALLBACK_MISSING');
 if(scenario==='batch002'){
  // Hold a real HTTP response in the client to reproduce credential-clear
  // during an in-flight read. It must not repopulate private artifact state.
  await evaluate("window.savedFetch=window.fetch;window.fetch=async(...args)=>{const r=await window.savedFetch(...args);if(String(args[0]).includes('/views/reasoning'))await new Promise(resolve=>{window.releaseHeldResponse=resolve});return r;};document.getElementById('view-reasoning').click();");
  await until("typeof window.releaseHeldResponse==='function'");
  await evaluate("document.getElementById('disconnect').click();window.releaseHeldResponse();window.fetch=window.savedFetch");
  await until("document.body.getAttribute('aria-busy')==='false'");
 }
 if(scenario==='batch003b'){
  await evaluate("window.savedFetch=window.fetch;window.fetch=async(...args)=>{const r=await window.savedFetch(...args);if(String(args[0]).includes('/quality/benchmark'))await new Promise(resolve=>{window.releaseHeldQuality=resolve});return r;};document.getElementById('quality-benchmark').click();");
  await until("typeof window.releaseHeldQuality==='function'");
  await evaluate("document.getElementById('disconnect').click();window.releaseHeldQuality();window.fetch=window.savedFetch");
  await until("document.body.getAttribute('aria-busy')==='false'");
 }
 if(scenario==='batch003c'){
  await evaluate("window.savedFetch=window.fetch;window.fetch=async(...args)=>{const r=await window.savedFetch(...args);if(String(args[0]).includes('/assurance/gates'))await new Promise(resolve=>{window.releaseHeldAssurance=resolve});return r;};document.getElementById('assurance-gates').click();");
  await until("typeof window.releaseHeldAssurance==='function'");
  await evaluate("document.getElementById('disconnect').click();window.releaseHeldAssurance();window.fetch=window.savedFetch");
  await until("document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('assurance-content').textContent==='' && document.getElementById('assurance-gates').disabled"),'PRIVATE_ASSURANCE_REPOPULATED');
 }
 if(scenario==='batch003d'){
  await evaluate("window.savedFetch=window.fetch;window.fetch=async(...args)=>{const r=await window.savedFetch(...args);if(String(args[0]).includes('/admin/queue'))await new Promise(resolve=>{window.releaseHeldAdmin=resolve});return r;};document.getElementById('admin-queue').click();");
  await until("typeof window.releaseHeldAdmin==='function'");
  await evaluate("document.getElementById('disconnect').click();window.releaseHeldAdmin();window.fetch=window.savedFetch");
  await until("document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('admin-content').textContent==='' && document.getElementById('admin-detail').textContent==='' && document.getElementById('admin-workers').disabled"),'PRIVATE_ADMIN_REPOPULATED');
 }
 if(scenario==='batch004'){
  await evaluate("window.savedFetch=window.fetch;window.fetch=async(...args)=>{const r=await window.savedFetch(...args);if(String(args[0]).includes('/admin/audit'))await new Promise(resolve=>{window.releaseHeldAudit=resolve});return r;};document.getElementById('governance-audit').click();");
  await until("typeof window.releaseHeldAudit==='function'");
  await evaluate("document.getElementById('disconnect').click();window.releaseHeldAudit();window.fetch=window.savedFetch");
  await until("document.body.getAttribute('aria-busy')==='false'");
  assert(await evaluate("document.getElementById('governance-content').textContent==='' && document.getElementById('governance-detail').textContent==='' && document.getElementById('governance-audit').disabled && selectedPolicy===null"),'PRIVATE_GOVERNANCE_REPOPULATED');
 }
 await evaluate("document.getElementById('disconnect').click()");
 assert(await evaluate("document.getElementById('token').value==='' && document.getElementById('run-summary').textContent===''"),'CREDENTIAL_CLEAR_FAILED');
 if(scenario==='batch002')assert(await evaluate("document.getElementById('artifact-view').textContent==='' && document.getElementById('code-view').textContent==='' && document.getElementById('lineage-view').textContent==='' && document.getElementById('view-reasoning').disabled"),'PRIVATE_VIEW_CLEAR_FAILED');
 if(scenario==='batch003')assert(await evaluate("document.getElementById('preview-content').textContent==='' && document.getElementById('preview-game').disabled && mediaURL===null"),'PRIVATE_PREVIEW_CLEAR_FAILED');
 if(scenario==='batch003b')assert(await evaluate("document.getElementById('quality-content').textContent==='' && document.getElementById('quality-benchmark').disabled"),'PRIVATE_QUALITY_CLEAR_FAILED');
 console.log(JSON.stringify({mode,passed:true,native_browser:true,structured_graph:true,keyboard:true,ax_tree:true,
    horizontal_overflow:false,synthetic_fixture:true,real_book_executed:false,product_accepted:false}));
}catch(e){
 if(e.message.startsWith('CDP_TIMEOUT:')){
  let healthStatus=null;
  try{const response=await fetch(base+'healthz',{signal:AbortSignal.timeout(1000)});healthStatus=response.status;}catch{}
  // Never log expressions, requests, tokens, source data or URLs.
  console.error('NATIVE_CDP_DIAGNOSTIC:'+JSON.stringify({rootResponse,domReady,loadSeen,healthStatus,
    childExited:child.exitCode!==null||child.signalCode!==null,contexts:contexts.size,sessions:sessions.size}));
 }
 console.error('NATIVE_UI_FAILED:'+e.message);process.exitCode=1;
}
finally{
 if(socket?.readyState===1){try{await call('Browser.close');}catch{}socket.close();}
 for(const p of pending.values())clearTimeout(p.timer);
 // Wait for the browser we created, not just its CDP socket. In particular,
 // Windows Crashpad can hold the isolated profile during asynchronous exit.
 async function waitForExit(){for(let n=0;n<100;n++){if(child.exitCode!==null||child.signalCode!==null)return true;await sleep(100);}return false;}
 if(!await waitForExit()){
  if(process.platform==='win32'){
   const stop=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore',windowsHide:true});
   await new Promise(resolve=>{stop.on('error',resolve);stop.on('exit',resolve);});
   // taskkill's process-tree enumeration can race Chromium's asynchronous
   // shutdown. Node still owns the original process handle: terminate that
   // handle as well, never enumerate or kill unrelated user browsers.
   if(child.exitCode===null && child.signalCode===null)child.kill('SIGKILL');
  }else child.kill('SIGKILL');
  if(!await waitForExit()){console.error('NATIVE_UI_FAILED:BROWSER_SHUTDOWN_FAILED');process.exitCode=1;}
 }
}
