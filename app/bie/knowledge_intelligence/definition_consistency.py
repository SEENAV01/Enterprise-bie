import re
class E(ValueError):pass
def norm(s):return set(re.findall(r"[a-z0-9]+",s.casefold()))
def compare(definitions):
 if len(definitions)<2:return {"consistent":True,"min_similarity":1.0}
 sets=[norm(d["text"]) for d in definitions]
 if any(not x for x in sets):raise E("definition")
 sims=[]
 for i in range(len(sets)):
  for j in range(i+1,len(sets)):sims.append(len(sets[i]&sets[j])/len(sets[i]|sets[j]))
 m=min(sims)
 return {"consistent":m>=.5,"min_similarity":m}
