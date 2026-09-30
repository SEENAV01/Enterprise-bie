from pathlib import Path
from dataclasses import asdict
from functools import lru_cache
from copy import deepcopy
import hashlib,json,tempfile,shutil,os
from bie.evaluation.benchmarks.models import digest,BenchmarkError
from bie.evaluation.benchmarks.browser.contracts import BrowserLimits,BrowserExecutionContext
from bie.evaluation.benchmarks.browser.service import binary_hash,execute
ROOT=Path(__file__).resolve().parents[2]
GAME=ROOT/'examples/section17_h4/game'
BROWSER=os.environ.get('BIE_SECTION17_CHROMIUM','/usr/lib/chromium/chromium')

def candidate(root=GAME,entry='index.html',origin='AUTHORED_FIXTURE'):
    return {'schema_version':'browser-candidate-1','entrypoint':entry,'origin_kind':origin,'load_mode':'CLASSIC_SNAPSHOT',
      'files':[{'path':p.relative_to(root).as_posix(),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(Path(root).rglob('*')) if p.is_file()]}

def reference(limits=BrowserLimits(),metric='BIE-EVAL-METRIC-014'):
    def ck(i,t,p,e):return {'id':i,'target':t,'property':p,'expected':e}
    def step(i,op='inspect',val=None,target=None,checks=None):return {'id':i,'action':op,'target':target,'value':val,'checks':checks}
    steps=[step('start',checks=[ck('question-text','#question','text','Which fraction equals 1/2?'),ck('question-visible','#question','visible',True),
             ck('question-in-view','#question','in_viewport',True),ck('question-contrast','#question','contrast_at_least',4.5),
             ck('button-name','#right','has_accessible_name',True)]),
        step('keyboard-wrong','press','Tab',checks=[ck('wrong-focus','#wrong','focused',True)]),
        step('wrong-answer','press','Enter',checks=[ck('wrong-feedback','#feedback','text','Try again. Multiply both numerator and denominator by 2.'),
                                                  ck('no-false-progress','#progress','text','Solved: 0/1')]),
        step('keyboard-right','press','Tab',checks=[ck('right-focus','#right','focused',True)]),
        step('right-answer','press','Enter',checks=[ck('right-feedback','#feedback','text','Correct. 1/2 = 2/4.'),
                 ck('progress-credit','#progress','text','Solved: 1/1'),ck('feedback-unclipped','#feedback','unclipped',True)]),
        step('fill-note','fill','Equivalent','#note',checks=[ck('note-value','#note','value','Equivalent')]),
        step('reset','reload',checks=[ck('reset-progress','#progress','text','Solved: 0/1')])]
    return {'schema_version':'browser-reference-1','metric_id':metric,'rubric_id':'fraction-ui-v1','version':'1.0.0',
        'evidence_grade':'AUTHORED_DIAGNOSTIC','limits_sha256':digest(asdict(limits)),'viewport':{'width':900,'height':800},
        'steps':steps,'objectives':[{'id':'equivalence-feedback','concept_id':'fractions-equivalence',
         'source_sha256':digest('Authored identity: 1/2 = 2/4; multiply numerator and denominator by two.'),
         'checks':[c['id'] for s in steps for c in s['checks']]}],'replay_count':2}

def context(root=GAME,limits=BrowserLimits()):
    return BrowserExecutionContext(str(root),BROWSER,binary_hash(BROWSER),limits,True)

@lru_cache(maxsize=1)
def _receipt():return execute(reference(),candidate(),context())
def receipt():return deepcopy(_receipt())

def assert_error(test,func,code=None):
    with test.assertRaises(BenchmarkError) as caught:func()
    if code:test.assertEqual(caught.exception.code,code)
    return caught.exception
