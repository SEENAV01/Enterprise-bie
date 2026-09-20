#!/usr/bin/env python3
"""Explicit SOURCE-only H9 benchmark. Never a full-dependency/render acceptance run."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from hashlib import sha256
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT)]
from bie.compiler.qa_common import digest

def worker(corpus,index):
    from bie.compiler.hardened_scene_compile import compile_h3_scene
    from bie.compiler.qa_scene_compile import CompilerQATarget
    from bie.compiler.host_toolchain import collect_host_toolchain
    c=json.loads(corpus.read_text())['cases'][index]
    try:
        r=compile_h3_scene(c['document'],target=CompilerQATarget(width=1280,height=720,fps=12,compiler_version='1.3.0-comp-h3'),motion_preference='standard')
        result={'case_id':c['case_id'],'source_passed':r.receipt.source_gate_passed,'codes':sorted({f.code for f in r.receipt.findings if f.severity=='ERROR'}),'manifest_sha256':r.codegen.manifest_sha256,'scene_fingerprint':r.receipt.scene_fingerprint,'host_identity':r.host['identity_sha256']}
    except ValueError as exc:
        result={'case_id':c['case_id'],'source_passed':False,'codes':[str(exc).split(':',1)[0]],'host_identity':collect_host_toolchain()['identity_sha256']}
    print(json.dumps(result,sort_keys=True))

def run(corpus,output,runs):
    data=json.loads(corpus.read_text());cases=data['cases']
    if not 2<=runs<=5 or not 1<=len(cases)<=100:raise ValueError('bounded fixture/run count required')
    if output.exists():raise ValueError('evidence output must be new')
    output.mkdir(parents=True)
    def invoke(job):
        i,n=job;start=time.monotonic();env={**os.environ,'PYTHONHASHSEED':str(n+10)}
        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--corpus',str(corpus),'--worker',str(i)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
        if p.returncode:raise RuntimeError('Worker failed for '+cases[i]['case_id']+': '+p.stderr[-4000:])
        result=json.loads(p.stdout);return {'case_index':i,'repetition':n,'child_exit':p.returncode,'elapsed_seconds':time.monotonic()-start,'observation':result,'observation_sha256':digest(result)}
    with ThreadPoolExecutor(max_workers=3) as pool:jobs=list(pool.map(invoke,[(i,n) for i in range(len(cases)) for n in range(runs)]))
    rows=[]
    for i,c in enumerate(cases):
        obs=[j for j in jobs if j['case_index']==i];r=obs[0]['observation'];det=len({j['observation_sha256'] for j in obs})==1
        match=r['source_passed']==c['expected_source_pass'] and set(([c['expected_error']] if c.get('expected_error') else []))==set(r['codes'])
        rows.append({'case_id':c['case_id'],'expected_source_pass':c['expected_source_pass'],'expected_codes':([c['expected_error']] if c.get('expected_error') else []),'source_expectation_matched':match,'independent_process_determinism_matched':det,'observations':obs})
    out={'schema_version':'bie.h9-source-benchmark.v1','scope':'SYNTHETIC_SOURCE_GENERATION_NOT_DEPENDENCY_COMPILE_OR_RENDER','corpus_sha256':sha256(corpus.read_bytes()).hexdigest(),'runner_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'case_count':len(cases),'independent_worker_executions':len(jobs),'runs_per_case':runs,'cases':rows,'source_expectations_matched':all(r['source_expectation_matched'] for r in rows),'determinism_matched':all(r['independent_process_determinism_matched'] for r in rows),'full_dependency_compile':'NOT_RUN_BY_THIS_SOURCE_BENCHMARK','real_remotion':'NOT_RUN','real_book':'NOT_RUN','accepted':False}
    (output/'SOURCE_BENCHMARK.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='cases'},indent=2));return 0 if out['source_expectations_matched'] and out['determinism_matched'] else 2

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,default=ROOT/'fixtures/comp_h9/corpus.json');p.add_argument('--output',type=Path);p.add_argument('--runs',type=int,default=3);p.add_argument('--worker',type=int);a=p.parse_args()
    if a.worker is not None:worker(a.corpus,a.worker);return 0
    if a.output is None:p.error('--output required')
    return run(a.corpus,a.output,a.runs)
if __name__=='__main__':raise SystemExit(main())
