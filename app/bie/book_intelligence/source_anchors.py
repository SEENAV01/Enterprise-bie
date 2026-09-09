from dataclasses import dataclass
class E(ValueError):pass
@dataclass(frozen=True)
class Anchor: source_hash:str;page:int;region_id:str;box:tuple
def validate(a):
 if len(a.source_hash)!=64 or a.page<1 or not a.region_id or len(a.box)!=4:raise E("anchor")
 x1,y1,x2,y2=a.box
 if not(0<=x1<x2<=1 and 0<=y1<y2<=1):raise E("box")
 return True
