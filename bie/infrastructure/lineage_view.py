
class LineageViewError(ValueError): pass
def build_lineage_view(records):
 nodes={r["artifact_id"]:{"artifact_id":r["artifact_id"],"stage_id":r.get("stage_id"),"type":r.get("type")} for r in records}
 edges=[]
 for r in records:
  for p in r.get("parent_refs",[]):
   if p not in nodes: raise LineageViewError(f"missing parent {p}")
   edges.append({"from":p,"to":r["artifact_id"]})
 return {"nodes":[nodes[k] for k in sorted(nodes)],"edges":sorted(edges,key=lambda e:(e["from"],e["to"]))}
