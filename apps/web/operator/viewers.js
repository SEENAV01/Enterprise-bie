'use strict';
// Fixed schema projections; never a recursive arbitrary JSON or HTML renderer.
const viewKinds=['reasoning','curriculum','lesson','director','scene_ir','game_plan'];
let artifactOffset=0,artifactFilter=null,codeOffset=null,codeArtifact=null;
function resetViews(enabled){
 for(const kind of viewKinds)byId('view-'+kind).disabled=!enabled;
 byId('browse-artifacts').disabled=!enabled;byId('more-artifacts').disabled=true;byId('more-code').disabled=true;
 for(const id of ['artifact-view','artifact-list','lineage-view','code-view'])byId(id).replaceChildren();
 byId('view-state').textContent='NOT_RUN · no artifact loaded.';artifactOffset=0;artifactFilter=null;codeOffset=null;codeArtifact=null;
}
function node(tag,text=null){const n=document.createElement(tag);if(text!==null)n.textContent=String(text);return n;}
function table(target,caption,head,rows){const t=node('table'),c=node('caption',caption),thead=node('thead'),hr=node('tr'),body=node('tbody');
 for(const label of head){const h=node('th',label);h.scope='col';hr.append(h);}thead.append(hr);t.append(c,thead);
 for(const row of rows){const tr=node('tr');for(const value of row)tr.append(node('td',value??'Not recorded'));body.append(tr);}t.append(body);target.append(t);return t;}
function refButton(target,ref,label='Open artifact lineage'){const b=node('button',label);b.onclick=()=>action(()=>openLineage(ref));target.append(b);}
function directed(target,nodes,edges,label){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 1000 ${Math.max(240,Math.ceil(nodes.length/3)*100+60)}`);svg.setAttribute('role','img');svg.setAttribute('aria-label',label+'; detailed accessible table follows');
 const pos=new Map(nodes.map((n,i)=>[n.id,{x:160+(i%3)*330,y:40+Math.floor(i/3)*100}]));
 const defs=document.createElementNS(ns,'defs'),marker=document.createElementNS(ns,'marker'),path=document.createElementNS(ns,'path');
 marker.setAttribute('id','view-arrow');marker.setAttribute('viewBox','0 0 10 10');marker.setAttribute('refX','9');marker.setAttribute('refY','5');marker.setAttribute('markerWidth','6');marker.setAttribute('markerHeight','6');marker.setAttribute('orient','auto');path.setAttribute('d','M 0 0 L 10 5 L 0 10 z');path.setAttribute('fill','#c6e784');marker.append(path);defs.append(marker);svg.append(defs);
 for(const e of edges){const a=pos.get(e.source),b=pos.get(e.target);if(!a||!b)continue;const line=document.createElementNS(ns,'line');for(const [k,v] of Object.entries({x1:a.x,y1:a.y,x2:b.x,y2:b.y}))line.setAttribute(k,String(v));line.setAttribute('marker-end','url(#view-arrow)');svg.append(line);}
 for(const n of nodes){const p=pos.get(n.id),circle=document.createElementNS(ns,'circle'),labelNode=document.createElementNS(ns,'text');circle.setAttribute('cx',String(p.x));circle.setAttribute('cy',String(p.y));circle.setAttribute('r','14');labelNode.setAttribute('x',String(p.x-100));labelNode.setAttribute('y',String(p.y+32));labelNode.textContent=n.label.slice(0,40);svg.append(circle,labelNode);}target.append(svg);
 table(target,label+' directed relationships',['From','To','Relationship'],edges.map(e=>[e.source,e.target,e.type]));
}
function article(target,title){const a=node('article');a.append(node('h3',title));target.append(a);return a;}
function info(target,values){const d=node('div');fields(d,values);target.append(d);}
function arrayText(value){return value?.length?value.join(' · '):'None recorded';}
async function openView(kind){
 const response=await api('runs/'+run.run_id+'/views/'+kind),target=byId('artifact-view');target.replaceChildren();
 byId('view-state').textContent=response.status==='AVAILABLE'?`${kind} · ${response.evidence_origin} · hash ${response.sha256} · contract validated, not product accepted`:`NOT_RUN · ${response.reason}`;
 if(response.status!=='AVAILABLE')return;
 refButton(target,response.artifact_id,'Open this artifact lineage');const e=node('button','Open validation evidence');e.onclick=()=>action(()=>openEvidence(response.evidence_ref));target.append(e);
 const v=response.view;
 if(kind==='reasoning'){
   directed(target,v.nodes,v.edges,'Reasoning decision dependencies');
   for(const d of v.nodes){const a=article(target,d.id+' · '+d.status);info(a,{'Question':d.label,'Decision type':d.decision_type,'Selected option':d.selected_option,'Rationale':d.rationale,'Confidence (producer-reported)':d.confidence,'Requires review':d.requires_review,'Assumptions':arrayText(d.assumptions),'Constraints':arrayText(d.constraints),'Uncertainty':arrayText(d.uncertainty)});
    table(a,'Evidence and roles',['Artifact','Role','Strength'],d.evidence_refs.map(e=>[e.artifact_id,e.role,e.strength]));for(const e of d.evidence_refs)refButton(a,e.artifact_id,'Inspect linked evidence lineage');
    table(a,'Alternatives; rejected is not resolved',['Option','Description','Score','Rejection reason'],d.alternatives.map(x=>[x.option_id,x.description,x.score,x.rejected_reason]));}
 }else if(kind==='curriculum'){
   info(target,{'Unit order':arrayText(v.order),'Planned total minutes':v.total_minutes,'Timing basis':v.timing_basis});
   directed(target,v.units.map(u=>({id:u.unit_id,label:u.title})),v.dependencies.map(d=>({source:d.before,target:d.after,type:d.kind+(d.hard?' (hard)':' (soft)')})),'Curriculum prerequisites');
   table(target,'Ordered curriculum units',['Unit','Title','Objectives','Planned minutes'],v.units.map(u=>[u.unit_id,u.title,arrayText(u.objective_ids),u.estimated_minutes]));
   table(target,'Lesson grouping',['Lesson group','Unit identities'],v.lesson_groups.map((g,i)=>[i+1,arrayText(g)]));
   table(target,'Review schedule',['Unit','Review after order position'],v.review_after_unit);
   for(const u of v.units)for(const ref of u.evidence_refs)refButton(target,ref,'Inspect '+u.unit_id+' grounding');
 }else if(kind==='lesson'){
   info(target,{'Lesson':v.architecture.title,'Objectives':arrayText(v.architecture.objective_ids),'Policy':v.architecture.policy_version,'Planned duration ms':v.duration_ms,'Timing basis':v.timing_basis,'Review required':v.pedagogy.requires_review});
   table(target,'Lesson sections in planned time',['Section','Scene','Start ms','End ms','Purpose'],v.sections.map(s=>[s.section_id,s.scene_id,s.start_ms,s.end_ms,s.purpose]));
   table(target,'Assessments',['Identity','Objective','Prompt','Success criteria'],v.assessments.map(s=>[s.assessment_id,s.objective_id,s.prompt,arrayText(s.success_criteria)]));
   table(target,'Pedagogy decisions',['Identity','Kind','Status','Confidence','Review'],v.pedagogy.decisions.map(d=>[d.decision_id,d.kind,d.status,d.confidence,d.requires_review]));
   for(const scene of v.architecture.scenes)for(const ref of scene.evidence_ids)refButton(target,ref,'Inspect lesson source grounding');
 }else if(kind==='director'){
   info(target,{'Lesson':v.architecture.title,'Voice profile':v.script_plan.voice_profile,'Planned duration ms':v.duration_ms,'Compiled':false,'Rendered':false});
   const ordered=node('ol');for(const timing of v.timings){const scene=v.architecture.scenes.find(s=>s.scene_id===timing.scene_id),li=node('li');li.append(node('h3',scene.scene_id+' · '+scene.purpose));info(li,{'Start ms':timing.start_ms,'End ms':timing.end_ms,'Objectives':arrayText(scene.objective_ids),'Narration refs':arrayText(timing.narration_refs),'Visual refs':arrayText(timing.visual_refs)});for(const ref of scene.evidence_ids)refButton(li,ref,'Inspect scene grounding');ordered.append(li);}target.append(ordered);
   table(target,'Script intent, not rendered media',['Segment','Scene','Purpose','Intent'],v.script_plan.segments.map(s=>[s.segment_id,s.scene_id,s.purpose,s.text_intent]));
 }else if(kind==='scene_ir'){
   info(target,{'Scene':v.title,'Duration ms':v.duration_ms,'Frame rate':v.fps,'Viewport':v.viewport.width+' × '+v.viewport.height,'Asset refs':arrayText(v.asset_refs),'Compiled':false,'Rendered':false,'Review required':true});
   table(target,'Element inventory; props never executed',['Element','Type','Source refs','Reasoning refs','Alternative text'],v.elements.map(e=>[e.id,e.type,arrayText(e.source_refs),arrayText(e.reasoning_refs),e.accessibility.alt||e.accessibility.label]));
   const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 1000 563');svg.setAttribute('role','img');svg.setAttribute('aria-label','Scene IR spatial boxes; not a compiled render');
   for(const e of v.elements)if(e.box){const rect=document.createElementNS(ns,'rect'),label=document.createElementNS(ns,'text');for(const [k,x] of Object.entries({x:e.box.x*1000,y:e.box.y*563,width:e.box.width*1000,height:e.box.height*563}))rect.setAttribute(k,String(x));label.setAttribute('x',String(e.box.x*1000+5));label.setAttribute('y',String(e.box.y*563+20));label.textContent=e.id;svg.append(rect,label);}target.append(svg);
   table(target,'Frame ranges; end is exclusive',['Track','Element','Action','Start frame','End frame'],v.tracks.map(t=>[t.id,t.element_id,t.action,t.start_frame,t.end_frame_exclusive]));
   for(const e of v.elements)for(const ref of e.source_refs)refButton(target,ref,'Inspect element source');
   for(const ref of v.asset_refs)refButton(target,ref,'Inspect asset lineage');
 }else if(kind==='game_plan'){
   info(target,{'Plan':v.plan_id,'Strategy':v.strategy,'Built':false,'Playable':false,'Product accepted':false});
   directed(target,v.levels.map(l=>({id:l.level_id,label:l.role+' · '+l.mechanic})),v.levels.flatMap(l=>l.prerequisites.map(p=>({source:p,target:l.level_id,type:'requires'}))),'Game plan level progression');
   table(target,'Learning rounds and mechanics',['Level','Objectives','Mechanic','Purpose','Planned seconds'],v.levels.map(l=>[l.level_id,arrayText(l.objectives),l.mechanic,l.purpose,l.estimated_seconds]));
   table(target,'Feedback and success policy',['Objective','Success feedback','Retry feedback','Explanation'],v.feedback.map(f=>[f.objective_id,f.success_ref,f.retry_ref,f.explanation_ref]));
   table(target,'Mastery targets, not learner improvement',['Objective','Target','Evidence state','Confidence'],v.mastery_targets.map(m=>[m.objective_id,m.target,m.evidence_state,m.confidence]));
   table(target,'Misconception remediation',['Misconception','Objective','Feedback','Remediation level'],v.misconceptions.map(m=>[m.id,m.objective,m.feedback,m.remediation_level]));
   table(target,'Adaptive feedback rules',['Rule','Objective','Condition','Action','Rationale'],v.adaptations.map(r=>[r.rule,r.objective,r.condition,r.action,r.rationale]));
 }
}
for(const kind of viewKinds)byId('view-'+kind).onclick=()=>action(()=>openView(kind));
async function browseArtifacts(more=false){
 if(!more){artifactFilter={type:byId('artifact-type').value,only:byId('evidence-only').value};artifactOffset=0;byId('artifact-list').replaceChildren();}
 const query='runs/'+run.run_id+'/artifacts?offset='+artifactOffset+'&evidence_only='+artifactFilter.only+(artifactFilter.type?'&artifact_type='+encodeURIComponent(artifactFilter.type):'');
 const page=await api(query),target=byId('artifact-list');target.append(node('p',page.total+' persisted artifacts match this filter.'));
 for(const r of page.items){const a=article(target,r.artifact_type);info(a,{'Identity':r.artifact_id,'SHA-256':r.sha256,'Bytes':r.size_bytes,'Stage':r.stage_id,'Run':r.run_id,'Evidence origin':r.origin,'Integrity':r.integrity});refButton(a,r.artifact_id);
  if(r.evidence){const b=node('button','Open evidence');b.onclick=()=>action(()=>openEvidence(r.artifact_id));a.append(b);}
  if(r.artifact_type==='operator.generated_code'){const b=node('button','Open verified code');b.onclick=()=>action(()=>openCode(r.artifact_id));a.append(b);}}
 artifactOffset=page.next_offset;byId('more-artifacts').disabled=artifactOffset===null;
}
byId('browse-artifacts').onclick=()=>action(()=>browseArtifacts());byId('more-artifacts').onclick=()=>action(()=>browseArtifacts(true));
async function openLineage(ref){const result=await api('runs/'+run.run_id+'/artifacts/'+encodeURIComponent(ref)+'/lineage'),target=byId('lineage-view');target.replaceChildren();
 directed(target,result.nodes.map(r=>({id:r.artifact_id,label:r.artifact_type})),result.edges,'Verified artifact lineage');
 info(target,{'Roots':arrayText(result.roots),'Complete within governed bound':result.complete,'Hash verification':'Passed'});
 table(target,'Persisted lineage inventory',['Artifact','Type','SHA-256','Stage'],result.nodes.map(r=>[r.artifact_id,r.artifact_type,r.sha256,r.stage_id]));target.scrollIntoView();}
async function openEvidence(ref){const e=await api('runs/'+run.run_id+'/artifacts/'+encodeURIComponent(ref)+'/evidence');
 fields(byId('evidence-view'),{'Identity':e.artifact_id,'SHA-256':e.sha256,'Kind':e.artifact_type,'Origin':e.origin,'Fixture evidence':e.fixture_evidence,'Gate':e.evidence.gate||'Native inspection','Status':e.evidence.status,'Reviewer state':e.reviewer_state,'Signature verified':e.signature_verified,'Product accepted':false});byId('evidence-title').scrollIntoView();}
async function openCode(ref,more=false){if(!more){codeArtifact=ref;codeOffset=0;byId('code-view').replaceChildren();}
 const result=await api('runs/'+run.run_id+'/artifacts/'+encodeURIComponent(codeArtifact)+'/code?offset='+codeOffset),target=byId('code-view');
 if(!more)info(target,{'Language':result.language,'SHA-256':result.sha256,'Integrity':result.integrity,'Lines':result.line_count,'Executed':false,'Compiled':false});
 table(target,'Generated code literal line display',['Line','Literal code'],result.lines.map(l=>[l.number,l.text]));codeOffset=result.next_offset;byId('more-code').disabled=codeOffset===null;target.scrollIntoView();}
byId('more-code').onclick=()=>action(()=>openCode(codeArtifact,true));
