#!/usr/bin/env python3
"""H7 local validation: actual Chromium diagnostic, OS isolation and PCM producers.
API-double component execution is labelled and cannot mint an actual-render witness.
"""
from pathlib import Path
from dataclasses import asdict
import argparse,json,sys,subprocess,shutil
from copy import deepcopy
from hashlib import sha256
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1])]
from tests.compiler.h7_test_support import *
from bie.compiler.hardened_scene_compile import compile_h3_scene,publish_h3_scene
from bie.compiler.layout_repair import repair_and_publish
from bie.compiler.layout_browser import ChromiumLayoutProbe
from bie.compiler.layout_measurements import inspect_owner_fit
from bie.compiler.paint_quality import inspect_paint_quality
from bie.compiler.font_coverage import system_font_coverage
from bie.compiler.linux_worker import run_isolated,WorkerPolicy
from bie.compiler.audio_preparation import normalize_local_audio,mix_pcm_segments,asset_descriptor
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from bie.compiler.qa_common import digest
from tests.compiler.h6_test_support import wav_signal

def combined_scene():
    p,assets=narration_scene();g=glyph_scene();e=g['elements'][0];e['element_id']='equation';e['normalized_box']={'x':.1,'y':.3,'width':.8,'height':.3}
    p['elements'][0]['normalized_box']={'x':.05,'y':.04,'width':.9,'height':.2};p['elements'][1]['normalized_box']={'x':.05,'y':.73,'width':.9,'height':.22}
    p['elements'].append(e);t=g['tracks'][0];t['element_id']='equation';p['tracks']=[t]
    p['source_refs']=sorted(set(p['source_refs']+g['source_refs']));p['reasoning_refs']=sorted(set(p['reasoning_refs']+g['reasoning_refs']))
    p['metadata']['compiler_h7']=reduced(g)['metadata']['compiler_h7']
    return p,assets

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output
    if out.exists():raise ValueError('OUTPUT_EXISTS')
    out.mkdir(parents=True);results=[]
    p,assets,policy=dynamic_repair_case();root=write_assets(out/'repair-assets',assets)
    repair=repair_and_publish(p,policy,out/'repair-published',out/'repair-evidence',target=BIG,asset_root=root,screenshots=True)
    (out/'REPAIR.json').write_text(json.dumps(repair,indent=2,ensure_ascii=False))
    if not repair['source_published']:raise ValueError('dynamic asset repair failed')
    combined,assets=combined_scene()
    cases=[('glyph-matched',glyph_scene(),'standard'),('glyph-reduced',reduced(glyph_scene()),'reduced'),
           ('camera-reduced',reduced(camera_scene()),'reduced'),('trace-reduced',reduced(trace_scene()),'reduced'),
           ('state-captions',narration_scene()[0],'standard'),('combined',combined,'standard'),('combined-reduced',combined,'reduced')]
    with ChromiumLayoutProbe() as probe:
        for cid,doc,motion in cases:
            folder=out/cid;folder.mkdir();r=compile_h3_scene(doc,target=BIG,motion_preference=motion)
            if not r.receipt.source_gate_passed:raise ValueError('source: '+cid+str(r.receipt.findings))
            (folder/'SCENE.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False));(folder/'SOURCE_RECEIPT.json').write_text(json.dumps(asdict(r.receipt),indent=2))
            measured=probe.measure(r,BIG,folder/'browser',screenshots=True,paint_checks=True)
            fit=inspect_owner_fit(measured,r.effective_document,BIG,r.codegen.manifest_sha256)
            paint=inspect_paint_quality(measured['paint_records'],element_ids=[e['element_id'] for e in doc['elements']],frame_count=48)
            (folder/'FIT.json').write_text(json.dumps(fit,indent=2));(folder/'PAINT.json').write_text(json.dumps(paint,indent=2))
            results.append({'case_id':cid,'source_passed':True,'fit_passed':fit['passed'],'paint_passed':paint['passed'],'fit_findings':fit['findings'],'paint_findings':paint['findings'],
                            'frames':48,'element_frame_records':len(measured['records']),'paint_records':len(measured['paint_records']),'screenshots':len(measured['screenshots'])})
    fonts={name:system_font_coverage([s]) for name,s in [('LatinGreek','English αβγ'),('Devanagari','हिंदी गणित'),('ArabicUrdu','اردو العربية'),('CJK','中文')]}
    (out/'FONT_MATRIX.json').write_text(json.dumps(fonts,indent=2,ensure_ascii=False))
    sandbox=out/'os-probe';sandbox.mkdir();(sandbox/'output').mkdir()
    command=[sys.executable,'-c','import os,socket,json; s=socket.socket();\ntry:s.connect(("1.1.1.1",443)); network="unexpected"\nexcept OSError:network="blocked"\nprint(json.dumps({"pid":os.getpid(),"host_data":os.path.exists("/mnt/data"),"host_home":os.path.exists("/home/oai"),"external_network":network}))']
    normal,k=run_isolated(command,workspace=sandbox,writable=['output'],policy=WorkerPolicy(procfs=False),timeout_s=8)
    strict,ks=run_isolated(['/usr/bin/true'],workspace=sandbox,policy=WorkerPolicy(),timeout_s=8)
    (out/'LINUX_ISOLATION.json').write_text(json.dumps({'no_proc_process':asdict(normal),'no_proc_kernel_proof':k,'private_proc_process':asdict(strict),'private_proc_kernel_proof':ks},indent=2))
    wav=wav_signal();(out/'technical-tone.wav').write_bytes(wav)
    enc=subprocess.run(['/usr/bin/ffmpeg','-nostdin','-v','error','-i',str(out/'technical-tone.wav'),'-c:a','libmp3lame','-b:a','128k',str(out/'technical-tone.mp3')],capture_output=True,text=True,timeout=20)
    if enc.returncode:raise ValueError(enc.stderr)
    pcm,ar=normalize_local_audio(out/'technical-tone.mp3',expected_sha256=sha256((out/'technical-tone.mp3').read_bytes()).hexdigest(),sample_rate=48000,channels=1)
    (out/'normalized-tone.wav').write_bytes(pcm)
    segments=[{'segment_id':'narration-test','asset_id':'a','start_sample':0,'trim_sample':0,'sample_count':48000,'gain':.5},
              {'segment_id':'sfx-test','asset_id':'b','start_sample':24000,'trim_sample':0,'sample_count':48000,'gain':.25}]
    mixed,mr=mix_pcm_segments({'a':wav,'b':pcm},segments,sample_rate=48000,channels=1,total_samples=96000);(out/'mixed-technical-tone.wav').write_bytes(mixed)
    (out/'AUDIO_PRODUCTION.json').write_text(json.dumps({'normalization':ar,'sample_mix':mr},indent=2))
    aroot=write_assets(out/'real-attempt-assets',assets);source=out/'real-attempt-source';receipt=publish_h3_scene(combined,source,target=BIG,asset_root=aroot)
    desc=CompositionDescriptor('BieQA'+digest(combined['scene_id'])[:16],1280,720,24,48)
    req=RenderRequest(str(source),'src/index.ts',desc,'out/result.mp4',receipt.scene_fingerprint,'h7-real',browser_executable='/usr/bin/chromium',require_audio=True)
    actual=full_render(req);(out/'REAL_VALIDATION.json').write_text(json.dumps(asdict(actual),indent=2))
    probe=subprocess.run(['npm','view','remotion@4.0.506','version','--fetch-retries=0','--fetch-timeout=8000'],capture_output=True,text=True,timeout=12)
    (out/'NPM_PROBE.json').write_text(json.dumps({'command':probe.args,'returncode':probe.returncode,'stdout':probe.stdout,'stderr':probe.stderr},indent=2))
    result={'schema_version':'bie.h7.validation.v1','cases':results,'repair_published':True,'frames':sum(r['frames'] for r in results),
            'element_frame_records':sum(r['element_frame_records'] for r in results),'screenshots':sum(r['screenshots'] for r in results),
            'diagnostic_scope':'REAL_CHROMIUM_WITH_EXPLICIT_REACT_REMOTION_API_DOUBLES','real_react':False,'real_remotion':False,
            'actual_render_failure':actual.failure_code,'operational_no_proc_verified':normal.process.passed,'private_proc_verified':strict.process.passed,
            'audio_decoder_actual':True,'audio_mix_samples':96000,'spoken_audio':False,'accepted':False}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
