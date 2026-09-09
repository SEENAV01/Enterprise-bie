class E(ValueError):pass
KINDS={"mcq","short_answer","long_answer","numerical","proof","matching","true_false","other"}
def normalize(xs):
 out=[];seen=set()
 for x in xs:
  i=str(x.get("id",""));p=str(x.get("prompt","")).strip();k=x.get("kind","other")
  if not i or i in seen or not p or k not in KINDS:raise E("invalid exercise")
  seen.add(i);out.append({"id":i,"prompt":p,"kind":k,"source_anchor":x.get("source_anchor")})
 return tuple(out)
