from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
from .compiler_asset_common import *

@dataclass(frozen=True)
class BundledAsset:
    asset_id:str
    public_path:str
    sha256:str
    media_type:str
    rights_basis:str
    source_path:str
    accepted:bool=False

@dataclass(frozen=True)
class AssetBundleReceipt:
    bundled:tuple[BundledAsset,...]
    bundle_root:str
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    passed:bool
    accepted:bool=False

_EXT_BY_TYPE={
    "image/png":".png",
    "image/jpeg":".jpg",
    "image/webp":".webp",
    "video/mp4":".mp4",
    "audio/mpeg":".mp3",
    "audio/wav":".wav",
    "model/gltf-binary":".glb",
    "model/gltf+json":".gltf",
    "application/json":".json",
}

def _target_name(record):
    ext=Path(record.source_path).suffix.lower()
    if not ext:
        ext=_EXT_BY_TYPE.get(record.media_type,".bin")
    return record.expected_sha256[:20]+ext

def bundle_assets(records, output_root):
    output_root=Path(output_root).resolve()
    public_root=output_root/"public"/"assets"
    public_root.mkdir(parents=True,exist_ok=True)
    blockers=[];warnings=[];bundled=[]
    seen_ids=set()
    seen_targets={}

    for record in sorted(records,key=lambda r:r.asset_id):
        if record.asset_id in seen_ids:
            blockers.append("duplicate_asset_id:"+record.asset_id)
            continue
        seen_ids.add(record.asset_id)

        if not record.current:
            blockers.append("asset_not_current:"+record.asset_id)
            continue
        src=Path(record.source_path).resolve()
        if not src.is_file():
            blockers.append("asset_source_missing:"+record.asset_id)
            continue

        actual=file_sha256(src)
        if actual!=record.expected_sha256:
            blockers.append("asset_source_hash_mismatch:"+record.asset_id)
            continue

        target_name=_target_name(record)
        target=(public_root/target_name).resolve()
        try:
            target.relative_to(public_root)
        except Exception:
            blockers.append("bundle_target_escape:"+record.asset_id)
            continue

        if target_name in seen_targets and seen_targets[target_name]!=actual:
            blockers.append("bundle_target_collision:"+target_name)
            continue

        if not target.exists():
            shutil.copyfile(src,target)
        else:
            existing=file_sha256(target)
            if existing!=actual:
                blockers.append("existing_bundle_hash_conflict:"+record.asset_id)
                continue

        if file_sha256(target)!=actual:
            blockers.append("bundled_hash_mismatch:"+record.asset_id)
            continue

        seen_targets[target_name]=actual
        bundled.append(BundledAsset(
            record.asset_id,
            "assets/"+target_name,
            actual,
            record.media_type,
            record.rights_basis,
            str(src),
            False
        ))

    return AssetBundleReceipt(
        tuple(bundled),
        str(output_root),
        tuple(sorted(set(blockers))),
        tuple(sorted(set(warnings))),
        not blockers,
        False
    )
