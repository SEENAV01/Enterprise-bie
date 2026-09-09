class E(ValueError):pass
def validate(artifacts,anchors):
 aset=set(anchors);seen=set();used=set()
 for a in artifacts:
  i=a.get("artifact_id");refs=tuple(a.get("anchor_ids",()))
  if not i or i in seen or not refs or any(r not in aset for r in refs):raise E("invalid provenance graph")
  seen.add(i);used.update(refs)
 return {"artifacts":len(seen),"anchors_used":len(used)}
