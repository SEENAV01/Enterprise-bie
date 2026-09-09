def evaluate(claims):
 unsupported=[];low=[]
 for c in claims:
  if not c.get("anchor_ids"):unsupported.append(c.get("claim_id"))
  elif c.get("confidence",0)<.65:low.append(c.get("claim_id"))
 return {"passed":not unsupported,"unsupported":tuple(unsupported),"low_confidence":tuple(low)}
