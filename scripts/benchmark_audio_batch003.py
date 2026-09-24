#!/usr/bin/env python3
"""Fixed synthetic-text real TTS/timing repetitions. No acoustic/lesson acceptance."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
COMPARE=('speech.wav','captions.vtt','captions.srt','WORD_TIMINGS.json','SCENE_SYNC.json','PAUSE_SYNC.json','ANIMATION_SYNC.json')

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    cases=[('english','batch001-144',()),('hindi','batch001-144',()),('mixed','batch001-144',('--language-terms',str(ROOT/'examples/audio_batch002/mixed_terms.json'))),
           ('compat204','batch001-204',()),('multiscene','batch001-144',('--sync-spec',str(ROOT/'examples/audio_batch003/scene_animation_pause.spec.json')))]
    records=[];began=time.monotonic()
    for name,profile,extra in cases:
        path=ROOT/('examples/audio_batch003/scene_animation_pause.json' if name=='multiscene' else f'examples/audio_batch002/{name}.json')
        runs=[]
        for n in (1,2,3):
            out=args.output/f'{name}-{n}';cache=args.output/f'cache-{name}-{2 if n==3 else n}'
            cmd=[sys.executable,str(ROOT/'scripts/audio_sync.py'),str(path),'--output',str(out),'--profile',profile,
                 '--cache',str(cache),'--cache-namespace','batch003-evidence','--allow-technical-voice','--standalone-fixture',*extra]
            p=subprocess.run(cmd,capture_output=True,text=True,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=90)
            (args.output/f'{name}-{n}.log').write_text(p.stdout+'\n'+p.stderr)
            if p.returncode:raise RuntimeError(f'{name}-{n}: {p.stderr}')
            summary=json.loads(p.stdout);digests={f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in COMPARE}
            checks=json.loads((out/'OUTPUT_SHA256.json').read_text())
            assert all(hashlib.sha256((out/f).read_bytes()).hexdigest()==h for f,h in checks.items())
            runs.append({'run':n,'result':summary,'hashes':digests})
        assert runs[0]['hashes']==runs[1]['hashes']==runs[2]['hashes'],name+' repeatability'
        assert runs[2]['result']['tts_generation_calls']==0 and runs[2]['result']['cache_hits']==runs[2]['result']['segments']
        assert runs[2]['result']['native_synthesis_calls_including_replay']>0
        records.append({'case':name,'scope':'SYNTHETIC_TEXT_REAL_NATIVE_SPEECH','repeatability_passed':True,'runs':runs})
    result={'schema_version':'bie.audio.sync-benchmark/1','cases':records,'case_count':len(records),'independent_cli_processes':len(records)*3,
            'all_selected_media_timing_hashes_equal':True,'cache_hit_timing_replay_still_performed':True,'seconds':round(time.monotonic()-began,3),
            'acoustic_alignment_verified':False,'real_remotion_render_verified':False,'product_accepted':False}
    (args.output/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
