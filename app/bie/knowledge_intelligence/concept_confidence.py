class E(ValueError):pass
def score(evidence_strength,definition_strength,structural_strength):
 vals=(evidence_strength,definition_strength,structural_strength)
 if any(not 0<=x<=1 for x in vals):raise E("confidence")
 s=.5*vals[0]+.3*vals[1]+.2*vals[2]
 return {"score":s,"status":"ACCEPT" if s>=.85 else ("REVIEW" if s>=.65 else "REJECT")}
