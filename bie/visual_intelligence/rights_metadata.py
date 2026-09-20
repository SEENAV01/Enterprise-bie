from dataclasses import dataclass
from .asset_contracts import *
ALLOWED={"owned","public_domain","licensed","source-permitted","unknown","restricted"}
@dataclass(frozen=True)
class RightsMetadata:
    rights_id:str; status:str; license_name:str|None; attribution_required:bool; attribution_text:str|None
    source_uri:str|None; commercial_use_allowed:bool|None; modification_allowed:bool|None; notes:dict
    def __post_init__(self):
        object.__setattr__(self,"rights_id",token(self.rights_id,field_name="rights_id"))
        s=token(self.status,field_name="status").lower()
        if s not in ALLOWED: raise AssetRightsError("unsupported rights status")
        object.__setattr__(self,"status",s)
        if self.attribution_required and not (self.attribution_text and self.attribution_text.strip()): raise AssetRightsError("attribution text required")
        object.__setattr__(self,"notes",canon(dict(self.notes)))
    @property
    def production_usable(self):
        return self.status in {"owned","public_domain","licensed","source-permitted"} and self.commercial_use_allowed is not False
def validate_rights_for_production(m):
    blockers=[]
    if m.status in {"unknown","restricted"}: blockers.append(f"rights_status={m.status}")
    if m.commercial_use_allowed is False: blockers.append("commercial_use_disallowed")
    return (not blockers,tuple(blockers))
