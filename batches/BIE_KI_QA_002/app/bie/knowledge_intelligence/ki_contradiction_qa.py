def evaluate(conflicts,unresolved_allowed=0):
 unresolved=[x for x in conflicts if x.get("status") not in {"RESOLVED","DISMISSED"}]
 severe=[x for x in unresolved if x.get("severity")=="CRITICAL"]
 return {"passed":not severe and len(unresolved)<=unresolved_allowed,"unresolved":tuple(unresolved),"critical":tuple(severe)}
