
from dataclasses import dataclass
class PageMapError(ValueError):pass
@dataclass(frozen=True)
class Anchor:logical_id:str;physical_page:int;region_id:str;box:tuple
def validate(anchors,page_count):
 if page_count<1:raise PageMapError("page count")
 ids=set()
 for a in anchors:
  if not a.logical_id or a.logical_id in ids:raise PageMapError("logical id")
  if not 1<=a.physical_page<=page_count or not a.region_id or len(a.box)!=4:raise PageMapError("anchor")
  x1,y1,x2,y2=a.box
  if not (0<=x1<x2<=1 and 0<=y1<y2<=1):raise PageMapError("normalized box")
  ids.add(a.logical_id)
 return tuple(anchors)
