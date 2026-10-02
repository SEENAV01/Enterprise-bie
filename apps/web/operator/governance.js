'use strict';
let governanceKind=null,governanceAfter=null,governanceSerial=0,selectedPolicy=null;
const governanceKeys=new Map();
function governanceKey(identity){if(!governanceKeys.has(identity))governanceKeys.set(identity,key());return governanceKeys.get(identity);}
function clearPolicy(){selectedPolicy=null;if(source)intentKey=key();byId('policy-binding-state').textContent='No versioned policy selected; fixed inspection defaults apply.';}
function resetGovernance(enabled){governanceSerial++;governanceKind=null;governanceAfter=null;governanceKeys.clear();clearPolicy();
 for(const id of ['governance-content','governance-detail'])byId(id).replaceChildren();
 for(const id of ['policy-id','benchmark-id','benchmark-file','audit-action','audit-target'])byId(id).value='';
 byId('policy-revision').value='0';byId('benchmark-revision').value='0';byId('policy-limit').value='26214400';byId('policy-locale').value='en';
 for(const kind of ['policy','benchmark','audit'])byId('governance-'+kind).disabled=!enabled;
 byId('governance-more').disabled=true;for(const id of ['policy-save','benchmark-save','policy-clear-binding'])byId(id).disabled=true;
 byId('governance-state').textContent='NOT_RUN · configuration not loaded.';}
async function governanceLoad(kind,more=false){const epoch=authEpoch,serial=++governanceSerial;
 if(!more){governanceKind=kind;governanceAfter=null;byId('governance-content').replaceChildren();byId('governance-detail').replaceChildren();}
 const query=new URLSearchParams({limit:'25'});if(more&&governanceAfter!==null)query.set('after',governanceAfter);
 if(kind==='audit'){for(const field of ['action','target'])if(byId('audit-'+field).value)query.set(field,byId('audit-'+field).value);}
 byId('governance-state').textContent='Loading verified '+kind+'…';
 try{const v=await api((kind==='audit'?'admin/audit':'governance/'+kind)+'?'+query);
  if(epoch!==authEpoch||serial!==governanceSerial)throw new Error('stale_governance_response');
  governanceAfter=v.next_after;byId('governance-more').disabled=governanceAfter===null;
  byId('governance-state').textContent=kind+' · '+v.status+' · product accepted No';
  if(kind==='audit'){
   qualityTable(byId('governance-content'),'Tenant-attributed verified audit history',['Sequence','Actor','Action','Target','Timestamp','Authorization','Before hash','After hash','Receipt','Attribution'],
    v.items.map(r=>[r.sequence,r.actor,r.action,r.target,r.timestamp,r.authorization,r.before_sha256||'Not recorded',r.after_sha256||'Not recorded',r.receipt_sha256,r.tenant_attribution]));return;}
  byId('policy-save').disabled=!(kind==='policy'&&v.can_configure);byId('benchmark-save').disabled=!(kind==='benchmark'&&v.can_configure);
  for(const item of v.items){const a=document.createElement('article'),h=document.createElement('h3');h.textContent=item.config_id+' · revision '+item.revision;a.append(h);
   const active=v.active?.config_id===item.config_id&&v.active?.revision===item.revision;
   fields(a.appendChild(document.createElement('div')),{'Configuration hash':item.configuration_sha256,'Created':item.created_at,'Actor':item.actor,'Active':active,'Execution':'NOT_RUN · configuration alone is not execution','Consumer scope':v.consumer_scope,'Release authorized':'No'});
   if(kind==='policy'){
    fields(a.appendChild(document.createElement('div')),{'Model policy':item.configuration.model_policy,'Locale':item.configuration.locale,'Deterministic':item.configuration.deterministic,'Admission bytes':item.configuration.limits.pdf_bytes});
    const use=document.createElement('button');use.textContent='Bind policy to next new run';use.disabled=!active;
    use.onclick=()=>{selectedPolicy={config_id:item.config_id,revision:item.revision,configuration_sha256:item.configuration_sha256};byId('locale').value=item.configuration.locale;if(source)intentKey=key();byId('policy-clear-binding').disabled=false;
     byId('policy-binding-state').textContent='Explicit policy '+item.config_id+' revision '+item.revision+' · '+item.configuration_sha256+'. Applies only to next requested run; no learning producer enabled.';};a.append(use);
    const edit=document.createElement('button');edit.textContent='Prepare next policy version';edit.disabled=!v.can_configure;edit.onclick=()=>{byId('policy-id').value=item.config_id;byId('policy-revision').value=item.revision;byId('policy-locale').value=item.configuration.locale;byId('policy-limit').value=item.configuration.limits.pdf_bytes;};a.append(edit);
   }else{
    const c=item.configuration,m=c.manifest,p=c.policy;
    fields(a.appendChild(document.createElement('div')),{'Benchmark':m.id,'Benchmark version':m.version,'Dataset hash':m.dataset_sha256,'Candidate hash':m.artifact_sha256,'Split':m.split,'Reference grade':m.reference_grade,'Mode':p.mode,'Threshold':p.enterprise.minimum_score,'Measured fraction floor':p.enterprise.minimum_measured_fraction});
    qualityTable(a,'Pinned raters',['Identity','Type','Independence group'],p.aggregation.raters.map(r=>[r.id,r.kind,r.independence_group]));
    qualityTable(a,'Critical floors',['Metric','Minimum'],p.critical_floors.floors.map(r=>[r.id,r.minimum]));
    qualityTable(a,'Domain floors',['Domain','Minimum','Cases','Measured fraction'],p.domains.domains.map(r=>[r.id,r.minimum_score,r.minimum_cases,r.minimum_measured_fraction]));
    qualityTable(a,'Complete pinned metric roster',['Metric','Weight'],p.enterprise.metrics.map(r=>[r.id,r.weight]));
    qualityTable(a,'Frozen case context',['Case','Domain','Metric','Reference hash','Rubric hash'],m.cases.map(r=>[r.context.case_id,r.context.domain,r.context.metric_id,r.context.reference_sha256,r.context.rubric_sha256]));
   }
   const history=document.createElement('button');history.textContent='Open immutable version history';history.onclick=()=>action(()=>governanceHistory(kind,item.config_id));a.append(history);
   const activate=document.createElement('button');activate.textContent='Activate pinned version';activate.disabled=active||!v.can_configure;
   activate.onclick=()=>action(async()=>{await api('governance/'+kind+'/'+item.config_id+'/activate','POST',{revision:item.revision,configuration_sha256:item.configuration_sha256,expected_active_sha256:v.active?.activation_sha256||null,
     idempotency_key:governanceKey('activate:'+kind+':'+item.config_id+':'+item.revision+':'+(v.active?.activation_sha256||'none'))});await governanceLoad(kind);notice('Pinned configuration activated · historical runs and evaluation receipts unchanged.');});a.append(activate);
   byId('governance-content').append(a);
  }
  if(!v.items.length){const p=document.createElement('p');p.textContent='No saved '+kind+' configuration. No execution or measured score is claimed.';byId('governance-content').append(p);}
 }catch(e){if(epoch===authEpoch&&serial===governanceSerial){byId('governance-content').replaceChildren();byId('governance-detail').replaceChildren();governanceAfter=null;byId('governance-more').disabled=true;byId('policy-save').disabled=true;byId('benchmark-save').disabled=true;byId('governance-state').textContent='BLOCKED · configuration or audit unverified';}throw e;}}
async function governanceHistory(kind,id,after=0){const epoch=authEpoch,serial=governanceSerial;
 const v=await api('governance/'+kind+'/'+id+'/history?after_revision='+after+'&limit=25');
 if(epoch!==authEpoch||serial!==governanceSerial)throw new Error('stale_governance_response');if(!after)byId('governance-detail').replaceChildren();
 qualityTable(byId('governance-detail'),'Immutable configuration versions',['Revision','Hash','Previous hash','Actor','Timestamp'],v.items.map(r=>[r.revision,r.configuration_sha256,r.previous_sha256||'Initial',r.actor,r.created_at]));
 for(const item of v.items)if(item.revision>1){const diff=document.createElement('button');diff.textContent='Compare revision '+(item.revision-1)+' → '+item.revision;
  diff.onclick=()=>action(async()=>{const d=await api('governance/'+kind+'/'+id+'/diff?left='+(item.revision-1)+'&right='+item.revision);if(epoch!==authEpoch||serial!==governanceSerial)throw new Error('stale_governance_response');
   qualityTable(byId('governance-detail'),'Verified version differences',['Field','Before','After'],d.changes.map(r=>[r.path,typeof r.before==='object'?'Structured value changed':String(r.before),typeof r.after==='object'?'Structured value changed':String(r.after)]));});byId('governance-detail').append(diff);}
 if(v.next_revision!==null){const more=document.createElement('button');more.textContent='More immutable versions';more.onclick=()=>action(()=>governanceHistory(kind,id,v.next_revision));byId('governance-detail').append(more);}}
byId('policy-save').onclick=()=>action(async()=>{const id=byId('policy-id').value,revision=Number(byId('policy-revision').value),configuration={model_policy:'offline_only',deterministic:true,locale:byId('policy-locale').value,limits:{pdf_bytes:Number(byId('policy-limit').value)}};
 await api('governance/policy/'+encodeURIComponent(id)+'/versions','POST',{configuration,expected_revision:revision,idempotency_key:governanceKey('policy:'+id+':'+revision+':'+configuration.locale+':'+configuration.limits.pdf_bytes)});
 await governanceLoad('policy');notice('Immutable policy saved · not automatically activated.');});
byId('benchmark-save').onclick=()=>action(async()=>{const f=byId('benchmark-file').files[0];if(!f)throw new Error('benchmark_configuration_required');if(f.size>16384)throw new Error('payload_too_large');
 const raw=await f.text(),id=byId('benchmark-id').value,revision=Number(byId('benchmark-revision').value);
 // Preserve raw keys for the SERVER'S strict duplicate-key validator. Parsing
 // and reserializing in the browser would silently discard conflicting keys.
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw)),hash=[...new Uint8Array(bytes)].map(v=>v.toString(16).padStart(2,'0')).join('');
 const request='{"configuration":'+raw+',"expected_revision":'+JSON.stringify(revision)+',"idempotency_key":'+JSON.stringify(governanceKey('benchmark:'+id+':'+revision+':'+hash))+'}';
 await api('governance/benchmark/'+encodeURIComponent(id)+'/versions','POST',request,false,true);
 byId('benchmark-file').value='';await governanceLoad('benchmark');notice('Frozen candidate benchmark inputs saved · no evaluator executed.');});
byId('policy-clear-binding').onclick=()=>{clearPolicy();byId('policy-clear-binding').disabled=true;};
for(const kind of ['policy','benchmark','audit'])byId('governance-'+kind).onclick=()=>action(()=>governanceLoad(kind));
byId('governance-more').onclick=()=>action(()=>governanceLoad(governanceKind,true));
