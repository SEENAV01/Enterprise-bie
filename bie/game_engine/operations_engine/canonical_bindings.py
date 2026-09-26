from __future__ import annotations
from pathlib import Path
import hashlib
from .errors import GameOperationsError

CANONICAL_MAIN='375d99af0edd0086206817dae932156ddf61c569'
CANONICAL_BLOBS={
 'bie/bie_core/artifact_contracts.py':'7d7bf7944ff2f3cb1121b38399652a968b89a0b5',
 'bie/infrastructure/artifact_store.py':'5ab0fbf90e6981585fdd4dfbe6aa6ddc6ebfa2f4',
 'bie/infrastructure/idempotency_store.py':'bbfa38c261e67d142ad96ee96baebdc211b21507',
}
def git_blob_sha(data:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def verify_canonical_bindings(package_root:Path):
    package_root=Path(package_root); out={}
    for rel,expected in CANONICAL_BLOBS.items():
        p=package_root/rel
        if not p.is_file(): raise GameOperationsError('GAME_OPS_CANONICAL_DEPENDENCY_MISSING:'+rel)
        actual=git_blob_sha(p.read_bytes())
        if actual!=expected: raise GameOperationsError('GAME_OPS_CANONICAL_DEPENDENCY_MISMATCH:'+rel)
        out[rel]=actual
    return out
