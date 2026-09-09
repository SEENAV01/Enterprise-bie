def detect(ps):
 out=[]
 for i,a in enumerate(ps):
  for b in ps[i+1:]:
   if (a.get("concept_id"),a.get("property"),a.get("scope"))==(b.get("concept_id"),b.get("property"),b.get("scope")) and a.get("value")!=b.get("value"):out.append({"left":a,"right":b,"status":"REVIEW"})
 return tuple(out)
