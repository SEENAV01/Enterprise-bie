"""Authored synthetic fixtures. Test keys/labels are NOT operational evidence."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,tempfile,unittest,json
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,canonical_bytes,ContractError
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.reasoning_v2 import *
from bie.qa.reasoning_v2.attestation import PURPOSES
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'
SENTENCES=('The switch is closed.','If the switch is closed, the lamp is on.','The lamp is on.',
           'A closed switch connects the path in this toy model.')

def artifact(root,path,payload,aid,role='support'):
    f=root/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)

def fixture(root):
    text='\n'.join(SENTENCES)
    sref=artifact(root,'inputs/toy-model.txt',text.encode(),'source-file','source')
    out=artifact(root,'surfaces/narration.txt',text.encode(),'narration-file')
    video=artifact(root,'fixtures/video.bin',b'NOT_A_RENDER_TEST_FIXTURE','video-fixture','video')
    game=artifact(root,'fixtures/game.bin',b'NOT_A_GAME_TEST_FIXTURE','game-fixture','game')
    caldata=dict(schema_version='1.0.0',calibration_id='cal-1',model_id='toy-model',model_version='1',domain='toy-circuit',language='en',
        issued_at=NOW-100,dataset_id='synthetic-holdout',split='heldout',source_hashes=[hashlib.sha256(b'INDEPENDENT_SYNTHETIC_TEST_ONLY').hexdigest()],
        samples=[dict(sample_id=f'sample-{i}',group_id=f'group-{i}',confidence_ppm=950000,correct=i<95) for i in range(100)])
    calref=artifact(root,'diagnostics/calibration.json',canonical_bytes(caldata),'calibration-file')
    candidate=ReleaseCandidate('2.0.0','toy-candidate','toy-run',REV,(sref,out,video,game,calref))
    source=Source('book',sref,'utf8',1)
    block=Block('block-1','book',sref.sha256,1,'region-1',(0,0,1000000,1000000),text,'utf8','1',1000000)
    citations=[];claims=[];pos=0
    for i,sentence in enumerate(SENTENCES,1):
        cid=f'cite-{i}';citations.append(Citation(cid,block.block_id,block.content_digest,pos,pos+len(sentence),sentence))
        claims.append(Claim(f'claim-{i}','narration',out.sha256,pos,pos+len(sentence),sentence,'FACT',(cid,)));pos+=len(sentence)+1
    src=Request('1.0.0','toy-run',REV,candidate.content_digest,(source,),(block,),(Output('narration',out,'narration'),),tuple(citations),tuple(claims))
    source_policy=Policy('source-test-policy',('narration',))
    policy=ReasoningPolicy('reasoning-test-policy',source_policy,'learner-test',('switch','circuit'),('circuit',),
        (PrerequisiteRule('rule-switch','switch','circuit'),),('arg-1',),(SourceLineage('book','lineage-a'),),'toy-circuit','en')
    A=Expr('atom','switch-closed');B=Expr('atom','lamp-on')
    statements=(Statement('s1','claim-1','toy-scope',A),Statement('s2','claim-2','toy-scope',Expr('implies','',(A,B))),Statement('s3','claim-3','toy-scope',B))
    events=(LearningEvent('teach-switch','switch',1,'teach',('claim-4',),2),LearningEvent('use-circuit','circuit',2,'use',('claim-3',),2))
    argument=Argument('arg-1','toy-scope',('s1','s2','s3'),('s1','s2'),('step-1',),'s3')
    cal=CalibrationArtifact('cal-1',calref,'toy-model','1','toy-circuit','en',NOW-100)
    decision=ConfidenceDecision('arg-1',950000,'publish','cal-1','toy-model','1','toy-circuit','en')
    req=ReasoningRequest('1.0.0',src,events,(),statements,(InferenceStep('step-1','s3',('s1','s2')),),(argument,),
        (EvidenceLink('ev-1','arg-1','s1',('cite-1',)),EvidenceLink('ev-2','arg-1','s2',('cite-2',))), (cal,),(decision,))
    return req,policy,candidate

def key(**changes):
    k=ReviewKey('re-key',b'SYNTHETIC_REVIEW_SECRET_NOT_PRODUCTION_001','re-assessor','1','independent-a',PURPOSES,'operator_managed')
    return replace(k,**changes)

def source_key(**changes):
    k=AssessmentKey('source-key',b'SYNTHETIC_SOURCE_SECRET_NOT_PRODUCTION_001','source-assessor','1',('semantic','extraction','nonfactual'),'operator_managed')
    return replace(k,**changes)

def sign(a,k):return replace(a,signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest())

def signed_reviews(request,policy,k=None):
    k=key() if k is None else k
    return tuple(sign(Review(f'review-{i}-{k.key_id}',request.content_digest,policy.content_digest,subject,purpose,'VERIFIED',ids,950000,
        'SYNTHETIC TEST JUDGMENT. Not a live review or real-book result.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k)
        for i,((purpose,subject),ids) in enumerate(sorted(review_targets(request).items())))

def source_reviews(request,policy,k=None):
    k=source_key() if k is None else k;out=[]
    for claim in request.source.claims:
        purpose='semantic' if claim.kind=='FACT' else 'nonfactual'
        verdict='SUPPORTED' if claim.kind=='FACT' else 'NO_FACTUAL_ASSERTION'
        a=Assessment(f'source-{claim.claim_id}',request.source.content_digest,policy.source.content_digest,claim.claim_id,purpose,verdict,950000,
            'Synthetic source-context judgment only.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id)
        out.append(sign(a,k))
    return tuple(out)

def options(request,policy,**changes):
    k=key();sk=source_key()
    opts=dict(reviews=signed_reviews(request,policy,k),verifier=ReviewVerifier((k,)),source_assessments=source_reviews(request,policy,sk),source_verifier=AssessmentVerifier((sk,)))
    opts.update(changes);return opts

def codes(report):return {x.code for x in report.findings}

def rebind(request,candidate,extra_refs=()):
    refs=list(candidate.artifacts)
    for new in extra_refs:refs=[x for x in refs if x.artifact_id!=new.artifact_id]+[new]
    candidate=replace(candidate,artifacts=tuple(refs))
    return replace(request,source=replace(request.source,candidate_digest=candidate.content_digest)),candidate

class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.request,self.policy,self.candidate=fixture(self.root)
    def run_check(self,request=None,policy=None,**kwargs):
        r=self.request if request is None else request;p=self.policy if policy is None else policy
        return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kwargs))
    def assertCode(self,result,area,code,status=None):
        report=getattr(result,area);self.assertIn(code,codes(report))
        if status:self.assertEqual(report.status,status)
        self.assertFalse(result.product_accepted)
    def change_calibration(self,mutate,request=None):
        r=request or self.request;cal=r.calibrations[0]
        data=json.loads((self.root/cal.artifact.path).read_text());mutate(data)
        ref=artifact(self.root,cal.artifact.path,canonical_bytes(data),cal.artifact.artifact_id)
        return replace(r,calibrations=(replace(cal,artifact=ref),))
    def add_mastery(self,correct=9,total=10,**changes):
        placeholder=ArtifactRef('mastery-file','diagnostics/mastery.json','0'*64,1,'support')
        m=MasteryEvidence('mastery-1','switch','learner-test',placeholder,correct,total,NOW-20,NOW+60)
        m=replace(m,**changes)
        ref=artifact(self.root,placeholder.path,canonical_bytes(m.payload()),placeholder.artifact_id)
        return replace(self.request,masteries=(replace(m,artifact=ref),))
