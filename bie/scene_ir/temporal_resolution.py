from dataclasses import dataclass
from .unified_scene_ir_codec import decode_scene_ir
@dataclass(frozen=True)
class TemporalResolutionReceipt:
    scene_id:str;input_fingerprint:str;output_fingerprint:str;ordered_event_ids:tuple[str,...];ordered_narration_ids:tuple[str,...];ordered_interaction_cue_ids:tuple[str,...];blockers:tuple[str,...];warnings:tuple[str,...];passed:bool;accepted:bool=False
def resolve_temporal_consistency(document):
    duration=document.duration_ms;elems={e.element_id for e in document.elements};blockers=[];warnings=[]
    metadata=dict(document.metadata);lifetimes={eid:(0,duration) for eid in elems};seen=set()
    for x in metadata.get("element_lifetimes",[]):
        eid=x.get("element_id")
        if eid not in elems:blockers.append("unknown_lifetime_element:"+str(eid));continue
        if eid in seen:blockers.append("duplicate_lifetime:"+eid);continue
        seen.add(eid);born=x.get("born_ms");dead=x.get("dead_ms")
        if not isinstance(born,int) or isinstance(born,bool) or not isinstance(dead,int) or isinstance(dead,bool) or born<0 or dead<=born or dead>duration:blockers.append("invalid_lifetime:"+eid);continue
        lifetimes[eid]=(born,dead)
    for t in document.tracks:
        b,d=lifetimes[t.element_id]
        if t.start_ms<b or t.end_ms>d:blockers.append("track_outside_lifetime:"+t.track_id)
    events=[dict(x) for x in document.events];narr=[dict(x) for x in document.narration_cues];cues=[dict(x) for x in document.interaction_cues]
    def unique(items,key,label):
        vals=[x.get(key) for x in items if x.get(key) is not None]
        if len(vals)!=len(set(vals)):blockers.append("duplicate_"+label+"_id")
    unique(events,"event_id","event");unique(narr,"cue_id","narration_cue");unique(cues,"cue_id","interaction_cue")
    for x in events:
        at=x.get("at_ms")
        if not isinstance(at,int) or isinstance(at,bool) or at<0 or at>duration:blockers.append("event_outside_scene:"+str(x.get("event_id","?")))
        for target in x.get("target_ids",()):
            if target not in elems:blockers.append("event_unknown_target:"+str(x.get("event_id","?"))+":"+str(target))
    for x in narr:
        s=x.get("start_ms");e=x.get("end_ms")
        if not isinstance(s,int) or not isinstance(e,int) or isinstance(s,bool) or isinstance(e,bool) or s<0 or e<=s or e>duration:blockers.append("narration_interval_invalid:"+str(x.get("cue_id","?")))
        for target in x.get("target_ids",()):
            if target not in elems:blockers.append("narration_unknown_target:"+str(x.get("cue_id","?"))+":"+str(target))
    for x in cues:
        at=x.get("at_ms")
        if not isinstance(at,int) or isinstance(at,bool) or at<0 or at>duration:blockers.append("interaction_cue_outside_scene:"+str(x.get("cue_id","?")))
        for target in x.get("target_ids",()):
            if target not in elems:blockers.append("interaction_cue_unknown_target:"+str(x.get("cue_id","?"))+":"+str(target))
    narr=sorted(narr,key=lambda x:(x.get("start_ms",0),x.get("end_ms",0),str(x.get("cue_id",""))))
    for a,b in zip(narr,narr[1:]):
        if a.get("end_ms",0)>b.get("start_ms",0):warnings.append("narration_overlap:"+str(a.get("cue_id","?"))+":"+str(b.get("cue_id","?")))
    events=sorted(events,key=lambda x:(x.get("at_ms",0),str(x.get("event_id",""))));cues=sorted(cues,key=lambda x:(x.get("at_ms",0),str(x.get("cue_id",""))))
    payload=document.to_dict();payload["events"]=events;payload["narration_cues"]=narr;payload["interaction_cues"]=cues;payload.pop("fingerprint",None)
    resolved=decode_scene_ir(payload)
    return resolved,TemporalResolutionReceipt(document.scene_id,document.fingerprint,resolved.fingerprint,tuple(str(x.get("event_id","")) for x in events),tuple(str(x.get("cue_id","")) for x in narr),tuple(str(x.get("cue_id","")) for x in cues),tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,False)
