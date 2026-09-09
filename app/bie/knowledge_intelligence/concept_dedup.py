import re
class E(ValueError):pass
def key(s): return re.sub(r"[^a-z0-9]+"," ",str(s).casefold()).strip()
def dedupe(concepts):
 out={}; redirects={}
 for c in concepts:
  cid=c.get("concept_id");label=c.get("label")
  if not cid or not key(label):raise E("concept")
  k=key(label)
  if k in out: redirects[cid]=out[k]["concept_id"]; out[k]["evidence"]=tuple(dict.fromkeys(out[k].get("evidence",())+tuple(c.get("evidence",()))))
  else: out[k]={**c,"evidence":tuple(c.get("evidence",()))}
 return {"concepts":tuple(out.values()),"redirects":redirects}
