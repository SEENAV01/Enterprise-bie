from __future__ import annotations
from dataclasses import dataclass
from .compiler_asset_common import *

@dataclass(frozen=True)
class AssetPathResolution:
    asset_id:str
    resolved_public_path:str
    sha256:str
    media_type:str
    blockers:tuple[str,...]
    passed:bool
    accepted:bool=False

class CompilerAssetPathRegistry:
    def __init__(self):
        self._records={}

    def register(self,bundled_asset):
        asset_id=nonblank(bundled_asset.asset_id,"asset_id")
        path=public_rel(bundled_asset.public_path)
        if asset_id in self._records:
            raise CompilerAssetError("duplicate asset_id")
        self._records[asset_id]=bundled_asset
        return True

    def resolve(self,asset_ref):
        asset_ref=nonblank(asset_ref,"asset_ref")
        if asset_ref.startswith("asset://"):
            asset_id=asset_ref[len("asset://"):]
        else:
            asset_id=asset_ref
        record=self._records.get(asset_id)
        if record is None:
            return AssetPathResolution(
                asset_id,"","", "",("asset_unresolved:"+asset_id,),False,False
            )
        try:
            path=public_rel(record.public_path)
            digest=valid_sha256(record.sha256)
        except Exception as exc:
            return AssetPathResolution(
                asset_id,"","", "",("asset_record_invalid:"+asset_id+":"+str(exc),),False,False
            )
        return AssetPathResolution(
            asset_id,path,digest,record.media_type,(),True,False
        )

    def require(self,asset_ref):
        result=self.resolve(asset_ref)
        if not result.passed:
            raise CompilerAssetError(";".join(result.blockers))
        return result

    def snapshot(self):
        return tuple(sorted(
            (asset_id,public_rel(record.public_path),record.sha256,record.media_type)
            for asset_id,record in self._records.items()
        ))
