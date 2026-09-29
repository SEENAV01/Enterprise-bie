"""Authored SYNTHETIC fixtures. These keys and judgments are NEVER production trust."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,tempfile,unittest
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,ContractError,canonical_bytes,digest
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.animation_v2 import *
from bie.qa.animation_v2.attestation import review_targets
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'

def artifact(root,path,payload,aid,role='support'):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)

def fixture(root):
    text='The marker moves from left to right.'
    sr=artifact(root,'source/authored.txt',text.encode(),'ani-source','source')
    out=artifact(root,'output/description.txt',text.encode(),'ani-description')
    v=artifact(root,'fixtures/video.bin',b'SYNTHETIC_NOT_VIDEO','fixture-video','video')
    g=artifact(root,'fixtures/game.bin',b'SYNTHETIC_NOT_GAME','fixture-game','game')
    cand=ReleaseCandidate('2.0.0','ani-candidate','ani-run',REV,(sr,out,v,g))
    block=Block('ani-block','authored-source',sr.sha256,1,'ani-region',(0,0,1000000,1000000),text,'utf8','1',1000000)
    cite=Citation('ani-cite',block.block_id,block.content_digest,0,len(text),text)
    claim=Claim('ani-claim','ani-output',out.sha256,0,len(text),text,'FACT',('ani-cite',))
    src=Request('1.0.0','ani-run',REV,cand.content_digest,(Source('authored-source',sr,'utf8',1),),(block,),(Output('ani-output',out,'on_screen'),),(cite,),(claim,))
    mode=Mode('standard','standard',3000,FrameRate(30),640,360)
    obj=ObjectSpec('marker','marker-meaning','object',0,3000,('ani-claim',))
    x=Track('move-x','standard','marker','x_mpx','rightward','explain',(Keyframe(0,40000),Keyframe(2000,200000)))
    y=Track('move-y','standard','marker','y_mpx','height','explain',(Keyframe(0,100000),Keyframe(2000,100000)))
    op=Track('opacity','standard','marker','opacity_ppm','visible','explain',(Keyframe(0,1000000),Keyframe(2000,1000000)))
    cue=Cue('narration','standard',0,2000,('ani-claim',))
    specs=tuple(TrackRequirement(t.track_id,t.mode_id,t.object_id,t.property,t.semantic_id,t.purpose,('ani-claim',),True,
        0,1000000,'increasing' if t.track_id=='move-x' else 'constant',t.keyframes[0].value,t.keyframes[-1].value,True) for t in (x,y,op))
    req=AnimationRequest('1.0.0',src,'lesson-motion',(mode,),(obj,),(x,y,op),(cue,))
    policy=AnimationPolicy('ani-policy',Policy('ani-source-policy',('ani-output',)),'lesson-motion',(mode,),(obj,),specs,(cue,),
        (TimingRule('start-together','move-x','narration','cue','start_sync',50),),(),(CaptureRequirement('standard',(0,15,30,45,60)),))
    return req,policy,cand

def key(**changes):
    return replace(ReviewKey('ani-key',b'SYNTHETIC_ANI_KEY_DO_NOT_USE_OPERATIONALLY','ani-assessor','1','ani-group',
        ('inventory','mapping','inference','disclosure'),'operator_managed'),**changes)

def source_key(**changes):
    return replace(AssessmentKey('ani-source-key',b'SYNTHETIC_ANI_SOURCE_DO_NOT_USE_OPERATIONALLY','source-assessor','1',
        ('semantic','extraction','nonfactual'),'operator_managed'),**changes)

def sign(r,k):return replace(r,signature=hmac.new(k.secret,r.signing_bytes(),hashlib.sha256).hexdigest())

def signed_reviews(r,p,k=None):
    k=k or key()
    return tuple(sign(Review('ani-review-'+str(i)+'-'+k.key_id,r.content_digest,p.content_digest,subject,purpose,'VERIFIED',evidence,950000,
        'SYNTHETIC authored animation assessment. No live or independent assessor.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k)
        for i,((purpose,subject),evidence) in enumerate(sorted(review_targets(r,p).items())))

def source_reviews(r,p,k=None):
    k=k or source_key()
    return tuple(sign(Assessment('source-'+c.claim_id,r.source.content_digest,p.source.content_digest,c.claim_id,'semantic','SUPPORTED',950000,
        'SYNTHETIC source assessment fixture.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for c in r.source.claims)

def options(r,p,**changes):
    k,sk=key(),source_key()
    out=dict(reviews=signed_reviews(r,p,k),verifier=ReviewVerifier((k,)),source_assessments=source_reviews(r,p,sk),source_verifier=AssessmentVerifier((sk,)))
    out.update(changes);return out

def change_track(r,tid='move-x',**changes):return replace(r,tracks=tuple(replace(t,**changes) if t.track_id==tid else t for t in r.tracks))

def codes(result):return {f.code for a in ('temporal','motion','alignment') for f in getattr(result,a).findings}

class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.r,self.p,self.c=fixture(self.root)
    def check(self,r=None,p=None,**kwargs):
        r=self.r if r is None else r;p=self.p if p is None else p
        return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kwargs))
    def assertCode(self,result,code):
        self.assertIn(code,codes(result));self.assertFalse(result.product_accepted)
