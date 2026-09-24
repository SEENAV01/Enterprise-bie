#!/usr/bin/env python3
"""Run prepared source through real timed TTS, synchronization and bounded mixing."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--mix-spec',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--cache-namespace',required=True);p.add_argument('--sync-spec',type=Path)
    p.add_argument('--profile',choices=('batch001-144','batch001-204'),default='batch001-144')
    p.add_argument('--allow-technical-voice',action='store_true');p.add_argument('--allow-review-output',action='store_true')
    p.add_argument('--standalone-fixture',action='store_true');a=p.parse_args()
    if a.standalone_fixture:sys.path.append(str(ROOT/'dependency_snapshot'))
    try:
        if not a.allow_technical_voice:raise ValueError('TECHNICAL_VOICE_OPT_IN_REQUIRED')
        from audio_synthesize import prepare_input
        from bie.audio.timed_espeak_provider import TimedEspeakProvider
        from bie.audio.tts_cache import TTSCache
        from bie.audio.voice_selection import SelectionPolicy
        from bie.audio.caption_alignment import CaptionPolicy
        from bie.audio.sync_pipeline import prepare_sync,bind_sync_spec
        from bie.audio.mix_io import read_mix_spec,publish_mix
        from bie.audio.mix_pipeline import mix_synchronized
        from bie.audio.common import strict_json
        plan=prepare_input(strict_json(a.input.read_text()),a.profile)
        cache=TTSCache(a.cache,namespace=a.cache_namespace)
        policy=SelectionPolicy(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False)
        sync=prepare_sync(plan,TimedEspeakProvider(),cache,policy,caption_policy=CaptionPolicy(channel='display'))
        animations=bind_sync_spec(sync,strict_json(a.sync_spec.read_text())) if a.sync_spec else None
        spec=strict_json(a.mix_spec.read_text());stems,mix_policy,copies=read_mix_spec(spec,a.mix_spec.parent,sync)
        result=mix_synchronized(sync,stems,policy=mix_policy,animations=animations)
        copies.update({'narration.json':a.input.read_bytes(),'mix.json':a.mix_spec.read_bytes()})
        if a.sync_spec:copies['sync.json']=a.sync_spec.read_bytes()
        publish_mix(result,a.output,sync=sync,inputs=copies,allow_review=a.allow_review_output)
        receipt=result.receipt();clock=result.clock()
        print(json.dumps({'status':'MIXED_TECHNICAL_AUDIO','audio_sha256':receipt['output_audio_sha256'],'frames':clock['total_samples'],
            'integrated_lufs':receipt['peak_control']['after']['integrated_lufs'],'true_peak_dbtp':receipt['peak_control']['after']['true_peak_dbtp'],
            'requires_review':receipt['requires_review'],'product_accepted':False},indent=2));return 0
    except (ValueError,TypeError,OSError) as e:print(json.dumps({'status':'BLOCKED','error':str(e),'output_published':False}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
