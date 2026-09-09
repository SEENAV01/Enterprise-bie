class E(ValueError):pass
def attach(concept_id,definitions):
 if not concept_id:raise E("concept")
 out=[]
 for d in definitions:
  text=str(d.get("text","")).strip();anchor=d.get("anchor_id");conf=float(d.get("confidence",0))
  if not text or not anchor or not 0<=conf<=1:raise E("definition")
  out.append({"text":text,"anchor_id":anchor,"confidence":conf})
 return {"concept_id":concept_id,"definitions":tuple(out)}
