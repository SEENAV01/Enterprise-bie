#!/usr/bin/env python3
"""Independent-process source reproducibility; not compile/render or book acceptance."""
from pathlib import Path
import argparse,json,subprocess,sys,os
from copy import deepcopy
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1])]
from tests.compiler.h7_test_support import *
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.qa_common import digest

def cases():
    bad=glyph_scene();bad['tracks'][0]['parameters']['glyph_pairs'][0]=[[0,0]]
    missing=reduced(trace_scene());missing['metadata']['compiler_h7']['reduced_variants'][missing['tracks'][0]['track_id']]['milestones'].pop(1)
    wrong=state_scene();wrong['events'][0]['payload']['value']=True
    return [('state',state_scene(),'standard',True),('narration',narration_scene()[0],'standard',True),('glyph',glyph_scene(),'standard',True),
            ('glyph-reduced',reduced(glyph_scene()),'reduced',True),('trace-reduced',reduced(trace_scene()),'reduced',True),('camera-reduced',reduced(camera_scene()),'reduced',True),
            ('bad-glyph-pair',bad,'standard',False),('missing-milestone',missing,'reduced',False),('wrong-state-type',wrong,'standard',False)]

def worker(cid):
    _,p,preference,expected=next(c for c in cases() if c[0]==cid)
    try:
        r=compile_h3_scene(p,target=BIG,motion_preference=preference)
        out={'case_id':cid,'passed':r.receipt.source_gate_passed,'source_sha256':digest({f.path:f.content for f in r.codegen.files}),'findings':[f.code for f in r.receipt.findings]}
    except ValueError as e:out={'case_id':cid,'passed':False,'error_code':str(e).split(':')[0]}
    print(json.dumps(out,sort_keys=True))

def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.worker:return worker(a.worker)
    if not a.output or a.output.exists():raise ValueError('new output required')
    a.output.mkdir(parents=True);rows=[]
    for cid,doc,pref,expected in cases():
        trials=[]
        for i in range(3):
            c=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',cid],env=dict(os.environ,PYTHONPATH='app',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=90)
            if c.returncode:raise ValueError(c.stderr)
            r=json.loads(c.stdout);(a.output/f'{cid}-{i}.json').write_text(json.dumps(r,indent=2));trials.append(r)
        rows.append({'case_id':cid,'expected_source_pass':expected,'expectation_matched':all(r['passed']==expected for r in trials),'repeatable':all(r==trials[0] for r in trials),'runs':trials})
    out={'schema_version':'bie.h7.source-benchmark.v1','cases':rows,'processes':len(rows)*3,'all_matched':all(r['expectation_matched'] and r['repeatable'] for r in rows),
         'scope':'INDEPENDENT_PROCESS_SOURCE_GENERATION_ONLY','real_remotion':False,'full_project_compiled':False,'accepted':False}
    (a.output/'RESULT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
