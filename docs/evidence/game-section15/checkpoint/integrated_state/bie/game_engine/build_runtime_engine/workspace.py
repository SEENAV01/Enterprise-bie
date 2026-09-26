from __future__ import annotations
from pathlib import Path
import hashlib,json,shutil
from dataclasses import dataclass
from ..canonical import fingerprint
from ..compiler_engine.pipeline import compile_game
from ..compiler_engine.contracts import CompilerContext
from .contracts import BuildPolicy,PackageArtifact,RuntimePackageManifest,safe_relative
from .errors import GameBuildError
from .process import run_bounded
from .toolchain import discover_toolchain
from .linker import link_browser_esm
from .entrypoint import ENTRY_JS
from .smoke_bundle import build_smoke_bundle
from ..compiler_engine.security import csp_value
from .integrity import verify_compiler_binding
from .module_graph import verify_module_graph

def _sha(data):return hashlib.sha256(data).hexdigest()
def _media(path):
    ext=Path(path).suffix.lower();return {'.js':'text/javascript','.json':'application/json','.html':'text/html','.wav':'audio/wav','.mp3':'audio/mpeg','.png':'image/png','.svg':'image/svg+xml','.css':'text/css'}.get(ext,'application/octet-stream')

def _asset_ext(media):return {'audio/wav':'.wav','audio/mpeg':'.mp3','image/png':'.png','image/svg+xml':'.svg'}.get(media,'')
def _safe_asset_name(ref,media,content_sha256):
    base=''.join(c if c.isalnum() or c in '-_' else '-' for c in ref).strip('-') or 'asset'
    # Content-addressed suffix prevents distinct refs that sanitize to the same basename from overwriting each other.
    return f'assets/{base}--{content_sha256[:24]}{_asset_ext(media)}'

def _manifest_payload(manifest,asset_bindings):
    return {'schema_version':manifest.schema_version,'compiler_receipt_id':manifest.compiler_receipt_id,'compiler_bundle_fingerprint':manifest.compiler_bundle_fingerprint,
            'toolchain_fingerprint':manifest.toolchain_fingerprint,'artifacts':[a.__dict__ for a in manifest.artifacts],'entrypoint':manifest.entrypoint,
            'package_fingerprint':manifest.package_fingerprint,'deterministic':True,'external_network':False,'product_accepted':False,
            'asset_bindings':[list(x) for x in asset_bindings]}

def _manifest_self_hash(payload):return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class BuiltWorkspace:
    root:Path;manifest:RuntimePackageManifest;compiler_bundle:object;toolchain:tuple;toolchain_fingerprint:str

def build_workspace(ctx:CompilerContext,asset_blobs,root:Path,policy=BuildPolicy()):
    policy.validate();ctx.validate();root=Path(root)
    if root.exists() and any(root.iterdir()):raise GameBuildError('GAME_BUILD_WORKSPACE_NOT_EMPTY')
    root.mkdir(parents=True,exist_ok=True);src=root/'src/runtime';dist=root/'dist';runtime=dist/'runtime';src.mkdir(parents=True);runtime.mkdir(parents=True)
    bundle=compile_game(ctx);verify_compiler_binding(ctx,bundle);tools,tool_fp=discover_toolchain()
    for a in bundle.artifacts:
        data=a.content.encode()
        if _sha(data)!=a.sha256:raise GameBuildError('GAME_BUILD_COMPILER_ARTIFACT_TAMPER',a.path)
        if len(data)>policy.max_artifact_bytes:raise GameBuildError('GAME_BUILD_ARTIFACT_TOO_LARGE',a.path)
        rel=safe_relative(a.path);f=root/'src'/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
    asset_rows=[];materialized={}
    for ref,desc in sorted(ctx.assets.items()):
        if ref not in asset_blobs:raise GameBuildError('GAME_BUILD_ASSET_BYTES_MISSING',ref)
        data=asset_blobs[ref]
        if not isinstance(data,(bytes,bytearray)):raise GameBuildError('GAME_BUILD_ASSET_BYTES_TYPE',ref)
        digest=_sha(data)
        if digest!=desc.content_sha256:raise GameBuildError('GAME_BUILD_ASSET_HASH_MISMATCH',ref)
        rel=_safe_asset_name(ref,desc.media_type,digest)
        prior=materialized.get(rel)
        if prior is not None and prior!=digest:raise GameBuildError('GAME_BUILD_ASSET_PATH_COLLISION',rel)
        f=dist/rel;f.parent.mkdir(parents=True,exist_ok=True)
        if not f.exists():f.write_bytes(data)
        materialized[rel]=digest;asset_rows.append((ref,rel,digest))
    ts=sorted(src.glob('*.ts'));tsc=next(t for t in tools if t.name=='typescript')
    cmd=[tsc.path,'--target','ES2020','--module','ES2020','--moduleResolution','node','--strict','--skipLibCheck','--lib','ES2020,DOM','--noEmitOnError','--outDir',str(runtime),*map(str,ts)]
    r=run_bounded(cmd,cwd=src,timeout=policy.compile_timeout_seconds,max_output=2_000_000,cpu_seconds=policy.process_cpu_seconds,memory_bytes=policy.process_memory_bytes,max_processes=policy.process_max_processes,max_open_files=policy.process_max_open_files,max_file_bytes=policy.max_package_bytes*2)
    if r.returncode!=0:raise GameBuildError('GAME_BUILD_TYPESCRIPT_FAILED',(r.stderr+r.stdout)[:1500])
    for f in sorted(runtime.glob('*.js')):f.write_text(link_browser_esm(f.read_text()))
    for f in sorted(src.glob('*.json')):shutil.copy2(f,runtime/f.name)
    html=(src/'index.html').read_text().replace('./bootstrap.js','./entry.js')
    html=html.replace('; frame-ancestors &#x27;none&#x27;','').replace("; frame-ancestors 'none'",'')
    (runtime/'index.html').write_text(html);(runtime/'entry.js').write_text(ENTRY_JS)
    headers={'Content-Security-Policy':csp_value(),'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Cross-Origin-Resource-Policy':'same-origin'}
    (runtime/'security-headers.json').write_text(json.dumps(headers,sort_keys=True,separators=(',',':')))
    graph=verify_module_graph(runtime);(runtime/'module-graph.json').write_text(json.dumps(graph,sort_keys=True,separators=(',',':')))
    smoke,_=build_smoke_bundle(runtime);(runtime/'smoke-bundle.js').write_text(smoke)
    artifacts=[];total=0
    for f in sorted(p for p in dist.rglob('*') if p.is_file()):
        rel=f.relative_to(dist).as_posix();data=f.read_bytes();total+=len(data)
        if len(data)>policy.max_artifact_bytes:raise GameBuildError('GAME_BUILD_ARTIFACT_TOO_LARGE',rel)
        artifacts.append(PackageArtifact(rel,len(data),_sha(data),_media(rel),'compiler_or_build').validate())
    if total>policy.max_package_bytes:raise GameBuildError('GAME_BUILD_PACKAGE_TOO_LARGE')
    body={'compiler_receipt_id':bundle.receipt.receipt_id,'compiler_bundle_fingerprint':bundle.receipt.bundle_fingerprint,'toolchain_fingerprint':tool_fp,
          'artifacts':[(a.path,a.sha256,a.size_bytes) for a in artifacts],'entrypoint':'runtime/index.html','asset_bindings':asset_rows}
    pf=fingerprint(body)
    preliminary=RuntimePackageManifest('bie.game.runtime-package/2',bundle.receipt.receipt_id,bundle.receipt.bundle_fingerprint,tool_fp,tuple(artifacts),'runtime/index.html',pf,True,False,False,'',tuple(asset_rows)).validate()
    payload=_manifest_payload(preliminary,asset_rows);self_hash=_manifest_self_hash(payload)
    manifest=RuntimePackageManifest(preliminary.schema_version,preliminary.compiler_receipt_id,preliminary.compiler_bundle_fingerprint,preliminary.toolchain_fingerprint,preliminary.artifacts,preliminary.entrypoint,preliminary.package_fingerprint,True,False,False,self_hash,tuple(asset_rows)).validate()
    payload['manifest_payload_sha256']=self_hash
    (dist/'build-manifest.json').write_text(json.dumps(payload,sort_keys=True,separators=(',',':')))
    return BuiltWorkspace(root,manifest,bundle,tools,tool_fp)
