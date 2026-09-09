class E(ValueError):pass
def normalize(xs):
 out=[];seen=set()
 for x in xs:
  i=str(x.get("id",""));t=str(x.get("text","")).strip();a=x.get("source_anchor")
  if not i or i in seen or not t or not a:raise E("invalid objective")
  seen.add(i);out.append({"id":i,"text":t,"source_anchor":a})
 return tuple(out)
