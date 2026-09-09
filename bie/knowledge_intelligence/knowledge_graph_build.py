class E(ValueError):pass
def build(concepts,relations):
 nodes={c["concept_id"]:dict(c) for c in concepts}
 if len(nodes)!=len(concepts):raise E("duplicate node")
 for r in relations:
  if r["source"] not in nodes or r["target"] not in nodes:raise E("dangling edge")
 return {"nodes":nodes,"edges":tuple(relations)}
