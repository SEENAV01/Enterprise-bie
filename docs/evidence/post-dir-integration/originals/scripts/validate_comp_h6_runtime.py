#!/usr/bin/env python3
"""Synthetic H6 source/DOM/PCM validation, explicitly not real Remotion or speech."""
from pathlib import Path
import argparse, json, sys
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from tests.compiler.h6_test_support import state_scene,narration_scene,execute,nodes,BIG,write_assets
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.frame_runtime_contract import plan_frame_runtime
from bie.compiler.frame_state_consumer import runtime_at
from bie.compiler.layout_browser import ChromiumLayoutProbe
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.narration_assets import verified_asset_bytes
from bie.compiler.narration_consumer import cue_schedule


def cases():
    p,a=narration_scene()
    hidden=state_scene();hidden['metadata']['compiler_h6']['initial_state']['lesson.phase']=True
    hidden['state_bindings'][0]['property_name']='visible';hidden['events']=[hidden['events'][0]];hidden['events'][0]['payload']['value']=False
    shifted=deepcopy(p);shifted['narration_cues'][0]['start_ms']=251;shifted['narration_cues'][0]['end_ms']=1001
    shifted['narration_cues'][1]['start_ms']=1251
    for seg in shifted['metadata']['compiler_h6']['audio_segments']:seg['trim_before_frames']=5
    overflow=state_scene();overflow['events'][0]['payload']['value']='This source-bound late state needs more layout space. '*200
    return [('state-events',state_scene(),{},True),('narration-captions',p,a,True),('explicit-visibility',hidden,{},True),
            ('shifted-trimmed-narration',shifted,a,True),('late-overflow-negative',overflow,{},False)]


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--chromium',default='/usr/bin/chromium');args=ap.parse_args()
    if args.output.exists():raise ValueError('Output must be fresh')
    args.output.mkdir(parents=True);results=[]
    with ChromiumLayoutProbe(args.chromium) as probe:
        for cid,p,assets,expected_fit in cases():
            out=args.output/cid;out.mkdir();(out/'SCENE.json').write_text(json.dumps(p,indent=2,ensure_ascii=False))
            r=compile_h3_scene(p,target=BIG);plan=plan_frame_runtime(r.effective_document,BIG)
            if not r.receipt.source_gate_passed:raise ValueError('Source failed '+cid)
            data=execute(r);all_match=True;audio_records=0
            for row in data['trees']:
                if row['state']!=runtime_at(plan,row['frame']):raise ValueError('Python/JS frame mismatch '+cid)
                played=[n['props'] for n in nodes(row['tree']) if n.get('props',{}).get('data-bie-test-audio')]
                if len(played)!=len(row['state']['active_cue_ids']):raise ValueError('Audio schedule mismatch')
                for voice in played:
                    c=next(c for c in plan['narration'] if c['cue_id']==row['state']['active_cue_ids'][0])
                    if voice['data-source-frame']!=c['trim_before_frames']+row['frame']-c['start_frame']:raise ValueError('Trim/sequence time mismatch')
                    audio_records+=1
            (out/'FRAME_SEMANTICS.json').write_text(json.dumps(data,ensure_ascii=False))
            asset_root=write_assets(out/'asset-inputs',assets) if assets else None
            _,ar=verified_asset_bytes(plan,asset_root)
            (out/'ASSET_VERIFICATION.json').write_text(json.dumps(ar,indent=2));(out/'CUE_SCHEDULE.json').write_text(json.dumps(cue_schedule(plan),indent=2,ensure_ascii=False))
            measurement=probe.measure(r,BIG,out/'browser',screenshots=True)
            fit=inspect_owner_fit(measurement,r.effective_document,BIG,r.codegen.manifest_sha256)
            (out/'FIT.json').write_text(json.dumps(fit,indent=2))
            results.append({'case_id':cid,'source_passed':True,'expected_fit':expected_fit,'fit_passed':fit['passed'],
                'expectation_matched':fit['passed']==expected_fit,'findings':fit['findings'],'frames':len(data['trees']),
                'element_frame_records':len(measurement['records']),'audio_component_frame_records':audio_records,
                'frame_semantics_match':all_match,'screenshots':len(measurement['screenshots']),
                'manifest_sha256':r.codegen.manifest_sha256,'plan_sha256':plan['plan_sha256']})
    report={'schema_version':'bie.comp-h6-browser.v1','scope':'REAL_CHROMIUM_AND_REAL_TS_EXECUTION_WITH_EXPLICIT_REACT_REMOTION_API_DOUBLES',
      'cases':results,'all_expectations_matched':all(r['expectation_matched'] for r in results),'frames':sum(r['frames'] for r in results),
      'element_frame_records':sum(r['element_frame_records'] for r in results),'audio_component_frame_records':sum(r['audio_component_frame_records'] for r in results),
      'screenshots':sum(r['screenshots'] for r in results),'real_react':False,'real_remotion':False,'audio_played':False,
      'speech_text_alignment':'NOT_VERIFIED','accepted':False}
    (args.output/'RESULT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report['all_expectations_matched'] else 2
if __name__=='__main__':raise SystemExit(main())
