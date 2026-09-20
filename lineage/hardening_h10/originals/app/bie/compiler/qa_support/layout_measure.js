options => {
 const rect=e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height]};
 const visible=e=>{for(let n=e;n&&n.nodeType===1;n=n.parentElement){const c=getComputedStyle(n);if(Number(c.opacity)===0||c.display==='none'||c.visibility==='hidden')return false;}return true;};
 const rows=[];
 for(const layer of document.querySelectorAll('[data-bie-layer-id]')){
  const id=layer.getAttribute('data-bie-layer-id'),tracks=Array.from(layer.querySelectorAll('[data-bie-track-id]'));
  const runtimeOwner=layer.querySelector('[data-bie-runtime-target]');
  const owner=runtimeOwner||(tracks.length?tracks[tracks.length-1]:layer);
  const ink=[],texts=[],rendered=[];let overflow=false;
  const descendants=Array.from(layer.querySelectorAll('*'));if(owner===layer)descendants.unshift(layer);
  for(const el of descendants){
   if(el.closest('defs,title,desc')||!visible(el))continue;
   if((el===owner||!el.hasAttribute('data-bie-track-id'))&&el.namespaceURI!=='http://www.w3.org/2000/svg'&&el.clientWidth>0&&el.clientHeight>0&&(el.scrollWidth>el.clientWidth+1||el.scrollHeight>el.clientHeight+1))overflow=true;
   if(el.matches('svg use,svg path,svg polyline,svg polygon,svg circle,svg rect')){const b=rect(el);if(b[2]>0&&b[3]>0)ink.push(b);}
  }
  const walker=document.createTreeWalker(layer,NodeFilter.SHOW_TEXT);let text,index=0;
  while(text=walker.nextNode()){
   const nodeIndex=index++;if(!text.textContent.trim())continue;const e=text.parentElement;
   if(!e||e.closest('defs,title,desc')||!visible(e))continue;
   rendered.push(text.textContent);
   const range=document.createRange();range.selectNodeContents(text);
   let size=parseFloat(getComputedStyle(e).fontSize);
   if(e.namespaceURI==='http://www.w3.org/2000/svg'&&e.getScreenCTM){const m=e.getScreenCTM();size*=Math.hypot(m.a,m.b);}
   else {let factor=1;for(let n=e;n&&n!==layer.parentElement;n=n.parentElement){const s=getComputedStyle(n).scale;if(s!=='none'){const vals=s.split(' ').map(Number);factor*=Math.min(...vals);}}size*=factor;}
   const tid=id+':node:'+nodeIndex;let line=0;
   for(const r of range.getClientRects()){
    if(r.width>0&&r.height>0){const b=[r.x,r.y,r.width,r.height];texts.push({box:b,font_px:size,text_id:tid,fragment_id:tid+':fragment:'+line++});ink.push(b);}
   }
  }
  let em=null;const math=layer.querySelector('[role="math"]'),svg=math&&math.querySelector('svg'),native=math&&math.querySelector('math');
  if(svg){const m=svg.getScreenCTM();em=(options.equationFonts[id]||32)*Math.hypot(m.a,m.b);}
  else if(native)em=parseFloat(getComputedStyle(native).fontSize);
  rows.push({element_id:id,frame:options.frame,visible:visible(owner),layer_box:rect(owner),ink_boxes:ink,text_boxes:texts,rendered_text:rendered,scroll_overflow:overflow,equation_em_px:em});
 }
 return rows;
}
