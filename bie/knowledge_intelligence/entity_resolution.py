class E(ValueError):pass
def resolve(mid,candidates):
 if not mid or not candidates:raise E("resolution")
 if any(not 0<=x["confidence"]<=1 for x in candidates):raise E("confidence")
 r=sorted(candidates,key=lambda x:x["confidence"],reverse=True);tie=len(r)>1 and r[0]["confidence"]==r[1]["confidence"]
 return {"mention_id":mid,"entity_id":None if tie else r[0]["entity_id"],"status":"REVIEW" if tie else "RESOLVED","candidates":tuple(r)}
