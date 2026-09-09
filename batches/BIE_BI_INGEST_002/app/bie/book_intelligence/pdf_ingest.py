
from dataclasses import dataclass
class PDFIngestError(ValueError):pass
@dataclass(frozen=True)
class PDFInventory:page_count:int;metadata:dict;encrypted:bool;text_pages:int
def ingest_pdf(adapter,data):
 if not data.startswith(b"%PDF"):raise PDFIngestError("not PDF")
 x=adapter.inspect(data)
 if x["page_count"]<1:raise PDFIngestError("empty PDF")
 return PDFInventory(x["page_count"],dict(x.get("metadata",{})),bool(x.get("encrypted")),int(x.get("text_pages",0)))
