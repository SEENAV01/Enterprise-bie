class E(ValueError):pass
def detect(definitions):
 out=[]
 for i,a in enumerate(definitions):
  for b in definitions[i+1:]:
   if a["concept_id"]!=b["concept_id"]:continue
   if a.get("polarity",1)!=b.get("polarity",1) or a.get("scope")!=b.get("scope"):
    out.append({"concept_id":a["concept_id"],"left":a["anchor_id"],"right":b["anchor_id"],"status":"REVIEW"})
 return tuple(out)
