"""H7 explicit discrete alternatives to existing specialized motion consumers.

The compiler preserves declared milestones, source data, full equation states,
side conditions, timeline events and audio. An upstream review reference is a
claim, not proof of educational equivalence. No automated pedagogy inference.
"""
from copy import deepcopy
import math
from .qa_common import CompilerQAError, digest
from .specialized_motion import is_specialized, specialized_contract, graph_contract
from .animation_behavior import frame_window

KEY='_bie_h7_discrete_progress'

def fail(code,detail):raise CompilerQAError(code+': '+detail)


def prepare_specialized_variants(raw,target,preference):
    tracks=[t for t in raw.get('tracks',[]) if is_specialized(t)]
    if any(KEY in t['parameters'] for t in raw.get('tracks',[])):
        fail('H7_DERIVATION_RESERVED','caller cannot supply internal execution progress')
    if preference!='reduced' or not tracks:return deepcopy(raw),[]
    cfg=raw.get('metadata',{}).get('compiler_h7',{})
    variants=cfg.get('reduced_variants')
    if not isinstance(variants,dict) or set(variants)!={t['track_id'] for t in tracks}:
        fail('SPECIALIZED_REDUCED_VARIANT_REQUIRED','exact source-bound alternatives required for all specialized tracks')
    effective=deepcopy(raw); effective.pop('fingerprint',None); by_id={e['element_id']:e for e in raw['elements']};records=[]
    for t in effective['tracks']:
        if not is_specialized(t):continue
        c=specialized_contract(t);v=variants[t['track_id']];first,last=frame_window(c,target.fps)
        if not isinstance(v,dict) or set(v)!={'mode','rationale','source_refs','reasoning_refs','teaching_review_ref','milestones'}:
            fail('H7_VARIANT_FIELDS','exact variant contract required')
        if v['mode']!='discrete-milestones':fail('H7_VARIANT_MODE','explicit discrete-milestones required')
        for key in ('rationale','teaching_review_ref'):
            if not isinstance(v[key],str) or not v[key].strip() or len(v[key])>2000:fail('H7_VARIANT_REVIEW','bounded rationale and review reference required')
        for key in ('source_refs','reasoning_refs'):
            refs=v[key]
            if not isinstance(refs,list) or not refs or len(set(refs))!=len(refs) or not set(refs)<=set(t[key]):fail('H7_VARIANT_PROVENANCE','must preserve existing track refs')
        ms=v['milestones']
        if not isinstance(ms,list) or not 2<=len(ms)<=32:fail('H7_VARIANT_MILESTONES','2..32 explicit milestones')
        checked=[]
        for i,m in enumerate(ms):
            if not isinstance(m,dict) or set(m)!={'frame','progress','observation_ref'}:fail('H7_VARIANT_MILESTONES','exact milestone fields')
            f,u=m['frame'],m['progress']
            if type(f) is not int or not first<=f<=last or type(u) not in (int,float) or not math.isfinite(u) or not 0<=u<=1:
                fail('H7_VARIANT_MILESTONES','finite progress and active frame required')
            if not isinstance(m['observation_ref'],str) or not m['observation_ref'].strip() or len(m['observation_ref'])>512:fail('H7_VARIANT_OBSERVATION','explicit teaching-observation link required')
            if i and (f<=checked[-1]['frame'] or u<=checked[-1]['progress']):fail('H7_VARIANT_ORDER','strict time/progress order required')
            checked.append({'frame':f,'progress':float(u),'observation_ref':m['observation_ref']})
        if checked[0]['frame']!=first or checked[0]['progress']!=0 or checked[-1]['progress']!=1:
            fail('H7_VARIANT_ENDPOINTS','preserve initial and final state')
        if any(b-a<max(1,math.ceil(target.fps*.125)) for a,b in zip([m['frame'] for m in checked],[m['frame'] for m in checked[1:]]+[last+1])):
            fail('H7_VARIANT_DWELL','milestones need at least 125ms technical dwell; not learning equivalence')
        required=[0.,1.]
        if c.action=='morph':required=[i/(len(c.parameters['states'])-1) for i in range(len(c.parameters['states']))]
        if c.action=='trace':
            graph=graph_contract(by_id[c.element_id]);series=next(x for x in graph['series'] if x['series_id']==c.parameters['series_id'])
            lengths=series['lengths'];total=sum(lengths);acc=0.;required=[0.]
            for length in lengths:acc+=length;required.append(acc/total)
        if any(not any(abs(u-m['progress'])<1e-9 for m in checked) for u in required):
            fail('H7_VARIANT_REQUIRED_STATE_MISSING','every equation state or graph vertex must remain visible')
        t['parameters'][KEY]={'fps':target.fps,'milestones':checked}
        records.append({'track_id':c.track_id,'action':c.action,'original_track_sha256':digest(next(x for x in raw['tracks'] if x['track_id']==c.track_id)),
                        'required_progress':required,'definition_sha256':digest(v),'teaching_review_ref':v['teaching_review_ref'],
                        'instructional_equivalence':'NOT_INDEPENDENTLY_EVALUATED','accepted':False})
    return effective,records
