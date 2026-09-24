#!/usr/bin/env python3
from __future__ import annotations
import json,sys,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'dependency_snapshot')]
from tests.audio.h10_test_support import baseline,repair_intent,statuses
from bie.audio.dir_audio_handoff import bind_dir_utterances
from bie.audio.compiler_handoff import build_compiler_handoff
from bie.audio.repair_dispatch import invalidation_plan
from bie.audio.render_evidence import render_technical_av
from bie.audio.f04_gate import evaluate_f04

out=Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'evidence/h10');out.mkdir(parents=True,exist_ok=True)
files,bundle,plan,utts=baseline();clock=json.loads(files['MIX_CLOCK.json'])
dir_r=bind_dir_utterances(utts,plan)
comp_r,assets=build_compiler_handoff(plan,files['master.wav'],clock,fps=24,caption_target_id='caption:text',
    target_ids_by_scene={'scene:1':('visual:primary',)},rights_ref='rights:synthetic-h5',reasoning_refs=('reasoning:synthetic-h5',))
inv=invalidation_plan(repair_intent(),statuses())
render_r,mp4=render_technical_av(files['master.wav'],files['captions.srt'],out/'render')
gate=evaluate_f04(dir_receipt=dir_r,compiler_receipt=comp_r,compiler_files=assets,invalidation_receipt=inv,render_receipt=render_r,render_bytes=mp4)
(out/'DIR_AUDIO_HANDOFF.json').write_text(json.dumps(dir_r,indent=2,sort_keys=True)+'\n')
(out/'COMPILER_HANDOFF.json').write_text(json.dumps(comp_r,indent=2,sort_keys=True)+'\n')
(out/'REPAIR_INVALIDATION.json').write_text(json.dumps(inv,indent=2,sort_keys=True)+'\n')
(out/'TECHNICAL_AV_RENDER.json').write_text(json.dumps(render_r,indent=2,sort_keys=True)+'\n')
(out/'F04_GATE.json').write_text(json.dumps(gate,indent=2,sort_keys=True)+'\n')
asset_dir=out/'compiler_assets';asset_dir.mkdir(exist_ok=True)
for path,data in assets.items():
    dest=asset_dir/Path(path).name;dest.write_bytes(data)
(out/'technical_av.mp4').write_bytes(mp4)
summary={'schema_version':'bie.audio.h10-benchmark/1','speech_plan_fingerprint':plan.fingerprint(),
 'dir_handoff_fingerprint':dir_r['fingerprint'],'compiler_handoff_fingerprint':comp_r['fingerprint'],
 'invalidation_fingerprint':inv['fingerprint'],'technical_render_fingerprint':render_r['fingerprint'],
 'f04_gate_fingerprint':gate['fingerprint'],'technical_mp4_sha256':hashlib.sha256(mp4).hexdigest(),
 'real_ffmpeg_av_render_verified':True,'real_remotion_render_verified':False,'full_audio_regression_completed':False,
 'section_exit_permitted':False,'product_accepted':False}
(out/'BENCHMARK_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,sort_keys=True))
