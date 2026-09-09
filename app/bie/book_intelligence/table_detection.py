
from dataclasses import dataclass
class TableError(ValueError):pass
@dataclass(frozen=True)
class TableRegion:table_id:str;page:int;box:tuple;confidence:float
def validate(t):
 if not t.table_id or t.page<1 or len(t.box)!=4 or not 0<=t.confidence<=1:raise TableError("invalid table")
 a,b,c,d=t.box
 if not (0<=a<c<=1 and 0<=b<d<=1):raise TableError("box")
 return True
