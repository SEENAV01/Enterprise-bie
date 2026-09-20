#!/usr/bin/env python3
"""H11 source-media diagnostic: genuine asset bytes, TS and native Chromium.

Not React/Remotion execution. Audio is never played. Fixed technical fixtures,
not textbooks. Separate FFmpeg-decoded pixel samples check native video seeking.
"""
from pathlib import Path
from dataclasses import asdict
from copy import deepcopy
import argparse,json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT)]
from tests.compiler.h11_test_support import scene,T,ASSET_ROOT
from tests.compiler.h10_test_support import bind
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene,require_h3_workspace
from bie.compiler.visual_assets import plan_visual_assets,verified_visual_bytes
from bie.compiler.media_presentation import media_presentations,source_video_frame
from bie.compiler.layout_browser import ChromiumLayoutProbe
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.qa_common import digest


def cases():
    docs={k:scene(k) for k in ('full-image','crop-image','trim-video')}
    docs['state-video']=bind(scene('trim-video'),consent=False)
    p=scene('crop-image');p['scene_id']='H11_COMBINED';p['elements'][0]['normalized_box']={'x':.04,'y':.18,'width':.42,'height':.6}
    v=scene('trim-video');e=v['elements'][0];e['element_id']='video';e['normalized_box']={'x':.54,'y':.18,'width':.42,'height':.6}
    p['elements'].append(e);p['metadata']['compiler_media_v1']['assets'].extend(v['metadata']['compiler_media_v1']['assets']);docs['combined']=p
    return docs


def worker(cid):
    d=cases()[cid];r=compile_h3_scene(d,target=T)
    return {'case_id':cid,'source_gate_passed':r.receipt.source_gate_passed,'manifest_sha256':r.codegen.manifest_sha256,
            'files':{f.path:f.sha256 for f in r.codegen.files},'findings':[f.code for f in r.receipt.findings]}


def native_reference(report,doc):
    rows=media_presentations(doc,T)['rows'];results=[]
    # Four a-priori point positions away from fixture marker; max channel error
    # <= 5 (8-bit) tolerates documented native-vs-FFmpeg YUV conversion rounding.
    for r in rows:
        if r['kind']!='video':continue
        a=r['asset'];m=a['media'];p=ASSET_ROOT/a['public_path'];w,h=m['width'],m['height'];count=m['frame_count']
        command=['ffmpeg','-v','error','-i',str(p),'-an','-frames:v',str(count),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']
        run=subprocess.run(command,capture_output=True,timeout=40)
        if run.returncode or len(run.stdout)!=w*h*3*count:raise ValueError('REFERENCE_DECODE_FAILED: '+run.stderr.decode(errors='replace')[:500])
        diffs=[];times=[];n=0
        for record in report['native_media_observations']:
            index=source_video_frame(r['presentation'],record['frame'])
            matches=[o for o in record['media'] if o['kind']=='video' and o['source']=='/'+a['public_path']]
            if index is None:
                if matches:raise ValueError('NATIVE_VIDEO_OUTSIDE_DECLARED_WINDOW')
                continue
            if len(matches)!=1:raise ValueError('NATIVE_VIDEO_OBSERVATION_MISSING')
            o=matches[0];times.append(abs(o['current_time']-o['requested_time']))
            for point in o['samples']:
                offset=(index*w*h+point['y']*w+point['x'])*3
                diffs.extend(abs(x-y) for x,y in zip(point['rgb'],run.stdout[offset:offset+3]));n+=1
        results.append({'element_id':r['element_id'],'sampled_points':n,'rgb_channel_comparisons':len(diffs),'max_abs_channel_error':max(diffs,default=0),
            'max_seek_time_error_seconds':max(times,default=0),'threshold_channel_error':5,'threshold_seek_time_error_seconds':1e-6,
            'ffmpeg_decoded_rgb_sha256':hashlib.sha256(run.stdout).hexdigest(),'asset_sha256':a['sha256'],
            'passed':bool(n) and max(diffs)<=5 and max(times)<=1e-6,'scope':'NATIVE_BROWSER_VS_FFMPEG_FIXED_FIXTURE_POINTS_NOT_REMOTION_OR_WHOLE_FRAME_QUALITY'})
    return results


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker');ap.add_argument('--output',type=Path);ap.add_argument('--browser',action='store_true');a=ap.parse_args()
    if a.worker:print(json.dumps(worker(a.worker),sort_keys=True));return 0
    if a.output is None or a.output.exists():ap.error('--output must be a new directory')
    a.output.mkdir(parents=True);docs=cases();source=[];brows=[];all_native=[]
    for cid,doc in docs.items():
        root=a.output/cid;root.mkdir();(root/'SCENE.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False))
        workers=[]
        for i in range(2):
            child=subprocess.run([sys.executable,__file__,'--worker',cid],capture_output=True,text=True,cwd=ROOT,timeout=120)
            if child.returncode:raise ValueError(child.stderr)
            workers.append(json.loads(child.stdout))
        (root/'WORKERS.json').write_text(json.dumps(workers,indent=2))
        source.append({'case_id':cid,'passed':workers[0]['source_gate_passed'] and workers[0]==workers[1],'manifest_sha256':workers[0]['manifest_sha256'],'workers':2})
    if a.browser:
        with ChromiumLayoutProbe() as probe:
            for cid,doc in docs.items():
                root=a.output/cid;r=compile_h3_scene(doc,target=T);assets,receipt=verified_visual_bytes(doc,ASSET_ROOT)
                (root/'BYTE_VERIFICATION.json').write_text(json.dumps(receipt,indent=2))
                report=probe.measure(r,T,root/'browser',screenshots=True,asset_bytes=assets)
                fit=inspect_owner_fit(report,r.effective_document,T,r.codegen.manifest_sha256);(root/'FIT.json').write_text(json.dumps(fit,indent=2))
                native=native_reference(report,doc);all_native.extend(native)
                (root/'NATIVE_VIDEO_REFERENCE.json').write_text(json.dumps(native,indent=2))
                brows.append({'case_id':cid,'fit_passed':fit['passed'],'findings':fit['findings'],'frames':report['frame_count'],'element_frame_records':len(report['records']),
                              'screenshots':len(report['screenshots']),'errors':report['browser_errors'],'native_media_frame_records':len(report['native_media_observations']),
                              'native_reference':native,'producer':report['producer']})
                print(cid,fit['passed'],[x['max_abs_channel_error'] for x in native],flush=True)
    r=publish_h3_scene(docs['combined'],a.output/'published',target=T,asset_root=ASSET_ROOT)
    require_h3_workspace(a.output/'published')
    report={'schema_version':'bie.h11-media-diagnostic.v1','source_cases':source,'source_processes':len(source)*2,'browser_cases':brows,
            'frames':sum(r['frames'] for r in brows),'element_frame_records':sum(r['element_frame_records'] for r in brows),
            'screenshots':sum(r['screenshots'] for r in brows),'native_video_reference':all_native,'publication_passed':r.source_gate_passed,
            'passed':all(r['passed'] for r in source) and all(r['fit_passed'] and not r['errors'] for r in brows) and all(r['passed'] for r in all_native),
            'scope':'REAL_TS_API_DOUBLES_NATIVE_CHROMIUM_AND_ACTUAL_ASSET_BYTES','react_remotion_doubles':True,'actual_remotion_render':False,
            'audio_playback':False,'full_pixel_qa':False,'real_book_e2e':False,'accepted':False}
    (a.output/'RESULT.json').write_text(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
