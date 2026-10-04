'use strict';
// Protocol-only controlled peer tests. NOT Chromium execution/acceptance.
const assert=require('assert/strict'),net=require('net'),crypto=require('crypto');
const {evaluate,exactNodeLimit}=require('./section18_chromium_resource_probe.cjs');
async function peer(mode) {
  const sockets=new Set();let gotCommand=false;
  const server=net.createServer(socket=>{
    sockets.add(socket);socket.on('close',()=>sockets.delete(socket));socket.on('error',()=>{});
    let buffer=Buffer.alloc(0),handshake=false;
    socket.on('data',chunk=>{
      buffer=Buffer.concat([buffer,chunk]);
      if(!handshake) {
        const end=buffer.indexOf('\r\n\r\n');if(end<0)return;
        const request=buffer.subarray(0,end).toString();
        const key=/Sec-WebSocket-Key: (.+)\r\n/.exec(request+'\r\n')[1];
        const accept=crypto.createHash('sha1').update(key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
        if(mode==='huge-header'){socket.write('x'.repeat(9000));return;}
        if(mode==='bad-accept'){socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: wrong\r\n\r\n');return;}
        socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+'\r\n\r\n');
        buffer=buffer.subarray(end+4);handshake=true;
      }
      if(buffer.length<6)return;
      let size=buffer[1]&127,offset=2;if(size===126){if(buffer.length<8)return;size=buffer.readUInt16BE(2);offset=4;}
      if(buffer.length<offset+4+size)return;
      assert.equal(buffer[0],129);assert.ok(buffer[1]&128);
      const mask=buffer.subarray(offset,offset+4),body=Buffer.from(buffer.subarray(offset+4,offset+4+size));
      for(let i=0;i<body.length;i++)body[i]^=mask[i%4];
      const command=JSON.parse(body.toString());assert.equal(command.method,'Runtime.evaluate');gotCommand=true;
      if(mode==='early-close'){socket.end();return;}
      if(mode==='masked'){socket.write(Buffer.from([129,128,0,0,0,0]));return;}
      if(mode==='fragmented'){socket.write(Buffer.from([1,0]));return;}
      if(mode==='huge-frame'){socket.write(Buffer.from([129,127,0,0,0,0,0,2,0,0]));return;}
      const result=Buffer.from(JSON.stringify({id:1,result:{result:{value:'{"arithmetic":42,"title":""}'}}}));
      assert.ok(result.length<126);const frame=Buffer.concat([Buffer.from([129,result.length]),result]);
      // Genuine TCP fragmentation is supported; RFC6455 message fragmentation
      // is deliberately unsupported for this one small trusted diagnostic.
      socket.write(frame.subarray(0,1));setTimeout(()=>{if(!socket.destroyed)socket.write(frame.subarray(1));},5);
    });
  });
  try {
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(9222,'127.0.0.1',resolve);});
    if(mode==='positive'){const v=await evaluate('ws://127.0.0.1:9222/devtools/page/test-target');assert.equal(JSON.parse(v.result.result.value).arithmetic,42);}
    else await assert.rejects(evaluate('ws://127.0.0.1:9222/devtools/page/test-target'));
    if(!['bad-accept','huge-header'].includes(mode))assert.ok(gotCommand);
  } finally {for(const socket of sockets)socket.destroy();if(server.listening)await new Promise(resolve=>server.close(resolve));}
}
(async()=>{
  let controls=0;
  for(const mode of ['positive','bad-accept','huge-header','masked','fragmented','huge-frame','early-close']){await peer(mode);controls++;}
  assert.throws(()=>evaluate('ws://external.test:9222/devtools/page/test-target'));controls++;
  assert.ok(exactNodeLimit('Max address space         8589934592           8589934592           bytes     \n'));
  assert.ok(!exactNodeLimit('Max address space         2199023255552        2199023255552        bytes\n'));controls++;
  assert.ok(!process.execArgv.length&&!process.env.NODE_OPTIONS);controls++;
  console.log(JSON.stringify({schema:'bie.section18.diagnostic-transport-controls/1',controls_run:controls,passed:true,
    new_atomic_methods:0,native_browser_pass_claimed:false,production_policy_changed:false}));
})().catch(error=>{console.error(error);process.exitCode=1;});
