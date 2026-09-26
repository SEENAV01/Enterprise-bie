const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
console.log('Loading browser verification driver');
const {chromium} = require(process.argv[2]);
const root = path.resolve(process.argv[3]);
const runtime = path.join(root,'runtime');
const executable = process.argv[4];
const headers = JSON.parse(fs.readFileSync(path.join(runtime,'security-headers.json'),'utf8'));
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const served = {};
const report = {schema_version:'bie.game.h6.browser-proof/1',checks:{},
  platform:process.platform,chromiumSandbox_requested:true,linux_sandbox_verified:false,
  product_accepted:false,external_requests:[],console_errors:[],page_errors:[]};
const check = (name, condition, detail=true) => {assert.ok(condition,name);report.checks[name]=detail;};
const server = http.createServer((req,res) => {
  const url = new URL(req.url,'http://localhost');
  if(url.pathname==='/favicon.ico'){res.writeHead(204);res.end();return;}
  const relative = decodeURIComponent(url.pathname).replace(/^\//,'');
  const file = path.resolve(runtime,relative || 'index.html');
  if(!file.startsWith(runtime+path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()){
    res.writeHead(404);res.end();return;
  }
  const data = fs.readFileSync(file);
  const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
    '.json':'application/json','.wav':'audio/wav','.txt':'text/plain; charset=utf-8'}[path.extname(file)] || 'application/octet-stream';
  served[path.basename(file)] = sha(data);
  res.writeHead(200,{...headers,'Content-Type':mime,'Content-Length':data.length});res.end(data);
});

async function main(){
 let browser;
 const deadline=setTimeout(()=>{
   report.passed=false;report.failure='BROWSER_PROBE_DEADLINE_EXCEEDED';
   fs.writeFileSync(path.join(root,'BROWSER_RECEIPT.json'),JSON.stringify(report,null,2)+'\n');
   console.error(report.failure);process.exit(1);
 },90000);
 try {
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin='http://127.0.0.1:'+server.address().port;
  report.stage='launch';console.log('Launching sandboxed browser');
  browser=await chromium.launch({executablePath:executable,headless:true,chromiumSandbox:true,timeout:20000});
  report.browser_version=browser.version();
  report.stage='context';console.log('Browser launched; creating isolated context');
  const context=await browser.newContext({viewport:{width:360,height:740},reducedMotion:'reduce'});
  await context.route('**/*',route=>{
    const url=route.request().url();
    if(url.startsWith(origin+'/'))return route.continue();
    report.external_requests.push(url);return route.abort();
  });
  await context.addInitScript(()=>{
    globalThis.__probeTelemetry=[];
    globalThis.__BIE_GAME_TELEMETRY_CONFIG__={enabled:true,policy_id:'policy:probe',session_id:'session:probe:1'};
    globalThis.__BIE_GAME_TELEMETRY_SINK__=event=>globalThis.__probeTelemetry.push(event);
    globalThis.__probeAudio={calls:0,playing:0,ended:0,time:0,errors:[]};
    const play=HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play=function(...args){
      globalThis.__probeAudio.calls++;
      this.addEventListener('playing',()=>globalThis.__probeAudio.playing++,{once:true});
      this.addEventListener('ended',()=>{globalThis.__probeAudio.ended++;globalThis.__probeAudio.time=this.currentTime;},{once:true});
      const result=play.apply(this,args);
      result.catch(e=>globalThis.__probeAudio.errors.push(e.name));
      return result;
    };
  });
  const page=await context.newPage();
  report.stage='navigation';console.log('Loading compiled runtime from local origin');
  page.on('console',msg=>{if(msg.type()==='error')report.console_errors.push(msg.text());});
  page.on('pageerror',error=>report.page_errors.push(error.message));
  const response=await page.goto(origin+'/index.html',{waitUntil:'load',timeout:30000});
  await page.waitForFunction(()=>globalThis.__BIE_GAME_RUNTIME__?.booted===true);
  report.stage='interaction';console.log('Runtime booted; checking interaction and lifecycle');
  check('native_origin_esm_loaded',response.status()===200);
  check('strict_csp_preserved',response.headers()['content-security-policy']===headers['Content-Security-Policy']);
  const vendor=await page.evaluate(async()=>{
    const module=await import('./react-vendor.js');
    return {react:module.React.version,reactDOM:module.reactDomVersion,
      valid:module.React.isValidElement(module.React.createElement('span',null,'probe'))};
  });
  check('actual_pinned_react_exports',vendor.react==='19.3.0'&&vendor.reactDOM==='19.3.0'&&vendor.valid,vendor);
  const application=page.locator('main[role="application"]');
  check('single_committed_application',await application.count()===1);
  check('rtl_locale',await application.getAttribute('dir')==='rtl'&&await application.getAttribute('lang')==='ur-IN');
  check('semantic_geometry',await page.locator('[data-entity-id]').evaluateAll(nodes=>nodes.every(n=>{
    const r=n.getBoundingClientRect();return r.width>=8&&r.height>=8&&n.textContent.trim();})));
  check('mobile_no_overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  check('live_feedback_region',await page.locator('#bie-game-feedback').getAttribute('aria-live')==='polite');
  const initial=await page.evaluate(()=>__BIE_GAME_RUNTIME__.getState());
  const target=page.locator('button[data-entity-id]').first();
  await target.focus();
  const started=performance.now();await target.press('Enter');
  report.interaction_roundtrip_ms=performance.now()-started;
  const after=await page.evaluate(()=>({state:__BIE_GAME_RUNTIME__.getState(),score:__BIE_GAME_RUNTIME__.getScore(),events:__probeTelemetry}));
  check('keyboard_state_transition',initial.x===1&&after.state.x===2&&after.score===10,after);
  check('focus_retained',await target.evaluate(node=>node===document.activeElement));
  check('telemetry_once_and_bound',after.events.length===1&&after.events[0].sequence_id===1&&after.events[0].session_id==='session:probe:1'&&!('raw_text' in after.events[0]));
  const unknown=await page.evaluate(()=>{try{__BIE_GAME_RUNTIME__.dispatch('unknown:action');return false;}catch(e){return e.message.includes('ACTION_UNKNOWN');}});
  check('unknown_action_fail_closed',unknown&&JSON.stringify(await page.evaluate(()=>__BIE_GAME_RUNTIME__.getState()))===JSON.stringify(after.state));
  await page.locator('[data-audio-control="play"]').click();
  await page.waitForFunction(()=>__probeAudio.ended>0,{},{timeout:5000});
  report.audio=await page.evaluate(()=>__probeAudio);
  check('native_audio_playback',report.audio.playing>0&&report.audio.time>0&&report.audio.errors.length===0,report.audio);
  check('caption_and_cue_bound',await page.locator('#bie-game-captions').getAttribute('data-cue-id')==='cue:narration:1'&&(await page.locator('#bie-game-captions').innerText()).length>0);
  check('rights_visible',(await page.locator('[data-rights-attribution]').innerText()).includes('CC0-1.0'));
  check('reduced_motion_effective',await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches&&document.getAnimations().length===0));
  await page.screenshot({path:path.join(root,'runtime-react-mobile.png'),fullPage:true});
  await page.setViewportSize({width:768,height:1024});
  check('tablet_no_overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const duplicate=await page.evaluate(async()=>{try{(await import('./entry.js')).startGameRuntime();return false;}catch(e){return e.message==='GAME_REACT_ALREADY_MOUNTED';}});
  check('duplicate_mount_rejected',duplicate);
  await target.evaluate(node=>{globalThis.__probeOldTarget=node;});
  const disposed=await page.evaluate(()=>{
    const old=__BIE_GAME_RUNTIME__;old.dispose();old.dispose();
    let rejected=false;try{old.dispatch('drag:mover');}catch(e){rejected=e.message==='GAME_RUNTIME_DISPOSED';}
    __probeOldTarget.dispatchEvent(new MouseEvent('click',{bubbles:true}));
    return {booted:old.booted,rejected,roots:document.querySelectorAll('main[role="application"]').length,events:__probeTelemetry.length};
  });
  check('dispose_unmounts_and_removes_handlers',!disposed.booted&&disposed.rejected&&disposed.roots===0&&disposed.events===1,disposed);
  const remount=await page.evaluate(async()=>{
    __BIE_GAME_TELEMETRY_CONFIG__.session_id='session:probe:2';
    (await import('./entry.js')).startGameRuntime();return __BIE_GAME_RUNTIME__.getState();
  });
  check('remount_initial_state',JSON.stringify(remount)===JSON.stringify(initial));
  await page.locator('button[data-entity-id]').first().press('Enter');
  const replay=await page.evaluate(()=>({state:__BIE_GAME_RUNTIME__.getState(),score:__BIE_GAME_RUNTIME__.getScore(),last:__probeTelemetry.at(-1),count:__probeTelemetry.length}));
  check('deterministic_remount_replay',JSON.stringify(replay.state)===JSON.stringify(after.state)&&replay.score===after.score);
  check('new_session_sequence_resets',replay.last.session_id==='session:probe:2'&&replay.last.sequence_id===1&&replay.count===2);
  check('no_console_or_page_errors',report.console_errors.length===0&&report.page_errors.length===0);
  check('no_external_network',report.external_requests.length===0);
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'BUILD_RECEIPT.json'),'utf8'));
  check('served_bytes_match_built_artifacts',Object.entries(served).every(([name,hash])=>manifest.artifact_sha256[name]===hash));
  report.served_sha256=served;report.passed=true;
 } catch(error){report.passed=false;report.failure=String(error.stack||error);process.exitCode=1;}
 finally {
  fs.writeFileSync(path.join(root,'BROWSER_RECEIPT.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
  if(browser)await browser.close();
  server.closeAllConnections();
  await new Promise(resolve=>server.close(resolve));
  clearTimeout(deadline);
 }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
