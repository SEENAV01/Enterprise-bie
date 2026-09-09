
from dataclasses import dataclass
class FigureProvError(ValueError):pass
@dataclass(frozen=True)
class FigureProvenance:figure_id:str;source_hash:str;page:int;box:tuple;artifact_ref:str
def validate(p):
 if not p.figure_id or len(p.source_hash)!=64 or p.page<1 or len(p.box)!=4 or not p.artifact_ref:raise FigureProvError("invalid provenance")
 return True
