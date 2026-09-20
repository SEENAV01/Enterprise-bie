from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json

from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir, encode_scene_ir
from bie.scene_ir.dsl_orchestrator import validate_scene_ir_document

class SceneIRLoadError(ValueError):
    pass

@dataclass(frozen=True)
class LoadedSceneIR:
    source_kind:str
    source_sha256:str
    scene_id:str
    scene_fingerprint:str
    canonical_json:str
    document:object
    validation_passed:bool
    accepted:bool=False

def _sha_bytes(data):
    return sha256(data).hexdigest()

def load_scene_ir_payload(payload):
    if hasattr(payload,"to_dict"):
        doc=payload
        source_kind="typed"
        raw=encode_scene_ir(doc).encode("utf-8")
    elif isinstance(payload,dict):
        source_kind="mapping"
        raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        doc=decode_scene_ir(payload)
    elif isinstance(payload,str):
        source_kind="json"
        raw=payload.encode("utf-8")
        doc=decode_scene_ir(payload)
    else:
        raise SceneIRLoadError("unsupported Scene IR payload type")

    gate=validate_scene_ir_document(doc)
    if not gate.passed:
        raise SceneIRLoadError("Scene IR validation gate failed: "+";".join(gate.blockers))
    canonical=encode_scene_ir(doc)
    return LoadedSceneIR(
        source_kind,_sha_bytes(raw),doc.scene_id,doc.fingerprint,canonical,doc,True,False
    )

def load_scene_ir_file(path, allowed_root):
    path=Path(path).resolve()
    root=Path(allowed_root).resolve()
    try:
        path.relative_to(root)
    except Exception as exc:
        raise SceneIRLoadError("Scene IR file escapes allowed_root") from exc
    if path.suffix.lower()!=".json":
        raise SceneIRLoadError("Scene IR file must be .json")
    if not path.is_file():
        raise SceneIRLoadError("Scene IR file missing")
    data=path.read_bytes()
    try:
        text=data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SceneIRLoadError("Scene IR file must be UTF-8") from exc
    loaded=load_scene_ir_payload(text)
    return LoadedSceneIR(
        "file",_sha_bytes(data),loaded.scene_id,loaded.scene_fingerprint,
        loaded.canonical_json,loaded.document,loaded.validation_passed,False
    )
