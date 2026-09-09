class E(ValueError):pass
def normalize(xs):
 out=[];seen=set()
 for x in xs:
  i=str(x.get("id","")).strip();t=str(x.get("text","")).strip()
  if not i or i in seen or not t:raise E("invalid reference")
  seen.add(i);out.append({"id":i,"text":t,"source_anchor":x.get("source_anchor")})
 return tuple(out)
