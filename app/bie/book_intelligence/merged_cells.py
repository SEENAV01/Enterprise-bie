
from dataclasses import dataclass
class MergeError(ValueError):pass
@dataclass(frozen=True)
class Span:row:int;col:int;rowspan:int;colspan:int
def validate_spans(spans,rows,cols):
 occupied=set()
 for s in spans:
  if min(s.rowspan,s.colspan)<1 or s.row<0 or s.col<0 or s.row+s.rowspan>rows or s.col+s.colspan>cols:raise MergeError("span")
  cells={(r,c) for r in range(s.row,s.row+s.rowspan) for c in range(s.col,s.col+s.colspan)}
  if occupied & cells:raise MergeError("overlap")
  occupied|=cells
 return tuple(spans)
