"""H4-001: separate trusted scenarios from candidate assets, with strict bounds."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import PurePosixPath
import re
from ..models import BenchmarkError, exact_fields, canonical_json, strict_loads, digest, digest_string, ident

SCHEMA = 'browser-reference-1'
CANDIDATE_SCHEMA = 'browser-candidate-1'
PROFILES = {'BIE-EVAL-METRIC-014': 'game-runtime-behavior-1',
            'BIE-EVAL-METRIC-015': 'rendered-accessibility-1'}
MIME = {'.html':'text/html', '.js':'text/javascript', '.mjs':'text/javascript',
        '.css':'text/css', '.json':'application/json', '.png':'image/png',
        '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.woff2':'font/woff2'}

@dataclass(frozen=True)
class BrowserLimits:
    max_files: int = 128
    max_bundle_bytes: int = 16_000_000
    max_file_bytes: int = 4_000_000
    max_steps: int = 80
    action_timeout_ms: int = 2000
    total_timeout_seconds: int = 45
    max_receipt_bytes: int = 8_000_000
    max_screenshot_bytes: int = 2_000_000
    max_events: int = 100
    def validate(self):
        bounds = {'max_files':(1,512), 'max_bundle_bytes':(1024,64_000_000),
          'max_file_bytes':(1,16_000_000),'max_steps':(1,200),
          'action_timeout_ms':(50,10000),'total_timeout_seconds':(1,120),
          'max_receipt_bytes':(1024,32_000_000),'max_screenshot_bytes':(1024,8_000_000),
          'max_events':(1,1000)}
        for key,(lo,hi) in bounds.items():
            x=getattr(self,key)
            if type(x) is not int or not lo<=x<=hi: raise BenchmarkError('BROWSER_LIMIT_INVALID',key)
        if self.max_file_bytes>self.max_bundle_bytes: raise BenchmarkError('BROWSER_LIMIT_INVALID')
        return self

@dataclass(frozen=True)
class BrowserExecutionContext:
    artifact_root: str
    chromium_executable: str
    chromium_sha256: str
    limits: BrowserLimits = BrowserLimits()
    # Operator-only opt-in for trusted authored fixtures. NEVER candidate supplied.
    allow_unsandboxed_diagnostic: bool = False
    def validate(self):
        self.limits.validate(); digest_string(self.chromium_sha256)
        if type(self.allow_unsandboxed_diagnostic) is not bool: raise BenchmarkError('BROWSER_CONTEXT_INVALID')
        if type(self.artifact_root) is not str or not self.artifact_root: raise BenchmarkError('BROWSER_CONTEXT_INVALID')
        if type(self.chromium_executable) is not str or not self.chromium_executable.startswith('/'):
            raise BenchmarkError('BROWSER_EXECUTABLE_NOT_PINNED')
        return self

def snapshot(value): return strict_loads(canonical_json(value))
def path(value):
    if type(value) is not str or not 1<=len(value)<=240: raise BenchmarkError('BROWSER_PATH_INVALID')
    if not re.fullmatch(r'[A-Za-z0-9_.\-/]+',value) or '\\' in value or value.startswith('/'):
        raise BenchmarkError('BROWSER_PATH_INVALID')
    if any(p in ('','.','..') for p in value.split('/')) or PurePosixPath(value).suffix.lower() not in MIME:
        raise BenchmarkError('BROWSER_PATH_INVALID')
    return value

def target(value):
    if type(value) is not str or not re.fullmatch(r'#[A-Za-z][A-Za-z0-9_-]{0,63}',value):
        raise BenchmarkError('BROWSER_TARGET_INVALID')
    return value

def bounded_text(value, maximum=2048):
    if type(value) is not str or len(value)>maximum or '\x00' in value: raise BenchmarkError('BROWSER_TEXT_INVALID')
    canonical_json(value); return value

def candidate(value,limits=BrowserLimits()):
    limits.validate(); c=snapshot(value)
    exact_fields(c,{'schema_version','entrypoint','files','origin_kind','load_mode'})
    if c['schema_version']!=CANDIDATE_SCHEMA: raise BenchmarkError('BROWSER_CANDIDATE_SCHEMA')
    if c['origin_kind'] not in ('AUTHORED_FIXTURE','CANONICAL_LAYOUT_UNVERIFIED'):
        raise BenchmarkError('BROWSER_ORIGIN_INVALID')
    if c['load_mode'] not in ('CLASSIC_SNAPSHOT','CANONICAL_SMOKE_BUNDLE','HTTP_MODULE_APP'): raise BenchmarkError('BROWSER_LOAD_MODE_INVALID')
    path(c['entrypoint'])
    if not c['entrypoint'].endswith('.html'): raise BenchmarkError('BROWSER_ENTRYPOINT_INVALID')
    if type(c['files']) is not list or not 1<=len(c['files'])<=limits.max_files: raise BenchmarkError('BROWSER_FILE_LIMIT')
    names=set(); total=0
    for row in c['files']:
        exact_fields(row,{'path','sha256','size_bytes'}); path(row['path']); digest_string(row['sha256'])
        if row['path'].casefold() in names: raise BenchmarkError('BROWSER_DUPLICATE_PATH')
        names.add(row['path'].casefold())
        if type(row['size_bytes']) is not int or not 1<=row['size_bytes']<=limits.max_file_bytes:
            raise BenchmarkError('BROWSER_FILE_LIMIT')
        total+=row['size_bytes']
    if total>limits.max_bundle_bytes: raise BenchmarkError('BROWSER_BUNDLE_LIMIT')
    if c['entrypoint'] not in {x['path'] for x in c['files']}: raise BenchmarkError('BROWSER_ENTRYPOINT_MISSING')
    return c

def content_identity(value):
    # Evidence label and input-directory rename do not create a new attempt.
    return digest({'entrypoint':value['entrypoint'],'load_mode':value['load_mode'],'files':sorted(value['files'],key=lambda r:r['path'])})

def reference(value,metric_id=None,limits=BrowserLimits()):
    if type(value) is dict and value.get('schema_version')=='browser-http-reference-1':
        from .served.contracts import reference as http_reference
        return http_reference(value,metric_id,limits)
    limits.validate(); r=snapshot(value)
    exact_fields(r,{'schema_version','metric_id','rubric_id','version','evidence_grade','limits_sha256',
        'viewport','steps','objectives','replay_count'})
    if r['schema_version']!=SCHEMA or r['metric_id'] not in PROFILES: raise BenchmarkError('BROWSER_REFERENCE_SCHEMA')
    if metric_id is not None and r['metric_id']!=metric_id: raise BenchmarkError('BROWSER_METRIC_MISMATCH')
    ident(r['rubric_id'])
    if r['version']!='1.0.0' or r['evidence_grade']!='AUTHORED_DIAGNOSTIC': raise BenchmarkError('BROWSER_UNSUPPORTED_REFERENCE_GRADE')
    if r['limits_sha256']!=digest(asdict(limits)): raise BenchmarkError('BROWSER_LIMIT_PIN_MISMATCH')
    exact_fields(r['viewport'],{'width','height'})
    for k in ('width','height'):
        if type(r['viewport'][k]) is not int or not 200<=r['viewport'][k]<=1920: raise BenchmarkError('BROWSER_VIEWPORT_INVALID')
    if type(r['replay_count']) is not int or r['replay_count'] not in (1,2): raise BenchmarkError('BROWSER_REPLAY_INVALID')
    if type(r['steps']) is not list or not 1<=len(r['steps'])<=limits.max_steps: raise BenchmarkError('BROWSER_STEP_LIMIT')
    step_ids=set(); check_ids=set(); assertions=0
    prop_types={'text':str,'value':str,'visible':bool,'enabled':bool,'focused':bool,'checked':bool,
                'in_viewport':bool,'unclipped':bool,'has_accessible_name':bool,'contrast_at_least':(int,float)}
    for s in r['steps']:
        exact_fields(s,{'id','action','target','value','checks'}); ident(s['id'])
        if s['id'] in step_ids: raise BenchmarkError('BROWSER_DUPLICATE_STEP')
        step_ids.add(s['id'])
        if s['action'] not in ('inspect','click','press','fill','reload'): raise BenchmarkError('BROWSER_ACTION_INVALID')
        if s['action'] in ('click','fill'): target(s['target'])
        elif s['target'] is not None: raise BenchmarkError('BROWSER_UNUSED_TARGET')
        if s['action']=='press':
            if s['value'] not in ('Tab','Shift+Tab','Enter','Space','ArrowDown','ArrowUp','ArrowLeft','ArrowRight','Escape'):
                raise BenchmarkError('BROWSER_KEY_INVALID')
        elif s['action']=='fill': bounded_text(s['value'],1000)
        elif s['value'] is not None: raise BenchmarkError('BROWSER_UNUSED_VALUE')
        if type(s['checks']) is not list or not 1<=len(s['checks'])<=20: raise BenchmarkError('BROWSER_EMPTY_CHECKS')
        for chk in s['checks']:
            exact_fields(chk,{'id','target','property','expected'}); ident(chk['id']); target(chk['target'])
            if chk['id'] in ('runtime-health','fresh-context-replay') or chk['id'] in check_ids: raise BenchmarkError('BROWSER_DUPLICATE_CHECK')
            check_ids.add(chk['id']); assertions+=1
            prop=chk['property']; exp=chk['expected']
            if prop not in prop_types: raise BenchmarkError('BROWSER_PROPERTY_INVALID')
            if prop=='contrast_at_least':
                if type(exp) not in (int,float) or not 1<=exp<=21: raise BenchmarkError('BROWSER_EXPECTATION_INVALID')
            elif type(exp) is not prop_types[prop]: raise BenchmarkError('BROWSER_EXPECTATION_INVALID')
            if type(exp) is str: bounded_text(exp)
    if assertions>400: raise BenchmarkError('BROWSER_CHECK_LIMIT')
    if type(r['objectives']) is not list or not 1<=len(r['objectives'])<=50: raise BenchmarkError('BROWSER_OBJECTIVES_INVALID')
    objectives=set();covered=set()
    for obj in r['objectives']:
        exact_fields(obj,{'id','concept_id','source_sha256','checks'});ident(obj['id']);ident(obj['concept_id']);digest_string(obj['source_sha256'])
        if obj['id'] in objectives:raise BenchmarkError('BROWSER_DUPLICATE_OBJECTIVE')
        objectives.add(obj['id'])
        if type(obj['checks']) is not list or not 1<=len(obj['checks'])<=400 or any(type(x) is not str for x in obj['checks']) or len(set(obj['checks']))!=len(obj['checks']):
            raise BenchmarkError('BROWSER_OBJECTIVE_CHECKS_INVALID')
        if any(x not in check_ids for x in obj['checks']):raise BenchmarkError('BROWSER_OBJECTIVE_CHECK_MISSING')
        covered.update(obj['checks'])
    if covered!=check_ids:raise BenchmarkError('BROWSER_UNMAPPED_CHECKS')
    return r
