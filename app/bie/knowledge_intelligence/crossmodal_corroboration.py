class E(ValueError):pass
def fuse(items):
 if not items:raise E("items")
 keys={x["semantic_key"] for x in items}
 if len(keys)!=1:raise E("different semantics")
 mods=tuple(sorted(set(x["modality"] for x in items)))
 conf=1
 for x in items:conf*=1-x.get("confidence",0)
 return {"semantic_key":next(iter(keys)),"modalities":mods,"confidence":1-conf,"status":"CORROBORATED" if len(mods)>1 else "SINGLE_SOURCE"}
