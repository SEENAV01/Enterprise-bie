#!/usr/bin/env python3
"""Explicit compressed local audio -> verified PCM asset for the current compiler.
No TTS, transcript inference or remote fetch. Source references remain mandatory.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bie.compiler.audio_preparation import normalize_local_audio,asset_descriptor

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--sha256',required=True);p.add_argument('--asset-id',required=True);p.add_argument('--rights-ref',required=True)
    p.add_argument('--source-ref',action='append',required=True);p.add_argument('--reasoning-ref',action='append',required=True)
    p.add_argument('--sample-rate',type=int,default=48000);p.add_argument('--channels',type=int,default=1);a=p.parse_args()
    if a.output.exists() or a.output.is_symlink():raise ValueError('OUTPUT_EXISTS')
    data,receipt=normalize_local_audio(a.input,expected_sha256=a.sha256,sample_rate=a.sample_rate,channels=a.channels)
    descriptor=asset_descriptor(data,asset_id=a.asset_id,rights_ref=a.rights_ref,source_refs=a.source_ref,reasoning_refs=a.reasoning_ref)
    a.output.mkdir(parents=True);dest=a.output/descriptor['public_path'];dest.parent.mkdir();dest.write_bytes(data)
    (a.output/'ASSET.json').write_text(json.dumps(descriptor,indent=2));(a.output/'PREPARATION.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'descriptor':descriptor,'speech_verified':False,'accepted':False}))
if __name__=='__main__':main()
