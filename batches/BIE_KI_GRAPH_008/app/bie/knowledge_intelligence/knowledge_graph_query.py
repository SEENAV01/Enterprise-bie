def query(graph,label=None,relation_type=None,min_confidence=0):
 nodes=[]
 for cid,n in graph["nodes"].items():
  if label is None or label.casefold() in n.get("label","").casefold():nodes.append(cid)
 edges=[e for e in graph.get("edges",()) if (relation_type is None or e.get("type")==relation_type) and e.get("confidence",1)>=min_confidence]
 return {"node_ids":tuple(sorted(nodes)),"edges":tuple(edges)}
