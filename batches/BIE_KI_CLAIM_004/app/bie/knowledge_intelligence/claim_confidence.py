class E(ValueError):pass
def score(source,corroboration,structure):
 vals=(source,corroboration,structure)
 if any(not 0<=x<=1 for x in vals):raise E("score")
 s=.55*source+.30*corroboration+.15*structure
 return {"confidence":s,"status":"ACCEPT" if s>=.85 else ("REVIEW" if s>=.65 else "REJECT")}
