class E(ValueError):pass
def bind(edges):
 out=[]
 for e in edges:
  anchors=tuple(dict.fromkeys(e.get("anchors",())))
  if not anchors:raise E("ungrounded edge")
  out.append({**e,"anchors":anchors,"grounded":True})
 return tuple(out)
