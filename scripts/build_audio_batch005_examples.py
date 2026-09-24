#!/usr/bin/env python3
"""Generate synthetic QA inputs using real local technical speech, never a paid API."""
from pathlib import Path
import argparse,json,sys,tempfile,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))

def main():
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);p.add_argument('--allow-technical-voice',action='store_true');p.add_argument('--standalone-fixture',action='store_true');a=p.parse_args()
    if not a.allow_technical_voice:raise SystemExit('TECHNICAL_VOICE_OPT_IN_REQUIRED')
    if a.standalone_fixture:sys.path.append(str(ROOT/'dependency_snapshot'))
    from audio_synthesize import prepare_input
    from bie.audio.timed_espeak_provider import TimedEspeakProvider
    from bie.audio.tts_cache import TTSCache
    from bie.audio.voice_selection import SelectionPolicy
    from bie.audio.caption_alignment import CaptionPolicy
    from bie.audio.sync_pipeline import prepare_sync
    from bie.audio.mix_contract import MixBuffer
    from bie.audio.tts_contract import AudioFormat
    from bie.audio.mix_pipeline import mix_synchronized
    from bie.audio.mix_io import publish_mix
    from bie.audio.sfx_mixing import Stem
    from bie.audio.qa_pipeline import audit_mix
    from bie.audio.qa_io import publish_qa
    if a.destination.exists():raise SystemExit('EXAMPLE_OUTPUT_EXISTS')
    a.destination.mkdir(parents=True);cases=[]
    for name,example,sound in (('english','audio_batch003/scene_animation_pause.json',False),('english-sound','audio_batch003/scene_animation_pause.json',True),('hindi','audio_batch002/hindi.json',False)):
        folder=a.destination/name;folder.mkdir();narration=(ROOT/'examples'/example).read_bytes()
        plan=prepare_input(json.loads(narration),'batch001-144')
        with tempfile.TemporaryDirectory(prefix='bie-qa-demo-cache-') as td:
            sync=prepare_sync(plan,TimedEspeakProvider(),TTSCache(td,namespace='qa005-demo'),
                 SelectionPolicy(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False),caption_policy=CaptionPolicy(channel='display'))
        stems=();inputs={'narration.json':narration}
        if sound:
            rate=sync.timeline.sample_rate;x=.025*np.sin(2*np.pi*600*np.arange(rate)/rate)
            wav=MixBuffer.from_array(x[:,None],rate).to_wav();pcm=MixBuffer.from_wav(wav,AudioFormat(rate,1))
            stems=(Stem('cue','sfx',pcm,0,0,pcm.frames,('synthetic:original-cue',),'synthetic:self-generated-technical-tone'),)
            inputs[hashlib.sha256(wav).hexdigest()+'.wav']=wav
        mixed=mix_synchronized(sync,stems)
        publish_mix(mixed,folder/'mix',sync=sync,inputs=inputs,allow_review=True)
        intent={'schema_version':'bie.audio.caption-intent/1','mix_fingerprint':mixed.receipt()['fingerprint'],'speakers':[],
                'sounds':[{'asset_id':'cue','meaningful':True,'caption':'Brief tone marks the demonstration','language':'en','source_refs':['synthetic:original-cue']}] if sound else []}
        (folder/'CAPTION_INTENT.json').write_text(json.dumps(intent,ensure_ascii=False,indent=2)+'\n')
        report,cap=audit_mix(mixed,sync,asset_wavs=tuple(b for n,b in inputs.items() if n.endswith('.wav')),intent=intent)
        publish_qa(report,cap,folder/'qa-direct')
        cases.append({'case':name,'expected_status':'REVIEW','audio_sha256':hashlib.sha256(mixed.wav_bytes).hexdigest(),
                      'checks':{c['task_id']:c['status'] for c in report['checks']},'total_samples':mixed.clock()['total_samples'],
                      'sample_rate':sync.timeline.sample_rate,'speech_profile':'REAL_LOCAL_ESPEAK_TECHNICAL_SYNTHETIC_TEXT'})
    (a.destination/'CASES.json').write_text(json.dumps({'cases':cases,'product_accepted':False,'voice_listening_verified':False},indent=2)+'\n')
    print(json.dumps(cases,indent=2))
if __name__=='__main__':main()
