options => {
 const out=[];const pointers=[];
 // Pointer hit-testing must not confuse transparent structural wrappers with ink.
 // Temporarily include pointer-events:none overlays, then restore before capture.
 for(const e of document.querySelectorAll('*'))if(getComputedStyle(e).pointerEvents==='none'){
  pointers.push([e,e.style.getPropertyValue('pointer-events'),e.style.getPropertyPriority('pointer-events')]);e.style.setProperty('pointer-events','auto','important');
 }
 const paintedAt=(e,x,y)=>{
  const c=getComputedStyle(e);if(c.display==='none'||c.visibility==='hidden'||+c.opacity===0)return false;
  if(/^(IMG|VIDEO|CANVAS|IFRAME)$/.test(e.tagName)||c.backgroundImage!=='none'||c.boxShadow!=='none')return true;
  const bg=/rgba?\(([^)]+)\)/.exec(c.backgroundColor);
  if(bg){const v=bg[1].split(/[,/ ]+/).filter(Boolean).map(Number);if(v.length===3||v[3]>0)return true;}
  if(e.namespaceURI==='http://www.w3.org/2000/svg'&&e.tagName.toLowerCase()!=='svg'&&(c.fill!=='none'||c.stroke!=='none'))return true;
  const r=e.getBoundingClientRect();for(const [side,d] of [['Left',x-r.left],['Right',r.right-x],['Top',y-r.top],['Bottom',r.bottom-y]]){
   if(parseFloat(c['border'+side+'Width'])>d&&c['border'+side+'Style']!=='none')return true;
  }
  for(const n of e.childNodes)if(n.nodeType===Node.TEXT_NODE&&n.textContent.trim()){
   const range=document.createRange();range.selectNodeContents(n);for(const b of range.getClientRects())if(x>=b.left&&x<=b.right&&y>=b.top&&y<=b.bottom)return true;
  }
  return false;
 };
 try {
 const rgb=value=>{const m=/^rgba?\(\s*([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:\s*[,/]\s*([\d.]+))?\s*\)$/.exec(value);return m?[+m[1],+m[2],+m[3],m[4]===undefined?1:+m[4]]:null;};
 const lum=c=>{const q=c.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4});return .2126*q[0]+.7152*q[1]+.0722*q[2];};
 for(const layer of document.querySelectorAll('[data-bie-layer-id]')){
  const walker=document.createTreeWalker(layer,NodeFilter.SHOW_TEXT);let text;const rows=[];let index=0;
  while(text=walker.nextNode()){
   const i=index++;if(!text.textContent.trim())continue;const e=text.parentElement;
   if(!e||e.closest('defs,title,desc'))continue;
   let visible=true,alpha=1,bg=null,complex=false;
   for(let n=e;n&&n.nodeType===1;n=n.parentElement){const c=getComputedStyle(n);if(c.display==='none'||c.visibility==='hidden'||+c.opacity===0)visible=false;alpha*=+c.opacity;
    if(c.backgroundImage!=='none'||c.filter!=='none'||c.mixBlendMode!=='normal')complex=true;
    const candidate=rgb(c.backgroundColor);if(!bg&&candidate&&candidate[3]===1)bg=candidate;
   }
   if(!visible)continue;
   const c=getComputedStyle(e),fg=rgb(e.namespaceURI==='http://www.w3.org/2000/svg'?c.fill:c.color);
   let contrast=null;if(fg&&bg&&!complex){const a=fg[3]*alpha;const blended=fg.slice(0,3).map((x,j)=>a*x+(1-a)*bg[j]);const l1=lum(blended),l2=lum(bg);contrast=(Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05);}
   const range=document.createRange();range.selectNodeContents(text);const boxes=[];
   for(const r of range.getClientRects()){
    if(r.width<=0||r.height<=0)continue;const points=[[r.x+r.width*.5,r.y+r.height*.5],[r.x+r.width*.2,r.y+r.height*.5],[r.x+r.width*.8,r.y+r.height*.5]];
    let occluded=0,checked=0;
    for(const [x,y] of points){if(x<0||y<0||x>=innerWidth||y>=innerHeight)continue;checked++;
     const top=document.elementsFromPoint(x,y).find(n=>paintedAt(n,x,y));
     if(top&&top!==e&&!e.contains(top)&&!top.contains(e))occluded++;
    }
    let clipped=false;for(let n=e;n;n=n.parentElement){const s=getComputedStyle(n);if(['hidden','clip','scroll','auto'].includes(s.overflowX)||['hidden','clip','scroll','auto'].includes(s.overflowY)){const b=n.getBoundingClientRect();if(r.x<b.x-.75||r.y<b.y-.75||r.right>b.right+.75||r.bottom>b.bottom+.75)clipped=true;}}
    boxes.push({box:[r.x,r.y,r.width,r.height],tested_points:checked,occluded_points:occluded,ancestor_clip:clipped});
   }
   rows.push({text_id:layer.dataset.bieLayerId+':node:'+i,text:text.textContent,font_family:c.fontFamily,font_ready:document.fonts.check(c.font,text.textContent),contrast,complex_background:complex,boxes});
  }
  const ink=[];let shapeIndex=0;
  for(const shape of layer.querySelectorAll('svg path,svg rect,svg line,svg polyline,svg polygon,svg circle,svg ellipse,svg use')){
   if(shape.closest('defs'))continue;const cs=getComputedStyle(shape);let visible=cs.fill!=='none'||cs.stroke!=='none';
   for(let n=shape;n;n=n.parentElement){const a=getComputedStyle(n);if(a.display==='none'||a.visibility==='hidden'||+a.opacity===0)visible=false;}
   if(!visible)continue;
   const item={shape_id:layer.dataset.bieLayerId+':ink:'+(shapeIndex++),box:null,clipped:false,unsupported_effect:false,error:null};
   try{
    const b=shape.getBBox(),m=shape.getScreenCTM();if(!m)throw Error('missing screen transform');
    const points=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));
    const pad=cs.stroke!=='none'?(parseFloat(cs.strokeWidth)||0)*Math.max(Math.hypot(m.a,m.b),Math.hypot(m.c,m.d))*.5:0;
    const left=Math.min(...points.map(p=>p.x))-pad,top=Math.min(...points.map(p=>p.y))-pad,right=Math.max(...points.map(p=>p.x))+pad,bottom=Math.max(...points.map(p=>p.y))+pad;
    item.box=[left,top,right-left,bottom-top];
    item.clipped=left<-.75||top<-.75||right>innerWidth+.75||bottom>innerHeight+.75;
    for(let n=shape;n;n=n.parentElement){const a=getComputedStyle(n),r=n.getBoundingClientRect();
     if(a.filter!=='none'||a.clipPath!=='none'||a.maskImage!=='none')item.unsupported_effect=true;
     if(['hidden','clip','auto','scroll'].includes(a.overflowX)&&(left<r.x-.75||right>r.right+.75))item.clipped=true;
     if(['hidden','clip','auto','scroll'].includes(a.overflowY)&&(top<r.y-.75||bottom>r.bottom+.75))item.clipped=true;
    }
   }catch(e){item.error=String(e);}
   ink.push(item);
  }
  out.push({element_id:layer.dataset.bieLayerId,frame:options.frame,text:rows,ink});
 }
 return out;
 } finally {for(const [e,value,priority] of pointers){if(value)e.style.setProperty('pointer-events',value,priority);else e.style.removeProperty('pointer-events');}}
}
