class E(ValueError):pass
def validate(xs):
 if not xs:raise E("segments")
 last=None
 for x in xs:
  k=(int(x["page"]),int(x["order"]))
  if k[0]<1 or k[1]<1 or not x.get("anchor_id") or (last is not None and k<=last):raise E("segment")
  last=k
 return tuple(xs)
