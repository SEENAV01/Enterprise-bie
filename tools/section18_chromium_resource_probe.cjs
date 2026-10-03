'use strict';
// Forensic probe ONLY. No arbitrary URL, script, executable, or command input.
const fs = require('fs');
const http = require('http');
const {spawn} = require('child_process');
const readLimits = () => fs.readFileSync('/proc/self/limits', 'utf8');
const readStatus = () => fs.readFileSync('/proc/self/status', 'utf8');
function get(path) {
  return new Promise((resolve, reject) => {
    const request = http.get({hostname:'127.0.0.1', port:9222, path, timeout:1000}, response => {
      let body = '';
      response.on('data', c => {
        body += c;
        if (body.length > 65536) { request.destroy(); reject(new Error('CDP_SIZE_LIMIT')); }
      });
      response.on('end', () => { try {resolve(JSON.parse(body));} catch(e) {reject(e);} });
    });
    request.on('error', reject);
    request.on('timeout', () => request.destroy(new Error('CDP_TIMEOUT')));
  });
}
function evaluate(url) {
  if (!/^ws:\/\/127\.0\.0\.1:9222\/devtools\/page\/[a-zA-Z0-9-]+$/.test(url)) {
    throw new Error('CDP_FOREIGN_TARGET');
  }
  return new Promise((resolve,reject) => {
    const ws = new WebSocket(url);
    const timer = setTimeout(() => {ws.close();reject(new Error('CDP_EVALUATION_TIMEOUT'));},3000);
    ws.addEventListener('open', () => ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',
      params:{expression:'JSON.stringify({arithmetic:6*7,title:document.title})',returnByValue:true}})));
    ws.addEventListener('error', () => {clearTimeout(timer);reject(new Error('CDP_EVALUATION_ERROR'));});
    ws.addEventListener('message', event => {
      const data = JSON.parse(event.data);
      if (data.id === 1) {clearTimeout(timer);ws.close();resolve(data);}
    });
  });
}
async function main() {
  if (process.version !== 'v22.16.0' || process.execArgv.length) throw new Error('NODE_IDENTITY_OR_SCOPE');
  const before = readLimits();
  if (!/^Max address space\s+8589934592\s+8589934592\s+bytes$/m.test(before)) throw new Error('NODE_AS_NOT_8GIB');
  const child = spawn('/opt/pyvenv/bin/python', ['-I',
    '/engine/tools/diagnose_section18_chromium_resource_policy.py', 'browser'],
    {stdio:['ignore','pipe','pipe']});
  let browserLog = '', browserError = '';
  child.stdout.on('data', data => {if (browserLog.length < 65536) browserLog += data.toString();});
  child.stderr.on('data', data => {if (browserError.length < 65536) browserError += data.toString();});
  child.on('error', () => {browserError += 'BROWSER_SPAWN_ERROR';});
  let result;
  try {
    const deadline = Date.now()+20000;
    while (Date.now() < deadline) {
      try {
        const targets = await get('/json/list');
        const target = targets.find(x => x.type === 'page');
        if (target) {result = await evaluate(target.webSocketDebuggerUrl);break;}
      } catch (_) {}
      if (child.exitCode !== null || child.signalCode !== null) break;
      await new Promise(resolve => setTimeout(resolve,100));
    }
    if (!result || result.error || result.result?.exceptionDetails ||
        JSON.parse(result.result?.result?.value || '{}').arithmetic !== 42) throw new Error('REAL_BROWSER_JS_NOT_EXECUTED');
    // Give the host observer a bounded opportunity to retain real VAS mappings.
    await new Promise(resolve => setTimeout(resolve,2000));
    const after = readLimits();
    if (before !== after || process.env.NODE_OPTIONS !== undefined) throw new Error('NODE_SCOPE_CHANGED');
    console.log(JSON.stringify({schema:'bie.section18.chromium-probe-node/1',node:process.version,
      execArgv:process.execArgv,limits_before:before,limits_after:after,status:readStatus(),
      actual_browser_javascript_result:result.result.result.value,browser_startup:browserLog,
      browser_stderr:browserError,diagnostic_only:true,render_gate_pass_claimed:false}));
  } finally {
    child.kill('SIGTERM');
    await new Promise(resolve => setTimeout(resolve,250));
    child.kill('SIGKILL');
  }
}
main().catch(error => {console.error(error.message);process.exitCode=1;});
