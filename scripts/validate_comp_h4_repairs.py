#!/usr/bin/env python3
"""Replay synthetic H4 repairs with real Chromium / explicit API doubles.

This is a diagnostic layout benchmark, never actual Remotion or book acceptance.
Every measured candidate covers all its frames. Only selected screenshot frames
are saved. Failure cases and successful transformations are both retained.
"""
from pathlib import Path
from dataclasses import replace,asdict
from copy import deepcopy
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT)]
from bie.compiler.layout_repair import _run_candidates,repair_and_publish,verify_repaired_workspace
from bie.compiler.layout_browser import ChromiumLayoutProbe
from bie.compiler.layout_repair_contracts import default_policy,canonical_scene
from bie.compiler.qa_common import digest
from bie.compiler.hardened_scene_compile import publish_h3_scene
from tests.compiler.h4_test_support import text_case,map_case,equation_case,scene,track,TARGET_BIG


def cases():
    rows=[]
    def add(name,pair,status='LOCAL_MEASURED_CANDIDATE',required=()):
        p,q=pair;rows.append({'case_id':name,'document':p,'policy':q,'expected_status':status,'required_codes':list(required),'target':asdict(TARGET_BIG)})
    add('paragraph-space-repair',text_case(),required=('LAYOUT_CONTENT_OVERFLOW',))
    add('long-legend-reflow',map_case(),required=('LAYOUT_TEXT_OUTSIDE_OWNER',))
    add('equation-space-repair',equation_case(),required=('LAYOUT_EQUATION_BELOW_MINIMUM',))
    p,q=map_case();p['elements'][0]['props']['layers'][0]['label']='W'*76;p['elements'][0]['props']['layers'][2]['label']='Another distinct route';q=default_policy(p)
    add('within-owner-legend-collision',(p,q),required=('LAYOUT_OWNER_TEXT_COLLISION',))
    add('no-space-upstream-revision',text_case('Preserve every word. '*100,expand=False),'UPSTREAM_REVISION_REQUIRED',('LAYOUT_CONTENT_OVERFLOW',))
    add('multilingual-literal-content',text_case('क्षेत्र = 2 m²\nرقبہ = 2 m²\nLiteral {x} and <tag> remain text.'))
    p=scene('text',{'text':'First unchanged explanation'});p['scene_id']='h4-two-owner-relocation'
    p['elements'][0]['normalized_box']={'x':.1,'y':.1,'width':.3,'height':.15}
    e=deepcopy(p['elements'][0]);e['element_id']='second';e['props']['text']='Second unchanged explanation';e['normalized_box']['x']=.3;p['elements'].append(e)
    q=default_policy(p);q['max_candidates']=32;q['owners']['second']['region']={'x':.3,'y':.1,'width':.65,'height':.3}
    add('authorized-owner-relocation',(p,q),required=('LAYOUT_UNDECLARED_OVERLAP',))
    p,q=text_case();p['scene_id']='h4-motion-preserved';p['tracks']=[track('transform',{'from':{'translate_x':0},'to':{'translate_x':40}},track_id='h4move',element_id='e0',source_refs=['fixture:h3'],reasoning_refs=['reasoning:h3'])];q['scene_identity']=digest(canonical_scene(p))
    add('frame-driven-repair-preserves-track',(p,q),required=('LAYOUT_CONTENT_OVERFLOW',))
    return rows


def run(output,browser):
    if output.exists():raise ValueError('new evidence directory required')
    output.mkdir(parents=True)
    data=cases();(output/'CORPUS.json').write_text(json.dumps({'schema_version':'bie.comp-h4-fixtures.v1','cases':data,'accepted':False},indent=2,ensure_ascii=False))
    results=[]
    with ChromiumLayoutProbe(browser) as probe:
        for case in data:
            folder=output/case['case_id'];folder.mkdir()
            result,selected=_run_candidates(case['document'],case['policy'],TARGET_BIG,probe,folder,screenshots=True)
            codes={code for row in result['attempts'] for code in row['codes']}
            match=result['status']==case['expected_status'] and set(case['required_codes'])<=codes
            if selected is not None:
                destination=folder/'selected-source'
                receipt=publish_h3_scene(selected,destination,target=TARGET_BIG)
                if receipt.manifest_sha256!=result['selected_source_receipt']['manifest_sha256']:raise ValueError('source changed after measurements')
            results.append({'case_id':case['case_id'],'expected_status':case['expected_status'],'observed_status':result['status'],
                            'expectation_matched':match,'required_codes':case['required_codes'],'observed_codes':sorted(codes),
                            'selected_index':result['selected_index'],'attempts':result['attempt_count'],
                            'measured_frames':sum(json.loads((folder/r['measurement_path']).read_text())['frame_count'] for r in result['attempts'] if 'measurement_path' in r),
                            'element_frame_records':sum(r.get('records_checked',0) for r in result['attempts']),
                            'screenshots':sum(len(json.loads((folder/r['measurement_path']).read_text())['screenshots']) for r in result['attempts'] if 'measurement_path' in r),
                            'selected_source_manifest':result['selected_source_receipt']['manifest_sha256'] if selected else None})
            print(case['case_id'],result['status'],'matched='+str(match),flush=True)
    report={'schema_version':'bie.comp-h4-repair-benchmark.v1','scope':'REAL_CHROMIUM_DIAGNOSTIC_REPAIR_WITH_EXPLICIT_REACT_REMOTION_DOUBLES',
            'case_count':len(results),'cases':results,'expectations_matched':all(r['expectation_matched'] for r in results),
            'measured_frames':sum(r['measured_frames'] for r in results),'element_frame_records':sum(r['element_frame_records'] for r in results),
            'screenshots':sum(r['screenshots'] for r in results),'source_repair_cases':sum(r['observed_status']=='LOCAL_MEASURED_CANDIDATE' for r in results),
            'upstream_revision_cases':sum(r['observed_status']=='UPSTREAM_REVISION_REQUIRED' for r in results),
            'real_react':False,'real_remotion':False,'real_book_e2e':'NOT_RUN','release_authorized':False,'accepted':False}
    (output/'BENCHMARK.json').write_text(json.dumps(report,indent=2));return 0 if report['expectations_matched'] else 2

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--browser',default='/usr/bin/chromium');args=p.parse_args();raise SystemExit(run(args.output,args.browser))
