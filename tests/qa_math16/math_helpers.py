"""Authored synthetic unit/integration fixtures, not a real book or real assessor."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,tempfile,unittest,json
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,ContractError,canonical_bytes
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.math_v2 import *
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'
SENTENCES=(
 'In this authored example, 2*x+2=6 is equivalent to x+1=3.',
 'Subtracting 2 on both sides gives 2*x=4.',
 'Dividing both sides by the nonzero number 2 gives x=2.',
 'With distance 10 m and time 2 s, speed is 5 m/s.',
 'For this example, distance lies in [0,100] m and time lies in [1,10] s.',
 'The dimensional relation is distance = speed * time.',
 '100 cm is 1 m; 0 degC is 273.15 K; a 1 delta_degC difference is 1 delta_K.',
)

def artifact(root,path,payload,aid,role='support'):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)

def eq(a,b):return Equation(parse(a),parse(b))

def fixture(root):
    text='\n'.join(SENTENCES)
    sr=artifact(root,'sources/authored-math.txt',text.encode(),'math-source','source')
    out=artifact(root,'outputs/math-script.txt',text.encode(),'math-script')
    v=artifact(root,'fixtures/video.bin',b'NOT_A_REAL_RENDER','fixture-video','video')
    g=artifact(root,'fixtures/game.bin',b'NOT_A_PLAYABLE_GAME','fixture-game','game')
    candidate=ReleaseCandidate('2.0.0','math-candidate','math-run',REV,(sr,out,v,g))
    source=Source('authored-math',sr,'utf8',1)
    block=Block('math-block','authored-math',sr.sha256,1,'math-region',(0,0,1000000,1000000),text,'utf8','1',1000000)
    claims=[];citations=[];pos=0
    for i,s in enumerate(SENTENCES,1):
        cid=f'cite-{i}';citations.append(Citation(cid,block.block_id,block.content_digest,pos,pos+len(s),s))
        claims.append(Claim(f'claim-{i}','math-output',out.sha256,pos,pos+len(s),s,'FACT',(cid,)));pos+=len(s)+1
    src=Request('1.0.0','math-run',REV,candidate.content_digest,(source,),(block,),(Output('math-output',out,'narration'),),tuple(citations),tuple(claims))
    algebra=Scope('algebra',(SymbolSpec('x','1'),))
    mechanics=Scope('mechanics',(SymbolSpec('d','m',('0','100')),SymbolSpec('t','s',('1','10')),SymbolSpec('v','m/s')))
    refs=(FormulaReference('start','algebra',eq('2*x+2','6')),FormulaReference('end','algebra',eq('x','2')))
    inputs=(Binding('d','10','10','m'),Binding('t','2','2','s'))
    numerical=NumericalReference('speed','mechanics',parse('d/t'),inputs,'m/s')
    requirements=(Requirement('formula-1','formula','algebra','start'),Requirement('derivation-1','derivation','algebra','start','end',2),Requirement('numerical-1','numerical','mechanics','speed'),Requirement('units-1','units','mechanics'))
    policy=MathPolicy('math-test-policy',Policy('math-source-policy',('math-output',)),(algebra,mechanics),refs,(numerical,),requirements)
    f=FormulaCase('formula-1','algebra','start',('claim-1',),(),eq('x+1','3'))
    steps=(DerivationStep('step-1',('claim-2',),eq('2*x+2','6'),eq('2*x','4'),'subtract_both',num(2)),DerivationStep('step-2',('claim-3',),eq('2*x','4'),eq('x','2'),'divide_both',num(2)))
    d=DerivationCase('derivation-1','algebra','start','end',('claim-2','claim-3'),(),steps)
    n=NumericalCase('numerical-1','mechanics','speed',('claim-4',),('claim-5',),parse('d/t'),inputs,'5','5','m/s')
    conversions=(Conversion('cm-m','100','100','cm','m','1','1'),Conversion('c-k','0','0','degC','K','273.15','273.15'),Conversion('dc-dk','1','1','delta_degC','delta_K','1','1'))
    u=UnitCase('units-1','mechanics',('claim-6','claim-7'),('claim-5',),eq('d','v*t'),conversions)
    return MathRequest('1.0.0',src,(f,),(d,),(n,),(u,)),policy,candidate

def key(**changes):return replace(ReviewKey('math-key',b'SYNTHETIC_MATH_TEST_KEY_NOT_PRODUCTION_001','math-assessor','1','math-review-group',('inventory','mapping','disclosure'),'operator_managed'),**changes)
def source_key(**changes):return replace(AssessmentKey('source-key',b'SYNTHETIC_MATH_SOURCE_KEY_NOT_PRODUCTION_01','source-assessor','1',('semantic','extraction','nonfactual'),'operator_managed'),**changes)
def sign(a,k):return replace(a,signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest())
def signed_reviews(request,policy,k=None):
    k=k or key()
    return tuple(sign(Review(f'math-review-{i}-{k.key_id}',request.content_digest,policy.content_digest,s,p,'VERIFIED',e,950000,'SYNTHETIC assessment fixture; not actual contextual review.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for i,((p,s),e) in enumerate(sorted(review_targets(request).items())))
def source_reviews(request,policy,k=None):
    k=k or source_key()
    return tuple(sign(Assessment(f'source-{c.claim_id}',request.source.content_digest,policy.source.content_digest,c.claim_id,'semantic','SUPPORTED',950000,'SYNTHETIC source assessment fixture.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for c in request.source.claims)
def options(r,p,**changes):
    k=key();sk=source_key();o=dict(reviews=signed_reviews(r,p,k),verifier=ReviewVerifier((k,)),source_assessments=source_reviews(r,p,sk),source_verifier=AssessmentVerifier((sk,)));o.update(changes);return o

def codes(report):return {f.code for f in report.findings}

class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.request,self.policy,self.candidate=fixture(self.root)
    def run_check(self,r=None,p=None,**kw):
        r=r or self.request;p=p or self.policy;return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kw))
    def assertCode(self,result,area,code,status=None):
        report=getattr(result,area);self.assertIn(code,codes(report))
        if status:self.assertEqual(report.status,status)
        self.assertFalse(result.product_accepted)
