
from dataclasses import dataclass
class CellError(ValueError):pass
@dataclass(frozen=True)
class Cell:row:int;col:int;text:str;confidence:float
def validate_cells(cells,rows,cols):
 if rows<1 or cols<1:raise CellError("shape")
 seen=set()
 for c in cells:
  k=(c.row,c.col)
  if not (0<=c.row<rows and 0<=c.col<cols) or k in seen or not 0<=c.confidence<=1:raise CellError("cell")
  seen.add(k)
 return tuple(cells)
