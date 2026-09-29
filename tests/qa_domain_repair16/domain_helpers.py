"""AUTHORED SYNTHETIC fixtures; no production credentials or live assessor claims."""
import sys,tempfile,unittest,json,hashlib,hmac
from pathlib import Path
from dataclasses import asdict,replace
W=Path(__file__).resolve().parents[2]
for name in ('source','reasoning','pedagogy','director'):sys.path.insert(0,str(W/'tests'/('qa_'+name+'16')))
import source_helpers as sh,re_helpers as rh,ped_helpers as ph,dir_helpers as dh
from bie.qa.release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,digest
from bie.qa.source_v2.io import SnapshotStore
from bie.qa.source_v2.models import Report,Finding
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
from bie.qa.repair_v2 import *
from bie.qa.repair_v2.models import CheckOutcome
from bie.qa.repair_v2.adapters import bind_report
from bie.qa.repair_v2.worker import validator_digest
from bie.qa.domain_repair_v2 import *
from bie.qa.domain_repair_v2 import source,reasoning,pedagogy,director
from bie.qa.domain_repair_v2.common import *
from bie.qa.domain_repair_v2.service import WORKERS
from bie.qa.domain_repair_v2.validation import evaluate_candidate,status_of
HELPERS={4:sh,5:rh,6:ph,7:dh}
KEY=ReviewKey('synthetic-domain-key',b'SYNTHETIC_ONLY_NOT_A_DEPLOYMENT_KEY_14','synthetic-domain-reviewer','1','synthetic-domain-group',('inventory','inference'),'operator_managed')
CONTEXTS={}

def options(number,r,p):
    h=HELPERS[number]
    if number==4:
        k=h.key();return dict(assessments=(h.signed(r,p,k),),verifier=h.AssessmentVerifier((k,)))
    return h.options(r,p)

def domain_check(root,snapshot,policy):
    """TEST-ONLY trusted callback: obtains synthetic reviewer fixtures, not a service."""
    ctx=CONTEXTS[policy.content_digest];ref=next(a for a in snapshot.artifacts if a.path=='generated/request.json')
    with SnapshotStore(root) as store:r=read_request(ctx.task,store.read(ref))
    result=evaluate_candidate(ctx.task,r,root,ctx.dp,as_of=ctx.now,**(options(ctx.number,r,ctx.dp) if ctx.positive_assessments else {}))
    state=status_of(result);status={'CHECKS_PASSED':'PASS','BLOCKED':'FAIL','REVIEW_REQUIRED':'REVIEW'}[state]
    return CheckOutcome('domain',snapshot.content_digest,policy.content_digest,status,() if status=='PASS' else ('ACTUAL_DOMAIN_'+state,),digest(result.to_dict()))

def preserve_check(root,snapshot,policy):
    ctx=CONTEXTS[policy.content_digest]
    with SnapshotStore(root) as store:ok=all(store.read(a)==ctx.original_bytes[a.path] for a in snapshot.artifacts if a.path!='generated/request.json')
    return CheckOutcome('preserve',snapshot.content_digest,policy.content_digest,'PASS' if ok else 'FAIL',() if ok else ('PROTECTED_BYTES_CHANGED',),digest(dict(ok=ok)))

def forged_check(root,snapshot,policy):
    return CheckOutcome('domain',snapshot.content_digest,policy.content_digest,'FAIL',('DELIBERATE_REGRESSION',),digest('failed'))

class Context:
    def __init__(self,root,number):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.number=number;self.task=f'BIE-QA-REPAIR-{number:03}';h=HELPERS[number];self.now=h.NOW
        if number==4:self.good,self.candidate,self.dp=h.fixture(self.root)
        else:self.good,self.dp,self.candidate=h.fixture(self.root)
        r=self.good
        if number==4:self.bad=replace(r,blocks=(replace(r.blocks[0],text='Damaged synthetic extraction.'),))
        elif number==5:self.bad=replace(r,steps=(replace(r.steps[0],premise_ids=('s1',)),))
        elif number==6:self.bad=replace(r,routes=(replace(r.routes[0],segment_ids=tuple(reversed(r.routes[0].segment_ids))),),events=tuple(replace(e,wait_for_response=False) if e.kind in ('solution','feedback') else e for e in r.events))
        else:self.bad=replace(r,scenes=(replace(r.scenes[0],duration_ms=29000),r.scenes[1]))
        self.positive_assessments=True;self.verifier=ReviewVerifier((KEY,));self.limits=Limits()
        self.set_bad(self.bad)
    def write(self,path,data,aid='generated-request',role='support'):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)
    def set_bad(self,bad):
        self.bad=bad;self.target=self.write('generated/request.json',canonical_bytes(asdict(bad)))
        src=source_of(bad);self.snapshot=Snapshot(src.run_id,src.revision,self.candidate.artifacts+(self.target,))
        self.original_bytes={a.path:(self.root/a.path).read_bytes() for a in self.snapshot.artifacts}
        res=evaluate_candidate(self.task,bad,self.root,self.dp,as_of=self.now,**options(self.number,bad,self.dp))
        area={4:'provenance',5:'validity',6:'sequence',7:'pacing'}[self.number];report=getattr(res,area)
        assert report.status=='BLOCKED',(self.task,report.to_dict())
        self.bound,data=bind_report(report,'failure-report','reports/failure.json');self.write(self.bound.artifact.path,data,self.bound.artifact.artifact_id,'report')
        self.batch=FailureBatch(self.snapshot.run_id,self.snapshot.revision,self.snapshot.content_digest,(self.bound,))
        owner=TASK_OWNERS[self.task];rules=tuple(FailureRule(report.task_id,c,'CONTENT',owner,True) for c in sorted({f.code for f in report.findings if f.severity=='BLOCKER'}))
        self.policy=RepairPolicy('domain-repair-test-'+str(self.number),rules,(OwnerRoute(owner,(self.target.path,),('domain',)),),
          (CheckNode('domain',(),validator_digest(domain_check)),CheckNode('preserve',('domain',),validator_digest(preserve_check))),('preserve',),worker_timeout_seconds=10)
        self.refresh()
    def refresh(self):
        self.job=Job('repair-job-'+str(self.number),self.task,self.target,self.snapshot.content_digest,self.batch.content_digest,self.policy.content_digest,self.dp.content_digest,self.limits.content_digest)
        CONTEXTS[self.policy.content_digest]=self
    def signed(self,subject,purpose,request_digest,evidence,**kw):
        key=kw.pop('key',KEY)
        r=Review('review-'+subject,request_digest,self.policy.content_digest,subject,purpose,'VERIFIED',tuple(sorted(evidence)),1000000,
                 'SYNTHETIC diagnostic authorization only; not a deployed assessor.',key.evaluator_id,key.evaluator_version,self.now-1,self.now+60,key.key_id)
        r=replace(r,**kw)
        return replace(r,signature=hmac.new(key.secret,r.signing_bytes(),hashlib.sha256).hexdigest())
    def inv(self):return (self.signed('repair-findings','inventory',self.batch.content_digest,(self.bound.artifact.artifact_id,)),)
    def gen_auth(self):return (self.signed(self.job.job_id,'inference',self.job.content_digest,(self.target.artifact_id,)),)
    def kwargs(self):return dict(as_of=self.now,limits=self.limits,inventory_reviews=self.inv(),generation_reviews=self.gen_auth(),verifier=self.verifier)
    def generate(self,**kw):
        opts=self.kwargs();opts.update(kw)
        return generate(self.job,self.batch,self.snapshot,self.root,self.policy,self.dp,**opts)
    def prepare(self,**kw):
        opts=self.kwargs();opts.update(kw)
        return prepare(self.job,self.batch,self.snapshot,self.root,self.policy,self.dp,**opts)
    def execute(self,proposal,**kw):
        out=self.root.parent/'staged';out.mkdir(exist_ok=True)
        j=Journal(self.root.parent/('journal-'+str(self.number)+'.sqlite'),self.snapshot,self.policy)
        opts=dict(as_of=self.now,output_root=out,journal=j,checks={'domain':domain_check,'preserve':preserve_check},inventory_reviews=self.inv(),
          proposal_reviews=(self.signed(proposal.proposal_id,'inference',proposal.content_digest,tuple(x.artifact.artifact_id for x in proposal.replacements)),),verifier=self.verifier)
        opts.update(kw)
        try:return execute(self.batch,self.snapshot,self.root,self.policy,proposal,**opts)
        finally:j.close()

class Base(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.home=Path(self.temp.name)
    def context(self,n=4):return Context(self.home/('domain'+str(n)),n)
    def assertError(self,code,fn,*a,**kw):
        with self.assertRaises(ContractError) as e:fn(*a,**kw)
        self.assertEqual(e.exception.code,code)
