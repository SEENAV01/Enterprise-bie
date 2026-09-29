"""Byte-grounded comparators. Typed semantics is not language understanding."""
from dataclasses import asdict
from io import BytesIO
from ..release_v2.contracts import ContractError, canonical_bytes, digest, token, integer
from ..source_v2.codec import loads
from ..repair_audit_v2.io import fields

def fail(code):raise ContractError(code)
def different(a,b):return canonical_bytes(a)!=canonical_bytes(b)
def items(v,limit=4096):
    if type(v) is not list or len(v)>limit:fail('REG_ARRAY')
    return v

def unique_strings(v):
    items(v)
    if any(type(s) is not str or not s or len(s)>4096 for s in v) or len(set(v))!=len(v):fail('REG_STRING_INVENTORY')
    return v

def artifact_diff(baseline,candidate,policy):
    before={a.artifact_id:a for a in baseline.artifacts};after={a.artifact_id:a for a in candidate.artifacts}
    permits={p.artifact_id:p for p in policy.change_permits};changes=[];issues=[]
    for aid in sorted(set(before)|set(after)):
        a=before.get(aid);b=after.get(aid)
        if a==b:continue
        old=digest(asdict(a)) if a else '';new=digest(asdict(b)) if b else ''
        kind='ADDED' if a is None else 'REMOVED' if b is None else 'MODIFIED'
        changes.append(dict(artifact_id=aid,kind=kind,before_ref_digest=old,after_ref_digest=new))
        if aid in policy.protected_artifact_ids:issues.append(('REG_PROTECTED_CHANGED',aid))
        p=permits.get(aid)
        if p is None or (p.before_ref_digest,p.after_ref_digest)!=(old,new):issues.append(('REG_UNAPPROVED_ARTIFACT_CHANGE',aid))
    changed={c['artifact_id'] for c in changes}
    for aid in permits.keys()-changed:issues.append(('REG_UNUSED_CHANGE_PERMIT',aid))
    for aid in policy.protected_artifact_ids:
        if aid not in before or aid not in after:issues.append(('REG_PROTECTED_MISSING',aid))
    return changes,issues

def semantic_snapshot(data):
    o=loads(data);fields(o,{'schema_version','claims','concept_ids','relations'},'REG_SEM_SCHEMA')
    if o['schema_version']!='bie.qa.semantic-snapshot/1':fail('REG_SEM_VERSION')
    unique_strings(o['concept_ids'])
    for c in o['concept_ids']:token(c,'concept_id')
    claims={}
    for c in items(o['claims'],2048):
        fields(c,{'claim_id','concept_id','text','source_refs','conditions','expression','status','confidence_ppm'},'REG_SEM_CLAIM_SCHEMA')
        token(c['claim_id'],'claim_id');token(c['concept_id'],'concept_id')
        if c['concept_id'] not in o['concept_ids'] or c['claim_id'] in claims:fail('REG_SEM_CLAIM_INVENTORY')
        for n in ('text','expression'):
            if type(c[n]) is not str or (n=='text' and not c[n].strip()) or len(c[n])>8192:fail('REG_SEM_TEXT')
        unique_strings(c['source_refs']);unique_strings(c['conditions'])
        for r in c['source_refs']:token(r,'source_ref')
        if not c['source_refs']:fail('REG_SEM_UNGROUNDED')
        if c['status'] not in ('SUPPORTED','UNCERTAIN','CONTRADICTED'):fail('REG_SEM_STATUS')
        integer(c['confidence_ppm'],'confidence_ppm',0,1000000);claims[c['claim_id']]=c
    relations=[]
    for r in items(o['relations']):
        fields(r,{'from','predicate','to'},'REG_SEM_RELATION_SCHEMA')
        for n in ('from','predicate','to'):token(r[n],n)
        if r['from'] not in o['concept_ids'] or r['to'] not in o['concept_ids']:fail('REG_SEM_RELATION_TARGET')
        relations.append(canonical_bytes(r))
    if len(set(relations))!=len(relations):fail('REG_SEM_DUPLICATE_RELATION')
    return o,claims,set(relations)

def semantic_diff(a,b,rule):
    x,xc,xr=semantic_snapshot(a);y,yc,yr=semantic_snapshot(b);issues=[];changes=[]
    for required,present,code in ((rule.required_claim_ids,xc,'REG_BASELINE_REQUIRED_CLAIM'),(rule.required_claim_ids,yc,'REG_REQUIRED_CLAIM_LOST'),(rule.required_concept_ids,x['concept_ids'],'REG_BASELINE_REQUIRED_CONCEPT'),(rule.required_concept_ids,y['concept_ids'],'REG_REQUIRED_CONCEPT_LOST')):
        for q in set(required)-set(present):issues.append((code,'BLOCKER',q))
    for cid in sorted(set(xc)|set(yc)):
        old=xc.get(cid);new=yc.get(cid)
        if different(old,new):
            keys=sorted(k for k in set(old or {})|set(new or {}) if different((old or {}).get(k),(new or {}).get(k)))
            changes.append(dict(claim_id=cid,changed_fields=keys,before_digest=digest(old),after_digest=digest(new)))
            issues.append(('REG_SEM_MEANING_REVIEW','REVIEW',cid))
        if new is None:continue
        if new['status']=='CONTRADICTED':issues.append(('REG_SEM_CONTRADICTED','BLOCKER',cid))
        elif new['status']!='SUPPORTED':issues.append(('REG_SEM_UNCERTAIN','REVIEW',cid))
        if old:
            if set(old['conditions'])-set(new['conditions']):issues.append(('REG_SEM_CONDITION_LOST','BLOCKER',cid))
            if set(old['source_refs'])-set(new['source_refs']):issues.append(('REG_SEM_SOURCE_LOST','BLOCKER',cid))
    if xr-yr:issues.append(('REG_SEM_RELATION_LOST','BLOCKER',rule.artifact_id))
    if set(x['concept_ids'])!=set(y['concept_ids']) or xr!=yr:issues.append(('REG_SEM_GRAPH_REVIEW','REVIEW',rule.artifact_id))
    return dict(claim_changes=changes,removed_relations=len(xr-yr),added_relations=len(yr-xr)),issues

def png(data,rule):
    from PIL import Image
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format!='PNG' or getattr(im,'n_frames',1)!=1:fail('REG_IMAGE_FORMAT')
            if im.size!=(rule.width,rule.height):fail('REG_IMAGE_DIMENSIONS')
            if im.mode not in ('RGB','RGBA','L','LA'):fail('REG_IMAGE_MODE')
            unsupported=any(k in im.info for k in ('icc_profile','exif','gamma','chromaticity','transparency'))
            im.load();return im.convert('RGBA').tobytes(),unsupported
    except ContractError:raise
    except (OSError,ValueError,Image.DecompressionBombError) as e:raise ContractError('REG_IMAGE_DECODE') from e

def visual_diff(a,b,rule):
    x,xprofile=png(a,rule);y,yprofile=png(b,rule);issues=[]
    masked=0;changed=0;raw_changed=0;maximum=0;critical=0;total_delta=0;bbox=None
    for i in range(rule.width*rule.height):
        px=i%rule.width;py=i//rule.width;j=i*4
        delta=max(abs(x[j+k]-y[j+k]) for k in range(4));total_delta+=sum(abs(x[j+k]-y[j+k]) for k in range(4))
        if delta:raw_changed+=1
        if any(r.contains(px,py) for r in rule.critical_regions) and delta:critical+=1
        if any(m.contains(px,py) for m in rule.masks):masked+=1;continue
        maximum=max(maximum,delta)
        if delta>rule.channel_tolerance:
            changed+=1
            bbox=[px,py,px+1,py+1] if bbox is None else [min(bbox[0],px),min(bbox[1],py),max(bbox[2],px+1),max(bbox[3],py+1)]
    compared=rule.width*rule.height-masked
    if compared<=0:fail('REG_NO_VISIBLE_COMPARISON')
    if changed*1000000>compared*rule.changed_pixel_limit_ppm:issues.append(('REG_VISUAL_DIFFERENCE','BLOCKER',rule.artifact_id))
    if critical:issues.append(('REG_CRITICAL_VISUAL_DIFFERENCE','BLOCKER',rule.artifact_id))
    if xprofile or yprofile:issues.append(('REG_COLOR_PROFILE_REVIEW','REVIEW',rule.artifact_id))
    return dict(sample_key=rule.sample_key,compared_pixels=compared,masked_pixels=masked,
        changed_pixels=changed,raw_changed_pixels=raw_changed,changed_ppm=changed*1000000//compared,
        max_channel_delta=maximum,critical_changed_pixels=critical,bbox=bbox,total_channel_delta=total_delta),issues

def game_snapshot(data,rule):
    o=loads(data);fields(o,{'schema_version','runs'},'REG_GAME_SCHEMA')
    if o['schema_version']!='bie.qa.game-traces/1':fail('REG_GAME_VERSION')
    runs={};expected={(s.scenario_id,s.seed):s for s in rule.scenarios}
    for r in items(o['runs'],128):
        fields(r,{'scenario_id','seed','execution_mode','steps'},'REG_GAME_RUN_SCHEMA')
        token(r['scenario_id'],'scenario_id');integer(r['seed'],'seed',0,2147483647)
        k=(r['scenario_id'],r['seed'])
        if k in runs or k not in expected:fail('REG_GAME_SCENARIO_IDENTITY')
        if r['execution_mode'] not in ('OBSERVED_BROWSER','NODE_REDUCER','REPORTED','SYNTHETIC'):fail('REG_GAME_MODE')
        steps=items(r['steps'])
        if len(steps)!=len(expected[k].action_ids):fail('REG_GAME_STEP_COVERAGE')
        for i,s in enumerate(steps):
            fields(s,{'action_id','input','state','score','feedback','terminal','enabled_actions'},'REG_GAME_STEP_SCHEMA')
            if s['action_id']!=expected[k].action_ids[i]:fail('REG_GAME_ACTION_ORDER')
            if type(s['input']) is not dict or type(s['state']) is not dict or not s['state']:fail('REG_GAME_STATE_OBJECT')
            integer(s['score'],'score',-(2**53-1),2**53-1)
            if type(s['terminal']) is not bool or type(s['feedback']) is not str:fail('REG_GAME_VALUE_TYPE')
            unique_strings(s['enabled_actions'])
            for q in s['enabled_actions']:token(q,'enabled_action')
        runs[k]=r
    if set(runs)!=set(expected):fail('REG_GAME_SCENARIO_COVERAGE')
    return runs

def game_diff(a,b,rule):
    x=game_snapshot(a,rule);y=game_snapshot(b,rule);changes=[];issues=[]
    for k in sorted(x):
        if x[k]['execution_mode']!='OBSERVED_BROWSER' or y[k]['execution_mode']!='OBSERVED_BROWSER':
            issues.append(('REG_GAME_NATIVE_OBSERVATION_PENDING','REVIEW',k[0]))
        for i,(old,new) in enumerate(zip(x[k]['steps'],y[k]['steps'])):
            changed=sorted(n for n in old if different(old[n],new[n]))
            if changed:
                changes.append(dict(scenario_id=k[0],seed=k[1],step=i,fields=changed,before_digest=digest(old),after_digest=digest(new)))
                issues.append(('REG_GAME_STATE_REGRESSION','BLOCKER',k[0]+':'+str(i)))
    return dict(changes=changes,scenarios=len(x),checkpoints=sum(len(r['steps']) for r in x.values())),issues
