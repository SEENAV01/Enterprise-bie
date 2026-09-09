
from dataclasses import dataclass
class EncryptionError(PermissionError):pass
@dataclass(frozen=True)
class EncryptionStatus:encrypted:bool;can_extract:bool;can_render:bool;scheme:str|None=None
def gate(s):
 if s.encrypted and not (s.can_extract or s.can_render):raise EncryptionError("encrypted source inaccessible")
 return "RENDER_ONLY" if s.encrypted and not s.can_extract and s.can_render else "EXTRACT"
