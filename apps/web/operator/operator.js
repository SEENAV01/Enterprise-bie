'use strict';
// No localStorage, cookies, raw JSON display, innerHTML, eval, or remote assets.
const byId=id=>document.getElementById(id);
let token='', source=null, run=null, intentKey=null, retryKey=null, timelineAfter=0, busy=false, authEpoch=0;
const notice=text=>{byId('notice').textContent=text;};
const key=()=>crypto.randomUUID().replaceAll('-','');
async function api(path,method='GET',data=null,pdf=false,rawJson=false){
  if(!token)throw new Error('unauthorized');
  const requestEpoch=authEpoch;const headers={'Authorization':'Bearer '+token};
  if(data!==null)headers['Content-Type']=pdf?'application/pdf':'application/json';
  const r=await fetch('/operator/v1/'+path,{method,headers,body:data===null?undefined:((pdf||rawJson)?data:JSON.stringify(data)),credentials:'omit',redirect:'error',cache:'no-store'});
  const result=await r.json();if(requestEpoch!==authEpoch)throw new Error('credential_changed');if(r.status===401)reset();if(!r.ok)throw new Error(result.error?.code||'backend_unavailable'); return result;
}
async function action(fn){
  if(busy)return;busy=true;document.body.setAttribute('aria-busy','true');for(const id of ['pdf','locale','token'])byId(id).disabled=true;
  try{await fn();}catch(e){notice('Action not completed · '+(e.message||'backend_unavailable'));}
  finally{busy=false;document.body.setAttribute('aria-busy','false');for(const id of ['pdf','locale','token'])byId(id).disabled=false;}
}
function fields(target,values){
  target.replaceChildren(); const dl=document.createElement('dl');
  for(const [k,v] of Object.entries(values)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=String(v);dl.append(dt,dd);}target.append(dl);
}
function reset(){authEpoch++;token='';byId('token').value='';source=null;run=null;intentKey=null;retryKey=null;byId('run-id').value='';resetPreviews(false);resetQuality(false);resetAssurance(false);resetAdministration(false);resetGovernance(false);
 for(const id of ['upload','create','refresh','open-run','pause','resume','cancel','retry','concept','prerequisite','more-timeline'])byId(id).disabled=true;
 for(const id of ['validation','run-summary','timeline','graph','graph-fallback','failure','evidence-view'])byId(id).replaceChildren();resetViews(false);notice('Credential cleared · private state removed from this page.');}
byId('disconnect').onclick=reset;
byId('connect').onclick=()=>action(async()=>{const nextCredential=byId('token').value;reset();token=nextCredential;byId('token').value=token;await api('runs?limit=1');byId('upload').disabled=false;byId('open-run').disabled=false;resetAdministration(true);resetGovernance(true);notice('Authorized workspace opened · no automatic work dispatched.');});
byId('pdf').onchange=()=>{source=null;intentKey=null;byId('create').disabled=true;byId('validation').replaceChildren();};
byId('locale').onchange=()=>{if(source)intentKey=key();};
byId('upload').onclick=()=>action(async()=>{const file=byId('pdf').files[0];if(!file)throw new Error('source_required');if(file.size>25*1024*1024)throw new Error('payload_too_large');
  source=await api('sources','POST',file,true);intentKey=key();
  fields(byId('validation'),{'Validation':source.validation.status,'Diagnostics':source.validation.diagnostic_codes.join(', ')||'None','SHA-256':source.sha256,'Bytes':source.size_bytes,'Pages':source.validation.page_count??'Unknown','Duplicate':source.duplicate});
  byId('create').disabled=source.validation.status!=='VALID';notice('Source validation · '+source.validation.status);});
byId('create').onclick=()=>action(async()=>{if(!source)throw new Error('source_required');
 const request={source_id:source.source_id,config:{locale:byId('locale').value},idempotency_key:intentKey};if(selectedPolicy)request.policy_binding=selectedPolicy;
 const created=await api('runs','POST',request);byId('run-id').value=created.run_id;await refresh(created.run_id);});
async function refresh(id=run?.run_id){if(!id)throw new Error('run_required');run=await api('runs/'+encodeURIComponent(id));resetViews(true);resetPreviews(true);resetQuality(true);resetAssurance(true);
 fields(byId('run-summary'),{'Run':run.run_id,'Status':run.status,'Native engine':run.engine_state,'Canonical queue':run.queue_state,'Executor admission':run.executor_admission,'Source hash':run.source_hash,'Config hash':run.config_hash,'Parent':run.parent_run_id||'None','Learning video/game':'NOT_RUN · producer not bound','Product accepted':'No'});
 for(const id of ['refresh','concept','prerequisite'])byId(id).disabled=false;
 byId('pause').disabled=run.status!=='READY';byId('resume').disabled=run.status!=='PAUSED';byId('cancel').disabled=!['READY','PAUSED'].includes(run.status);byId('retry').disabled=run.status!=='FAILED';
 timelineAfter=0;byId('timeline').replaceChildren();await timeline();
 if(['FAILED','BLOCKED','CANCELLED'].includes(run.status)){const f=await api('runs/'+run.run_id+'/failure');fields(byId('failure'),{'Status':f.status,'Codes':f.diagnostic_codes.join(', ')||'None','Evidence':f.evidence_refs.join(', ')||'None'});}else byId('failure').textContent='No failure in persisted state.';
 notice('Loaded persisted '+run.status+' · no completion percentage fabricated.');}
byId('refresh').onclick=()=>action(()=>refresh());
byId('open-run').onclick=()=>action(()=>refresh(byId('run-id').value));
async function evidence(ref){const e=await api('runs/'+run.run_id+'/evidence/'+encodeURIComponent(ref));fields(byId('evidence-view'),{'Identity':e.evidence_id,'SHA-256':e.sha256,'Kind':e.artifact_type,'Parents':e.parent_refs.join(', '),'Origin':e.provenance,'Status':e.evidence.status,'Diagnostic':e.evidence.diagnostic_code||'None'});byId('evidence-title').scrollIntoView();}
async function timeline(){const page=await api('runs/'+run.run_id+'/timeline?after='+timelineAfter);for(const e of page.items){const li=document.createElement('li');li.textContent=`${e.timestamp} · ${e.stage_id} · ${e.from_state||'—'} → ${e.to_state} · ${e.reason} · attempt ${e.attempt} · ${e.event_origin}`;for(const ref of e.evidence_refs){const b=document.createElement('button');b.textContent='Open evidence '+ref;b.onclick=()=>action(()=>evidence(ref));li.append(b);}byId('timeline').append(li);}timelineAfter=page.next_after;byId('more-timeline').disabled=timelineAfter===null;}
byId('more-timeline').onclick=()=>action(timeline);
for(const name of ['pause','resume','cancel'])byId(name).onclick=()=>action(async()=>{await api('runs/'+run.run_id+'/control','POST',{action:name,expected_revision:run.revision});await refresh();});
byId('retry').onclick=()=>action(async()=>{retryKey??=key();const child=await api('runs/'+run.run_id+'/retry','POST',{idempotency_key:retryKey});byId('run-id').value=child.run_id;retryKey=null;await refresh(child.run_id);});
for(const kind of ['concept','prerequisite'])byId(kind).onclick=()=>action(async()=>{const value=await api('runs/'+run.run_id+'/graphs/'+kind);byId('graph').replaceChildren();byId('graph-fallback').replaceChildren();
 byId('graph-state').textContent=value.status==='AVAILABLE'?`${kind} · verified artifact ${value.sha256} · origin ${value.evidence_origin} · semantic correctness not claimed`:`NOT_RUN · ${value.reason}`;
 if(value.status!=='AVAILABLE')return;const sourceLink=document.createElement('button');sourceLink.textContent='Open linked source validation';sourceLink.onclick=()=>action(async()=>{const s=await api('sources/'+value.source_id);fields(byId('validation'),{'Source':s.source_id,'SHA-256':s.sha256,'Validation':s.validation.status,'Pages':s.validation.page_count});byId('source-title').scrollIntoView();});const evidenceLink=document.createElement('button');evidenceLink.textContent='Open graph provenance';evidenceLink.onclick=()=>action(()=>evidence(value.evidence_ref));byId('graph-fallback').append(sourceLink,evidenceLink);
 const {nodes,edges}=value.graph;const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 1000 ${Math.max(300,Math.ceil(nodes.length/3)*90+40)}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',kind+' graph; accessible nodes and edges table follows');
 const pos=new Map(nodes.map((n,i)=>[n.id,{x:200+(i%3)*290,y:45+Math.floor(i/3)*90}]));
 const defs=document.createElementNS(ns,'defs'),marker=document.createElementNS(ns,'marker'),arrow=document.createElementNS(ns,'path');marker.setAttribute('id','arrow');marker.setAttribute('viewBox','0 0 10 10');marker.setAttribute('refX','9');marker.setAttribute('refY','5');marker.setAttribute('markerWidth','7');marker.setAttribute('markerHeight','7');marker.setAttribute('orient','auto');arrow.setAttribute('d','M 0 0 L 10 5 L 0 10 z');arrow.setAttribute('fill','#c6e784');marker.append(arrow);defs.append(marker);svg.append(defs);
 for(const e of edges){const a=pos.get(e.source),b=pos.get(e.target),line=document.createElementNS(ns,'line');for(const [k,v] of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y}))line.setAttribute(k,String(v));line.setAttribute('marker-end','url(#arrow)');svg.append(line);}
 for(const n of nodes){const p=pos.get(n.id),circle=document.createElementNS(ns,'circle'),text=document.createElementNS(ns,'text');circle.setAttribute('cx',String(p.x));circle.setAttribute('cy',String(p.y));circle.setAttribute('r','15');text.setAttribute('x',String(p.x-80));text.setAttribute('y',String(p.y+32));text.textContent=n.label;svg.append(circle,text);}byId('graph').append(svg);
 const table=document.createElement('table'),caption=document.createElement('caption');caption.textContent='Accessible '+kind+' nodes and directed relations';table.append(caption);for(const n of nodes){const tr=document.createElement('tr');for(const v of [n.id,n.label]){const td=document.createElement('td');td.textContent=v;tr.append(td);}table.append(tr);}for(const e of edges){const tr=document.createElement('tr');for(const v of [e.source+' → '+e.target,e.type]){const td=document.createElement('td');td.textContent=v;tr.append(td);}table.append(tr);}byId('graph-fallback').append(table);
 if(kind==='prerequisite'){const p=document.createElement('p');p.textContent='Teaching order: '+value.graph.order.join(' → ')+'. Ready roots: '+value.graph.roots.join(', ');byId('graph-fallback').append(p);}});
