
from dataclasses import dataclass
class MultimodalError(ValueError):pass
@dataclass(frozen=True)
class Part:
 kind:str;data:object;mime_type:str|None=None
ALLOWED={"text","image","audio","video","document"}
def validate_parts(parts):
 if not parts:raise MultimodalError("parts required")
 for p in parts:
  if p.kind not in ALLOWED:raise MultimodalError("unsupported modality")
  if p.kind!="text" and not p.mime_type:raise MultimodalError("mime required")
 return tuple(parts)
