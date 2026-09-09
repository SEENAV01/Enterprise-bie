class E(ValueError):pass
def assess(edges,accept=.85,review=.65):
 out=[]
 for e in edges:
  c=e.get("confidence")
  if c is None or not 0<=c<=1:raise E("confidence")
  status="ACCEPT" if c>=accept else ("REVIEW" if c>=review else "REJECT")
  out.append({**e,"confidence_status":status})
 return tuple(out)
