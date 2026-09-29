"""AUTHORED SYNTHETIC review fixtures. No live assessor or native renderer claimed."""
import sys,tempfile,unittest,json,hashlib,hmac,subprocess,os,shutil
from pathlib import Path
from dataclasses import asdict,replace
W=Path(__file__).resolve().parents[2]
for name in ('visual','animation','game'):sys.path.insert(0,str(W/'tests'/('qa_'+name+'16')))
import vis_helpers as vh,ani_helpers as ah,game_helpers as gh
from bie.qa.release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,digest
from bie.qa.source_v2.io import SnapshotStore
from bie.qa.source_v2.models import Finding,Report
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
from bie.qa.repair_v2 import *
from bie.qa.repair_v2.worker import validator_digest
from bie.qa.repair_v2.models import CheckOutcome
from bie.qa.repair_v2.adapters import bind_report
from bie.qa.media_repair_v2 import *
from bie.qa.media_repair_v2.emitter import *
from bie.qa.media_repair_v2.inspection import inspect_generated
from bie.qa.media_repair_v2.service import TYPES,WORKERS
from bie.qa.visual_v2.evaluator import evaluate as eval_visual
from bie.qa.animation_v2.evaluator import evaluate as eval_animation
from bie.qa.visual_v2.models import Rect
from bie.qa.animation_v2.models import Keyframe
NOW=1800000000
KEY=ReviewKey('media-synthetic-key',b'SYNTHETIC_ONLY_NEVER_DEPLOY_REPAIR_KEY15','synthetic-reviewer','1','synthetic-group',('inventory','inference'),'operator_managed')
CONTEXTS={}

def runtime_module(payload,number,policy):
    """Actual tsc and Node, only after identity matches the fixed safe emitter."""
    expected=emit_constants(policy) if number==10 else emit_reducer(policy.qa)
    if payload!=expected:return dict(passed=False,reason='MODULE_BYTES_NOT_APPROVED',processes=[])
    with tempfile.TemporaryDirectory(prefix='qa-module-replay-') as d:
        root=Path(d);(root/'module.ts').write_bytes(payload)
        tsc=shutil.which('tsc');node=shutil.which('node')
        if not tsc or not node:return dict(passed=False,reason='TOOL_UNAVAILABLE',processes=[])
        cmd=[tsc,'--strict','--skipLibCheck','--target','ES2020','--module','commonjs','--outDir',str(root/'out'),str(root/'module.ts')]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
        rows=[dict(tool='tsc',exit=p.returncode,stdout=p.stdout,stderr=p.stderr)]
        if p.returncode:return dict(passed=False,reason='COMPILE_FAILED',processes=rows)
        if number==10:
            oracle={e.name:read_value(e.json_value) for e in policy.exports}
            script="const assert=require('node:assert/strict');const m=require('./out/module.js');const expected="+literal(oracle)+";assert.deepEqual(m,expected);console.log(JSON.stringify({passed:true,exports:Object.keys(expected).length}));"
        else:
            pqa=policy.qa
            cases=dict(initial=pqa.initial_state,states=[asdict(s) for s in pqa.states],transitions=[asdict(t) for t in pqa.transitions],scenarios=[asdict(s) for s in pqa.scenarios])
            script="""const assert=require('node:assert/strict'),m=require('./out/module.js');const p="""+literal(cases)+""";
assert.equal(m.initialState,p.initial);
for(const state of p.states){let expected=Object.fromEntries(state.values.map(x=>[x.key,x.text]));assert.deepEqual(m.observe(state.state_id),expected);let o=m.observe(state.state_id);o.score='999999';assert.deepEqual(m.observe(state.state_id),expected);}
for(const t of p.transitions)assert.equal(m.step(t.before,t.action_id),t.after);
for(const scenario of p.scenarios){let state=p.initial;for(const action of scenario.action_ids){const t=p.transitions.find(t=>t.before===state&&t.action_id===action);assert.ok(t);state=m.step(state,action);assert.equal(state,t.after);}}
for(const s of ['__proto__','missing-state','constructor'])assert.throws(()=>m.observe(s));
assert.throws(()=>m.step(p.initial,'missing-action'));assert.throws(()=>m.step('missing-state','submit'));
console.log(JSON.stringify({passed:true,states:p.states.length,transitions:p.transitions.length,scenarios:p.scenarios.length}));
"""
        (root/'test.cjs').write_text(script)
        q=subprocess.run([node,str(root/'test.cjs')],capture_output=True,text=True,timeout=10,cwd=root)
        rows.append(dict(tool='node',exit=q.returncode,stdout=q.stdout,stderr=q.stderr))
        return dict(passed=q.returncode==0,reason='' if q.returncode==0 else 'REPLAY_FAILED',processes=rows,
            typescript_sha256=hashlib.sha256(payload).hexdigest(),javascript_sha256=hashlib.sha256((root/'out/module.js').read_bytes()).hexdigest())

def check_media(root,snapshot,policy):
    c=CONTEXTS[policy.content_digest];ref=next(a for a in snapshot.artifacts if a.path==c.target.path)
    with SnapshotStore(root) as store:b=store.read(ref)
    if c.number in (8,9):
        r=read_request(c.task,b);h=vh if c.number==8 else ah;fun=eval_visual if c.number==8 else eval_animation
        result=fun(r,root,c.dp.qa,as_of=NOW,**(h.options(r,c.dp.qa) if c.positive else {}))
        status={'CHECKS_PASSED':'PASS','REVIEW_REQUIRED':'REVIEW','BLOCKED':'FAIL'}[result.status];witness=result.to_dict()
    else:
        result=runtime_module(b,c.number,c.dp);status='PASS' if result['passed'] else 'FAIL';witness=result
    if getattr(c,'worker_evidence_path',None):Path(c.worker_evidence_path).write_text(json.dumps(witness,indent=2)+'\n')
    return CheckOutcome('media',snapshot.content_digest,policy.content_digest,status,() if status=='PASS' else ('MEDIA_POSTCHECK_'+status,),digest(witness))

def check_preserved(root,snapshot,policy):
    c=CONTEXTS[policy.content_digest]
    with SnapshotStore(root) as store:ok=all(store.read(a)==c.original[a.path] for a in snapshot.artifacts if a.path!=c.target.path)
    return CheckOutcome('preserve',snapshot.content_digest,policy.content_digest,'PASS' if ok else 'FAIL',() if ok else ('PROTECTED_CHANGED',),digest(ok))

class Context:
    def __init__(self,root,number):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.number=number;self.task=f'BIE-QA-REPAIR-{number:03}';self.now=NOW;self.limits=Limits();self.verifier=ReviewVerifier((KEY,));self.positive=True
        if number in (8,9,10):
            h=ah if number==9 else vh;self.good,qa,self.candidate=h.fixture(self.root)
        else:self.good,qa,self.candidate=gh.fixture(self.root)
        if number==8:
            state=self.good.states[0];b=state.measurements[0].box;old=state.measurements[1]
            moved=replace(old,box=b,line_boxes=tuple(replace(l,x=l.x+b.x-old.box.x,y=l.y+b.y-old.box.y) for l in old.line_boxes))
            self.bad=replace(self.good,states=(replace(state,measurements=(state.measurements[0],moved,state.measurements[2])),))
            self.dp=VisualRepairPolicy(qa,(LayoutPermission(state.state_id,old.object_id,qa.views[0].safe,1000000),))
        elif number==9:
            t=self.good.tracks[0];new=replace(t,keyframes=(Keyframe(0,t.keyframes[0].value),Keyframe(100,t.keyframes[-1].value)))
            self.bad=replace(self.good,tracks=(new,)+self.good.tracks[1:]);self.dp=AnimationRepairPolicy(qa,(TrackWindow(t.track_id,0,2000),))
        elif number==10:
            self.dp=CodePolicy('code-policy','counts',qa.source,(ExportValue('total','6'),ExportValue('groups','[3,3]')),('claim-3',))
            ref=self.write('generated/module.ts',(code_header('counts')+'export const total: number = ;\n').encode(),'module')
            self.bad=CodeRequest('1.0.0',self.good.source,'counts',ref)
        else:
            self.dp=GameRepairPolicy(qa);ref=self.write('generated/module.ts',(game_header(qa.game_id)+'export function step(s:string,a:string){return "win";}\n').encode(),'module')
            self.bad=GameRepairRequest('1.0.0',self.good.source,qa.game_id,ref)
        self.set_bad(self.bad)
    def write(self,path,data,aid='request',role='support'):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)
    def set_bad(self,r):
        self.bad=r;self.request_ref=self.write('generated/request.json',canonical_bytes(asdict(r)))
        self.target=self.request_ref if self.number in (8,9) else r.module
        refs=list(self.candidate.artifacts)+[self.request_ref]
        if self.number>=10:refs.append(r.module)
        self.snapshot=Snapshot(r.source.run_id,r.source.revision,tuple(refs));self.original={a.path:(self.root/a.path).read_bytes() for a in self.snapshot.artifacts}
        if self.number==8:report=eval_visual(r,self.root,self.dp.qa,as_of=NOW,**vh.options(r,self.dp.qa)).layout
        elif self.number==9:report=eval_animation(r,self.root,self.dp.qa,as_of=NOW,**ah.options(r,self.dp.qa)).motion
        else:report=inspect_generated(self.task,r,self.root,self.dp,as_of=NOW)
        assert report.status=='BLOCKED',(report.status,report.to_dict())
        self.bound,data=bind_report(report,'failure-report','reports/failure.json');self.write(self.bound.artifact.path,data,self.bound.artifact.artifact_id,'report')
        self.batch=FailureBatch(self.snapshot.run_id,self.snapshot.revision,self.snapshot.content_digest,(self.bound,))
        owner=TASK_OWNERS[self.task]
        rules=tuple(FailureRule(report.task_id,c,'CONTENT',owner,True) for c in sorted({f.code for f in report.findings if f.severity=='BLOCKER'}))
        self.policy=RepairPolicy('media-test-'+str(self.number),rules,(OwnerRoute(owner,(self.target.path,),('media',)),),(CheckNode('media',(),validator_digest(check_media)),CheckNode('preserve',('media',),validator_digest(check_preserved))),('preserve',),worker_timeout_seconds=20,max_total_worker_seconds=100)
        self.refresh()
    def refresh(self):
        self.job=Job('media-job-'+str(self.number),self.task,self.request_ref,self.target,self.snapshot.content_digest,self.batch.content_digest,self.policy.content_digest,self.dp.content_digest,self.limits.content_digest)
        CONTEXTS[self.policy.content_digest]=self
    def signed(self,subject,purpose,rd,evidence,**kw):
        k=kw.pop('key',KEY);r=Review('auth-'+subject,rd,self.policy.content_digest,subject,purpose,'VERIFIED',tuple(sorted(set(evidence))),1000000,'SYNTHETIC test authorization, not production trust.',k.evaluator_id,k.evaluator_version,NOW-1,NOW+60,k.key_id)
        r=replace(r,**kw);return replace(r,signature=hmac.new(k.secret,r.signing_bytes(),hashlib.sha256).hexdigest())
    def inv(self):return (self.signed('repair-findings','inventory',self.batch.content_digest,(self.bound.artifact.artifact_id,)),)
    def gen(self):return (self.signed(self.job.job_id,'inference',self.job.content_digest,(self.target.artifact_id,self.request_ref.artifact_id)),)
    def kwargs(self):return dict(as_of=NOW,limits=self.limits,inventory_reviews=self.inv(),generation_reviews=self.gen(),verifier=self.verifier)
    def generate(self,**kw):
        opts=self.kwargs();opts.update(kw);return generate(self.job,self.batch,self.snapshot,self.root,self.policy,self.dp,**opts)
    def prepare(self,**kw):
        opts=self.kwargs();opts.update(kw);return prepare(self.job,self.batch,self.snapshot,self.root,self.policy,self.dp,**opts)
    def preview(self,r=None,p=None,**kw):return preview(self.task,r or self.bad,self.root,p or self.dp,**kw)
    def execute(self,proposal,**kw):
        out=self.root.parent/('stage-'+str(self.number));out.mkdir(exist_ok=True);j=Journal(self.root.parent/('journal-'+str(self.number)+'.sqlite'),self.snapshot,self.policy)
        opts=dict(as_of=NOW,output_root=out,journal=j,checks={'media':check_media,'preserve':check_preserved},inventory_reviews=self.inv(),proposal_reviews=(self.signed(proposal.proposal_id,'inference',proposal.content_digest,tuple(x.artifact.artifact_id for x in proposal.replacements)),),verifier=self.verifier)
        opts.update(kw)
        try:return execute(self.batch,self.snapshot,self.root,self.policy,proposal,**opts)
        finally:j.close()

class Base(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.home=Path(self.temp.name)
    def context(self,n=8):return Context(self.home/('case'+str(n)),n)
    def assertError(self,code,fn,*a,**kw):
        with self.assertRaises(ContractError) as e:fn(*a,**kw)
        self.assertEqual(e.exception.code,code)
