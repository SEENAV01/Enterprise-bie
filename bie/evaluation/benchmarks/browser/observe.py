"""H4-005: fixed DOM observation code; no candidate-reported PASS is consumed.
Only solid opaque text/background contrast is supported. Browser pixels are
retained separately. This is not a complete accessibility or legibility audit.
"""
DOM_SCRIPT = r'''(el) => {
 const r=el.getBoundingClientRect(), s=getComputedStyle(el);
 const rgba=v=>{const m=v.match(/^rgba?\(([^)]+)\)$/);if(!m)return null;
  const a=m[1].split(',').map(Number);return a.length===3?[...a,1]:a.length===4?a:null;};
 let bg=null, complex=false, node=el;
 while(node){const cs=getComputedStyle(node);
  if(cs.backgroundImage!=='none'||Number(cs.opacity)!==1||cs.filter!=='none'||cs.mixBlendMode!=='normal') complex=true;
  const color=rgba(cs.backgroundColor);
  if(!bg&&color&&color[3]===1)bg=color;
  if(!bg&&color&&color[3]>0&&color[3]<1)complex=true;
  node=node.parentElement;
 }
 const fg=rgba(s.color);if(!bg)bg=[255,255,255,1];
 function lum(c){const v=c.slice(0,3).map(x=>{x/=255;return x<=0.04045?x/12.92:((x+0.055)/1.055)**2.4;});return .2126*v[0]+.7152*v[1]+.0722*v[2];}
 let contrast=null;if(!complex&&fg&&fg[3]===1){const a=lum(fg),b=lum(bg);contrast=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);}
 let vis=r.width>0&&r.height>0&&s.display!=='none'&&s.visibility==='visible';
 for(let n=el;n;n=n.parentElement){const cs=getComputedStyle(n);if(cs.display==='none'||cs.visibility!=='visible'||Number(cs.opacity)===0)vis=false;}
 let unclipped=el.scrollWidth<=el.clientWidth+1&&el.scrollHeight<=el.clientHeight+1;
 for(let n=el.parentElement;n;n=n.parentElement){const cs=getComputedStyle(n),a=n.getBoundingClientRect();
  if(['hidden','clip','scroll','auto'].includes(cs.overflowX)&&(r.left<a.left-1||r.right>a.right+1))unclipped=false;
  if(['hidden','clip','scroll','auto'].includes(cs.overflowY)&&(r.top<a.top-1||r.bottom>a.bottom+1))unclipped=false;}
 const text=(el.innerText||'').trim(); const name=(el.getAttribute('aria-label')||el.getAttribute('alt')||text).trim();
 return {text:text.slice(0,2049),value:typeof el.value==='string'?el.value.slice(0,2049):null,
  visible:vis,enabled:!el.disabled&&el.getAttribute('aria-disabled')!=='true',focused:document.activeElement===el,
  checked:typeof el.checked==='boolean'?el.checked:null,in_viewport:vis&&r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,
  unclipped:vis&&unclipped,has_accessible_name:!!name,contrast_at_least:contrast,
  bounds:{x:r.x,y:r.y,width:r.width,height:r.height},tag:el.tagName.toLowerCase(),
  role:el.getAttribute('role'),aria_live:el.getAttribute('aria-live'),
  observation_scope:'SOLID_COLOR_DOM_GEOMETRY_NOT_COMPLETE_ACCESSIBILITY'};
}'''

def observe(page,selector):
    # Use an isolated CDP world, not page-main-world methods that candidate JS
    # can replace (getComputedStyle/getBoundingClientRect/querySelectorAll).
    import json
    from ..models import BenchmarkError
    from .contracts import target
    target(selector)
    session=page.context.new_cdp_session(page)
    try:
        frame=session.send('Page.getFrameTree')['frameTree']['frame']['id']
        world=session.send('Page.createIsolatedWorld',{'frameId':frame,'worldName':'bie-observer-h4'})['executionContextId']
        expression='(() => { const nodes=document.querySelectorAll('+json.dumps(selector)+'); if(nodes.length!==1)return {present:false,count:nodes.length,reason:"TARGET_MISSING_OR_AMBIGUOUS"}; return {present:true,count:1,...('+DOM_SCRIPT+')(nodes[0])}; })()'
        response=session.send('Runtime.evaluate',{'expression':expression,'contextId':world,'returnByValue':True,'timeout':2000})
        if 'exceptionDetails' in response:raise BenchmarkError('BROWSER_ISOLATED_OBSERVER_FAILED')
        result=response['result'].get('value')
        if type(result) is not dict:raise BenchmarkError('BROWSER_ISOLATED_OBSERVER_FAILED')
        if any(isinstance(result.get(k),str) and len(result[k])>2048 for k in ('text','value')):
            return {'present':False,'count':result.get('count',0),'reason':'OBSERVED_TEXT_LIMIT'}
        result['observer_world']='ISOLATED_CDP'
        return result
    finally:session.detach()
