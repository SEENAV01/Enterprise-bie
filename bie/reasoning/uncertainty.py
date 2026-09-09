def represent(confidence,coverage,conflict):
 if any(v<0 or v>1 for v in (confidence,coverage,conflict)):raise ValueError("normalized")
 e=confidence*coverage*(1-.5*conflict)
 return {"confidence":e,"label":"high" if e>=.75 else "medium" if e>=.45 else "low"}
