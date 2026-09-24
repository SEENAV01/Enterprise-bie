#!/usr/bin/env python3
"""Four synthetic speech cases: two uncached processes and one cached process each."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);args=ap.parse_args()
    root=args.output_dir.absolute()
    if root.exists():raise SystemExit('Benchmark output already exists')
    root.mkdir(parents=True);cache=root/'cache';rows=[]
    for case in ('english','hindi','mixed','compat204'):
        trials=[]
        for trial,namespace in ((1,case+'-one'),(2,case+'-two'),(3,case+'-one')):
            output=root/(case+f'-{trial}')
            command=[sys.executable,'-B',str(ROOT/'scripts/audio_synthesize.py'),str(ROOT/f'examples/audio_batch002/{case}.json'),
                '--output',str(output),'--cache',str(cache),'--cache-namespace',namespace,'--allow-technical-voice','--standalone-fixture']
            if case=='mixed':command+=['--language-terms',str(ROOT/'examples/audio_batch002/mixed_terms.json')]
            if case=='compat204':command+=['--profile','batch001-204']
            run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=60)
            (root/(case+f'-{trial}.log')).write_text(run.stdout+run.stderr)
            if run.returncode:raise RuntimeError(run.stderr)
            report=json.loads((output/'SYNTHESIS_REPORT.json').read_text());media=report['assembled_media']
            trials.append({'trial':trial,'plan_fingerprint':report['plan_fingerprint'],'output_sha256':media['sha256'],
                'samples':media['samples_per_channel'],'sample_rate':media['sample_rate'],'peak':media['peak'],
                'provider_invocations':report['provider_invocations_this_run'],'cache_hits':sum(x['cache_hit'] for x in report['segments']),
                'source_retained':''.join(s['display_text'] for s in report['plan']['segments']),
                'runtime_fingerprint':report['selection']['personas'][0]['voice']['runtime_fingerprint']})
        stable=len({x['output_sha256'] for x in trials})==1 and len({x['plan_fingerprint'] for x in trials})==1
        hit=trials[2]['provider_invocations']==0 and trials[2]['cache_hits']>0
        rows.append({'case':case,'trials':trials,'stable_pcm':stable,'cache_hit_verified':hit})
    result={'schema_version':'bie.audio.batch002-real-benchmark/1','cases':rows,'process_executions':12,
        'passed':all(r['stable_pcm'] and r['cache_hit_verified'] for r in rows),
        'evidence':'REAL_INSTALLED_ESPEAK_FORMANT_SYNTHESIS_ON_SYNTHETIC_TEXT','neural_provider_tested':False,
        'human_listening_verified':False,'word_alignment_verified':False,'cinematic_quality_verified':False,'product_accepted':False}
    (root/'BENCHMARK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'cases':len(rows),'processes':12}))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
