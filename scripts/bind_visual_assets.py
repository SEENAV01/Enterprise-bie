#!/usr/bin/env python3
"""Bind the existing asset bundle to a Scene IR with actual image/video bytes."""
from pathlib import Path
import argparse,json,sys,os,tempfile,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bie.compiler.asset_bundler import AssetBundleReceipt,BundledAsset
from bie.compiler.visual_assets import bind_visual_bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scene',type=Path);p.add_argument('bundle_receipt',type=Path);p.add_argument('asset_root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    try:
        dst=a.output.absolute()
        if dst.exists() or dst.is_symlink() or any(x.is_symlink() for x in dst.parents):raise ValueError('BIND_OUTPUT_EXISTS_OR_SYMLINK')
        row=json.loads(a.bundle_receipt.read_text());row['bundled']=tuple(BundledAsset(**x) for x in row['bundled']);row['blockers']=tuple(row['blockers']);row['warnings']=tuple(row['warnings'])
        scene,proof=bind_visual_bundle(json.loads(a.scene.read_text()),AssetBundleReceipt(**row),a.asset_root)
        dst.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.bie-bind-',dir=dst.parent))
        try:
            (stage/'BOUND_SCENE.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2));(stage/'BINDING.json').write_text(json.dumps(proof,indent=2))
            dst.mkdir(exist_ok=False)
            try:os.replace(stage,dst)
            except BaseException:dst.rmdir();raise
        finally:
            if stage.exists():shutil.rmtree(stage)
        print(json.dumps({'status':'ASSET_BINDING_READY_NOT_RELEASE','output':str(dst),'accepted':False}));return 0
    except (ValueError,TypeError,KeyError,OSError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
