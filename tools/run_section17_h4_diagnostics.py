#!/usr/bin/env python3
"""Actual local browser scenarios with persisted good/negative outcomes; not native BIE E2E."""
from pathlib import Path
from dataclasses import replace,asdict
from copy import deepcopy
import argparse,sys,shutil,json,base64
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests/section17')];sys.dont_write_bytecode=True
from h4_support import GAME,reference,candidate,context
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.browser.contracts import BrowserLimits
from bie.evaluation.benchmarks.browser.ledger import BrowserStore
from bie.evaluation.benchmarks.browser.native import map_dist
from bie.evaluation.benchmarks.release.deterministic import execute as rater,service_code_sha256

def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=False)
 scenarios=[('desktop-keyboard','PASS'),('mobile-keyboard','PASS'),('wrong-reference','FAIL'),('broken-feedback','FAIL'),
  ('low-contrast','FAIL'),('offscreen-question','FAIL'),('javascript-error','FAIL'),('network-request','FAIL'),
  ('style-api-spoof','PASS'),('stale-manifest','BLOCKED'),('wrong-tool-pin','BLOCKED'),('hang-deadline','BLOCKED'),
  ('unsupported-module','BLOCKED'),('canonical-layout-fixture','PASS')]
 summary=[]
 with BrowserStore(out/'browser_runs.sqlite') as store:
  for i,(name,expected) in enumerate(scenarios):
   case=out/name;root=case/'assets';shutil.copytree(GAME,root);limits=replace(BrowserLimits(),total_timeout_seconds=2) if name=='hang-deadline' else BrowserLimits()
   r=reference(limits);js=root/'game.js';css=root/'styles.css'
   if name=='mobile-keyboard':r['viewport']={'width':390,'height':900}
   if name=='wrong-reference':r['steps'][0]['checks'][0]['expected']='A different question'
   if name=='broken-feedback':js.write_text(js.read_text().replace('Correct. 1/2 = 2/4.','Unrelated response.'))
   if name=='low-contrast':css.write_text(css.read_text()+'\n#question{color:#fff;background:#fff}')
   if name=='offscreen-question':css.write_text(css.read_text()+'\n#question{transform:translateX(2000px)}')
   if name=='javascript-error':js.write_text(js.read_text()+"\nsetTimeout(()=>{throw new Error('fault-control')},0);")
   if name=='network-request':js.write_text(js.read_text()+"\nfetch('https://example.com/blocked').catch(()=>{});")
   if name=='style-api-spoof':js.write_text(js.read_text()+"\nwindow.getComputedStyle=()=>{throw new Error('candidate override')};")
   if name=='hang-deadline':js.write_text('while(true){}')
   if name=='unsupported-module':
    h=root/'index.html';h.write_text(h.read_text().replace('<script src=','<script type="module" src='))
   if name=='canonical-layout-fixture':
    runtime=root/'runtime';runtime.mkdir()
    for f in list(root.iterdir()):
     if f.is_file():f.rename(runtime/f.name)
    (runtime/'smoke-bundle.js').write_bytes((runtime/'game.js').read_bytes());(runtime/'game.js').unlink()
    h=runtime/'index.html';h.write_text(h.read_text().replace('<script src="game.js">','<script type="module" src="entry.js">'))
    (runtime/'security-headers.json').write_text('{"Content-Security-Policy":"connect-src \'none\'"}')
    c=candidate(root,entry='runtime/index.html');c=map_dist(c['files'],expected_manifest_sha256=digest(c['files']))
   else:c=candidate(root)
   ctx=context(root,limits)
   if name=='stale-manifest':js.write_text('changed')
   if name=='wrong-tool-pin':ctx=replace(ctx,chromium_sha256='0'*64)
   for fname,value in [('reference.json',r),('candidate.json',c),('context.json',asdict(ctx))]:
    (case/fname).write_text(json.dumps(value,indent=2))
   run=store.execute(name,'diag-'+name,r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),context=ctx)
   result=run['result'];actual=result.get('outcome',result['status']);ok=actual==expected
   (case/'result.json').write_text(json.dumps(run,indent=2))
   if result['status']=='MEASURED':
    for k,b in enumerate(result['details']['browser_receipt']['observed']['runs']):
     (case/f'browser-{k}.png').write_bytes(base64.b64decode(b['screenshot']['png_base64']))
   summary.append({'case':name,'expected':expected,'actual':actual,'matched':ok,'native_e2e':False})
  # Read actual persisted bytes after closing and reopening another SQLite handle.
 with BrowserStore(out/'browser_runs.sqlite') as reopened:
  for row in summary:
   expected=json.loads((out/row['case']/'result.json').read_text());assert reopened.get(row['case'])==expected
 r=reference();c=candidate();ctx={'run_id':'rater-positive','case_id':'fraction','domain':'math','metric_id':r['metric_id'],
    'candidate_sha256':digest(c),'reference_sha256':digest(r),'rubric_sha256':digest(r),'dataset_sha256':digest('diagnostic-fixtures'),
    'environment_sha256':digest('local-chromium-fixture'),'split':'DEVELOPMENT'}
 positive=rater(ctx,r,c,expected_code_sha256=service_code_sha256(),execution_context=context())
 blocked=rater({**ctx,'run_id':'rater-blocked'},r,c,expected_code_sha256=service_code_sha256(),execution_context=replace(context(),chromium_sha256='0'*64))
 (out/'rater_positive.json').write_text(json.dumps(positive,indent=2));(out/'rater_blocked.json').write_text(json.dumps(blocked,indent=2))
 assert positive['status']=='MEASURED' and positive['score_exact']=='1'
 assert blocked['status']=='BLOCKED' and 'browser_collection' in blocked['evidence']
 result={'scenarios':summary,'matched':sum(x['matched'] for x in summary),'total':len(summary),
  'counts':{v:sum(x['actual']==v for x in summary) for v in ('PASS','FAIL','BLOCKED')},
  'sqlite_reopen_equal':True,'actual_deterministic_rater_positive':positive['status'],
  'actual_deterministic_rater_negative':blocked['status'],'native_bie_execution':False,
  'live_model_calls':0,'independent_human_reviews':0,'learner_trials':0,'product_accepted':False}
 (out/'DIAGNOSTICS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return 0 if all(x['matched'] for x in summary) else 1
if __name__=='__main__':raise SystemExit(main())
