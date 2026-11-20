// BIE voice for the studio players (film and PYQ lab), inlined into each page by bie/brain/studio_voice.py.
// Navin, 20 November 2026: the first Photosynthesis films played without a voice on his tablet. The clips were inside the
// file, but the page played them as blob: URLs through an <audio> element; a viewer that refuses media loads (a page
// policy with media-src) blocks that, and the player went on silently. Now a clip plays as a data: URI through the
// <audio> element first (it also sounds when a phone's silent switch mutes Web Audio); when the viewer refuses it, the
// clip is decoded and played through the Web Audio API (no media load to refuse); when neither can sound the page is
// told, so it shows that the sound is blocked instead of running a silent film.
const BIEVoice=(()=>{
  let ctx=null,node=null,tok=0,state='idle',onState=null;const cache=new Map();const el=new Audio();el.preload='auto';
  function unlock(){try{const C=window.AudioContext||window.webkitAudioContext;if(C&&!ctx)ctx=new C();
      if(ctx){if(ctx.state==='suspended')ctx.resume();const b=ctx.createBuffer(1,1,22050),s=ctx.createBufferSource();s.buffer=b;s.connect(ctx.destination);s.start(0);}}
    catch(e){ctx=null;}}
  ['pointerdown','touchend','keydown','click'].forEach(t=>document.addEventListener(t,unlock,{capture:true,passive:true}));
  function bytes(uri){const b64=uri.slice(uri.indexOf(',')+1),bin=atob(b64),a=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)a[i]=bin.charCodeAt(i);return a.buffer;}
  function decode(uri){if(!cache.has(uri))cache.set(uri,new Promise((ok,no)=>{try{const p=ctx.decodeAudioData(bytes(uri),ok,no);if(p&&p.then)p.then(ok,no);}catch(e){no(e);}}));
    const p=cache.get(uri);p.catch(()=>cache.delete(uri));return p;}
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  function set(s){state=s;if(onState)try{onState(s);}catch(e){}}
  function stop(){tok++;if(node){try{node.onended=null;node.stop();}catch(e){}node=null;}try{el.onended=null;el.pause();}catch(e){}}
  async function viaContext(uri,rate,my,done){if(!ctx)throw new Error('no audio context');
    if(ctx.state!=='running'){try{await Promise.race([ctx.resume(),wait(500)]);}catch(e){}}
    if(ctx.state!=='running')throw new Error('audio context '+ctx.state);
    const buf=await decode(uri);if(my!==tok)return;
    const s=ctx.createBufferSource();s.buffer=buf;s.playbackRate.value=rate;s.connect(ctx.destination);
    s.onended=()=>{if(node===s){node=null;done();}};node=s;s.start(0);}
  async function viaElement(uri,rate,my,done){el.src=uri;el.playbackRate=rate;el.onended=()=>{if(my===tok)done();};await el.play();}
  // play(uri,{rate,done,fail}): done() when the clip ends; fail(why) when no route can sound (the page then times the line itself)
  async function play(uri,o){o=o||{};const rate=o.rate||1,done=o.done||(()=>{}),fail=o.fail||(()=>{});stop();const my=++tok;
    if(!uri){fail('no clip');return;}
    try{await viaElement(uri,rate,my,done);if(my===tok)set('element');return;}catch(e){}
    if(my!==tok)return;
    try{await viaContext(uri,rate,my,done);if(my===tok)set('context');return;}catch(e){}
    if(my!==tok)return;set('blocked');fail('blocked');}
  function prefetch(uri){if(ctx&&uri)decode(uri).catch(()=>{});}
  return {play,stop,unlock,prefetch,get state(){return state;},set onState(f){onState=f;}};
})();
