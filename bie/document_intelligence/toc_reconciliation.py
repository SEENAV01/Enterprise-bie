class E(ValueError):pass
def reconcile(toc,detected):
 d={x["title"].casefold():x for x in detected};out=[];unmatched=[]
 for t in toc:
  k=t["title"].strip().casefold()
  if not k:raise E("title")
  if k in d:out.append({"title":t["title"],"toc_page":t.get("page"),"detected_id":d[k]["id"]})
  else:unmatched.append(t["title"])
 return {"matches":tuple(out),"unmatched":tuple(unmatched)}
