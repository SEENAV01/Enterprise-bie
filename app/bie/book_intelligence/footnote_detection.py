
class FootnoteError(ValueError):pass
def link_footnotes(markers,notes):
 by={str(n["marker"]):n for n in notes}
 out=[]
 for m in markers:
  key=str(m["marker"])
  if key not in by:raise FootnoteError("unresolved footnote "+key)
  out.append((m["id"],by[key]["id"]))
 if len({a for a,_ in out})!=len(out):raise FootnoteError("duplicate marker ids")
 return tuple(out)
