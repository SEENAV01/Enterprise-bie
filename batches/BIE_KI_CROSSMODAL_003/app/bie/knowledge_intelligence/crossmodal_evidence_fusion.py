class E(ValueError):pass
WEIGHT={"TEXT":1.0,"EQUATION":1.0,"FIGURE":.9,"TABLE":.95}
def fuse(items):
 if not items:raise E("items")
 if len({x["semantic_key"] for x in items})!=1:raise E("semantic mismatch")
 scored=[]
 for x in items:
  c=x.get("confidence");m=x.get("modality")
  if m not in WEIGHT or c is None or not 0<=c<=1 or not x.get("anchor_id"):raise E("evidence")
  scored.append((WEIGHT[m]*c,x))
 denom=sum(WEIGHT[x["modality"]] for x in items)
 return {"semantic_key":items[0]["semantic_key"],"confidence":sum(s for s,_ in scored)/denom,
 "anchors":tuple(dict.fromkeys(x["anchor_id"] for x in items)),"modalities":tuple(sorted(set(x["modality"] for x in items)))}
