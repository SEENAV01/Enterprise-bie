"""AUDIO QA-001..005: deterministic findings, NEVER a product acceptance authority."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from .common import AudioError, fingerprint, text, refs, strict_json

TASKS = tuple(f'BIE-AUDIO-QA-{i:03}' for i in range(1,6))
PRIORITY = {'PASS':0,'REVIEW':1,'NOT_RUN':2,'BLOCKED':3,'FAIL':4}

@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    owner: str
    path: str
    detail: str
    source_refs: tuple[str,...] = ()
    def __post_init__(self):
        for k in ('code','owner','path','detail'): text(getattr(self,k),k,8192)
        if self.severity not in ('REVIEW','BLOCKED','FAIL'): raise AudioError('QA_SEVERITY')
        refs(self.source_refs,'finding source refs',False)

@dataclass(frozen=True)
class Check:
    task_id: str
    scope: str
    findings: tuple[Finding,...]
    metrics_json: str
    executed: bool = True
    def __post_init__(self):
        if self.task_id not in TASKS or type(self.executed)is not bool: raise AudioError('QA_TASK')
        text(self.scope,'QA scope')
        if type(self.findings)is not tuple or any(type(x)is not Finding for x in self.findings) or len(self.findings)>20000: raise AudioError('QA_FINDINGS')
        if type(strict_json(self.metrics_json))is not dict: raise AudioError('QA_METRICS')
    @property
    def status(self):
        values=[x.severity for x in self.findings]+(['PASS'] if self.executed else ['NOT_RUN'])
        return max(values,key=PRIORITY.get)
    def to_dict(self):
        return {'task_id':self.task_id,'scope':self.scope,'status':self.status,'executed':self.executed,
                'findings':[json.loads(json.dumps(asdict(x))) for x in self.findings],'metrics':strict_json(self.metrics_json)}

def check(task,scope,findings=(),metrics=None,*,executed=True):
    return Check(task,scope,tuple(findings),json.dumps(metrics or {},ensure_ascii=False,sort_keys=True,allow_nan=False),executed)

def aggregate(checks,binding):
    if type(checks)is not tuple or tuple(c.task_id for c in checks)!=TASKS: raise AudioError('QA_COMPLETE_TASK_SET_REQUIRED')
    if type(binding)is not dict or not binding: raise AudioError('QA_BINDING_REQUIRED')
    out={'schema_version':'bie.audio.qa-run/1','binding':binding,'checks':[c.to_dict() for c in checks],
         'status':max((c.status for c in checks),key=PRIORITY.get),
         'product_accepted':False,'cinematic_quality_verified':False,'actual_remotion_render_verified':False,
         'scope':'Source/media/DSP/timing checks plus explicit unverified listening and rendered-accessibility boundaries'}
    out['fingerprint']=fingerprint(out)
    return out

def validate_report(value):
    if type(value)is not dict: raise AudioError('QA_REPORT_TYPE')
    expected={'schema_version','binding','checks','status','product_accepted','cinematic_quality_verified','actual_remotion_render_verified','scope','fingerprint'}
    if set(value)!=expected or value['schema_version']!='bie.audio.qa-run/1': raise AudioError('QA_REPORT_FIELDS')
    if type(value['checks'])is not list: raise AudioError('QA_REPORT_CHECKS')
    checks=[]
    for row in value['checks']:
        if type(row)is not dict or set(row)!={'task_id','scope','status','executed','findings','metrics'}: raise AudioError('QA_CHECK_FIELDS')
        if type(row['findings'])is not list: raise AudioError('QA_FINDING_FIELDS')
        fs=[]
        for f in row['findings']:
            if type(f)is not dict or set(f)!={'code','severity','owner','path','detail','source_refs'} or type(f['source_refs'])is not list: raise AudioError('QA_FINDING_FIELDS')
            fs.append(Finding(**{**f,'source_refs':tuple(f['source_refs'])}))
        c=check(row['task_id'],row['scope'],fs,row['metrics'],executed=row['executed'])
        if c.status!=row['status']: raise AudioError('QA_STATUS_TAMPER')
        checks.append(c)
    required_boundaries={
        TASKS[0]: {'INDEPENDENT_PRONUNCIATION_UNVERIFIED'},
        TASKS[3]: {'INDEPENDENT_ACOUSTIC_ALIGNMENT_UNVERIFIED','ACTUAL_RENDERED_AV_SYNC_UNVERIFIED'},
        TASKS[4]: {'RENDERED_CAPTION_ACCESSIBILITY_UNVERIFIED'},
    }
    for c in checks:
        if c.executed:
            required=required_boundaries.get(c.task_id,set())
            if not required<={f.code for f in c.findings if f.severity=='REVIEW'}:
                raise AudioError('QA_REQUIRED_BOUNDARY_MISSING',c.task_id)
    canonical=aggregate(tuple(checks),value['binding'])
    # Fingerprints distinguish JSON representation only after exact schema validation.
    if fingerprint(canonical)!=fingerprint(value): raise AudioError('QA_REPORT_TAMPER')
    return value

def require_qa_pass(value):
    validate_report(value)
    if value['status']!='PASS': raise AudioError('QA_NOT_PASSED',value['status'])
    return value  # never grants product acceptance
