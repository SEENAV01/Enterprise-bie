class E(ValueError):pass
def arbitrate(definitions):
 if not definitions:raise E("definitions")
 for d in definitions:
  if not d.get("anchor_id") or not 0<=d.get("confidence",-1)<=1:raise E("evidence")
 ranked=sorted(definitions,key=lambda d:(d["confidence"],d.get("source_priority",0)),reverse=True)
 top=ranked[0];tie=len(ranked)>1 and ranked[1]["confidence"]==top["confidence"] and ranked[1].get("source_priority",0)==top.get("source_priority",0)
 return {"selected":None if tie else top,"status":"REVIEW" if tie else "SELECTED","alternatives":tuple(ranked)}
