class E(ValueError):pass
def bind(canonical,aliases):
 c=canonical.strip();seen={c.casefold()};out=[]
 if not c:raise E("canonical")
 for a in aliases:
  x=str(a).strip();k=x.casefold()
  if x and k not in seen:out.append(x);seen.add(k)
 return {"canonical":c,"aliases":tuple(out)}
