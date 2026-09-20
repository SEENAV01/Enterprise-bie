from dataclasses import dataclass
from .unified_scene_ir_codec import decode_scene_ir
@dataclass(frozen=True)
class AccessibilityMergeReceipt:
    scene_id:str;input_fingerprint:str;output_fingerprint:str;reading_order:tuple[str,...];keyboard_focus_order:tuple[str,...];blockers:tuple[str,...];warnings:tuple[str,...];passed:bool;accepted:bool=False
VISUAL={"image","diagram","graph","chart","map","model2d","model3d"}
def merge_accessibility(document):
    records=[dict(x) for x in document.accessibility_metadata];by_id={};blockers=[];warnings=[]
    for r in records:
        eid=r.get("element_id")
        if not eid:blockers.append("accessibility_metadata_missing_element_id");continue
        if eid in by_id:blockers.append("duplicate_accessibility_metadata:"+eid);continue
        by_id[eid]=r
    elements=document.to_dict()["elements"];valid={e["element_id"] for e in elements}
    for eid in by_id:
        if eid not in valid:blockers.append("accessibility_metadata_unknown_element:"+eid)
    used=set();merged={}
    for e in elements:
        eid=e["element_id"];acc=dict(e.get("accessibility") or {});extra=dict(by_id.get(eid,{}));extra.pop("element_id",None);acc.update(extra)
        ro=acc.get("reading_order")
        if ro is not None:
            if isinstance(ro,bool) or not isinstance(ro,int) or ro<0:blockers.append("invalid_reading_order:"+eid)
            elif ro in used:blockers.append("duplicate_reading_order:"+str(ro))
            else:used.add(ro)
        merged[eid]=acc
    next_order=0
    for e in elements:
        acc=merged[e["element_id"]]
        if acc.get("reading_order") is None:
            while next_order in used:next_order+=1
            acc["reading_order"]=next_order;used.add(next_order);next_order+=1
    for e in elements:
        eid=e["element_id"];et=e["element_type"];acc=merged[eid]
        if et in VISUAL and not (acc.get("alt") or acc.get("alt_text") or acc.get("long_description_ref")):blockers.append("visual_description_missing:"+eid)
        if et=="video" and not (acc.get("captions_ref") or acc.get("transcript_ref")):blockers.append("video_text_alternative_missing:"+eid)
        if et in {"simulation","particle_system"} and not acc.get("reduced_motion_variant"):blockers.append("reduced_motion_variant_missing:"+eid)
        if et in {"graph","chart","map"} and acc.get("color_independent_encoding") is not True:blockers.append("color_independent_encoding_missing:"+eid)
        e["accessibility"]=acc
    canonical=[{"element_id":e["element_id"],**e["accessibility"]} for e in elements]
    reading=tuple(x["element_id"] for x in sorted(canonical,key=lambda x:(x["reading_order"],x["element_id"])))
    focus=tuple(x["element_id"] for x in sorted(canonical,key=lambda x:(x["reading_order"],x["element_id"])) if x.get("keyboard_focusable"))
    payload=document.to_dict();payload["elements"]=elements;payload["accessibility_metadata"]=canonical;payload.pop("fingerprint",None)
    resolved=decode_scene_ir(payload)
    return resolved,AccessibilityMergeReceipt(document.scene_id,document.fingerprint,resolved.fingerprint,reading,focus,tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,False)
