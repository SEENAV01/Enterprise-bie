from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
import hashlib,base64
from h4_support import reference as old_reference,context as old_context,assert_error,ROOT,BROWSER
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.browser.contracts import BrowserLimits
from bie.evaluation.benchmarks.browser.served.admission import build_candidate
from bie.evaluation.benchmarks.browser.served.origin import headers
GAME=ROOT/'examples/section17_h5/module_game'
def candidate(root=GAME):return build_candidate(root)
def context(root=GAME,limits=BrowserLimits()):return old_context(root,limits)
def reference(limits=BrowserLimits()):
    r=old_reference(limits);r['schema_version']='browser-http-reference-1';r['rubric_id']='module-fraction-game-v1'
    r['steps'][-1]['checks'][0].update(id='persist-progress',expected='Solved: 1/1')
    r['steps'].append({'id':'explicit-reset','action':'click','target':'#reset','value':None,'checks':[
       {'id':'explicit-reset-progress','target':'#progress','property':'text','expected':'Solved: 0/1'},
       {'id':'explicit-reset-note','target':'#note','property':'value','expected':''}]})
    r['objectives'][0]['checks']=[c['id'] for s in r['steps'] for c in s['checks']]
    r['http_policy']={'ready':{'target':'#ready','text':'Lesson ready'},
       'required_assets':[v['path'] for v in candidate()['files']],
       'ax_checks':[{'id':'native-right-name','target':'#right','role':'button','name':'2/4'},
                    {'id':'native-note-label','target':'#note','role':'textbox','name':'Your explanation'}],
       'max_requests':200,'max_response_bytes':32_000_000}
    return r
@lru_cache(maxsize=1)
def _runtime():
    from bie.evaluation.benchmarks.browser.service import execute
    return execute(reference(),candidate(),context())
def runtime():return deepcopy(_runtime())
def result_blocked():
    return {'status':'BLOCKED','error_code':'BROWSER_COLLECTION_BLOCKED','reference_sha256':digest(reference()),
            'candidate_sha256':digest(candidate()),'browser_receipt':runtime(),'release_authorized':False,'product_accepted':False}
def synthetic_observed():
    """STRUCTURAL VALIDATOR FIXTURE ONLY; not actual HTTP browser execution."""
    r=reference();c=candidate();runs=[]
    for index in range(r['replay_count']):
        steps=[]
        for s in r['steps']:
            obs={}
            for k in s['checks']:obs.setdefault(k['target'],{'present':True})[k['property']]=k['expected']
            steps.append({'step_id':s['id'],'action':s['action'],'action_error':None,'observations':obs})
        wire=[];server=[]
        for row in c['files']:
            raw=(GAME/row['path']).read_bytes();h=headers(row['path'],raw)
            wire.append({**row,'method':'GET','status':200,'headers':{k.lower():v for k,v in h.items()}})
            server.append({**row,'method':'GET','status':200,'headers':h,'response_completed':True})
        shot=(GAME/'tile.png').read_bytes()
        runs.append({'steps':steps,'events':{k:[] for k in ('blocked_requests','page_errors','console_errors','violations')},
          'fresh_context_index':index,'http_responses':wire,'http_server':server,
          'readiness':[{'ready':True,'target':'#ready','observed_text':'Lesson ready'}],
          'ax':{k['id']:{'present':True,'ignored':False,'role':k['role'],'name':k['name']} for k in r['http_policy']['ax_checks']},
          'screenshot':{'sha256':hashlib.sha256(shot).hexdigest(),'size_bytes':len(shot),'png_base64':base64.b64encode(shot).decode()}})
    records=[v for run in runs for v in run['http_server']]
    return {'status':'COLLECTED','transport':'REAL_LOOPBACK_HTTP_MODULE_APP','hostile_code_sandbox_verified':False,
            'trusted_fixture_execution_only':True,'runs':runs,'server_accounting':{'records':records,'requests':len(records),
            'response_bytes_reserved':sum(v['size_bytes'] for v in records),'limit_exceeded':False}}
