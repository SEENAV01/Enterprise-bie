#!/usr/bin/env python3
"""Repeatable H9 diagnostic: real Chromium, explicit React/Remotion API doubles.
Does not install dependencies, authorize release, or treat diagnostics as a render.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import asdict,replace
from copy import deepcopy
import argparse,json,sys,subprocess
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'app')]
from tests.compiler.h9_test_support import shape_scene,diagram_scene,highlight_scene,action_scene,T
from bie.compiler.registered_actions import ACTIONS
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene
from bie.compiler.layout_browser import ChromiumLayoutProbe
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.consumer_coverage import inspect_consumer_coverage
from bie.compiler.frame_layout import dimensions

BIG=replace(T,width=1280,height=720)
def cases():
    docs=[('shape-'+k,shape_scene(k)) for k in ('rectangle','circle','ellipse','line','polygon','polyline','arrow')]
    docs += [('diagram',diagram_scene())]
    docs += [('highlight-'+m,highlight_scene(m,moving=True)) for m in ('outline','fill','spotlight','underline')]
    for action in sorted(ACTIONS):
        p=action_scene(action)
        if action=='static_focus':
            q=p['tracks'][0]['parameters'];q['viewport']={'width':1024,'height':504};q['pose']={'focus_x':512,'focus_y':252,'zoom':1}
        elif action=='path_endpoints_with_progress_marker':
            # Independently declared larger-target fixture. Never a runtime auto-rescale.
            q=p['tracks'][0]['parameters'];q['viewport']={'width':960,'height':576}
            q['points']=[[128,176],[480,368],[784,128]]
            p['elements'][0]['props']['geometry']={'view_box':[0,0,960,576],'points':deepcopy(q['points'])}
        docs.append((action,p))
    return docs

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output
    if out.exists():raise ValueError('OUTPUT_EXISTS')
    out.mkdir(parents=True);rows=[]
    with ChromiumLayoutProbe() as probe:
        for cid,doc in cases():
            root=out/cid;root.mkdir();(root/'SCENE.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False))
            result=compile_h3_scene(doc,target=BIG)
            (root/'SOURCE_RECEIPT.json').write_text(json.dumps(asdict(result.receipt),indent=2))
            if not result.receipt.source_gate_passed:raise ValueError(f'{cid}: source rejected {result.receipt.findings}')
            measured=probe.measure(result,BIG,root/'browser',screenshots=True)
            fit=inspect_owner_fit(measured,result.effective_document,BIG,result.codegen.manifest_sha256)
            (root/'FIT.json').write_text(json.dumps(fit,indent=2,ensure_ascii=False))
            rows.append({'case_id':cid,'source_passed':True,'fit_passed':fit['passed'],'fit_findings':fit['findings'],
                         'frames':dimensions(doc,BIG),'element_frame_records':len(measured['records']),
                         'screenshots':len(measured['screenshots']),'browser_errors':measured['browser_errors']})
            print(cid,'fit=',fit['passed'],flush=True)
    coverage=inspect_consumer_coverage();(out/'CONSUMER_COVERAGE.json').write_text(json.dumps(coverage,indent=2))
    report={'schema_version':'bie.h9.browser-diagnostic.v1','cases':rows,'case_count':len(rows),
            'frames':sum(x['frames'] for x in rows),'element_frame_records':sum(x['element_frame_records'] for x in rows),
            'screenshots':sum(x['screenshots'] for x in rows),'fit_passed_cases':sum(x['fit_passed'] for x in rows),
            'scope':'REAL_CHROMIUM_WITH_EXPLICIT_REACT_REMOTION_API_DOUBLES','real_react':False,'real_remotion':False,
            'actual_video_rendered':False,'pixel_qa_executed':False,'accepted':False}
    (out/'RESULT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    # A technical fit failure is recorded as such, never converted into a success.
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
