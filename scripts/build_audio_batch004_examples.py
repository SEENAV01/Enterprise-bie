#!/usr/bin/env python3
"""Build source-bound MIX fixtures using actual timed speech on this host.

Writes new files under an exclusive output directory. No network/provider charge.
Synthesized tone-bed and cue are technical originals, not production music.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'));sys.path.append(str(ROOT/'dependency_snapshot'))
from audio_synthesize import prepare_input
from bie.audio.timed_espeak_provider import TimedEspeakProvider
from bie.audio.tts_cache import TTSCache
from bie.audio.voice_selection import SelectionPolicy
from bie.audio.caption_alignment import CaptionPolicy
from bie.audio.sync_pipeline import prepare_sync
from bie.audio.mix_contract import MixBuffer
from bie.audio.mix_pipeline import MixPolicy
from bie.audio.sfx_mixing import Stem


def build(destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('EXAMPLE_OUTPUT_EXISTS')
    destination.mkdir(parents=True)
    reports=[]
    for name,src,profile,has_stems,has_animation in (
        ('english-dry','audio_batch003/scene_animation_pause.json','batch001-144',False,True),
        ('english-mix','audio_batch003/scene_animation_pause.json','batch001-144',True,True),
        ('hindi-mix','audio_batch002/hindi.json','batch001-144',True,False),
        ('compat204-mix','audio_batch002/compat204.json','batch001-204',True,False)):
        folder=destination/name;folder.mkdir();raw=(ROOT/'examples'/src).read_bytes();(folder/'narration.json').write_bytes(raw)
        plan=prepare_input(json.loads(raw),profile)
        # Cache is outside the source fixture directory and removed when finished.
        import tempfile
        with tempfile.TemporaryDirectory(prefix='bie-example-sync-') as td:
            sync=prepare_sync(plan,TimedEspeakProvider(),TTSCache(td,namespace='batch004-examples'),
                  SelectionPolicy(('espeak-timed-local',),('technical_formant',),require_same_voice_code_switching=False),caption_policy=CaptionPolicy(channel='display'))
        n=sync.timeline.total_samples;rate=sync.timeline.sample_rate
        rows=[]
        if has_stems:
            t=np.arange(n)/rate
            # Three stable sine components: no copyrighted library or external media.
            bed=(.018*np.sin(2*np.pi*130.8128*t)+.012*np.sin(2*np.pi*164.8138*t)+.008*np.sin(2*np.pi*196*t))
            ramp=min(rate//4,n//4);bed[:ramp]*=np.arange(ramp)/ramp;bed[-ramp:]*=np.arange(ramp-1,-1,-1)/ramp
            cue_len=rate//12;t2=np.arange(cue_len)/rate
            cue=.035*np.sin(2*np.pi*880*t2)*(np.sin(np.pi*np.arange(cue_len)/(cue_len-1))**2)
            for asset,signal,role,start in (('bed',bed,'music',0),('cue',cue,'sfx',rate//4)):
                p=MixBuffer.from_array(signal[:,None],rate);data=p.to_wav();file=asset+'.wav';(folder/file).write_bytes(data)
                s=Stem(asset,'music' if role=='music' else 'sfx',p,start,0,p.frames,('synthetic:original-'+asset,), 'synthetic:self-generated-technical-tone')
                row={k:v for k,v in asdict(s).items() if k!='pcm'}
                row.update(path=file,sha256=hashlib.sha256(data).hexdigest(),sample_rate=rate,channels=1);rows.append(row)
        spec={'schema_version':'bie.audio.mix-spec/1','plan_fingerprint':plan.fingerprint(),'timeline_fingerprint':sync.timeline.fingerprint(),
              'policy':asdict(MixPolicy()),'stems':rows}
        (folder/'mix.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
        if has_animation:(folder/'sync.json').write_bytes((ROOT/'examples/audio_batch003/scene_animation_pause.spec.json').read_bytes())
        reports.append({'case':name,'profile':profile,'animation':has_animation,'frames':n,'sample_rate':rate,
                        'plan_fingerprint':plan.fingerprint(),'source_timeline_fingerprint':sync.timeline.fingerprint()})
    (destination/'CASES.json').write_text(json.dumps({'schema_version':'bie.audio.mix-fixtures/1','cases':reports,
        'scope':'synthetic local eSpeak/tone fixtures; not real-book or production-music acceptance','product_accepted':False},indent=2)+'\n')
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(build(a.output),indent=2))
