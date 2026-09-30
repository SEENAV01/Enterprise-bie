"""Authored test inputs; no real book, human review or native renderer provenance."""
from pathlib import Path
from dataclasses import asdict
from functools import lru_cache
from copy import deepcopy
import atexit,tempfile,hashlib,json,shutil
from bie.evaluation.benchmarks.models import digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import ExecutionContext,METRICS
from bie.evaluation.benchmarks.av.custody import Limits
from bie.evaluation.benchmarks.metrics import evaluate
from bie.evaluation.benchmarks.release.deterministic import execute,service_code_sha256
from h2_support import media,sha,policy,report,native,CONTRACT,ROOT
from batch005_helpers import ctx as base_ctx,cohort,make_assessment,token,trust,NOW
TMP=tempfile.TemporaryDirectory(prefix='h3-fixtures-');atexit.register(TMP.cleanup)
TD=Path(TMP.name)
LIMITS=Limits(deadline_s=30)

def a11y():
    f=json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures/BIE-EVAL-METRIC-015.json').read_text())
    return deepcopy(f['reference']['payload']),deepcopy(f['cases'][0]['candidate'])

@lru_cache(None)
def _fixture(n):
    p=media('tone');pol=policy();ar=ac=None;caption=None
    if n==15:
        ar,ac=a11y();pol=policy(require_captions=True,caption_text_sha256=hashlib.sha256(b'Distance changes force').hexdigest())
        cap=TD/'lesson.srt';cap.write_text('1\n00:00:00,000 --> 00:00:02,000\nDistance changes force\n',encoding='utf-8')
        caption={'path':cap.name,'sha256':sha(cap),'size_bytes':cap.stat().st_size}
    target=TD/'lesson.mkv'
    if not target.exists():shutil.copy2(p,target)
    fr=None
    if n==13:
        rep=report('tone');obs=rep['observations']
        fr={k:obs['video'][k] for k in ('decoded_sha256','frame_chain_sha256')};fr['ffmpeg_sha256']=obs['tool_binary_identity']['ffmpeg']['sha256']
    ref={'schema_version':'metric-av-reference-3','metric_id':f'BIE-EVAL-METRIC-{n:03}',
      'rubric_id':f'av-rubric-{n}','version':'1.0.0','reference_owner_id':'fixture-author',
      'evidence_grade':'AUTHORED_DIAGNOSTIC','source_refs':[{'id':'authored','locator':'Local original synthetic test media','basis_sha256':digest(pol)}],
      'av_policy':pol,'limits_sha256':digest(asdict(LIMITS)),'frame_reference':fr,'a11y_reference':ar}
    c={'schema_version':'metric-av-candidate-3','media':{'path':target.name,'sha256':sha(target),'size_bytes':target.stat().st_size},
       'captions':caption,'caption_format':'srt' if caption else None,'a11y_candidate':ac}
    return ref,c

def fixture(n=12):return deepcopy(_fixture(n))
def context(n=12,ref=None,candidate=None,run_id=None):
    if ref is None:ref,candidate=fixture(n)
    c=base_ctx(metric=f'BIE-EVAL-METRIC-{n:03}',case=f'av{n}',reference=ref,candidate=candidate)
    c['run_id']=run_id or f'h3_run_{n}';c['domain']='physics';return c

def measure(n=12,ref=None,candidate=None,root=TD,limits=LIMITS,**kw):
    if ref is None:ref,candidate=fixture(n)
    opts={'expected_reference_sha256':digest(ref),'expected_candidate_sha256':digest(candidate),'execution_context':ExecutionContext(root,limits)}
    opts.update(kw);return evaluate(f'BIE-EVAL-METRIC-{n:03}',ref,candidate,**opts)

def rater(n=12,ref=None,candidate=None,**kw):
    if ref is None:ref,candidate=fixture(n)
    opts={'expected_code_sha256':service_code_sha256(),'execution_context':ExecutionContext(TD,LIMITS)};opts.update(kw)
    return execute(context(n,ref,candidate),ref,candidate,**opts)

@lru_cache(None)
def _measured(n):return measure(n)
def measured(n=12):return deepcopy(_measured(n))

def campaign(ns=(12,13,15),name='campaign'):
    x=context(ns[0]);return {'schema_version':'av-campaign-3','id':name,'dataset_sha256':x['dataset_sha256'],
       'environment_sha256':x['environment_sha256'],'split':x['split'],
       'cases':[{'case_id':context(n)['case_id'],'domain':'physics','metric_id':f'BIE-EVAL-METRIC-{n:03}','reference_sha256':digest(fixture(n)[0])} for n in ns]}

def store_run(store,n=12,contract=None,ref=None,candidate=None,ctx=None,**kw):
    if ref is None:ref,candidate=fixture(n)
    contract=campaign() if contract is None else contract;ctx=context(n,ref,candidate) if ctx is None else ctx
    opts={'expected_campaign_sha256':digest(contract),'expected_code_sha256':service_code_sha256(),
          'execution_context':ExecutionContext(TD,LIMITS)};opts.update(kw)
    return store.execute(contract,ctx,ref,candidate,**opts)

def gate_inputs(ns=(12,13,15)):
    m,p,_=cohort();contexts=[context(n) for n in ns]
    m['cases']=[{'context':c,'weight':'1','leakage_group':c['case_id']} for c in contexts]
    p['enterprise']['metrics']=[{'id':c['metric_id'],'weight':'1'} for c in contexts]
    p['critical_floors']['floors']=[{'id':c['metric_id'],'minimum':'1'} for c in contexts]
    p['domains']['domains']=[{'id':'physics','minimum_score':'1','minimum_cases':1,'minimum_measured_fraction':'1'}]
    p['aggregation']['raters'][0]['id']='av-deterministic-v3'
    rows=[make_assessment(c,'human','HUMAN','1',execution='FIXTURE') for c in contexts]
    adoption={'schema_version':'av-release-policy-3','campaign_sha256':digest(campaign(ns)),
              'required_cases':[c['case_id'] for c in contexts]}
    return m,p,rows,adoption

def json_file(root,path,value):
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(canonical_json(value)+'\n',encoding='utf-8');return p

def manifest(root,names,binding):
    rows=[]
    for name in sorted(names):
        p=Path(root)/name;rows.append({'path':name,'sha256':sha(p),'size_bytes':p.stat().st_size})
    body={'schema_version':'bie.artifacts.v1','binding_sha256':binding,'artifacts':rows,'accepted':False}
    return {**body,'manifest_sha256':digest(body)}

def native_workspace(root):
    # Authored declarations and synthetic FFmpeg bytes: intentionally NOT native execution.
    root=Path(root);av=report('mp4');n=native(av);base=n['evidence_directory'];scene=digest('synthetic-scene')
    (root/'out').mkdir(parents=True,exist_ok=True);shutil.copy2(media('mp4'),root/n['output_path'])
    sources=['package.json','package-lock.json','tsconfig.json','src/index.tsx']
    for name in sources:json_file(root,name,{'fixture_only':True,'file':name})
    src=manifest(root,sources,scene);json_file(root,base+'/input-manifest.json',src);n['input_sha256']=src['manifest_sha256']
    recipe={'schema_version':'bie.render-recipe.v1','scene_fingerprint':scene,'input_sha256':n['input_sha256'],
      'composition':{'composition_id':'Lesson','width':64,'height':36,'fps':4,'duration_in_frames':8},
      'plan':{'mode':'full','first_frame':0,'last_frame':7,'expected_frames':8},'codec':'h264','pixel_format':'yuv420p',
      'crf':18,'concurrency':1,'frame_timeout_ms':30000,'require_audio':False,'props_file':None,
      'tool_versions':{'fixture':'not-remotion'},'cli_sha256':digest('fixture-cli'),'node_sha256':digest('fixture-node'),
      'ffprobe_sha256':digest('fixture-probe'),'browser_launcher_sha256':digest('fixture-browser')}
    n['recipe_sha256']=digest(recipe);recipe['recipe_sha256']=n['recipe_sha256'];json_file(root,base+'/recipe.json',recipe)
    receipt=base+'/RENDER_RECEIPT.json';json_file(root,receipt,n)
    extra=['render-process.json','probe-process.json','toolchain.json','source-qa.json','full-typecheck.json',
           'actual-paint-witness.json','installed-toolchain.json','isolation.json']
    for name in extra:json_file(root,base+'/'+name,{'fixture_only':True,'accepted':False})
    paths=[base+'/'+name for name in extra]+[receipt,base+'/recipe.json',base+'/input-manifest.json',n['output_path']]
    seal=manifest(root,paths,n['recipe_sha256']);json_file(root,base+'/ARTIFACT_MANIFEST.json',seal)
    e={'schema_version':'native-lineage-policy-3','commit':'a68e054025b8fe7756a71e998d9e9103dad8e0f4',
       'run_id':n['run_id'],'composition_id':n['composition_id'],'scene_sha256':scene,'input_sha256':n['input_sha256'],
       'recipe_sha256':n['recipe_sha256'],'artifact_manifest_sha256':seal['manifest_sha256'],'required_source_paths':sources}
    return av,receipt,e
