'use strict';
let qualityKind=null,qualityOffset=null;
function resetQuality(enabled){qualityKind=null;qualityOffset=null;byId('quality-content').replaceChildren();byId('quality-state').textContent='NOT_RUN · no native ledger snapshot loaded.';
 for(const k of ['benchmark','release'])byId('quality-'+k).disabled=!enabled;byId('quality-more').disabled=true;}
function qualityTable(target,caption,headings,rows){const table=document.createElement('table'),cap=document.createElement('caption');cap.textContent=caption;table.append(cap);
 const tr=document.createElement('tr');for(const h of headings){const th=document.createElement('th');th.scope='col';th.textContent=h;tr.append(th);}const thead=document.createElement('thead');thead.append(tr);table.append(thead);
 const body=document.createElement('tbody');for(const row of rows){const r=document.createElement('tr');for(const value of row){const td=document.createElement('td');td.textContent=String(value??'NOT_MEASURED');r.append(td);}body.append(r);}table.append(body);target.append(table);}
async function qualityLoad(kind,more=false){const selectedRun=run?.run_id,epoch=authEpoch;if(!selectedRun)throw new Error('run_required');
 if(!more){qualityKind=kind;qualityOffset=0;byId('quality-content').replaceChildren();}byId('quality-state').textContent='Loading verified '+kind+' snapshots…';
 try{const value=await api('runs/'+selectedRun+'/quality/'+kind+'?offset='+(more?qualityOffset:0)+'&limit=10');
  if(epoch!==authEpoch||selectedRun!==run?.run_id)throw new Error('stale_quality_response');
  qualityOffset=value.next_offset;byId('quality-more').disabled=qualityOffset===null;
  byId('quality-state').textContent=value.status==='AVAILABLE'?kind+' · verified persisted historical snapshots · no deployment or product acceptance':`NOT_RUN · ${value.reason}`;
  for(const item of value.items){const section=document.createElement('article'),h=document.createElement('h3'),v=item.view;h.textContent=v.attempt_id+' · '+(v.status||v.outcome);section.append(h);
   fields(section.appendChild(document.createElement('div')),{'Origin':item.evidence_origin,'Fixture evidence':item.fixture_evidence,'Receipt hash':item.receipt_sha256,'Candidate hash':v.candidate_sha256,'Artifact integrity':item.integrity,'Signature verified':item.signature_verified,'Deployment authorized':'No','Product accepted':'No'});
   const b=document.createElement('button');b.textContent='Open decision artifact lineage';b.onclick=()=>action(()=>openLineage(item.artifact_id));section.append(b);
   if(kind==='benchmark'){
    fields(section.appendChild(document.createElement('div')),{'Dataset':v.dataset.dataset_id,'Dataset version':v.dataset.version,'Dataset hash':v.dataset.sha256,'Split':v.split,'Evaluator':v.evaluator_type,'Live independent assessor':v.live_assessor_status,'Received / denominator':v.received_count+' / '+v.denominator,'Passed / denominator':v.passed_count+' / '+v.denominator,'Diagnostic score':v.score,'Measured coverage':v.measured_coverage,'Missing cases':v.missing_case_ids.join(', ')||'None','Golden certified':v.golden_benchmark_certified});
    qualityTable(section,'Actual case decisions',['Case','Registry task','Domain','Status','Evidence hash'],v.cases.map(c=>[c.case_id,c.task_id,c.domain,c.status,c.evidence_sha256]));
   }else{
    fields(section.appendChild(document.createElement('div')),{'Benchmark':v.benchmark_id,'Version':v.benchmark_version,'Dataset hash':v.dataset_sha256,'Reference grade':v.reference_grade,'Policy version':v.policy_version,'Policy hash':v.policy_sha256,'Mode':v.mode,'Evaluated at':v.evaluated_at,'Native outcome':v.outcome,'Blockers':v.reasons.join(', ')||'No native benchmark blockers; separate release approvals still required'});
    qualityTable(section,'Actual metric measurements',['Metric','Status','Score'],v.metric_rows.map(c=>[c.metric_id,c.status,c.score]));
    qualityTable(section,'Critical floors · not averaged away',['Metric','Minimum'],v.critical_floors.map(c=>[c.metric_id,c.minimum]));
    qualityTable(section,'Domain floors',['Domain','Minimum score','Minimum cases','Required coverage'],v.domain_floors.map(c=>[c.domain,c.minimum_score,c.minimum_cases,c.minimum_measured_fraction]));
    qualityTable(section,'Actual gate/coverage decisions',['Gate','Status','Reasons'],v.coverage.map(c=>[c.gate,c.status,c.reasons.join(', ')||'None']));
    qualityTable(section,'Configured evaluators · identity is not proof of execution',['Rater','Type','Independence group'],v.raters.map(c=>[c.id,c.kind,c.independence_group]));
    qualityTable(section,'Native evaluator agreement',['Pair','Observed agreement','Score difference','Kappa'],v.agreement.map(c=>[c.pair||[c.assessor_a,c.assessor_b].filter(Boolean).join(' / '),c.observed_agreement,c.mean_absolute_score_difference,c.kappa]));
   }
   byId('quality-content').append(section);
  }
 }catch(e){byId('quality-content').replaceChildren();qualityOffset=null;byId('quality-more').disabled=true;byId('quality-state').textContent='BLOCKED · evaluation snapshot could not be verified';throw e;}}
for(const kind of ['benchmark','release'])byId('quality-'+kind).onclick=()=>action(()=>qualityLoad(kind));
byId('quality-more').onclick=()=>action(()=>qualityLoad(qualityKind,true));
