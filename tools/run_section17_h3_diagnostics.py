#!/usr/bin/env python3
"""Reproducible AUTHORED diagnostic exercise, not a native BIE or learner run.

Requires installed ffmpeg/ffprobe. Produces its own 25-second media, independent
raw-frame reference decode, actual AV evaluations, SQLite and negative controls.
No network access, installs, real keys, model calls, humans or repository writes.
"""
from pathlib import Path
from dataclasses import asdict
from copy import deepcopy
from fractions import Fraction
import argparse,hashlib,json,os,shutil,sqlite3,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/section17')]
sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import ExecutionContext
from bie.evaluation.benchmarks.adoption.ledger import AdoptionStore
from bie.evaluation.benchmarks.adoption.release import evaluate as release_av
from bie.evaluation.benchmarks.adoption import native,preflight
from bie.evaluation.benchmarks.release.deterministic import service_code_sha256
from bie.evaluation.benchmarks.av.custody import Limits
from bie.evaluation.benchmarks.av.service import tool_identity
from h3_support import a11y,policy,sha,json_file,context,campaign,gate_inputs,make_assessment,native_workspace,CONTRACT,token,trust,NOW

def write(out,name,value):
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');return p

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True);args=parser.parse_args()
    out=Path(args.output_dir).absolute();out.mkdir(parents=True,exist_ok=False)
    media_root=out/'media';media_root.mkdir();media=media_root/'authored_25s.mkv'
    evidence=[];code=service_code_sha256();limits=Limits(deadline_s=60);ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('Installed ffmpeg required')
    cmd=[ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=640x360:rate=12:duration=25',
         '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=25','-ac','2',
         '-c:v','libx264','-threads','1','-pix_fmt','yuv420p','-c:a','pcm_s16le','-y',str(media)]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    write(out,'media/ENCODE.json',{'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode:raise RuntimeError('Fixture encoding failed')
    transcript='Authored signal test, not a textbook lesson.'
    cap=media_root/'authored.srt';cap.write_text('1\n00:00:00,000 --> 00:00:25,000\n'+transcript+'\n',encoding='utf-8')
    # Separate decoder invocation and file-based hashing: not collector receipt replay.
    raw=out/'independent_rgb.raw';oracle_cmd=[ffmpeg,'-nostdin','-v','error','-threads','1','-noautorotate','-i',str(media),
      '-map','0:v:0','-an','-sn','-dn','-fps_mode','passthrough','-threads','1','-pix_fmt','rgb24','-f','rawvideo','-y',str(raw)]
    p=subprocess.run(oracle_cmd,capture_output=True,text=True,timeout=60)
    if p.returncode:raise RuntimeError('Reference decode failed')
    allh=hashlib.sha256();chain=hashlib.sha256();count=0
    with raw.open('rb') as f:
        while b:=f.read(640*360*3):
            if len(b)!=640*360*3:raise RuntimeError('Incomplete oracle frame')
            allh.update(b);chain.update(hashlib.sha256(b).digest());count+=1
    if count!=300:raise RuntimeError('Unexpected reference frame count')
    oracle={'decoded_sha256':allh.hexdigest(),'frame_chain_sha256':chain.hexdigest(),
            'ffmpeg_sha256':tool_identity()['ffmpeg']['sha256']}
    write(out,'ORACLE.json',{'command':oracle_cmd,'exit_code':p.returncode,'frames':count,'decoded_bytes':raw.stat().st_size,
                          'frame_reference':oracle,'independent_reviewer':False,'scope':'SEPARATE_AUTHORED_RAW_DECODE_NOT_GOLDEN_BENCHMARK'})
    raw.unlink()
    refs={};cands={};contexts={}
    for n in (12,13,15):
        pol=policy(width=640,height=360,expected_frames=300,fps='12',narration_intervals_s=[[0,25]],
           require_captions=n==15,caption_text_sha256=hashlib.sha256(transcript.encode()).hexdigest() if n==15 else None)
        ar=ac=None
        if n==15:
            ar,ac=a11y();ar['duration_ms']=25000
            ar['speech']=[{'id':'speech','start':0,'end':25000,'transcript':transcript,'weight':'1'}]
            ac['captions']=[{'id':'c1','speech_id':'speech','start':0,'end':25000,'text':transcript}]
        ref={'schema_version':'metric-av-reference-3','metric_id':f'BIE-EVAL-METRIC-{n:03}','rubric_id':f'av-rubric-{n}',
          'version':'1.0.0','reference_owner_id':'authored-diagnostic-author','evidence_grade':'AUTHORED_DIAGNOSTIC',
          'source_refs':[{'id':'authored-video','locator':'Original 25-second generated signal fixture','basis_sha256':digest(pol)}],
          'av_policy':pol,'limits_sha256':digest(asdict(limits)),'frame_reference':oracle if n==13 else None,'a11y_reference':ar}
        c={'schema_version':'metric-av-candidate-3','media':{'path':media.name,'sha256':sha(media),'size_bytes':media.stat().st_size},
           'captions':{'path':cap.name,'sha256':sha(cap),'size_bytes':cap.stat().st_size} if n==15 else None,
           'caption_format':'srt' if n==15 else None,'a11y_candidate':ac}
        refs[n]=ref;cands[n]=c;contexts[n]=context(n,ref,c,run_id=f'longform_{n}')
        write(out,f'inputs/ref_{n}.json',ref);write(out,f'inputs/candidate_{n}.json',c);write(out,f'inputs/context_{n}.json',contexts[n])
    contract=campaign(name='h3-longform');contract['cases']=[{k:contexts[n][k] for k in ('case_id','domain','metric_id','reference_sha256')} for n in (12,13,15)]
    write(out,'inputs/campaign.json',contract);write(out,'inputs/limits.json',asdict(limits));db=out/'adoption.sqlite3'
    def record(name,expected,actual,details=None):
        item={'name':name,'expected':expected,'actual':actual,'matched':expected==actual,'details':details or {}}
        evidence.append(item);write(out,'SCENARIOS_PARTIAL.json',evidence)
    def blocked(name,fn):
        try:result=fn();actual=result.get('outcome',result.get('status','RETURNED'));details=result
        except BenchmarkError as e:actual='BLOCKED';details={'reason':e.code}
        record(name,'BLOCKED',actual,details)
    # First evaluation goes through the real public command-line interface.
    command=[sys.executable,'-B','-m','bie.evaluation.benchmarks.adoption','--db',str(db),'run',
      '--campaign',str(out/'inputs/campaign.json'),'--campaign-sha256',digest(contract),
      '--context',str(out/'inputs/context_12.json'),'--reference',str(out/'inputs/ref_12.json'),
      '--candidate',str(out/'inputs/candidate_12.json'),'--code-sha256',code,
      '--artifact-root',str(media_root),'--limits',str(out/'inputs/limits.json')]
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
    write(out,'CLI_EXECUTION.json',{'command':command,'exit_code':p.returncode,'stderr':p.stderr})
    (out/'CLI_STDOUT.json').write_text(p.stdout)
    cli_assessment=json.loads(p.stdout);record('longform_render_cli','MEASURED',cli_assessment.get('status'),{'exit_code':p.returncode})
    with AdoptionStore(db) as store:
        if store.get('longform_12')!=cli_assessment:raise RuntimeError('CLI record differs from stored data')
        measured=[cli_assessment]
        for n in (13,15):
            row=store.execute(contract,contexts[n],refs[n],cands[n],expected_campaign_sha256=digest(contract),expected_code_sha256=code,execution_context=ExecutionContext(media_root,limits));measured.append(row)
            record(f'longform_metric_{n}','PASS',row['evidence']['metric_result']['outcome'])
        for n,row in zip((12,13,15),measured):write(out,f'actual_assessments/metric_{n}.json',row)
        m,p,h,a=gate_inputs();m['cases']=[{'context':contexts[n],'weight':'1','leakage_group':f'authored-av{n}'} for n in (12,13,15)]
        h=[make_assessment(contexts[n],'human','HUMAN','1',execution='FIXTURE') for n in (12,13,15)]
        a['campaign_sha256']=digest(contract)
        def gate_result(assessments=h,adoption=a):return release_av(m,p,assessments,adoption_policy=adoption,expected_adoption_sha256=digest(adoption),
          store=store,expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p))
        g=gate_result();write(out,'RELEASE_GATE.json',g);record('fixture_review_release_gate','DIAGNOSTIC_PASS',g['outcome'],{'human_fixture_assessments':3,'real_human_reviews':0})
        blocked('injected_deterministic_pass',lambda:gate_result(h+[measured[0]]))
        weaker=deepcopy(a);weaker['required_cases'].pop();blocked('weakened_adoption_roster',lambda:gate_result(adoption=weaker))
        nc=deepcopy(cands[12]);nc['media']['path']='renamed.mkv';shutil.copy2(media,media_root/'renamed.mkv')
        blocked('renamed_same_content_retry',lambda:store.execute(contract,context(12,refs[12],nc,run_id='renamed'),refs[12],nc,
           expected_campaign_sha256=digest(contract),expected_code_sha256=code,execution_context=ExecutionContext(media_root,limits)))
        # Three distinct actual negative AV profile executions, each policy-scoped.
        for n,name,mutate in [(12,'wrong_frame_count',lambda r,c:r['av_policy'].update(expected_frames=301)),
                             (13,'wrong_frame_reference',lambda r,c:r['frame_reference'].update(decoded_sha256='0'*64)),
                             (15,'caption_metadata_divergence',lambda r,c:(r['a11y_reference']['speech'][0].update(transcript='Wrong metadata'),c['a11y_candidate']['captions'][0].update(text='Wrong metadata')))]:
            ref=deepcopy(refs[n]);c=deepcopy(cands[n]);mutate(ref,c);ctx=context(n,ref,c,run_id=name);cg=deepcopy(contract);cg['id']=name;cg['cases']=[{k:ctx[k] for k in ('case_id','domain','metric_id','reference_sha256')}]
            row=store.execute(cg,ctx,ref,c,expected_campaign_sha256=digest(cg),expected_code_sha256=code,execution_context=ExecutionContext(media_root,limits))
            write(out,f'negative_assessments/{name}.json',row);record(name,'FAIL',row['evidence']['metric_result']['outcome'])
        corrupt=media_root/'corrupt.mkv';corrupt.write_bytes(b'not a media container');c=deepcopy(cands[12]);c['media']={'path':corrupt.name,'sha256':sha(corrupt),'size_bytes':corrupt.stat().st_size}
        ctx=context(12,refs[12],c,run_id='corrupt');cg=deepcopy(contract);cg['id']='corrupt'
        row=store.execute(cg,ctx,refs[12],c,expected_campaign_sha256=digest(cg),expected_code_sha256=code,execution_context=ExecutionContext(media_root,limits))
        write(out,'negative_assessments/corrupt.json',row);record('corrupt_media_persisted','BLOCKED',row['status'],{'negative_receipt_retained':'av_collection' in row['evidence']})
        backup=sqlite3.connect(out/'tampered_control.sqlite3');store.db.backup(backup);backup.execute("UPDATE av_h3_runs SET assessment_json='{}' WHERE run_id='longform_12'");backup.commit();backup.close()
    with AdoptionStore(out/'tampered_control.sqlite3') as bad:blocked('database_receipt_tamper',lambda:bad.get('longform_12'))
    with AdoptionStore(out/'missing_runs.sqlite3') as empty:
        blocked('missing_actual_av_runs',lambda:release_av(m,p,h,adoption_policy=a,expected_adoption_sha256=digest(a),store=empty,expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p)))
    # Actual abrupt process exit after committed reservation, before AV execution.
    script="""import os,sys,json
from unittest.mock import patch
from bie.evaluation.benchmarks.adoption.ledger import AdoptionStore
from bie.evaluation.benchmarks.adoption.contracts import ExecutionContext
from bie.evaluation.benchmarks.av.custody import Limits
from bie.evaluation.benchmarks.release.deterministic import service_code_sha256
from bie.evaluation.benchmarks.models import digest
from pathlib import Path
out=Path(sys.argv[1]);load=lambda name:json.loads((out/name).read_text())
cg=load('inputs/campaign.json');cg['id']='abrupt';ctx=load('inputs/context_12.json');ctx['run_id']='abrupt'
with AdoptionStore(out/'abrupt.sqlite3') as s,patch('bie.evaluation.benchmarks.adoption.ledger.run_rater',side_effect=lambda *a,**k:os._exit(71)):
 s.execute(cg,ctx,load('inputs/ref_12.json'),load('inputs/candidate_12.json'),expected_campaign_sha256=digest(cg),expected_code_sha256=service_code_sha256(),execution_context=ExecutionContext(out/'media',Limits(**load('inputs/limits.json'))))
"""
    pr=subprocess.run([sys.executable,'-B','-c',script,str(out)],cwd=ROOT,capture_output=True,text=True,timeout=30)
    write(out,'ABRUPT_WORKER.json',{'exit_code':pr.returncode,'stderr':pr.stderr,'stdout':pr.stdout,'fault':'os._exit(71) after committed reservation before decoder','native_execution':False})
    if pr.returncode!=71:raise RuntimeError('Unexpected abrupt worker outcome')
    with AdoptionStore(out/'abrupt.sqlite3') as stopped:
        blocked('abrupt_run_not_final',lambda:stopped.get('abrupt'))
        cx=deepcopy(contexts[12]);cx['run_id']='abrupt';r=stopped.recover('abrupt',expected_context_sha256=digest(cx),operator_reason='PROCESS_EXIT_71_CONFIRMED')
        write(out,'RECOVERY.json',r);record('abrupt_run_recovery','BLOCKED',r['status'])
    # Actual byte custody with explicitly authored native-format declarations.
    native_root=out/'native_format_fixture';native_root.mkdir();av,npath,expect=native_workspace(native_root)
    lineage=native.inspect(native_root,npath,av,expectation=expect,expected_expectation_sha256=digest(expect),contract_path=CONTRACT)
    write(out,'NATIVE_FORMAT_CUSTODY.json',lineage);record('authored_native_format_custody','CUSTODY_VERIFIED_UNSIGNED',lineage['status'])
    tok=token('NATIVE_AV_COLLECTION',lineage['lineage_sha256'],{'execution_kind':'LOCAL_REMOTION_CLI','lineage_sha256':lineage['lineage_sha256']});t=trust(roles=['NATIVE_AV_COLLECTION'])
    auth=native.authorize(lineage,tok,t,now=NOW,production=False);write(out,'FIXTURE_AUTHORIZATION.json',auth)
    record('fixture_key_diagnostic_authorization','AUTHORIZED_WORKER_ASSERTION',auth['status'])
    blocked('fixture_key_production_rejection',lambda:native.authorize(lineage,tok,t,now=NOW,production=True))
    pinned=out/'partial_checkout';dest=pinned/'bie/compiler/render_contracts.py';dest.parent.mkdir(parents=True);shutil.copy2(CONTRACT,dest)
    pr=preflight.check(pinned,expected_commit=preflight.COMMIT);write(out,'CANONICAL_PREFLIGHT.json',pr);record('partial_checkout_not_full_native','BLOCKED',pr['status'])
    if service_code_sha256()!=code:raise RuntimeError('Evaluator source changed during diagnostics')
    summary={'schema_version':'1.0.0','scenarios':evidence,'scenarios_total':len(evidence),'scenarios_matched':sum(x['matched'] for x in evidence),
      'all_matched':all(x['matched'] for x in evidence),'evaluator_code_sha256':code,
      'actual_media':{'duration_s':25,'width':640,'height':360,'fps':12,'decoded_frames':300,'samples_per_channel':400000,'audio_channels':2,'audio_rate':16000},
      'actual_av_metric_executions':7,'native_bie_runs':0,'remotion_runs':0,'live_model_calls':0,'actual_human_reviews':0,'learner_trials':0,
      'fixture_human_assessments':3,'fixture_worker_attestations':1,'production_acceptance':False,
      'scope':'Authored signal/reference diagnostics and operator integration, not textbook or cinematic quality acceptance'}
    write(out,'EXECUTION_RESULT.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='scenarios'},indent=2))
    return 0 if summary['all_matched'] else 1
if __name__=='__main__':raise SystemExit(main())
