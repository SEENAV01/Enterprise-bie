
from dataclasses import dataclass
class FigureError(ValueError):pass
@dataclass(frozen=True)
class FigureRegion:figure_id:str;page:int;box:tuple;confidence:float
def normalize(xs):
 out=[];ids=set()
 for x in xs:
  if not x.figure_id or x.figure_id in ids or x.page<1 or len(x.box)!=4 or not 0<=x.confidence<=1:raise FigureError("invalid figure")
  a,b,c,d=x.box
  if not (0<=a<c<=1 and 0<=b<d<=1):raise FigureError("box")
  ids.add(x.figure_id);out.append(x)
 return tuple(out)
