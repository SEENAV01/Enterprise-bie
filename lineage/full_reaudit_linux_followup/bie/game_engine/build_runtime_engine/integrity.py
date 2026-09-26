from __future__ import annotations
from pathlib import Path
import hashlib,json
from ..canonical import fingerprint
from .contracts import RuntimePackageManifest
from .errors import GameBuildError

def verify_compiler_binding(ctx,bundle):
    bundle.validate();actual=tuple(sorted((a.path,a.sha256) for a in bundle.artifacts))
    if actual!=bundle.receipt.artifact_hashes:raise GameBuildError('GAME_BUILD_COMPILER_RECEIPT_ARTIFACT_MISMATCH')
    body={'input':fingerprint(ctx),'hashes':actual,'profile':ctx.compile_profile}
    if fingerprint(body)!=bundle.receipt.bundle_fingerprint:raise GameBuildError('GAME_BUILD_COMPILER_RECEIPT_FINGERPRINT_MISMATCH')
    return True

def _canonical_json(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def verify_package(dist:Path,manifest:RuntimePackageManifest):
    dist=Path(dist);manifest.validate();seen=[]
    for a in manifest.artifacts:
        p=dist/a.path
        if not p.is_file():raise GameBuildError('GAME_BUILD_PACKAGE_ARTIFACT_MISSING',a.path)
        data=p.read_bytes()
        if len(data)!=a.size_bytes or hashlib.sha256(data).hexdigest()!=a.sha256:raise GameBuildError('GAME_BUILD_PACKAGE_ARTIFACT_TAMPER',a.path)
        seen.append(a.path)
    manifest_path=dist/'build-manifest.json'
    if not manifest_path.is_file():raise GameBuildError('GAME_BUILD_SELF_MANIFEST_MISSING')
    try:raw=json.loads(manifest_path.read_text())
    except Exception as e:raise GameBuildError('GAME_BUILD_SELF_MANIFEST_INVALID_JSON') from e
    self_hash=raw.pop('manifest_payload_sha256',None)
    if not isinstance(self_hash,str) or self_hash!=manifest.manifest_payload_sha256 or hashlib.sha256(_canonical_json(raw)).hexdigest()!=self_hash:
        raise GameBuildError('GAME_BUILD_SELF_MANIFEST_TAMPER')
    expected={'schema_version':manifest.schema_version,'compiler_receipt_id':manifest.compiler_receipt_id,'compiler_bundle_fingerprint':manifest.compiler_bundle_fingerprint,
              'toolchain_fingerprint':manifest.toolchain_fingerprint,'artifacts':[a.__dict__ for a in manifest.artifacts],'entrypoint':manifest.entrypoint,
              'package_fingerprint':manifest.package_fingerprint,'deterministic':True,'external_network':False,'product_accepted':False,
              'asset_bindings':[list(x) for x in manifest.asset_bindings]}
    if raw!=expected:raise GameBuildError('GAME_BUILD_SELF_MANIFEST_OBJECT_MISMATCH')
    actual_files={p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
    expected_files=set(seen)|{'build-manifest.json'}
    if actual_files!=expected_files:raise GameBuildError('GAME_BUILD_PACKAGE_UNTRACKED_FILE',','.join(sorted(actual_files^expected_files))[:1000])
    return {'checked':len(seen)+1,'package_fingerprint':manifest.package_fingerprint,'manifest_payload_sha256':self_hash,'passed':True,'product_accepted':False}
