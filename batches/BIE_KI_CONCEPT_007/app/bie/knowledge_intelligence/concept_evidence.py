class E(ValueError):pass
def bind(concept_id,anchors):
 vals=tuple(dict.fromkeys(str(a).strip() for a in anchors if str(a).strip()))
 if not concept_id or not vals:raise E("evidence")
 return {"concept_id":concept_id,"anchor_ids":vals,"evidence_count":len(vals)}
