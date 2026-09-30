#!/usr/bin/env python3
"""Generate authored media, then run actual full-decode AV diagnostics.

No network, model API, real book, Remotion, independent reviewer, or real learner.
These are signal/byte/timing controls, not cinematic or educational acceptance.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time,resource,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import digest,canonical_json,BenchmarkError
from bie.evaluation.benchmarks.av.custody import sha_file,Limits
from bie.evaluation.benchmarks.av.ledger import AVRunStore
from bie.evaluation.benchmarks.av.native import map_render_receipt,COMMIT

def write(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def policy(width=64,height=36,frames=8,fps='4',duration=2):
 return {'schema_version':'av-policy-2','width':width,'height':height,'expected_frames':frames,'fps':fps,
  'require_audio':True,'require_captions':True,'caption_text_sha256':None,'narration_intervals_s':[[0,duration]],
  'max_dark_fraction':.05,'max_identical_run_s':2,'max_silent_fraction':.01,'max_clipped_fraction':.001,
  'min_caption_coverage':1.0,'min_narration_activity':.99,'sync_tolerance_s':.01}
def stamp(seconds):return f'{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d},000'
def captions(path,duration,chunk,text):
 bodies=[];parts=[]
 for i,start in enumerate(range(0,duration,chunk),1):
  body=text.format(i=i);bodies.append(body);parts.append(f'{i}\n{stamp(start)} --> {stamp(min(duration,start+chunk))}\n{body}\n')
 path.write_text('\n'.join(parts),encoding='utf-8');return hashlib.sha256('\n'.join(bodies).encode()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--long-seconds',type=int,default=120);a=p.parse_args()
 if not 30<=a.long_seconds<=600:raise SystemExit('long-seconds must be 30..600')
 out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=False);assets=out/'assets';assets.mkdir();receipts=out/'receipts';receipts.mkdir();policies=out/'policies';policies.mkdir()
 commands=[];results=[];start=time.monotonic()
 def run(cmd):
  t=time.monotonic();r=subprocess.run(cmd,capture_output=True,timeout=180)
  record={'argv':cmd,'exit_code':r.returncode,'duration_seconds':time.monotonic()-t,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest(),'stderr_bytes':len(r.stderr)};commands.append(record);write(out/'generation_commands.json',commands)
  if r.returncode:raise RuntimeError('Synthetic fixture generation failed: '+r.stderr.decode(errors='replace')[:500])
 def video(name,source='testsrc2',audio='tone',width=64,height=36,fps=4,duration=2,filters=None):
  file=assets/name;v=f'{source}=size={width}x{height}:rate={fps}:duration={duration}' if source=='testsrc2' else f'color=c=black:size={width}x{height}:rate={fps}:duration={duration}'
  cmd=['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',v]
  if audio:
   sig={'tone':f'sine=frequency=440:sample_rate=16000:duration={duration}',
    'stereo':f'aevalsrc=0.2*sin(2*PI*440*t)|0.2*sin(2*PI*550*t):s=16000:d={duration}',
    'silence':f'anullsrc=sample_rate=16000:channel_layout=mono:d={duration}',
    'clip':f'aevalsrc=1:s=16000:d={duration}',
    'antiphase':f'aevalsrc=0.1|-0.1:s=16000:d={duration}'}[audio]
   cmd+=['-f','lavfi','-i',sig]
  if filters:cmd+=['-vf',filters,'-fps_mode','passthrough']
  cmd+=['-c:v','libx264','-preset','ultrafast','-crf','30','-threads','2','-pix_fmt','yuv420p']
  if audio:cmd+=['-c:a','pcm_s16le']
  cmd+=[str(file)];run(cmd);return file
 cap=assets/'small.srt';base=policy();base['caption_text_sha256']=captions(cap,2,2,'Authored signal diagnostic.');write(policies/'small.json',base)
 longcap=assets/'long.srt';longp=policy(1280,720,24*a.long_seconds,'24',a.long_seconds);longp['caption_text_sha256']=captions(longcap,a.long_seconds,10,'Synthetic HD diagnostic segment {i}.');write(policies/'long.json',longp)
 longfile=video('long_hd.mkv',audio='stereo',width=1280,height=720,fps=24,duration=a.long_seconds)
 db=out/'av_runs.sqlite'
 with AVRunStore(db) as store:
  def evaluate(name,file,p,expected,caption=cap,limits=Limits(),claimed=None):
   t=time.monotonic();r=store.execute(campaign_id=name,run_id=name,media_path=file,media_sha256=claimed or sha_file(file)[0],policy=p,policy_sha256=digest(p),caption_path=caption,caption_sha256=sha_file(caption)[0] if caption else None,limits=limits)
   write(receipts/(name+'.json'),r);reread=store.get(name);assert reread==r
   entry={'id':name,'status':r['status'],'expected':expected,'matched':r['status'] in expected,'reasons':r['reasons'],'receipt_sha256':r['receipt_sha256'],'duration_seconds':time.monotonic()-t,'reopened_equal':True}
   results.append(entry);write(out/'scenarios.json',results);return r
  longr=evaluate('long_hd_stereo_all_frames',longfile,longp,['DIAGNOSTIC_PASS'],longcap)
  good=video('small.mkv');goodr=evaluate('small_positive',good,base,['DIAGNOSTIC_PASS'])
  evaluate('missing_audio',video('missing_audio.mkv',audio=None),base,['FAIL'])
  evaluate('silent_audio',video('silence.mkv',audio='silence'),base,['FAIL'])
  evaluate('clipped_audio',video('clip.mkv',audio='clip'),base,['FAIL'])
  evaluate('black_frames',video('black.mkv',source='black'),base,['FAIL'])
  evaluate('antiphase_not_downmixed',video('antiphase.mkv',audio='antiphase'),base,['DIAGNOSTIC_PASS'])
  evaluate('actual_timestamp_gap',video('gap.mkv',filters='setpts=PTS+if(gte(N\\,4)\\,0.5/TB\\,0)'),base,['FAIL'])
  bad=assets/'corrupt.mkv';bad.write_bytes(b'invalid video container');evaluate('corrupt_bytes',bad,base,['BLOCKED'])
  trunc=assets/'truncated.mkv';raw=good.read_bytes();trunc.write_bytes(raw[:len(raw)//2]);evaluate('truncated_media',trunc,base,['BLOCKED','FAIL'])
  badcap=assets/'wrong.srt';captions(badcap,2,2,'Incorrect substituted caption.');evaluate('wrong_caption_text',good,base,['FAIL'],badcap)
  evaluate('missing_captions',good,base,['FAIL'],None)
  evaluate('wrong_artifact_hash',good,base,['BLOCKED'],claimed='0'*64)
  evaluate('decode_byte_budget',good,base,['BLOCKED'],limits=Limits(max_decoded_bytes=1000))
  evaluate('frame_budget',good,base,['BLOCKED'],limits=Limits(max_frames=2))
  nativefile=video('native_profile_only.mp4',audio=None);np=copy.deepcopy(base);np.update(require_audio=False,require_captions=False,caption_text_sha256=None,narration_intervals_s=[]);write(policies/'native_profile_only.json',np)
  nr=evaluate('canonical_media_profile_only',nativefile,np,['DIAGNOSTIC_PASS'],None)
  n={'schema_version':'bie.render-receipt.v1','run_id':'synthetic_native_declaration','mode':'full','composition_id':'Lesson','passed':True,'failure_code':None,'errors':[],'output_path':'out/native_profile_only.mp4','expected_frames':8,
    'media':{'width':64,'height':36,'fps':4,'decoded_frames':8,'duration_s':2,'codec_name':'h264','pixel_format':'yuv420p','audio_streams':0},
    'input_sha256':'a'*64,'recipe_sha256':'b'*64,'evidence_directory':'render-evidence/synthetic_native_declaration','execution_kind':'LOCAL_REMOTION_CLI','process_started':True,
    'artifact_sha256':sha_file(nativefile)[0],'artifact_size_bytes':nativefile.stat().st_size,'accepted':False}
  write(out/'SYNTHETIC_NATIVE_DECLARATION_NOT_EXECUTION.json',n)
  mapped=map_render_receipt(n,nr,expected_commit=COMMIT,expected_run_id=n['run_id'],expected_input_sha256='a'*64,expected_recipe_sha256='b'*64,expected_composition_id='Lesson',contract_path=ROOT/'provenance/section17/h2/native/render_contracts.py');write(out/'NATIVE_MAPPING_RESULT.json',mapped)
  # Local TTS is a separate signal/caption experiment, not a provider or BIE lesson.
  script='This is an authored audio diagnostic. We verify decoded samples and caption timing. This recording does not demonstrate educational understanding or a native book intelligence engine run.'
  speech=assets/'local_speech.wav';run(['espeak','-s','140','-w',str(speech),script])
  import wave,math
  with wave.open(str(speech)) as wf:secs=wf.getnframes()/wf.getframerate()
  duration=math.ceil(secs);spoken=assets/'local_speech.mkv'
  run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',f'testsrc2=size=640x360:rate=24:duration={duration}','-i',str(speech),'-af','apad','-t',str(duration),'-c:v','libx264','-preset','ultrafast','-threads','2','-pix_fmt','yuv420p','-c:a','pcm_s16le',str(spoken)])
  sc=assets/'local_speech.srt';sp=policy(640,360,duration*24,'24',duration);sp['caption_text_sha256']=captions(sc,duration,duration,script)
  # Frozen illustrative speech profile permits pauses; not tuned to observed measurements.
  sp['max_silent_fraction']=.65;sp['min_narration_activity']=.35;write(policies/'local_speech.json',sp)
  sr=evaluate('local_tts_signal_caption_profile',spoken,sp,['DIAGNOSTIC_PASS'],sc)
 # Reopen the entire database in a separate connection, preserving all statuses.
 with AVRunStore(db) as reopened:
  for row in results:assert reopened.get(row['id'])==json.loads((receipts/(row['id']+'.json')).read_text())
 obs=longr.get('observations');summary={'schema_version':'h2-diagnostics-1','scenarios':len(results),'matched':sum(x['matched'] for x in results),
 'status_counts':{s:sum(x['status']==s for x in results) for s in ('DIAGNOSTIC_PASS','FAIL','BLOCKED')},'all_expected':all(x['matched'] for x in results),
 'long_media_observations':obs,'duration_seconds':time.monotonic()-start,'producer_max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'generator_child_max_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'process_rss_scope':'whole diagnostic producer/child maxima; not a dedicated OS-enforced memory sandbox',
 'synthetic_media':True,'local_tts_used':True,'speech_content_recognized':False,'native_bie_runs':0,'remotion_renders':0,'live_provider_calls':0,'human_reviews':0,'real_learners':0,'product_accepted':False}
 write(out/'DIAGNOSTIC_SUMMARY.json',summary)
 manifest={str(p.relative_to(out)):sha_file(p,maximum=4*1024**3)[0] for p in out.rglob('*') if p.is_file() and not p.name.endswith(('-wal','-shm'))};write(out/'FILE_SHA256.json',manifest)
 print(json.dumps({k:summary[k] for k in ('scenarios','matched','status_counts','all_expected','producer_max_rss_kib','duration_seconds')},indent=2))
 return 0 if summary['all_expected'] else 1
if __name__=='__main__':raise SystemExit(main())
