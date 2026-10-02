'use strict';
let assuranceKind=null,assuranceOffset=null,assuranceSerial=0;
function resetAssurance(enabled){assuranceSerial++;assuranceKind=null;assuranceOffset=null;byId('assurance-content').replaceChildren();
 byId('assurance-state').textContent='NOT_RUN · no native QA or repair snapshot loaded.';
 for(const k of ['gates','repairs'])byId('assurance-'+k).disabled=!enabled;byId('assurance-more').disabled=true;}
async function assuranceLoad(kind,more=false){const selectedRun=run?.run_id,epoch=authEpoch,serial=++assuranceSerial;
 if(!selectedRun)throw new Error('run_required');
 if(!more){assuranceKind=kind;assuranceOffset=0;byId('assurance-content').replaceChildren();}
 byId('assurance-state').textContent='Loading native '+kind+' evidence…';
 try{const value=await api('runs/'+selectedRun+'/assurance/'+kind+'?offset='+(more?assuranceOffset:0)+'&limit=10');
  if(epoch!==authEpoch||selectedRun!==run?.run_id||serial!==assuranceSerial)throw new Error('stale_assurance_response');
  assuranceOffset=value.next_offset;byId('assurance-more').disabled=assuranceOffset===null;
  byId('assurance-state').textContent=value.status==='AVAILABLE'?'Verified historical '+kind+' · no release or product acceptance':`NOT_RUN · ${value.reason}`;
  if(value.required_gates)qualityTable(byId('assurance-content'),'Required canonical floors · evidence not run',['Gate','Owner','Status','Reason'],value.required_gates.map(g=>[g.gate_id,g.owner,g.status,g.reason]));
  for(const item of value.items){const article=document.createElement('article'),h=document.createElement('h3'),v=item.view;
   h.textContent=v.attempt_id;article.append(h);
   fields(article.appendChild(document.createElement('div')),{'Origin':item.evidence_origin,'Fixture evidence':item.fixture_evidence,'Receipt hash':item.receipt_sha256,'Policy hash':v.policy_sha256,'Integrity':item.integrity,'Signature verified':item.signature_verified,'Historical decision':true,'Deployment authorized':'No','Product accepted':'No'});
   const button=document.createElement('button');button.textContent='Open QA artifact lineage';button.onclick=()=>action(()=>openLineage(item.artifact_id));article.append(button);
   if(kind==='gates'){
    fields(article.appendChild(document.createElement('div')),{'Native release status':v.native_release_status,'Evaluated as of':v.as_of,'Policy':v.policy_id,'Global diagnostics':v.global_reasons.join(', ')||'None','Blocking gates':v.blocking_gates.join(', ')||'None'});
    qualityTable(article,'Actual canonical gate decisions',['Gate','Owner','Status','Reasons','Required roles'],v.gates.map(g=>[g.gate_id,g.owner,g.status,g.reasons.join(', '),g.required_roles.join(', ')]));
    qualityTable(article,'Evidence and trust at evaluation time',['Gate','Evidence','Evaluator','Status','Assurance','Expiry','Reasons'],v.gates.flatMap(g=>g.evidence.map(e=>[g.gate_id,e.evidence_id,e.evaluator_id,e.status,e.assurance,e.trust_expires_at,e.reasons.join(', ')])));
    qualityTable(article,'Canonical artifact inspection',['Artifact','Status','Diagnostic','Expected hash','Actual hash'],v.artifact_checks.map(a=>[a.artifact_id,a.status,a.diagnostic,a.expected_sha256,a.actual_sha256]));
   }else{
    fields(article.appendChild(document.createElement('div')),{'Plan status':v.plan_status,'Inventory authenticated':v.authenticated_inventory,'Inventory reasons':v.inventory_reasons.join(', ')||'None','Journal chain':v.journal_chain_head,'Automatic retry':'No','Repository writes':'No'});
    qualityTable(article,'Native classified defects',['Failure','Task','Code','Owner','Severity','Report hash'],v.defects.map(d=>[d.failure_id,d.task_id,d.code,d.owner,d.severity,d.report_sha256]));
    qualityTable(article,'Verified repair attempt history',['Attempt','Proposal','Status','Before snapshot','After candidate','Reason','Remaining failures'],v.attempts.map(a=>[a.attempt,a.proposal_id,a.status,v.snapshot_digest,a.candidate_digest,a.reason||a.diagnostics?.join(', ')||'None',a.remaining_failure_ids.join(', ')]));
    qualityTable(article,'Fresh regression outcomes · prior evidence invalidated',['Attempt','Check','Status','Diagnostic','Witness hash'],v.attempts.flatMap(a=>a.checks.map(c=>[a.attempt,c.check_id,c.status,c.diagnostics.join(', '),c.witness_digest])));
   }
   byId('assurance-content').append(article);
  }
 }catch(e){if(serial===assuranceSerial&&epoch===authEpoch&&selectedRun===run?.run_id){byId('assurance-content').replaceChildren();assuranceOffset=null;byId('assurance-more').disabled=true;byId('assurance-state').textContent='BLOCKED · native QA/repair snapshot could not be verified';}throw e;}}
for(const kind of ['gates','repairs'])byId('assurance-'+kind).onclick=()=>action(()=>assuranceLoad(kind));
byId('assurance-more').onclick=()=>action(()=>assuranceLoad(assuranceKind,true));
