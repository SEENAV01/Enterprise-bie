#!/usr/bin/env python3
"""Real WAVs + native inspection + independent-process repeatability; no acceptance."""
from pathlib import Path
import argparse,copy,hashlib,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'));sys.path.insert(0,str(ROOT/'scripts'))
from verify_audio_mix_output import check

def run(output):
    if output.exists():raise ValueError('BENCHMARK_OUTPUT_EXISTS')
    output.mkdir(parents=True)
    cases=json.loads((ROOT/'examples/audio_batch004/CASES.json').read_text())['cases'];results=[];commands=[]
    def cli(src,dest,profile,cache,animation):
        argv=[sys.executable,'-B',str(ROOT/'scripts/audio_mix.py'),str(src/'narration.json'),
              '--mix-spec',str(src/'mix.json'),'--profile',profile,'--output',str(dest),'--cache',str(cache),
              '--cache-namespace','mix-benchmark','--allow-technical-voice','--standalone-fixture']
        if animation:argv+=['--sync-spec',str(src/'sync.json')]
        start=time.monotonic();p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,timeout=90,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        name=dest.name;log={'argv':argv,'returncode':p.returncode,'duration_seconds':time.monotonic()-start,'stdout':p.stdout,'stderr':p.stderr}
        (output/(name+'_EXECUTION.json')).write_text(json.dumps(log,indent=2));commands.append(log)
        return p
    for case in cases:
        name=case['case'];src=ROOT/'examples/audio_batch004'/name;runs=[]
        for i in range(3):
            cache=output/(name+'-cache-'+str(0 if i==2 else i));dest=output/(name+'-run-'+str(i))
            p=cli(src,dest,case['profile'],cache,case['animation'])
            if p.returncode:raise ValueError('NATIVE_CASE_FAILED:'+name+':'+p.stderr)
            verified=check(dest);(output/(dest.name+'_NATIVE_VERIFICATION.json')).write_text(json.dumps(verified,indent=2))
            sync=json.loads((dest/'SOURCE_SYNC.json').read_text());clock=json.loads((dest/'MIX_CLOCK.json').read_text())
            row={'run':i,'verified':verified,'hashes':{f:hashlib.sha256((dest/f).read_bytes()).hexdigest() for f in ('source.wav','master.wav','MIX_CLOCK.json','captions.vtt','captions.srt')},
                 'source_cache_hits':sync['cache_hits'],'source_segments':len(sync['speech_receipts']),'timing_replay_calls':sync['engine_replay_calls'],
                 'tts_generation_calls':sum(not x for x in sync['cache_hits'])}
            runs.append(row)
        if not all(r['hashes']==runs[0]['hashes'] for r in runs):raise ValueError('PROCESS_OUTPUT_MISMATCH:'+name)
        if runs[2]['tts_generation_calls']!=0 or runs[2]['timing_replay_calls']<=0:raise ValueError('CACHE_BOUNDARY_MISMATCH')
        results.append({'case':name,'status':'PASS','runs':runs,'scope':'audio/caption/clock repeatability only; receipts retain changing cache/execution provenance'})
    negatives=[];original=ROOT/'examples/audio_batch004/english-mix'
    for name in ('tampered-stem','stale-timeline','sfx-over-pause'):
        src=output/(name+'-input');shutil.copytree(original,src);spec=json.loads((src/'mix.json').read_text())
        expected={'tampered-stem':'MIX_ASSET_HASH','stale-timeline':'MIX_SPEC_STALE','sfx-over-pause':'SFX_OVER_REQUIRED_SILENCE'}[name]
        if name=='tampered-stem':
            p=src/'cue.wav';b=bytearray(p.read_bytes());b[-2]^=1;p.write_bytes(b)
        elif name=='stale-timeline':spec['timeline_fingerprint']='sha256:'+'0'*64
        else:
            baseline=json.loads((output/'english-mix-run-0/MIX_CLOCK.json').read_text())
            spec['stems'][1]['start_sample']=baseline['pauses'][0]['start_sample']+baseline['source_start_sample']
        (src/'mix.json').write_text(json.dumps(spec));dest=output/(name+'-should-not-exist')
        p=cli(src,dest,'batch001-144',output/'english-mix-cache-0',True)
        ok=p.returncode==2 and expected in p.stderr and not dest.exists()
        if not ok:raise ValueError('NEGATIVE_EXPECTATION_FAILED:'+name+':'+p.stderr)
        negatives.append({'case':name,'expected_code':expected,'returncode':p.returncode,'output_directory_exists':dest.exists(),'passed':ok})
    for p in output.glob('*-cache-*'):shutil.rmtree(p)
    report={'schema_version':'bie.audio.mix-native-benchmark/1','positive_cases':len(results),'independent_positive_cli_processes':sum(len(r['runs']) for r in results),
            'negative_cli_cases':negatives,'cases':results,'all_expectations_matched':True,'ffmpeg_version':subprocess.check_output(['ffmpeg','-version'],text=True),
            'python':sys.version,'platform':sys.platform,'full_enterprise_regression_rerun':False,'human_listening_verified':False,
            'actual_remotion_render_verified':False,'product_accepted':False}
    (output/'BENCHMARK.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return {'positive_cases':len(results),'positive_processes':report['independent_positive_cli_processes'],'negative_cases':len(negatives),'passed':True}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output',type=Path);args=a.parse_args();print(json.dumps(run(args.output),indent=2))
