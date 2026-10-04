'use strict';
// Forensic probe ONLY. No arbitrary URL, script, executable, or command input.
const fs = require('fs');
const http = require('http');
const net = require('net');
const crypto = require('crypto');
const {spawn} = require('child_process');
const readLimits = () => fs.readFileSync('/proc/self/limits', 'utf8');
const readStatus = () => fs.readFileSync('/proc/self/status', 'utf8');
function exactNodeLimit(text) {
  // /proc/self/limits pads the units column with trailing spaces. Only trim
  // that formatting; both numeric soft/hard limits remain exact requirements.
  const line = text.split('\n').find(row => row.startsWith('Max address space'));
  return line !== undefined && /^Max address space\s+8589934592\s+8589934592\s+bytes$/.test(line.trimEnd());
}
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
  // Node22's built-in WebSocket starts Undici's llhttp Wasm. This unrelated
  // diagnostic Node must keep its original 8GiB / unflagged invocation. Use a
  // tiny bounded RFC6455 wire transport for this single trusted local CDP call,
  // not a VM option or a dependency change. No extensions/foreign targets.
  return new Promise((resolve,reject) => {
    const key=crypto.randomBytes(16).toString('base64');
    const accept=crypto.createHash('sha1').update(key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
    const socket=net.createConnection({host:'127.0.0.1',port:9222});
    let pending=Buffer.alloc(0), upgraded=false, finished=false;
    const timer=setTimeout(()=>done(new Error('CDP_EVALUATION_TIMEOUT')),3000);
    function done(error,value) {
      if(finished)return;finished=true;clearTimeout(timer);socket.destroy();
      if(error)reject(error);else resolve(value);
    }
    function send(opcode,body) {
      if(body.length>65535)throw new Error('CDP_SIZE_LIMIT');
      const mask=crypto.randomBytes(4),long=body.length>=126;
      const header=Buffer.alloc(long?8:6);header[0]=0x80|opcode;header[1]=0x80|(long?126:body.length);
      if(long)header.writeUInt16BE(body.length,2);mask.copy(header,long?4:2);
      const data=Buffer.from(body);for(let i=0;i<data.length;i++)data[i]^=mask[i%4];
      socket.write(Buffer.concat([header,data]));
    }
    socket.on('connect',()=>socket.write('GET '+new URL(url).pathname+' HTTP/1.1\r\nHost: 127.0.0.1:9222\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: '+key+'\r\nSec-WebSocket-Version: 13\r\n\r\n'));
    socket.on('error',()=>done(new Error('CDP_EVALUATION_ERROR')));
    socket.on('close',()=>{if(!finished)done(new Error('CDP_EARLY_CLOSE'));});
    socket.on('data',chunk=>{
      try {
        if(pending.length+chunk.length>131072)throw new Error('CDP_SIZE_LIMIT');
        pending=Buffer.concat([pending,chunk]);
        if(!upgraded) {
          const end=pending.indexOf('\r\n\r\n');
          if(end<0){if(pending.length>8192)throw new Error('CDP_HANDSHAKE_LIMIT');return;}
          const rows=pending.subarray(0,end).toString('ascii').split('\r\n');
          if(!/^HTTP\/1\.1 101(?: |$)/.test(rows.shift()))throw new Error('CDP_UPGRADE_REJECTED');
          const headers={};for(const row of rows){const at=row.indexOf(':');if(at<1)throw new Error('CDP_HEADER_INVALID');
            const name=row.slice(0,at).toLowerCase();if(headers[name]!==undefined)throw new Error('CDP_DUPLICATE_HEADER');headers[name]=row.slice(at+1).trim();}
          if(headers['sec-websocket-accept']!==accept || headers.upgrade?.toLowerCase()!=='websocket' ||
             !headers.connection?.toLowerCase().split(',').map(x=>x.trim()).includes('upgrade') ||
             headers['sec-websocket-extensions'])throw new Error('CDP_HANDSHAKE_INVALID');
          pending=pending.subarray(end+4);upgraded=true;
          send(1,Buffer.from(JSON.stringify({id:1,method:'Runtime.evaluate',params:{
            expression:'JSON.stringify({arithmetic:6*7,title:document.title})',returnByValue:true}})));
        }
        while(pending.length>=2) {
          const opcode=pending[0]&15;let length=pending[1]&127,offset=2;
          if(!(pending[0]&128)||(pending[0]&112)||(pending[1]&128))throw new Error('CDP_FRAME_INVALID');
          if(length===126){if(pending.length<4)return;length=pending.readUInt16BE(2);offset=4;}
          if(length===127)throw new Error('CDP_SIZE_LIMIT');
          if(pending.length<offset+length)return;
          const body=pending.subarray(offset,offset+length);pending=pending.subarray(offset+length);
          if(opcode===9){if(length>125)throw new Error('CDP_PING_INVALID');send(10,body);continue;}
          if(opcode!==1)throw new Error('CDP_FRAME_OPCODE');
          const data=JSON.parse(body.toString('utf8'));if(data.id===1){done(null,data);return;}
        }
      } catch(error){done(error);}
    });
  });
}
async function main() {
  if (process.version !== 'v22.16.0' || process.execArgv.length) throw new Error('NODE_IDENTITY_OR_SCOPE');
  const before = readLimits();
  if (!exactNodeLimit(before)) throw new Error('NODE_AS_NOT_8GIB');
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
module.exports = {exactNodeLimit,evaluate};
if (require.main === module) main().catch(error => {console.error(error.message);process.exitCode=1;});
