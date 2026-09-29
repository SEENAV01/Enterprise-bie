"""Authored test fixtures; ALL positive review identities/keys are synthetic."""
from pathlib import Path
from dataclasses import asdict,replace
import hashlib,hmac,json,tempfile,unittest,sys,time,os
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from bie.qa.release_v2.contracts import *
from bie.qa.source_v2.models import Report,Finding
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
from bie.qa.repair_v2 import *
from bie.qa.repair_v2.planner import approved,inspect_report,validate_proposal
from bie.qa.repair_v2.adapters import bind_report
from bie.qa.repair_v2.codec import *
from bie.qa.repair_v2.controller import verify_snapshot
from bie.qa.repair_v2.worker import validator_digest
NOW=1790485200
KEY=ReviewKey('synthetic-key',b'not-a-production-secret-0123456789','synthetic-operator','1','synthetic-group',('inventory','inference'),'operator_managed')

def signed(subject,purpose,request,policy,evidence,*,key=KEY,verdict='VERIFIED'):
    r=Review('review-'+subject,request,policy.content_digest,subject,purpose,verdict,tuple(sorted(evidence)),1000000,'SYNTHETIC fixture approval; not live assessor',key.evaluator_id,key.evaluator_version,NOW-1,NOW+600,key.key_id)
    return replace(r,signature=hmac.new(key.secret,r.signing_bytes(),hashlib.sha256).hexdigest())

def outcome(name,root,snapshot,policy,status='PASS',codes=()):
    with SnapshotStore(root) as store:values=[(a.path,hashlib.sha256(store.read(a)).hexdigest()) for a in snapshot.artifacts]
    return CheckOutcome(name,snapshot.content_digest,policy.content_digest,status,codes,digest(values))
from bie.qa.source_v2.io import SnapshotStore

def syntax_check(root,snapshot,policy):
    from bie.qa.math_v2.expression import parse
    try:parse((Path(root)/'generated/lesson.txt').read_text());status='PASS';codes=()
    except ContractError:status='FAIL';codes=('INVALID_EXPRESSION',)
    return outcome('syntax',root,snapshot,policy,status,codes)

def numeric_check(root,snapshot,policy):
    from bie.qa.math_v2.expression import parse
    from bie.qa.math_v2.algebra import interval
    try:r=interval(parse((Path(root)/'generated/lesson.txt').read_text()),{});ok=r.lo==r.hi==5
    except ContractError:ok=False
    return outcome('numeric',root,snapshot,policy,'PASS' if ok else 'FAIL',() if ok else ('WRONG_SUM',))

def regression_check(root,snapshot,policy):
    ok=(Path(root)/'generated/caption.txt').read_bytes()==b'keep caption'
    return outcome('regression',root,snapshot,policy,'PASS' if ok else 'FAIL',() if ok else ('CAPTION_REGRESSION',))

def hang_check(root,snapshot,policy):time.sleep(4);return outcome('numeric',root,snapshot,policy)
def exception_check(root,snapshot,policy):raise RuntimeError('synthetic failure')
def wrong_binding(root,snapshot,policy):return replace(numeric_check(root,snapshot,policy),candidate_digest='0'*64)
def mutate_stage(root,snapshot,policy):
    (Path(root)/'generated/lesson.txt').write_bytes(b'poisoned');return CheckOutcome('numeric',snapshot.content_digest,policy.content_digest,'PASS',(),digest('forged-report'))
def inject_extra(root,snapshot,policy):
    (Path(root)/'extra.txt').write_bytes(b'not approved');return numeric_check(root,snapshot,policy)

def review_check(root,snapshot,policy):return outcome('numeric',root,snapshot,policy,'REVIEW',('NEEDS_REVIEW',))
def wrong_check(root,snapshot,policy):return outcome('other',root,snapshot,policy)

class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name);self.root=self.home/'original';self.root.mkdir();self.out=self.home/'stages';self.out.mkdir()
        self.verifier=ReviewVerifier((KEY,))
        self.snapshot=Snapshot('fixture-run','a'*40,(
            self.write('source','sources/book.txt',b'An authored diagnostic: two plus three is five.','source'),
            self.write('lesson','generated/lesson.txt',b'2+4','support'),
            self.write('caption','generated/caption.txt',b'keep caption','support'),
            self.write('video','media/video.bin',b'NOT-A-REAL-VIDEO','video'),
            self.write('game','media/game.bin',b'NOT-A-REAL-GAME','game')))
        self.policy=RepairPolicy('fixture-policy',(FailureRule('BIE-QA-MATH-003','DEMO_WRONG_SUM','CONTENT','MATH',True),),
            (OwnerRoute('MATH',('generated/lesson.txt','generated/caption.txt'),('numeric',)),),
            (CheckNode('syntax',(),validator_digest(syntax_check)),CheckNode('numeric',('syntax',),validator_digest(numeric_check)),CheckNode('regression',('numeric',),validator_digest(regression_check))),('regression',))
        self.make_batch()
        self.checks={'syntax':syntax_check,'numeric':numeric_check,'regression':regression_check}
    def tearDown(self):self.temp.cleanup()
    def write(self,aid,path,data,role='support'):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)
    def make_batch(self,findings=None):
        if findings is None:findings=(Finding('DEMO_WRONG_SUM','BLOCKER','sum','UNTRUSTED_OWNER','Actual bounded arithmetic diagnostic failed.'),)
        r=Report('BIE-QA-MATH-003',digest('request'),digest('evaluator-policy'),digest('numeric-evidence'),NOW,findings,(),tuple(a.artifact_id for a in self.snapshot.artifacts),('Authored diagnostic, no real-book claim.',))
        b,data=bind_report(r,'math-report','reports/math.json');self.write(b.artifact.artifact_id,b.artifact.path,data,'report')
        self.batch=FailureBatch(self.snapshot.run_id,self.snapshot.revision,self.snapshot.content_digest,(b,));self.report=r
    def inv(self):return (signed('repair-findings','inventory',self.batch.content_digest,self.policy,tuple(x.artifact.artifact_id for x in self.batch.reports)),)
    def plan(self,**kw):
        return classify(self.batch,self.snapshot,self.root,self.policy,as_of=NOW,reviews=kw.get('reviews',self.inv()),verifier=kw.get('verifier',self.verifier))
    def proposal(self,text=b'2+3',pid='repair-one',**kw):
        a=self.write('replacement-'+pid,'proposals/'+pid+'.txt',text)
        p=Proposal(pid,self.snapshot.run_id,self.snapshot.revision,self.snapshot.content_digest,self.policy.content_digest,self.plan().content_digest,'MATH',tuple(f.failure_id for f in self.plan().failures if f.automatic),(Replacement('generated/lesson.txt',self.snapshot.artifacts[1].sha256,a),))
        return replace(p,**kw) if kw else p
    def auth(self,p):return (signed(p.proposal_id,'inference',p.content_digest,self.policy,tuple(r.artifact.artifact_id for r in p.replacements)),)
    def journal(self):return Journal(self.home/'journal.sqlite',self.snapshot,self.policy)
    def run_proposal(self,p=None,**kw):
        # Fault-injection callbacks are explicitly pinned by this synthetic operator.
        callbacks=kw.get('checks',self.checks)
        if p is None and type(callbacks) is dict and set(self.checks)<=set(callbacks):
            self.policy=replace(self.policy,checks=tuple(replace(n,validator_digest=validator_digest(callbacks[n.check_id])) for n in self.policy.checks))
        p=p or self.proposal()
        return execute(self.batch,self.snapshot,self.root,self.policy,p,as_of=NOW,output_root=kw.pop('output_root',self.out),journal=kw.pop('journal',self.journal()),checks=kw.pop('checks',self.checks),inventory_reviews=kw.pop('inventory_reviews',self.inv()),proposal_reviews=kw.pop('proposal_reviews',self.auth(p)),verifier=kw.pop('verifier',self.verifier),**kw)
