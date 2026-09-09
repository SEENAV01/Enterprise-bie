
from dataclasses import dataclass
class PageInventoryError(ValueError):pass
@dataclass(frozen=True)
class PageRecord:index:int;label:str|None;width:float;height:float;has_text:bool;image_count:int
def validate_pages(pages):
 if not pages:raise PageInventoryError("pages required")
 for i,p in enumerate(pages,1):
  if p.index!=i:raise PageInventoryError("non-contiguous pages")
  if p.width<=0 or p.height<=0 or p.image_count<0:raise PageInventoryError("invalid page metrics")
 return tuple(pages)
