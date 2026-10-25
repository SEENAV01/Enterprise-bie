from __future__ import annotations
from dataclasses import dataclass
import re

_SHA256=re.compile(r"^[0-9a-f]{64}$")
ASSET_TYPES={"image","video","model3d"}

@dataclass(frozen=True)
class AssetRecord:
    asset_id:str
    uri:str
    sha256:str
    rights_basis:str
    media_type:str
    current:bool=True
    source_ref:str|None=None

    def __post_init__(self):
        for name in ("asset_id","uri","rights_basis","media_type"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip():
                raise ValueError(f"{name} must be nonblank")
        if not isinstance(self.sha256,str) or not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        if self.source_ref is not None and (not isinstance(self.source_ref,str) or not self.source_ref.strip()):
            raise ValueError("source_ref invalid")

@dataclass(frozen=True)
class AssetResolutionReceipt:
    scene_id:str
    resolved_assets:tuple[str,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    passed:bool
    accepted:bool=False

class AssetRegistry:
    def __init__(self):
        self._records={}
    def register(self,record):
        if record.asset_id in self._records:
            raise ValueError("duplicate asset_id")
        self._records[record.asset_id]=record
        return True
    def get(self,asset_id):
        return self._records.get(asset_id)

def resolve_assets(document, registry):
    blockers=[];warnings=[];resolved=[]
    for e in document.elements:
        if e.element_type not in ASSET_TYPES:
            continue
        asset_ref=e.props.get("asset_ref")
        if not asset_ref:
            blockers.append("asset_ref_missing:"+e.element_id)
            continue
        record=registry.get(str(asset_ref))
        if record is None:
            blockers.append("asset_unresolved:"+e.element_id+":"+str(asset_ref))
            continue
        if not record.current:
            blockers.append("asset_stale:"+record.asset_id)
        if not record.rights_basis.strip():
            blockers.append("asset_rights_missing:"+record.asset_id)
        if record.source_ref is not None and record.source_ref not in e.source_refs:
            warnings.append("asset_source_not_in_element_lineage:"+record.asset_id)
        resolved.append(record.asset_id)
    return AssetResolutionReceipt(
        document.scene_id,
        tuple(sorted(set(resolved))),
        tuple(sorted(set(blockers))),
        tuple(sorted(set(warnings))),
        not blockers,
        False
    )

def require_assets(receipt):
    if not receipt.passed:
        raise ValueError("asset resolution failed")
    return True
