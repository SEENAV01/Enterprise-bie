
from dataclasses import dataclass
class LayoutError(ValueError):pass
@dataclass(frozen=True)
class Region:region_id:str;kind:str;box:tuple;confidence:float
KINDS={"text","title","heading","list","table","figure","equation","caption","footnote","callout"}
def normalize(regions):
 ids=set();out=[]
 for r in regions:
  if not r.region_id or r.region_id in ids or r.kind not in KINDS or len(r.box)!=4 or not 0<=r.confidence<=1:raise LayoutError("invalid region")
  x1,y1,x2,y2=r.box
  if x2<=x1 or y2<=y1:raise LayoutError("invalid geometry")
  ids.add(r.region_id);out.append(r)
 return tuple(out)
