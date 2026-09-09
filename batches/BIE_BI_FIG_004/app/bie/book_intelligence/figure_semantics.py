
from dataclasses import dataclass
class FigureSemanticError(ValueError):pass
@dataclass(frozen=True)
class FigureSemantics:figure_id:str;summary:str;entities:tuple;relations:tuple;confidence:float
def build(fid,summary,entities,relations,confidence):
 if not fid or not summary.strip() or not 0<=confidence<=1:raise FigureSemanticError("invalid semantics")
 eset=set(entities)
 for a,r,b in relations:
  if a not in eset or b not in eset or not r:raise FigureSemanticError("unbound relation")
 return FigureSemantics(fid,summary.strip(),tuple(entities),tuple(relations),confidence)
