REQUIRED={"physics","mathematics","biology","chemistry","history_geography"}
GATES=("completeness","structure","provenance","source_loss")
class E(ValueError):pass
def evaluate(books):
 domains={b["domain"] for b in books}
 if not REQUIRED<=domains:raise E("domain coverage")
 failures=[]
 for b in books:
  if not b.get("source_hash") or len(b["source_hash"])!=64:raise E("source hash")
  for g in GATES:
   if b.get("gates",{}).get(g) is not True:failures.append((b["id"],g))
 return {"passed":not failures,"failures":tuple(failures),"books":len(books)}
