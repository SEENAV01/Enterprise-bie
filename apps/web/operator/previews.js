'use strict';
let mediaURL=null,previewExpires=null;
function resetPreviews(enabled=false){
  if(mediaURL){URL.revokeObjectURL(mediaURL);mediaURL=null;}
  if(previewExpires){clearTimeout(previewExpires);previewExpires=null;}
  byId('preview-content').replaceChildren();byId('preview-state').textContent='NOT_RUN · no native output loaded.';
  for(const id of ['preview-render','preview-game','stop-preview'])byId(id).disabled=!enabled;
}
async function preview(kind){
  resetPreviews(true);const epoch=authEpoch,id=run.run_id;
  const meta=await api('runs/'+id+'/previews/'+kind);
  byId('preview-state').textContent=meta.status==='AVAILABLE'?kind+' · '+meta.integrity+' · '+meta.origin+' · QA REVIEW_REQUIRED · not product-accepted':'NOT_RUN · '+meta.reason;
  if(meta.status!=='AVAILABLE')return;
  fields(byId('preview-content'),Object.assign({'Artifact':meta.artifact_id,'SHA-256':meta.sha256,'Fixture evidence':meta.fixture_evidence},meta.info));
  if(kind==='render'){
    const r=await fetch('/operator/v1/runs/'+id+'/render/media',{headers:{Authorization:'Bearer '+token},credentials:'omit',redirect:'error',cache:'no-store'});
    if(!r.ok||r.headers.get('Content-Type')!=='video/mp4')throw new Error('render_unavailable');
    const reader=r.body.getReader();let size=0;const chunks=[];
    try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>25*1024*1024)throw new Error('preview_size_limit');chunks.push(value);}}
    catch(e){await reader.cancel();throw e;}
    if(epoch!==authEpoch||run?.run_id!==id)throw new Error('credential_changed');
    mediaURL=URL.createObjectURL(new Blob(chunks,{type:'video/mp4'}));
    const video=document.createElement('video');video.controls=true;video.preload='metadata';video.setAttribute('aria-label','Verified media artifact; release review still required');video.src=mediaURL;
    video.onerror=()=>{if(epoch===authEpoch)byId('preview-state').textContent='Media decode failed · no playback success claimed.';};
    video.style.maxWidth='100%';byId('preview-content').append(video);
  }else{
    const grant=await api('runs/'+id+'/game/preview-grant','POST',{});
    if(epoch!==authEpoch||run?.run_id!==id)throw new Error('credential_changed');
    const frame=document.createElement('iframe');frame.title='Isolated compiled game preview; not learning-quality acceptance';
    frame.setAttribute('sandbox','allow-scripts');frame.referrerPolicy='no-referrer';frame.src=grant.preview_path;
    frame.style.width='100%';frame.style.height='520px';byId('preview-content').append(frame);
    previewExpires=setTimeout(()=>{resetPreviews(Boolean(run));byId('preview-state').textContent='Preview grant expired · reopen explicitly.';},grant.expires_in_seconds*1000);
  }
}
for(const kind of ['render','game'])byId('preview-'+kind).onclick=()=>action(()=>preview(kind));
byId('stop-preview').onclick=()=>action(async()=>{resetPreviews(Boolean(run));await api('preview-grants/revoke','POST',{});});
