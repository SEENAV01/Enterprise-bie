
class ColumnError(ValueError):pass
def detect_columns(regions,page_width,gap_ratio=.03):
 if page_width<=0 or not 0<=gap_ratio<1:raise ColumnError("invalid page/gap")
 xs=sorted((r["box"][0],r["box"][2],r["id"]) for r in regions if r.get("kind") in {"text","heading","list"})
 if not xs:return ()
 groups=[];cur=[]
 last_right=None
 for x1,x2,rid in xs:
  if x2<=x1 or x1<0 or x2>page_width:raise ColumnError("invalid region box")
  if last_right is not None and x1-last_right>=page_width*gap_ratio:
   groups.append(tuple(cur));cur=[]
  cur.append(rid);last_right=max(last_right or x2,x2)
 if cur:groups.append(tuple(cur))
 return tuple(groups)
