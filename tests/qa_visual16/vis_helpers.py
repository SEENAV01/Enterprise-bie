"""Authored SYNTHETIC source, judgments and candidate placeholders for tests only."""
from pathlib import Path
from dataclasses import replace,asdict
import hashlib,hmac,tempfile,unittest
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,ContractError,canonical_bytes,digest
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.visual_v2 import *
from bie.qa.visual_v2.attestation import review_targets
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'


def artifact(root,path,payload,aid,role='support'):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)


def fixture(root):
    sentences=('Group A has three counters.','Group B has three counters.','Together the groups contain six counters.')
    st='\n'.join(sentences)
    sr=artifact(root,'sources/authored-visual.txt',st.encode(),'vis-source','source')
    out=artifact(root,'outputs/visual-text.txt',st.encode(),'vis-output-artifact')
    v=artifact(root,'fixtures/video.bin',b'SYNTHETIC_NOT_A_RENDER','fixture-video','video')
    g=artifact(root,'fixtures/game.bin',b'SYNTHETIC_NOT_A_GAME','fixture-game','game')
    candidate=ReleaseCandidate('2.0.0','vis-candidate','vis-run',REV,(sr,out,v,g))
    block=Block('vis-block','authored-vis',sr.sha256,1,'vis-region',(0,0,1000000,1000000),st,'utf8','1',1000000)
    claims=[];cites=[];offset=0
    for i,s in enumerate(sentences,1):
        cites.append(Citation('cite-'+str(i),block.block_id,block.content_digest,offset,offset+len(s),s))
        claims.append(Claim('claim-'+str(i),'vis-output',out.sha256,offset,offset+len(s),s,'FACT',('cite-'+str(i),)))
        offset+=len(s)+1
    source=Request('1.0.0','vis-run',REV,candidate.content_digest,(Source('authored-vis',sr,'utf8',1),),(block,),
        (Output('vis-output',out,'on_screen'),),tuple(cites),tuple(claims))
    elems=tuple(VisualElement('object-'+str(i),'scene-main','text',('claim-'+str(i),),'meaning-'+str(i)) for i in range(1,4))
    scene=VisualScene('scene-main','diagram',('obj-count',),('equal-groups',))
    boxes=(Rect(40000,40000,600000,45000),Rect(40000,135000,600000,45000),Rect(40000,230000,680000,45000))
    canvas=Rect(0,0,800000,450000)
    ms=tuple(Measurement(e.object_id,b,canvas,t,24000,RGBA(0,0,0),RGBA(255,255,255),line_boxes=(Rect(b.x,b.y+5000,len(t)*12000,28000),)) for e,b,t in zip(elems,boxes,sentences))
    state=VisualState('state-desktop','scene-main','desktop',0,20000,ms)
    relation=VisualRelation('rel-above','scene-main','above','object-1','object-2',('claim-1','claim-2'))
    r=VisualRequest('1.0.0',source,'lesson-count','beginner','en',(scene,),elems,(state,),(relation,))
    view=ViewRequirement('desktop',800,450,Rect(20000,20000,760000,380000),(Rect(0,410000,800000,40000),))
    p=VisualPolicy('vis-test-policy',Policy('vis-source-policy',('vis-output',)),'lesson-count','beginner','en',
        (SceneRequirement('scene-main',('obj-count',),('diagram',),('equal-groups',)),),elems,
        (StateRequirement('state-desktop','scene-main','desktop',0,20000,tuple(e.object_id for e in elems),('rel-above',)),),(view,),(relation,))
    return r,p,candidate


def key(**changes):
    return replace(ReviewKey('vis-key',b'SYNTHETIC_VIS_TEST_KEY_NOT_PRODUCTION_001','vis-assessor','1','vis-group',
        ('inventory','mapping','teaching','support','inference'),'operator_managed'),**changes)


def source_key(**changes):
    return replace(AssessmentKey('vis-source-key',b'SYNTHETIC_VIS_SOURCE_NOT_PRODUCTION_001','source-assessor','1',
        ('semantic','extraction','nonfactual'),'operator_managed'),**changes)


def sign(a,k):return replace(a,signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest())


def signed_reviews(r,p,k=None):
    k=k or key();rd,pd=r.content_digest,p.content_digest
    return tuple(sign(Review(f'vis-review-{i}-{k.key_id}',rd,pd,s,purpose,'VERIFIED',evidence,950000,
        'SYNTHETIC visual assessment fixture; no actual assessor or calibration.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k)
        for i,((purpose,s),evidence) in enumerate(sorted(review_targets(r,p).items())))


def source_reviews(r,p,k=None):
    k=k or source_key();rd,pd=r.source.content_digest,p.source.content_digest
    return tuple(sign(Assessment('vis-source-'+c.claim_id,rd,pd,c.claim_id,'semantic','SUPPORTED',950000,
        'SYNTHETIC source review fixture.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for c in r.source.claims)


def options(r,p,**changes):
    k,sk=key(),source_key()
    out=dict(reviews=signed_reviews(r,p,k),verifier=ReviewVerifier((k,)),source_assessments=source_reviews(r,p,sk),source_verifier=AssessmentVerifier((sk,)))
    out.update(changes);return out


def change(rows,key,value,**kwargs):return tuple(replace(x,**kwargs) if getattr(x,key)==value else x for x in rows)
def codes(result):return {f.code for f in result.findings}


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.request,self.policy,self.candidate=fixture(self.root)
    def run_check(self,r=None,p=None,**kwargs):
        r=self.request if r is None else r;p=self.policy if p is None else p
        return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kwargs))
    def measured(self,oid='object-1',**changes):
        state=self.request.states[0];m=tuple(replace(x,**changes) if x.object_id==oid else x for x in state.measurements)
        return replace(self.request,states=(replace(state,measurements=m),))
    def limit(self,**changes):return replace(self.policy,limits=replace(self.policy.limits,**changes))
    def assertCode(self,result,area,code,status=None):
        report=getattr(result,area);self.assertIn(code,codes(report))
        if status:self.assertEqual(report.status,status)
        self.assertFalse(result.product_accepted)


def fake_capture(root,r,p,*,png=None,changes=None):
    """Byte-real PNG but authored metadata, not browser execution; test only."""
    from PIL import Image
    from io import BytesIO
    view=p.views[0];state=replace(r.states[0],capture_id='capture-test',geometry_mode='sampled')
    html=artifact(root,'capture-test/page.html',b'<!doctype html><p>SYNTHETIC CAPTURE FIXTURE</p>','capture-html')
    if png is None:
        b=BytesIO();Image.new('RGB',(view.width_px,view.height_px),'white').save(b,format='PNG');png=b.getvalue()
    shot=artifact(root,'capture-test/frame.png',png,'capture-png')
    payload=dict(schema_version='1.0.0',html_sha256=html.sha256,screenshot_sha256=shot.sha256,viewport=[view.width_px,view.height_px],
        state=asdict(state),renderer_id='synthetic-metadata',renderer_version='1',mode='static-html-sample',unsupported=[])
    payload.update(changes or {})
    raw=artifact(root,'capture-test/measurements.json',canonical_bytes(payload),'capture-measurement','support')
    cap=CaptureRef('capture-test',state.state_id,html,raw,shot,'synthetic-metadata','1')
    return replace(r,states=(state,),captures=(cap,)),cap
