'use strict';
let adminKind=null,adminAfter=null,adminSerial=0;
const adminIntentKeys=new Map();
function resetAdministration(enabled){adminSerial++;adminKind=null;adminAfter=null;adminIntentKeys.clear();
 for(const id of ['admin-content','admin-detail'])byId(id).replaceChildren();
 byId('admin-state').textContent='NOT_RUN · control plane not loaded.';
 for(const kind of ['providers','workers','queue','dead-letters'])byId('admin-'+kind).disabled=!enabled;
 byId('admin-more').disabled=true;byId('queue-state').value='';}
function adminIntent(identity){if(!adminIntentKeys.has(identity))adminIntentKeys.set(identity,key());return adminIntentKeys.get(identity);}
async function adminLoad(kind,more=false){const epoch=authEpoch,serial=++adminSerial;
 if(!more){adminKind=kind;adminAfter=null;byId('admin-content').replaceChildren();byId('admin-detail').replaceChildren();}
 const state=kind==='dead-letters'?'DEAD_LETTER':kind==='queue'?byId('queue-state').value:'';
 const query=new URLSearchParams({limit:'25'});if(more&&adminAfter)query.set('after',adminAfter);if(state)query.set('state',state);
 byId('admin-state').textContent='Loading actual persisted '+kind+'…';
 try{const value=await api('admin/'+(kind==='dead-letters'?'queue':kind)+'?'+query);
  if(epoch!==authEpoch||serial!==adminSerial)throw new Error('stale_admin_response');
  adminAfter=value.next_after;byId('admin-more').disabled=adminAfter===null;
  byId('admin-state').textContent=kind+' · '+value.status+' · tenant-scoped; product accepted No';
  if(!value.items.length){const p=document.createElement('p');p.textContent=kind==='providers'?'No provider configuration. No connection health or live generation is claimed.':'No persisted records in this bounded page.';byId('admin-content').append(p);return;}
  for(const item of value.items){const article=document.createElement('article'),h=document.createElement('h3');
   h.textContent=item.config_id||item.worker_id||item.task_id;article.append(h);
   if(kind==='providers'){
    fields(article.appendChild(document.createElement('div')),{'Provider':item.provider_id,'Model':item.model_id,'Capabilities':item.capabilities.join(', '),'Revision':item.revision,'Configuration hash':item.configuration_sha256,'Enabled':item.enabled,'Bound in this process':item.bound_in_this_process,'Secret reference':item.secret_reference||'None','Secret values exposed':'No','Health':item.health_status,'Health reason':item.health_reason,'Health origin':item.health_origin||'None','Origin':item.evidence_origin,'Live probe performed':'No','Inspection profile generation':'Disabled'});
    const history=document.createElement('button');history.textContent='Open immutable provider history';history.onclick=()=>action(()=>adminProviderHistory(item.config_id));article.append(history);
    const toggle=document.createElement('button');toggle.textContent=item.enabled?'Disable registered model':'Enable registered model';toggle.disabled=!value.can_configure||(!item.enabled&&!item.bound_in_this_process);
    toggle.onclick=()=>action(async()=>{const id=`provider:${item.config_id}:${item.revision}:${!item.enabled}`;
     await api('admin/providers/'+item.config_id+'/enabled','POST',{enabled:!item.enabled,expected_revision:item.revision,idempotency_key:adminIntent(id)});
     await adminLoad('providers');notice('Actual canonical registry configuration changed; no provider call performed.');});article.append(toggle);
   }else if(kind==='workers'){
    fields(article.appendChild(document.createElement('div')),{'Run':item.run_id,'Capabilities':item.capability_tags.join(', '),'Lifecycle':item.lifecycle,'Health':item.health,'Liveness':item.liveness,'Heartbeat':item.heartbeat_at,'Heartbeat mode':item.heartbeat_refresh_mode,'Capacity':item.capacity,'Recorded active tasks':item.active_tasks,'Actual queue':item.queue_state,'Lease':item.lease_status,'Outcome':item.outcome||'None','Process death inferred':'No','Measured hardware resources':'No'});
    qualityTable(article,'Actual lease-owned workload',['Run','Stage','Task'],item.current_workload.map(w=>[w.run_id,w.stage_id,w.task_id]));
   }else{
    fields(article.appendChild(document.createElement('div')),{'Run':item.run_id,'Canonical queue':item.state,'Stage':item.stage_id,'Attempt':item.attempt,'Deliveries':item.delivery_count,'Delivery ceiling':item.max_deliveries,'Consumer':item.consumer_id||'None','Lease':item.lease_status,'Visible at':item.visible_at,'Executor admission':item.executor_admission,'Source hash':item.source_hash,'Reason code':item.reason_code,'Reason hash':item.reason_sha256,'Queue digest':item.queue_digest});
    if(item.state==='DEAD_LETTER'){const detail=document.createElement('button');detail.textContent='Open dead-letter events and recovery';detail.onclick=()=>action(()=>adminDeadLetter(item.run_id));article.append(detail);}
    const open=document.createElement('button');open.textContent='Open persisted run';open.onclick=()=>action(async()=>{byId('run-id').value=item.run_id;await refresh(item.run_id);});article.append(open);
   }
   byId('admin-content').append(article);
  }
 }catch(e){if(serial===adminSerial&&epoch===authEpoch){byId('admin-content').replaceChildren();byId('admin-detail').replaceChildren();adminAfter=null;byId('admin-more').disabled=true;byId('admin-state').textContent='BLOCKED · control-plane state unavailable or unverified';}throw e;}}
async function adminProviderHistory(id,after=0){const epoch=authEpoch,serial=adminSerial;const value=await api('admin/providers/'+id+'/history?after_revision='+after+'&limit=25');
 if(epoch!==authEpoch||serial!==adminSerial)throw new Error('stale_admin_response');if(!after)byId('admin-detail').replaceChildren();
 qualityTable(byId('admin-detail'),'Immutable actual provider configuration versions',['Revision','Activated','Hash','Enabled','Capabilities'],value.items.map(v=>[v.revision,v.activated_at,v.configuration_sha256,v.configuration.enabled,v.configuration.capabilities.join(', ')]));
 const p=document.createElement('p');p.textContent='Hash-chained local history; privileged whole-store rewrite is not externally notarized.';byId('admin-detail').append(p);
 if(value.next_revision!==null){const more=document.createElement('button');more.textContent='More provider versions';more.onclick=()=>action(async()=>{more.disabled=true;await adminProviderHistory(id,value.next_revision);});byId('admin-detail').append(more);}}
async function adminDeadLetter(id,after=0){const epoch=authEpoch,serial=adminSerial;const value=await api('admin/dead-letters/'+id+'?after_sequence='+after+'&limit=25');
 if(epoch!==authEpoch||serial!==adminSerial)throw new Error('stale_admin_response');if(!after)byId('admin-detail').replaceChildren();
 if(!after)fields(byId('admin-detail'),{'Run':id,'Engine':value.engine_state,'Queue':value.queue.state,'Recovery':value.recovery_action,'Failed parent preserved':value.failed_parent_will_be_preserved,'Original queue redrive':'Not permitted'});
 qualityTable(byId('admin-detail'),'Canonical dead-letter event history',['Sequence','Event','Timestamp','Deliveries','Safe reason','Reason hash'],value.events.map(e=>[e.sequence,e.event_type,e.event_at,e.delivery_count,e.reason_code,e.reason_sha256]));
 const recover=document.createElement('button');recover.textContent='Create governed child retry';recover.disabled=!value.can_recover;
 recover.onclick=()=>action(async()=>{const identity=`recovery:${id}:${value.parent_revision}:${value.queue.queue_digest}`;
  const child=await api('admin/dead-letters/'+id+'/retry','POST',{idempotency_key:adminIntent(identity),expected_revision:value.parent_revision,expected_queue_digest:value.queue.queue_digest});
  if(epoch!==authEpoch||serial!==adminSerial)throw new Error('stale_admin_response');
  const p=document.createElement('p');p.textContent='Persisted child '+child.run_id+' · '+child.child_status+' / '+child.child_queue_state+'. Parent stays FAILED / DEAD_LETTER. This action dispatched no worker.';byId('admin-detail').append(p);
  recover.disabled=true;});if(!after)byId('admin-detail').append(recover);
 if(value.next_sequence!==null){const more=document.createElement('button');more.textContent='More dead-letter events';more.onclick=()=>action(async()=>{more.disabled=true;await adminDeadLetter(id,value.next_sequence);});byId('admin-detail').append(more);}}
for(const kind of ['providers','workers','queue','dead-letters'])byId('admin-'+kind).onclick=()=>action(()=>adminLoad(kind));
byId('admin-more').onclick=()=>action(()=>adminLoad(adminKind,true));
