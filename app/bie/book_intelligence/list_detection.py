
class ListError(ValueError):pass
MARKERS={"bullet","number","letter","roman"}
def build_list(items):
 if not items:return ()
 kinds={i.get("marker_kind") for i in items}
 if any(k not in MARKERS for k in kinds):raise ListError("marker")
 levels=[int(i.get("level",1)) for i in items]
 if any(l<1 for l in levels):raise ListError("level")
 for a,b in zip(levels,levels[1:]):
  if b>a+1:raise ListError("nesting jump")
 return tuple({"text":str(i.get("text","")).strip(),"marker_kind":i["marker_kind"],"level":int(i.get("level",1))} for i in items)
