"""Actual source-repair generation/staging with explicitly synthetic approvals."""
from audit_helpers import *
import tempfile,unittest
sys.path.insert(0,str(ROOT/'tests/qa_domain_repair16'))
import domain_helpers as dh
from bie.qa.domain_repair_v2.validation import evaluate_candidate,status_of
from bie.qa.repair_v2.planner import classify
CONTEXTS={}

def domain_cases(root,snapshot,repair_policy,rule):
    ctx=CONTEXTS[repair_policy.content_digest]
    ref=next(a for a in snapshot.artifacts if a.path=='generated/request.json')
    with SnapshotStore(root) as store:r=dh.read_request(ctx.task,store.read(ref))
    result=evaluate_candidate(ctx.task,r,root,ctx.dp,as_of=ctx.now,**dh.options(ctx.number,r,ctx.dp))
    report=result.provenance;out=[]
    for case,failure in zip(rule.case_ids,ctx.audit_failures):
        present=any(f.code==failure.code and f.subject_id==failure.subject_id for f in report.findings)
        out.append(obs(case,not present and report.status=='CHECKS_PASSED',dict(report_digest=report.content_digest,
            report_status=report.status,target_diagnostic=failure.code,present=present)))
    return tuple(out)

def preserve_cases(root,snapshot,repair_policy,rule):
    ctx=CONTEXTS[repair_policy.content_digest]
    with SnapshotStore(root) as store:
        values={a.artifact_id:hashlib.sha256(store.read(a)).hexdigest() for a in snapshot.artifacts if a.path!='generated/request.json'}
    expected={a.artifact_id:a.sha256 for a in ctx.snapshot.artifacts if a.path!='generated/request.json'}
    return (obs('protected',values==expected,dict(actual=values,expected=expected)),)

class GenerationFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.home=Path(self.temp.name)
        self.ctx=dh.Context(self.home/'original',4);c=self.ctx
        self.p,self.generation=c.prepare();self.attempt=c.execute(self.p)
        assert self.attempt['status']=='STAGED_FOR_REVIEW'
        self.candidate_root=Path(self.attempt['staged_directory'])
        c.audit_failures=classify(c.batch,c.snapshot,c.root,c.policy,as_of=c.now,reviews=c.inv(),verifier=c.verifier).failures
        cases=tuple('failure-'+str(i) for i in range(len(c.audit_failures)))
        fixtures=tuple(sorted(a.artifact_id for a in c.snapshot.artifacts if a.role=='source'))
        self.ap=AuditPolicy('source-audit',(
            CaseRule('domain',cases,fixtures,validator_digest(domain_cases)),
            CaseRule('preserve',('protected',),fixtures,validator_digest(preserve_cases))),
            tuple(TargetCase(f.failure_id,'domain',case) for f,case in zip(c.audit_failures,cases)),
            tuple(sorted(a.artifact_id for a in c.snapshot.artifacts if a!=c.target)),True)
        CONTEXTS[c.policy.content_digest]=c
        reg=collect_regression(c.snapshot,self.p,c.root,self.candidate_root,c.policy,self.ap,
            registry=dict(domain=domain_cases,preserve=preserve_cases),as_of=c.now)
        j=Journal(self.home/'journal-4.sqlite',c.snapshot,c.policy)
        try:journal=j.export()
        finally:j.close()
        self.request=AuditRequest(c.snapshot,c.batch,self.p,
            self.put('attempt',self.attempt),self.put('journal',journal),self.put('regression',reg),(
                GenerationLink(self.put('job',asdict(c.job),'support'),self.put('generation',self.generation),
                    self.put('domain-policy',asdict(c.dp),'support'),self.put('limits',asdict(c.limits),'support')),))
    def put(self,name,obj,role='report'):
        return self.ctx.write('audit/'+name+'.json',canonical_bytes(obj),'audit-'+name,role)
    def audit(self,**kwargs):
        c=self.ctx
        options=dict(as_of=c.now,inventory_reviews=c.inv(),proposal_reviews=(c.signed(self.p.proposal_id,'inference',self.p.content_digest,tuple(x.artifact.artifact_id for x in self.p.replacements)),),
            audit_reviews=(audit_review(self.request,self.ap,now=c.now),),verifier=ReviewVerifier((dh.KEY,AUDIT_KEY)))
        options.update(kwargs)
        return evaluate(self.request,c.root,self.candidate_root,c.policy,self.ap,**options)
    def mutate_generation(self,fn):
        raw=json.loads(canonical_bytes(self.generation));fn(raw)
        link=replace(self.request.generation[0],receipt=self.put('generation',raw))
        self.request=replace(self.request,generation=(link,))
    def assertCode(self,code):
        r=self.audit();self.assertIn(code,{f.code for x in (r.evidence,r.regression) for f in x.findings})
