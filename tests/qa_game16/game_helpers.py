"""Explicit SYNTHETIC unit fixtures. No real game/assessor claimed by these helpers."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,tempfile,unittest,json,io
from PIL import Image
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,ContractError,canonical_bytes,EvidenceBundle
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
from bie.qa.video_v2.evaluator import encode_log
from bie.qa.game_v2.models import *
from bie.qa.game_v2.evaluator import evaluate,review_targets,oracle_paths
from bie.qa.game_v2.codec import load_build,load_runtime
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'
ROOT=Path(__file__).resolve().parents[2]
TEXTS={'prompt':'Find x so that 2 + x = 5.','correct':'x = 3 because 2 + 3 = 5.','incorrect':'x = 1 gives 3, not 5. Increase x.','hint':'Subtract 2 from 5 to find x.','instruction':'Choose x, then check the sum.'}
def artifact(root,path,payload,aid,role='support'):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)
def policy(inputs):
    def state(sid,x=1,score=0,status='ready',feedback='instruction',terminal=False,success=False):
        return State(sid,tuple(Value(k,str(v)) for k,v in [('x',x),('score',score),('status',status),('prompt',TEXTS['prompt']),('feedback',TEXTS[feedback])]),terminal,success)
    states=(state('initial'),state('two',2),state('three',3),state('win',3,10,'correct','correct',True,True),state('wrong',1,0,'retry','incorrect'),state('hint',1,0,'ready','hint'))
    actions=(Action('increase','click','#increase',''),Action('decrease','click','#decrease',''),Action('submit','click','#submit',''),Action('hint','click','#hint',''),Action('reset','click','#reset',''),Action('key-increase','press','#increase','Enter'),Action('key-submit','press','#submit','Enter'),Action('reload','reload','',''))
    specs=[('initial','increase','two'),('two','increase','three'),('three','submit','win'),('win','submit','win'),('win','reset','initial'),('initial','hint','hint'),('hint','reset','initial'),('initial','submit','wrong'),('wrong','reset','initial'),('initial','key-increase','two'),('two','key-increase','three'),('three','key-submit','win'),('two','decrease','initial'),('win','reload','initial')]
    transitions=tuple(Transition('edge-'+str(i),*v) for i,v in enumerate(specs))
    scenarios=(Scenario('pointer',480,320,('increase','increase','submit','submit','reset','hint','reset','submit','reset')),Scenario('keyboard',480,320,('key-increase','key-increase','key-submit','reset')),Scenario('mobile',320,480,('increase','decrease','increase','increase','submit','reload')))
    learn=(LearningTarget('solve-equation','balance','manipulate-parameter','prompt','prompt','correct','incorrect','feedback',('submit','key-submit'),'win','wrong'),)
    return GamePolicy('game-policy','balance',inventory(inputs),'dist/index.html',('dist/index.html','dist/game.js'),'initial',tuple(Observable(k,'#'+k) for k in ('x','score','status','prompt','feedback')),states,actions,transitions,scenarios,learn,(TextBinding('hint','feedback',('hint',)),TextBinding('instruction','feedback',('initial','two','three'))),Policy('source-policy',tuple(TEXTS)))
def png(w,h):
    im=Image.new('RGB',(w,h),(245,245,245));b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def fixture(root):
    src=artifact(root,'source/lesson.txt','\n'.join(TEXTS.values()).encode(),'source','source')
    outrefs=tuple(artifact(root,f'text/{k}.txt',v.encode(),'text-'+k) for k,v in TEXTS.items())
    code=artifact(root,'src/game.ts',b'// SYNTHETIC unit source, not a native compiler run','input-code')
    lock=artifact(root,'src/toolchain.json',b'{"fixture":true}','input-lock')
    inputs=(code,lock)
    html=artifact(root,'dist/index.html',b'<html>SYNTHETIC</html>','game-entry','game');js=artifact(root,'dist/game.js',b'// SYNTHETIC compiled code','game-js')
    outputs=(html,js);p=policy(inputs)
    stdout=artifact(root,'build/stdout.json',encode_log(b''),'build-stdout');stderr=artifact(root,'build/stderr.json',encode_log(b''),'build-stderr')
    b=BuildReceipt('bie.qa.game-build/1','game-run',REV,'balance',inventory(inputs),inventory(outputs),p.entrypoint,'tsc','SYNTHETIC',True,0,False,NOW-20,'native',stdout,stderr)
    br=artifact(root,'build/receipt.json',canonical_bytes(asdict(b)),'build-receipt')
    paths=oracle_paths(p);states={s.state_id:s for s in p.states};traces=[];screens=[]
    for c in p.scenarios:
        for replay in range(p.replays):
            steps=[];ids=(p.initial_state,)+tuple(t.after for t in paths[c.scenario_id])
            for i,(act,sid) in enumerate(zip(('boot',)+c.action_ids,ids)):
                aid=f'screen-{c.scenario_id}-{replay}-{i}';ref=artifact(root,'screens/'+aid+'.png',png(c.width,c.height),aid);screens.append(ref)
                vals=tuple(ObservedValue(v.key,v.text,1,True) for v in states[sid].values)
                steps.append(Step(act,i*100,i*100+50,True,'',vals,ref))
            traces.append(Trace(c.scenario_id,replay,c.width,c.height,tuple(steps),tuple(a.path for a in outputs)))
    rr=RuntimeReceipt('bie.qa.game-runtime/1','game-run',REV,'balance',br.sha256,inventory(outputs),p.oracle_digest,p.entrypoint,'http://127.0.0.1:1234','http_entrypoint','SYNTHETIC',NOW-10,'native',True,tuple(LoadedAsset(a.path,a.sha256,a.size) for a in outputs),tuple(traces),(),(),())
    runtime=artifact(root,'runtime/receipt.json',canonical_bytes(asdict(rr)),'runtime-receipt')
    vid=artifact(root,'fixtures/not-video.txt',b'SYNTHETIC_NOT_VIDEO','placeholder-video','video')
    cand=ReleaseCandidate('2.0.0','game-candidate','game-run',REV,(src,)+outrefs+inputs+outputs+(stdout,stderr,br,runtime,vid)+tuple(screens))
    source_text='\n'.join(TEXTS.values());block=Block('block','lesson',src.sha256,1,'region',(0,0,1000000,1000000),source_text,'utf8','1',1000000);cites=[];claims=[];outs=[];pos=0
    for (k,v),ref in zip(TEXTS.items(),outrefs):
        cites.append(Citation('cite-'+k,'block',block.content_digest,pos,pos+len(v),v));claims.append(Claim(k,k,ref.sha256,0,len(v),v,'FACT',('cite-'+k,)));outs.append(Output(k,ref,'game_prompt' if k=='prompt' else 'game_feedback'));pos+=len(v)+1
    sr=Request('1.0.0','game-run',REV,cand.content_digest,(Source('lesson',src,'utf8',1),),(block,),tuple(outs),tuple(cites),tuple(claims))
    r=GameRequest('game-run',REV,cand.content_digest,'balance',inputs,outputs,br,runtime,sr)
    return r,p,cand

def key(**kw):return replace(ReviewKey('game-key',b'SYNTHETIC_GAME_REVIEW_KEY_NOT_PRODUCTION','assessor','1','group',('calibration','inventory','teaching'),'operator_managed'),**kw)
def source_key():return AssessmentKey('source-key',b'SYNTHETIC_GAME_SOURCE_KEY_NOT_PRODUCTION','source-assessor','1',('semantic','extraction','nonfactual'),'operator_managed')
def sign(r,k):return replace(r,signature=hmac.new(k.secret,r.signing_bytes(),hashlib.sha256).hexdigest())
def signed_reviews(r,p,k=None):
    k=k or key();return tuple(sign(Review('review-'+str(i)+'-'+k.key_id,r.content_digest,p.content_digest,t[1],t[0],'VERIFIED',e,950000,'SYNTHETIC test-only assessment, not live execution/learning proof.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for i,(t,e) in enumerate(sorted(review_targets(r,p).items())))
def options(r,p,**kw):
    k=key();sk=source_key();ss=tuple(sign(Assessment('assessment-'+c.claim_id,r.source.content_digest,p.source.content_digest,c.claim_id,'semantic','SUPPORTED',950000,'SYNTHETIC source interpretation.',sk.evaluator_id,sk.evaluator_version,NOW-10,NOW+60,sk.key_id),sk) for c in r.source.claims)
    d=dict(reviews=signed_reviews(r,p,k),verifier=ReviewVerifier((k,)),source_assessments=ss,source_verifier=AssessmentVerifier((sk,)));d.update(kw);return d
def codes(result):return {f.code for r in result.reports for f in r.findings}
class FixtureCase(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.r,self.p,self.c=fixture(self.root)
    def check(self,r=None,p=None,**kw):
        r=r or self.r;p=p or self.p;return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kw))
    def runtime(self,**kw):
        rr=replace(load_runtime((self.root/self.r.runtime_receipt.path).read_bytes()),**kw);a=artifact(self.root,'runtime/changed.json',canonical_bytes(asdict(rr)),'changed-runtime');return replace(self.r,runtime_receipt=a)
    def build(self,**kw):
        b=replace(load_build((self.root/self.r.build_receipt.path).read_bytes()),**kw);a=artifact(self.root,'build/changed.json',canonical_bytes(asdict(b)),'changed-build');return replace(self.r,build_receipt=a)
    def trace_change(self,fn,index=0):
        rr=load_runtime((self.root/self.r.runtime_receipt.path).read_bytes());ts=list(rr.traces);ts[index]=fn(ts[index]);return self.runtime(traces=tuple(ts))
    def step_change(self,fn,index=0,trace=0):
        def f(t):ss=list(t.steps);ss[index]=fn(ss[index]);return replace(t,steps=tuple(ss))
        return self.trace_change(f,trace)
    def assertCode(self,res,code):self.assertIn(code,codes(res));self.assertFalse(res.product_accepted)
