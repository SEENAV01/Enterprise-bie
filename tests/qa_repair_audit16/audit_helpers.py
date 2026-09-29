"""Authored diagnostics. Every key/approval is explicitly SYNTHETIC, not a service."""
from pathlib import Path
from dataclasses import asdict,replace
import sys,hashlib,hmac,json,time,os
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/qa_repair16')]
from repair_helpers import Fixture,NOW,KEY,signed,validator_digest
from bie.qa.release_v2.contracts import *
from bie.qa.source_v2.io import SnapshotStore
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
from bie.qa.repair_v2 import Journal
from bie.qa.repair_v2.codec import decode
from bie.qa.repair_audit_v2 import *
from bie.qa.repair_audit_v2.io import write_new
from bie.qa.repair_audit_v2.evidence import inspect_attempt,inspect_journal
from bie.qa.repair_audit_v2.regression import inspect_regression
AUDIT_KEY=ReviewKey('synthetic-audit-key',b'SYNTHETIC_AUDIT_016_NOT_A_SECRET_0000','synthetic-auditor','1',
    'synthetic-audit-group',('support',),'operator_managed')

def obs(name,ok,witness):
    return Observation(name,'PASS' if ok else 'FAIL',() if ok else ('EXPECTED_VALUE_NOT_MET',),canonical_bytes(witness).decode('utf8'))

def syntax_cases(root,snapshot,repair_policy,rule):
    from bie.qa.math_v2.expression import parse
    ref=next(a for a in snapshot.artifacts if a.artifact_id=='lesson')
    with SnapshotStore(root) as store:raw=store.read(ref)
    try:parse(raw.decode());ok=True
    except ContractError:ok=False
    return (obs('parse',ok,dict(actual_sha256=ref.sha256,parsed=ok)),)

def numeric_cases(root,snapshot,repair_policy,rule):
    from bie.qa.math_v2.expression import parse
    from bie.qa.math_v2.algebra import interval
    ref=next(a for a in snapshot.artifacts if a.artifact_id=='lesson')
    with SnapshotStore(root) as store:raw=store.read(ref)
    try:
        value=interval(parse(raw.decode()),{});correct=value.lo==value.hi==5
        witness=dict(lo=str(value.lo),hi=str(value.hi),expected='5')
    except ContractError:correct=False;witness=dict(error='INVALID_EXPRESSION')
    return (obs('sum',correct,witness),)

def caption_cases(root,snapshot,repair_policy,rule):
    ref=next(a for a in snapshot.artifacts if a.artifact_id=='caption')
    with SnapshotStore(root) as store:raw=store.read(ref)
    return (obs('caption',raw==b'keep caption',dict(actual_sha256=ref.sha256,expected_sha256=hashlib.sha256(b'keep caption').hexdigest())),)

def omitted_cases(root,snapshot,repair_policy,rule):return ()
def exception_cases(root,snapshot,repair_policy,rule):raise RuntimeError('SYNTHETIC worker failure')
def timeout_cases(root,snapshot,repair_policy,rule):time.sleep(4);return numeric_cases(root,snapshot,repair_policy,rule)
def mutate_cases(root,snapshot,repair_policy,rule):
    (Path(root)/'generated/lesson.txt').write_bytes(b'5')
    return numeric_cases(root,snapshot,repair_policy,rule)
def added_file_cases(root,snapshot,repair_policy,rule):
    (Path(root)/'extra.txt').write_text('SYNTHETIC extra')
    return numeric_cases(root,snapshot,repair_policy,rule)

def audit_review(request,policy,now=NOW,key=AUDIT_KEY):
    r=Review('review-audit-execution',request.content_digest,policy.content_digest,'repair-audit-execution','support',
        'VERIFIED',tuple(sorted(a.artifact_id for a in request.evidence_refs)),1000000,
        'SYNTHETIC diagnostic attestation, not independent operational execution proof.',key.evaluator_id,key.evaluator_version,
        now-1,now+600,key.key_id)
    return replace(r,signature=hmac.new(key.secret,r.signing_bytes(),hashlib.sha256).hexdigest())

class AuditFixture(Fixture):
    def setUp(self):
        super().setUp()
        self.p=self.proposal();self.j=self.journal()
        self.addCleanup(self.j.close)
        self.attempt=self.run_proposal(self.p,journal=self.j)
        assert self.attempt['status']=='STAGED_FOR_REVIEW',self.attempt
        self.candidate_root=Path(self.attempt['staged_directory'])
        self.ap=AuditPolicy('audit-policy',(
            CaseRule('syntax',('parse',),('source',),validator_digest(syntax_cases)),
            CaseRule('numeric',('sum',),('source',),validator_digest(numeric_cases)),
            CaseRule('regression',('caption',),('source',),validator_digest(caption_cases))),
            tuple(TargetCase(fid,'numeric','sum') for fid in self.p.target_failure_ids),('source','video','game'))
        self.registry=dict(syntax=syntax_cases,numeric=numeric_cases,regression=caption_cases)
        self.reg=collect_regression(self.snapshot,self.p,self.root,self.candidate_root,self.policy,self.ap,registry=self.registry,as_of=NOW)
        self.journal_data=self.j.export()
        self.request=AuditRequest(self.snapshot,self.batch,self.p,
            self.put('audit/attempt.json',self.attempt,'attempt'),self.put('audit/journal.json',self.journal_data,'journal'),
            self.put('audit/regression.json',self.reg,'regression'))
        self.verifier=ReviewVerifier((KEY,AUDIT_KEY))
    def put(self,path,obj,aid,role='report'):
        return self.write(aid,path,canonical_bytes(obj),role)
    def audit(self,**kw):
        opts=dict(as_of=NOW,inventory_reviews=self.inv(),proposal_reviews=self.auth(self.p),
            audit_reviews=(audit_review(self.request,self.ap),),verifier=self.verifier)
        opts.update(kw)
        return evaluate(self.request,self.root,self.candidate_root,self.policy,self.ap,**opts)
    def codes(self,result=None):
        r=result or self.audit()
        return {x.code for y in (r.evidence,r.regression) for x in y.findings}
    def assertCode(self,code,result=None):
        r=result or self.audit();self.assertIn(code,self.codes(r));self.assertNotEqual(r.status,'CHECKS_PASSED')
    def edit_attempt(self,fn,*,rehash=True,rechain=True):
        obj=json.loads(canonical_bytes(self.attempt));fn(obj)
        if rehash:obj['receipt_digest']=digest({k:v for k,v in obj.items() if k not in ('receipt_digest','journal_head')})
        if rechain:
            j=json.loads(canonical_bytes(self.journal_data));j['events'][-1]['receipt_digest']=obj['receipt_digest']
            head=digest(j['binding'])
            for n,row in enumerate(j['events'],1):head=digest(dict(seq=n,body=row,previous=head))
            j['chain_head']=head;obj['journal_head']=head;self.journal_data=j
            self.request=replace(self.request,journal=self.put('audit/journal.json',j,'journal'))
        self.attempt=obj;self.request=replace(self.request,attempt=self.put('audit/attempt.json',obj,'attempt'))
    def edit_journal(self,fn,*,rechain=True):
        j=json.loads(canonical_bytes(self.journal_data));fn(j)
        if rechain:
            head=digest(j['binding'])
            selected=self.attempt['journal_head']
            for n,row in enumerate(j['events'],1):
                head=digest(dict(seq=n,body=row,previous=head))
                if row.get('kind')=='FINISHED' and row.get('attempt')==self.attempt['attempt']:selected=head
            j['chain_head']=head;self.attempt['journal_head']=selected
            self.request=replace(self.request,attempt=self.put('audit/attempt.json',self.attempt,'attempt'))
        self.journal_data=j;self.request=replace(self.request,journal=self.put('audit/journal.json',j,'journal'))
    def edit_regression(self,fn):
        obj=json.loads(canonical_bytes(self.reg));fn(obj);self.reg=obj
        self.request=replace(self.request,regression=self.put('audit/regression.json',obj,'regression'))
