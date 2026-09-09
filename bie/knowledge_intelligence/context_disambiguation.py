class E(ValueError):pass
def choose(term,candidates):
 if not term or not candidates:raise E("input")
 r=sorted(candidates,key=lambda x:x["confidence"],reverse=True)
 if any(not 0<=x["confidence"]<=1 for x in r):raise E("confidence")
 tie=len(r)>1 and r[0]["confidence"]==r[1]["confidence"]
 return {"term":term,"sense_id":None if tie else r[0]["sense_id"],"status":"REVIEW" if tie else "RESOLVED","candidates":tuple(r)}
