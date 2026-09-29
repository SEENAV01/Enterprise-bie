"""SYNTHETIC test credentials and deterministic fixtures; NEVER production trust."""
from dataclasses import asdict,replace
from pathlib import Path
from io import BytesIO
import copy,hashlib,hmac,json,tempfile
from PIL import Image
from bie.qa.release_v2.contracts import ArtifactRef,canonical_bytes,digest,ReleaseCandidate
from bie.qa.repair_v2.models import Snapshot
from bie.qa.repair_v2.worker import validator_digest
from bie.qa.regression_v2.models import *
from bie.qa.regression_v2.models import binding
from bie.qa.regression_v2 import collect,evaluate
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
NOW=1801000000
SECRET=b'SYNTHETIC-REG017-TEST-KEY-NOT-FOR-PRODUCTION'
KEY=ReviewKey('synthetic-key',SECRET,'synthetic-assessor','1','test-group',('inventory','support','mapping'),'operator_managed')
VERIFIER=ReviewVerifier((KEY,))
def image(pixel=None,size=(16,12),rgba=False):
    im=Image.new('RGBA' if rgba else 'RGB',size,(220,220,220,255) if rgba else (220,220,220))
    if pixel:
        for xy,value in pixel:im.putpixel(xy,value)
    b=BytesIO();im.save(b,format='PNG');return b.getvalue()
def semantic():
    return dict(schema_version='bie.qa.semantic-snapshot/1',concept_ids=['addition','number'],claims=[dict(claim_id='claim1',concept_id='addition',text='Two plus two equals four.',source_refs=['textbook-anchor'],conditions=['ordinary integer addition'],expression='2+2=4',status='SUPPORTED',confidence_ppm=900000)],relations=[{'from':'addition','predicate':'uses','to':'number'}])
def game(mode='OBSERVED_BROWSER'):
    return dict(schema_version='bie.qa.game-traces/1',runs=[dict(scenario_id='basic',seed=1,execution_mode=mode,steps=[
        dict(action_id='INIT',input={},state={'answer':None,'submitted':False},score=0,feedback='Choose an answer.',terminal=False,enabled_actions=['correct']),
        dict(action_id='correct',input={'answer':4},state={'answer':4,'submitted':True},score=1,feedback='Two plus two equals four.',terminal=True,enabled_actions=['reset'])])])
def validator(root,snapshot,rule):
    data=json.loads((Path(root)/'generated/value.json').read_text());expected=json.loads((Path(root)/'fixtures/expected.json').read_text())
    ok=type(data['answer']) is int and data['answer']==expected['answer']
    return (Observation('arithmetic','PASS' if ok else 'FAIL',() if ok else ('BAD_ARITHMETIC',),canonical_bytes({'computed':data['answer'],'expected':expected['answer']}).decode()),)
def bad_return(root,snapshot,rule):return []
def omit_case(root,snapshot,rule):return ()
def mutator(root,snapshot,rule):
    (Path(root)/'generated/value.json').write_text('{"answer":9}')
    return (Observation('arithmetic','PASS',(),'{"claimed":true}'),)
def exception(root,snapshot,rule):raise RuntimeError('deliberate')
def timeout(root,snapshot,rule):
    import time
    time.sleep(3)
    return validator(root,snapshot,rule)
def make_ref(aid,path,data,role='support'):return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)
class Fixture:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.left=self.root/'baseline';self.right=self.root/'candidate';self.evidence=self.root/'evidence'
        for p in (self.left,self.right,self.evidence):p.mkdir()
        self.blobs={'fixture':('fixtures/expected.json',canonical_bytes({'answer':4}),'source'),
            'calc':('generated/value.json',canonical_bytes({'answer':4}),'support'),
            'sem':('generated/semantic.json',canonical_bytes(semantic()),'support'),
            'visual':('generated/frame.png',image(),'video'),
            'game':('generated/game.json',canonical_bytes(game()),'game')}
        self.a=copy.deepcopy(self.blobs);self.b=copy.deepcopy(self.blobs);self.refresh()
    def close(self):self.tmp.cleanup()
    def _snapshot(self,data,root,revision):
        # Only overwrite existing fixture test data, never any package source.
        for f in root.rglob('*'):
            if f.is_file():f.unlink()
        refs=[]
        for aid,(path,payload,role) in data.items():
            p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload);refs.append(make_ref(aid,path,payload,role))
        return Snapshot('run-'+revision[0],revision,tuple(sorted(refs,key=lambda r:r.artifact_id)))
    def refresh(self,*,permit=True,callback=validator,phase_timeout=5):
        self.baseline=self._snapshot(self.a,self.left,'a'*40);self.candidate=self._snapshot(self.b,self.right,'b'*40)
        aa={r.artifact_id:r for r in self.baseline.artifacts};bb={r.artifact_id:r for r in self.candidate.artifacts};per=[]
        for aid in sorted(set(aa)|set(bb)):
            if aa.get(aid)!=bb.get(aid) and aid!='fixture' and permit:
                per.append(ChangePermit(aid,digest(asdict(aa[aid])) if aid in aa else '',digest(asdict(bb[aid])) if aid in bb else '','Synthetic pre-approved byte change, not semantic acceptance.'))
        self.policy=RegressionPolicy('test-policy',(SuiteCheck('math',validator_digest(callback),('arithmetic',),('fixture',)),),('fixture',),tuple(per),(SemanticRule('sem',('claim1',),('addition',)),),(VisualRule('visual','scene1-frame0',16,12),),(GameRule('game',(Scenario('basic',1,('INIT','correct')),)),),phase_timeout_seconds=phase_timeout)
        self.record=self.synthetic_record();self.rebind()
    def synthetic_record(self):
        phases={}
        for i,(name,snap) in enumerate((('baseline',self.baseline),('candidate',self.candidate))):
            phases[name]=dict(phase=name,snapshot_digest=snap.content_digest,execution_id='synthetic-'+name,executed_at=NOW,wall_started_ns=100+i*100,wall_finished_ns=150+i*100,elapsed_ms=1,worker_executed=True,process_exit=0,error='',checks=[dict(check_id=r.check_id,validator_digest=r.validator_digest,fixture_ids=list(r.fixture_ids),cases=[asdict(Observation(cid,'PASS',(),'{"synthetic":true}')) for cid in r.case_ids]) for r in self.policy.checks])
        env={'fixture_scope':'SYNTHETIC_RECORD_NOT_EXECUTION'}
        return dict(schema_version='bie.qa.regression-execution/1',binding=binding('compare',self.baseline,self.candidate,self.policy),evaluated_at=NOW,environment=env,environment_digest=digest(env),**phases,full_repository_regression_run=False,product_accepted=False)
    def rebind(self):
        payload=canonical_bytes(self.record);self.ref=make_ref('execution','execution.json',payload,'report');(self.evidence/self.ref.path).write_bytes(payload)
        self.request=RegressionRequest('compare',self.baseline,self.candidate,self.ref)
        ids=tuple(sorted({x.artifact_id for x in self.baseline.artifacts+self.candidate.artifacts}))
        self.reviews=tuple(self.review(sub,purpose,ev,i) for i,(sub,purpose,ev) in enumerate((('regression-inventory','inventory',ids),('regression-execution','support',('execution',)),('semantic-sem','mapping',('sem',)))))
    def review(self,subject,purpose,ids,i):
        r=Review('synthetic-review-'+str(i),self.request.content_digest,self.policy.content_digest,subject,purpose,'VERIFIED',ids,1000000,'SYNTHETIC test authorization; not a real assessor.','synthetic-assessor','1',NOW-1,NOW+100,'synthetic-key')
        return replace(r,signature=hmac.new(SECRET,r.signing_bytes(),hashlib.sha256).hexdigest())
    def evaluate(self,**kw):return evaluate(self.request,self.left,self.right,self.evidence,self.policy,as_of=kw.pop('as_of',NOW),reviews=kw.pop('reviews',self.reviews),verifier=kw.pop('verifier',VERIFIER),**kw)
    def set_json(self,aid,obj,which='b'):
        table=getattr(self,which);path,_,role=table[aid];table[aid]=(path,canonical_bytes(obj),role)
    def actual(self,callback=validator):
        self.record=collect('compare',self.baseline,self.candidate,self.left,self.right,self.policy,registry={'math':callback},as_of=NOW);self.rebind();return self.record

def codes(result,index=None):
    reports=result.reports if index is None else (result.reports[index],)
    return {f.code for r in reports for f in r.findings}
