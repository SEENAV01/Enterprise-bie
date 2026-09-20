from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from hashlib import sha256
import re

class CompilerAssetError(ValueError):
    pass

_SHA256=re.compile(r"^[0-9a-f]{64}$")

def nonblank(value,name):
    if not isinstance(value,str) or not value.strip():
        raise CompilerAssetError(f"{name} required")
    return value.strip()

def valid_sha256(value,name="sha256"):
    if not isinstance(value,str) or not _SHA256.fullmatch(value):
        raise CompilerAssetError(f"{name} must be 64 lowercase hex chars")
    return value

def public_rel(value,name="public_path"):
    value=nonblank(value,name)
    p=PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or "://" in value:
        raise CompilerAssetError(f"{name} must be public-relative")
    return p.as_posix()

def file_sha256(path):
    path=Path(path)
    if not path.is_file():
        raise CompilerAssetError("asset source file missing")
    h=sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):
            h.update(chunk)
    return h.hexdigest()

@dataclass(frozen=True)
class CompilerAssetRecord:
    asset_id:str
    source_path:str
    expected_sha256:str
    media_type:str
    rights_basis:str
    current:bool=True

    def __post_init__(self):
        object.__setattr__(self,"asset_id",nonblank(self.asset_id,"asset_id"))
        object.__setattr__(self,"source_path",nonblank(self.source_path,"source_path"))
        object.__setattr__(self,"expected_sha256",valid_sha256(self.expected_sha256,"expected_sha256"))
        object.__setattr__(self,"media_type",nonblank(self.media_type,"media_type"))
        object.__setattr__(self,"rights_basis",nonblank(self.rights_basis,"rights_basis"))
