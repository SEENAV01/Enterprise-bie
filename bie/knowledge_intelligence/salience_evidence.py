class E(ValueError):pass
def bind(concept_id,signals):
 if not concept_id or not signals:raise E("signals")
 for s in signals:
  if not s.get("anchor_id") or s.get("kind") not in {"HEADING","OBJECTIVE","REPETITION","ASSESSMENT","DEFINITION","GRAPH_CENTRALITY"}:raise E("signal")
 return {"concept_id":concept_id,"signals":tuple(signals),"grounded":True}
