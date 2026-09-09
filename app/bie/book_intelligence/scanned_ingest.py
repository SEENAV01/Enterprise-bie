
from dataclasses import dataclass
class ScanError(ValueError):pass
@dataclass(frozen=True)
class ScanPage:page:int;image_ref:str;width:int;height:int
def ingest_scanned(adapter,data):
 xs=adapter.render_pages(data)
 if not xs:raise ScanError("no rendered pages")
 out=[]
 for i,x in enumerate(xs,1):
  if x.get("width",0)<1 or x.get("height",0)<1 or not x.get("image_ref"):raise ScanError("invalid page image")
  out.append(ScanPage(i,x["image_ref"],x["width"],x["height"]))
 return tuple(out)
