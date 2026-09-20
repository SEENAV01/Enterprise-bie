from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .compiler_asset_common import *

@dataclass(frozen=True)
class AssetHashVerification:
    asset_id:str
    expected_sha256:str
    actual_sha256:str
    path:str
    passed:bool
    blockers:tuple[str,...]
    accepted:bool=False

def verify_asset_hash(asset_id,path,expected_sha256):
    asset_id=nonblank(asset_id,"asset_id")
    expected_sha256=valid_sha256(expected_sha256,"expected_sha256")
    path=Path(path)
    if not path.is_file():
        return AssetHashVerification(
            asset_id,expected_sha256,"",str(path),
            False,("asset_file_missing:"+asset_id,),False
        )
    actual=file_sha256(path)
    blockers=() if actual==expected_sha256 else ("asset_hash_mismatch:"+asset_id,)
    return AssetHashVerification(
        asset_id,expected_sha256,actual,str(path),
        not blockers,blockers,False
    )

def verify_bundle_hashes(bundle_receipt):
    root=Path(bundle_receipt.bundle_root)/"public"
    results=[]
    for item in bundle_receipt.bundled:
        results.append(
            verify_asset_hash(
                item.asset_id,
                root/public_rel(item.public_path),
                item.sha256
            )
        )
    return tuple(results)

def require_all_hashes(results):
    failed=[r for r in results if not r.passed]
    if failed:
        raise CompilerAssetError(
            ";".join(x for r in failed for x in r.blockers)
        )
    return True
