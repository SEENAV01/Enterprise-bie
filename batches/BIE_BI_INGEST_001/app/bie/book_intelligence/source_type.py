
from dataclasses import dataclass
class SourceTypeError(ValueError):pass
SUPPORTED={"pdf","epub","docx","html","scanned_pdf"}
@dataclass(frozen=True)
class SourceDescriptor:source_id:str;kind:str;media_type:str;name:str
def classify(name,media_type,scanned=False):
 ext=name.lower().rsplit(".",1)[-1] if "." in name else ""
 if ext=="pdf":kind="scanned_pdf" if scanned else "pdf"
 elif ext in {"epub","docx","html","htm"}:kind="html" if ext=="htm" else ext
 else:raise SourceTypeError("unsupported source")
 return SourceDescriptor("",kind,media_type,name)
