from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath
import json
import re

class ReactEmitterError(ValueError):
    pass

_TS_IDENT=re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

def ts_identifier(value,name="identifier"):
    if not isinstance(value,str) or not _TS_IDENT.fullmatch(value):
        raise ReactEmitterError(f"{name} must be a valid TypeScript identifier")
    return value

def nonblank(value,name):
    if not isinstance(value,str) or not value.strip():
        raise ReactEmitterError(f"{name} must be nonblank")
    return value.strip()

def safe_rel_path(value):
    value=nonblank(value,"path")
    p=PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:
        raise ReactEmitterError("unsafe relative path")
    return p.as_posix()

def normalized_text(value):
    if not isinstance(value,str):
        raise ReactEmitterError("content must be text")
    return value.replace("\r\n","\n").replace("\r","\n").rstrip("\n")+"\n"

@dataclass(frozen=True)
class EmittedTextFile:
    path:str
    content:str
    sha256:str
    def __post_init__(self):
        object.__setattr__(self,"path",safe_rel_path(self.path))
        content=normalized_text(self.content)
        object.__setattr__(self,"content",content)
        object.__setattr__(self,"sha256",sha256(content.encode("utf-8")).hexdigest())

def emitted_file(path,content):
    return EmittedTextFile(path,content,"")

def stable_json(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def js_string(value):
    return json.dumps(str(value),ensure_ascii=False)
