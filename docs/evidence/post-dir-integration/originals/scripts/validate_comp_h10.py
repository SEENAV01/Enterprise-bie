#!/usr/bin/env python3
"""Finite H10 combination matrix and independent-process source repeatability.
Actual generated TS is executed with explicit API doubles. Optional Chromium
checks are diagnostics, not actual Remotion rendering or educational acceptance.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,json,subprocess,sys
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'app')]
from tests.compiler.h10_test_support import composed_scene,bind,T,native_request
from tests.compiler.h9_test_support import highlight_scene
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.composition_conformance import verify_composition
from bie.compiler.layout_browser import ChromiumLayoutProbe
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.qa_common import digest
from bie.compiler.artifact_hashing import canonical_json

ACTIONS=('enter','exit','reveal','emphasize','transform','path_follow','camera','morph','trace',
         'static_focus','static_trace','progressive_static_trace','crossfade_states','simulation_state',
         'state_snapshots','path_endpoints_with_progress_marker')

def cases():
    result={a:composed_scene(a) for a in ACTIONS}
    for a in ('trace','simulation_state','transform'):result[a+'-opacity']=composed_scene(a,('opacity',))
    result['text-and-controls']=composed_scene('transform',('text','visible'))
    result['highlight-and-motion']=bind(highlight_scene(moving=True))
    return result

def worker(case_id):
    r=compile_h3_scene(cases()[case_id],target=T)
    return {'case_id':case_id,'source_passed':r.receipt.source_gate_passed,'manifest_sha256':r.codegen.manifest_sha256,
            'file_hashes':{f.path:f.sha256 for f in r.codegen.files},'findings':[f.code for f in r.receipt.findings]}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker');ap.add_argument('--output',type=Path);ap.add_argument('--browser',action='store_true');a=ap.parse_args()
    if a.worker:
        print(json.dumps(worker(a.worker),sort_keys=True));return 0
    if a.output is None:ap.error('--output required')
    out=a.output
    if out.exists():ap.error('output must be new')
    out.mkdir(parents=True);rows=[]
    documents=cases()
    for cid,doc in documents.items():
        root=out/cid;root.mkdir();(root/'SCENE.json').write_bytes(canonical_json(doc))
        r=compile_h3_scene(doc,target=T);conf=verify_composition(r,T)
        (root/'CONFORMANCE.json').write_text(json.dumps(conf,indent=2))
        workers=[]
        for repeat in range(2):
            run=subprocess.run([sys.executable,__file__,'--worker',cid],cwd=ROOT,capture_output=True,text=True,timeout=120)
            if run.returncode:raise RuntimeError(run.stderr)
            workers.append(json.loads(run.stdout))
        (root/'WORKERS.json').write_text(json.dumps(workers,indent=2))
        row={'case_id':cid,'source_passed':r.receipt.source_gate_passed,'conformance_passed':conf['passed'],
             'source_repeatable':workers[0]==workers[1], 'frame_executions':conf['executions'],
             'unique_frames':conf['unique_frames'],'control_records':len(conf['records']),
             'findings':conf['findings'],'scene_sha256':digest(doc)}
        rows.append(row);print(cid,row['conformance_passed'],flush=True)
    brows=[]
    if a.browser:
        with ChromiumLayoutProbe() as probe:
            for cid in ('trace','morph','trace-opacity','text-and-controls','highlight-and-motion'):
                r=compile_h3_scene(documents[cid],target=T);root=out/cid
                measured=probe.measure(r,T,root/'browser',screenshots=True)
                fit=inspect_owner_fit(measured,r.effective_document,T,r.codegen.manifest_sha256)
                (root/'BROWSER_FIT.json').write_text(json.dumps(fit,indent=2))
                brows.append({'case_id':cid,'fit_passed':fit['passed'],'findings':fit['findings'],
                     'frames':measured['frame_count'],'records':len(measured['records']),
                     'screenshots':len(measured['screenshots']),'errors':measured['browser_errors']})
                print('browser',cid,fit['passed'],flush=True)
    report={'schema_version':'bie.h10-combination-matrix.v1','cases':rows,'case_count':len(rows),
            'independent_generator_processes':2*len(rows),'frame_executions':sum(r['frame_executions'] for r in rows),
            'control_records':sum(r['control_records'] for r in rows),'browser_cases':brows,
            'passed':all(r['source_passed'] and r['conformance_passed'] and r['source_repeatable'] for r in rows)
                and all(b['fit_passed'] for b in brows),
            'scope':'REAL_TS_WITH_EXPLICIT_REACT_REMOTION_API_DOUBLES; OPTIONAL_REAL_CHROMIUM',
            'real_remotion':False,'actual_video_rendered':False,'educational_equivalence_verified':False,'accepted':False}
    (out/'RESULT.json').write_text(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
