from __future__ import annotations
from dataclasses import dataclass
from .unified_scene_ir_contract import UnifiedElement, UnifiedTrack, UnifiedSceneIRDocument

class AniAdoptionError(ValueError): pass

@dataclass(frozen=True)
class AniAdoptionReceipt:
    ani_handoff_id:str
    ani_revision:int
    dsl_scene_id:str
    dsl_fingerprint:str
    adopted_track_count:int
    adopted_target_count:int
    blockers:tuple[str,...]
    accepted:bool=False

def _get(obj,name,default=None):
    if isinstance(obj,dict):
        return obj.get(name,default)
    return getattr(obj,name,default)

def adopt_ani_handoff(handoff, *, scene_id, title, duration_ms, element_catalog, ani_revision=1, schema_version="1.0.0"):
    hid=_get(handoff,"handoff_id") or _get(handoff,"sceneir_handoff_id")
    if not hid:
        raise AniAdoptionError("ANI handoff id required")
    if isinstance(ani_revision,bool) or not isinstance(ani_revision,int) or ani_revision<1:
        raise AniAdoptionError("ani_revision invalid")

    raw_tracks=_get(handoff,"tracks")
    if raw_tracks is None:
        raw_tracks=_get(handoff,"scene_ir_tracks")
    if raw_tracks is None:
        raw_tracks=_get(handoff,"nodes")
    raw_tracks=tuple(raw_tracks or ())
    if not raw_tracks:
        raise AniAdoptionError("ANI handoff has no tracks")

    catalog={str(x["element_id"]):dict(x) for x in element_catalog}
    target_ids=[]
    blockers=[]
    tracks=[]
    for i,node in enumerate(raw_tracks):
        tid=_get(node,"track_id") or _get(node,"node_id")
        action=_get(node,"action")
        targets=_get(node,"target_ids")
        if targets is None:
            one=_get(node,"element_id")
            targets=() if one is None else (one,)
        targets=tuple(targets or ())
        if not tid or not action or not targets:
            blockers.append(f"malformed_ani_track:{i}")
            continue
        start=_get(node,"start_ms",0)
        end=_get(node,"end_ms",duration_ms)
        src=tuple(_get(node,"source_refs",()) or ())
        rsn=tuple(_get(node,"reasoning_refs",()) or ())
        params=dict(_get(node,"parameters",{}) or {})
        for j,target in enumerate(targets):
            target=str(target)
            target_ids.append(target)
            if target not in catalog:
                blockers.append(f"unknown_ani_target:{target}")
                continue
            tracks.append(UnifiedTrack(
                f"{tid}:{j}" if len(targets)>1 else str(tid),
                target,str(action),int(start),int(end),params,src,rsn
            ))

    if blockers:
        raise AniAdoptionError(";".join(sorted(set(blockers))))

    elements=[]
    for target in sorted(set(target_ids)):
        e=catalog[target]
        elements.append(UnifiedElement(
            element_id=target,
            element_type=e["element_type"],
            props=e.get("props",{}),
            source_refs=tuple(e.get("source_refs",())),
            reasoning_refs=tuple(e.get("reasoning_refs",())),
            accessibility=e.get("accessibility",{}),
            normalized_box=e.get("normalized_box"),
        ))

    source_refs=tuple(sorted({r for e in elements for r in e.source_refs} | {r for t in tracks for r in t.source_refs}))
    reasoning_refs=tuple(sorted({r for e in elements for r in e.reasoning_refs} | {r for t in tracks for r in t.reasoning_refs}))

    doc=UnifiedSceneIRDocument(
        scene_id=scene_id,schema_version=schema_version,title=title,duration_ms=duration_ms,
        elements=tuple(elements),tracks=tuple(tracks),
        source_refs=source_refs,reasoning_refs=reasoning_refs,
        upstream_revision=ani_revision,
        metadata={"ani_handoff_id":str(hid),"ani_revision":ani_revision},
    )
    receipt=AniAdoptionReceipt(str(hid),ani_revision,doc.scene_id,doc.fingerprint,len(tracks),len(elements),(),False)
    return doc,receipt
