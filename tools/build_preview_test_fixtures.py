"""Synthetic local fixture compiler, NOT a production/Linux worker fallback.

Uses actual unchanged BIE compile_game/linker/vendor/entrypoint and real pinned
tsc. Does not forge a Linux build/browser receipt. No real-book material.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict
import argparse,base64,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.build_runtime_engine.integrity import verify_compiler_binding,verify_package
from bie.game_engine.build_runtime_engine.module_graph import verify_module_graph
from bie.game_engine.build_runtime_engine.linker import link_browser_esm
from bie.game_engine.build_runtime_engine.entrypoint import ENTRY_JS
from bie.game_engine.build_runtime_engine.contracts import PackageArtifact,RuntimePackageManifest
from bie.game_engine.react_runtime_engine.vendor import materialize_vendor
from bie.game_engine.canonical import fingerprint
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--node',type=Path,required=True);parser.add_argument('--tsc',type=Path,required=True)
    parser.add_argument('--diagnostic-mp4',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    require_mp4='4f4687b86284fe7a170741515169f783d97a0aca88418680ebe8c6cb52381271'
    data=a.diagnostic_mp4.read_bytes();assert sha(data)==require_mp4,'DIAGNOSTIC_FIXTURE_HASH_CHANGED'
    version=subprocess.check_output([str(a.node),str(a.tsc),'--version'],text=True).strip();assert version=='Version 5.9.3'
    ctx,assets=build_inputs();bundle=compile_game(ctx);verify_compiler_binding(ctx,bundle)
    with TemporaryDirectory(prefix='bie-native-preview-fixture-') as temp:
        root=Path(temp);src=root/'src';runtime=root/'dist/runtime';src.mkdir();runtime.mkdir(parents=True)
        for item in bundle.artifacts:
            target=src/item.path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(item.content,encoding='utf-8',newline='\n')
        ts=sorted((src/'runtime').glob('*.ts'))
        args=[str(a.node),str(a.tsc),'--target','ES2020','--module','ES2020','--moduleResolution','node','--strict',
              '--skipLibCheck','--lib','ES2020,DOM','--noEmitOnError','--outDir',str(runtime),*map(str,ts)]
        result=subprocess.run(args,capture_output=True,text=True,timeout=60)
        assert result.returncode==0,result.stdout+result.stderr
        for f in runtime.glob('*.js'):f.write_text(link_browser_esm(f.read_text()),encoding='utf-8',newline='\n')
        for f in (src/'runtime').glob('*.json'):(runtime/f.name).write_bytes(f.read_bytes())
        html=(src/'runtime/index.html').read_text().replace('./bootstrap.js','./entry.js')
        (runtime/'index.html').write_text(html,encoding='utf-8',newline='\n')
        # The same physical path convention as the native workspace builder.
        asset_rows=[]
        for ref,blob in sorted(assets.items()):
            path='assets/'+sha(blob)+'.wav';target=root/'dist'/path;target.parent.mkdir(exist_ok=True);target.write_bytes(blob)
            asset_rows.append((ref,path,sha(blob)))
        amap={ref:'../'+path for ref,path,_ in asset_rows}
        (runtime/'entry.js').write_text(ENTRY_JS.replace('__ASSET_BINDINGS__',json.dumps(amap,sort_keys=True,separators=(',',':'))),encoding='utf-8',newline='\n')
        materialize_vendor(runtime);graph=verify_module_graph(runtime)
        files={p.relative_to(root/'dist').as_posix():p.read_bytes() for p in (root/'dist').rglob('*') if p.is_file()}
        media={'.js':'application/javascript','.json':'application/json','.html':'text/html','.wav':'audio/wav','.txt':'text/plain'}
        artifacts=tuple(PackageArtifact(path,len(raw),sha(raw),media[Path(path).suffix],'compiler_or_build') for path,raw in sorted(files.items()))
        tools=fingerprint(dict(test_only=True,node_sha256=sha(a.node.read_bytes()),tsc_sha256=sha(a.tsc.read_bytes()),typescript_version=version))
        pf=fingerprint(dict(compiler_receipt_id=bundle.receipt.receipt_id,compiler_bundle_fingerprint=bundle.receipt.bundle_fingerprint,
            toolchain_fingerprint=tools,artifacts=[(x.path,x.sha256,x.size_bytes) for x in artifacts],entrypoint='runtime/index.html',asset_bindings=asset_rows))
        preliminary=RuntimePackageManifest('bie.game.runtime-package/2',bundle.receipt.receipt_id,bundle.receipt.bundle_fingerprint,tools,artifacts,
            'runtime/index.html',pf,True,False,False,'',tuple(asset_rows))
        payload=asdict(preliminary);payload.pop('manifest_payload_sha256');self_hash=sha(canonical(payload))
        payload['manifest_payload_sha256']=self_hash
        manifest=RuntimePackageManifest(**dict(payload,artifacts=artifacts,asset_bindings=tuple(asset_rows)))
        files['build-manifest.json']=canonical(payload);(root/'dist/build-manifest.json').write_bytes(files['build-manifest.json'])
        verified=verify_package(root/'dist',manifest)
        receipt=dict(fixture_kind='SYNTHETIC_NATIVE_COMPILER_LOCAL_TSC',canonical_linux_build_supervisor_executed=False,
            native_remotion_render_executed=False,real_book_executed=False,product_accepted=False,typescript=version,
            tsc_sha256=sha(a.tsc.read_bytes()),compiler_bundle_fingerprint=bundle.receipt.bundle_fingerprint,
            module_graph=graph,package_verification=verified,mp4_origin='Section16 synthetic diagnostic; NOT Remotion/learning-video acceptance',
            mp4_sha256=require_mp4)
        wire=dict(receipt=receipt,game_manifest=payload,game_files={p:base64.b64encode(b).decode() for p,b in sorted(files.items())},
                  diagnostic_mp4_base64=base64.b64encode(data).decode())
        assert not a.output.exists(),'NEVER_OVERWRITE_FIXTURE_SEAL'
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(wire,sort_keys=True,indent=2)+'\n')
        print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
