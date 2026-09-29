"""Internal per-run state. Nothing is accepted as a caller-supplied PASS report."""
from ..source_v2.models import Finding
from ..release_v2.contracts import ContractError

class Context:
    def __init__(self,request,policy,source,as_of):
        self.request=request;self.policy=policy;self.source=source;self.as_of=as_of
        self.findings={k:[] for k in ('common','pr','validity','evidence','uncertainty')}
        self.findings['common'].extend(source.grounding.findings)
        self.claims={x.claim_id:x for x in request.source.claims}
        self.citations={x.citation_id:x for x in request.source.citations}
        self.blocks={x.block_id:x for x in request.source.blocks}
        self.statements={x.statement_id:x for x in request.statements}
        self.steps={x.step_id:x for x in request.steps}
        self.arguments={x.argument_id:x for x in request.arguments}
        self.ready=set();self.payloads={};self.inspected=set(source.provenance.inspected_artifact_ids)
        self.metrics={k:{} for k in ('pr','validity','evidence','uncertainty')}
    def add(self,area,code,subject,detail,severity='BLOCKER',owner=None):
        self.findings[area].append(Finding(code,severity,subject,owner or {'common':'QA_TRUST','pr':'PR_PED','validity':'RE_VALIDITY','evidence':'RE_EVIDENCE','uncertainty':'RE_UNCERTAINTY'}[area],detail))
    def status(self,area):
        f=self.findings['common']+self.findings[area]
        if any(x.severity=='BLOCKER' for x in f):return 'BLOCKED'
        if any(x.severity=='REVIEW' for x in f):return 'REVIEW_REQUIRED'
        return 'CHECKS_PASSED'
    def actual_claims(self,ids):
        return bool(ids) and all(i in self.claims for i in ids)

class Budget:
    def __init__(self,limit):self.limit=limit;self.used=0
    def spend(self,n=1):
        if self.used+n>self.limit:raise ContractError('GRAPH_CHECK_BUDGET_EXCEEDED')
        self.used+=n
