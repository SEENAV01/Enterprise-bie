
from dataclasses import dataclass
class DocumentSecurityError(ValueError):pass
@dataclass(frozen=True)
class DocumentLimits:
 max_bytes:int=100_000_000; max_pages:int=5000; max_embedded_files:int=0; max_compression_ratio:float=100.0
def validate_document(meta,limits=DocumentLimits()):
 if meta.get("bytes",0)<=0 or meta["bytes"]>limits.max_bytes:raise DocumentSecurityError("size")
 if meta.get("pages",0)<1 or meta["pages"]>limits.max_pages:raise DocumentSecurityError("pages")
 if meta.get("embedded_files",0)>limits.max_embedded_files:raise DocumentSecurityError("embedded files")
 if meta.get("compression_ratio",1)>limits.max_compression_ratio:raise DocumentSecurityError("compression bomb risk")
 if meta.get("javascript",False):raise DocumentSecurityError("active content")
 return True
