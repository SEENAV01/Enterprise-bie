"""Authored SYNTHETIC assessment fixtures; keys are not operational trust."""
from pathlib import Path
from dataclasses import replace,asdict
import io,wave,math,struct,hashlib,hmac,tempfile,unittest,json
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,ContractError,canonical_bytes
from bie.qa.source_v2.models import Source,Block,Output,Citation,Claim,Request,Policy
from bie.qa.source_v2.attestation import Assessment,AssessmentKey,AssessmentVerifier
from bie.qa.audio_v2 import *
from bie.qa.audio_v2.attestation import review_targets
NOW=1800000000
REV='375d99af0edd0086206817dae932156ddf61c569'
ROOT=Path(__file__).resolve().parents[2]
def artifact(root,path,payload,aid,role='support'):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)
def wav_bytes(rate=8000,channels=1,samples=8000,mode='tone'):
    data=bytearray()
    for i in range(samples):
        a=0 if mode=='silence' else 32767 if mode=='clipped' else int(8000*math.sin(2*math.pi*440*i/rate))
        for ch in range(channels):data.extend(struct.pack('<h',-a if mode=='opposed' and ch==1 else a))
    buf=io.BytesIO()
    with wave.open(buf,'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
    return buf.getvalue()
def fixture(root):
    text='Force moves objects.'
    sr=artifact(root,'source/authored.txt',text.encode(),'audio-source','source');out=artifact(root,'output/script.txt',text.encode(),'audio-script')
    audio=artifact(root,'audio/narration.wav',wav_bytes(),'audio-pcm')
    timing=TimingReceipt('bie.qa.audio-timing/1','clip',audio.sha256,hashlib.sha256(text.encode()).hexdigest(),8000,8000,'synthetic-assessor','human_alignment',(Word(0,0,5,'Force',0,2000),Word(1,6,11,'moves',2000,4000),Word(2,12,20,'objects.',4000,8000)))
    tr=artifact(root,'audio/timing.json',canonical_bytes(asdict(timing)),'audio-timing')
    cap=artifact(root,'audio/captions.srt',b'1\n00:00:00,000 --> 00:00:01,000\nForce moves objects.\n','audio-captions')
    pr=PronunciationReceipt('bie.qa.pronunciation/1','clip',audio.sha256,timing.transcript_sha256,'en','voice','human_listening',(PronunciationObservation('force',0,2000,'fɔːs','correct'),))
    pe=artifact(root,'audio/pronunciation.json',canonical_bytes(asdict(pr)),'audio-pronunciation')
    v=artifact(root,'fixtures/not-video.bin',b'SYNTHETIC_NOT_VIDEO','fixture-video','video');g=artifact(root,'fixtures/not-game.bin',b'SYNTHETIC_NOT_GAME','fixture-game','game')
    cand=ReleaseCandidate('2.0.0','audio-candidate','audio-run',REV,(sr,out,audio,tr,cap,pe,v,g))
    block=Block('block','source',sr.sha256,1,'region',(0,0,1000000,1000000),text,'utf8','1',1000000)
    cite=Citation('cite','block',block.content_digest,0,len(text),text);claim=Claim('claim','output',out.sha256,0,len(text),text,'FACT',('cite',))
    source=Request('1.0.0','audio-run',REV,cand.content_digest,(Source('source',sr,'utf8',1),),(block,),(Output('output',out,'narration'),),(cite,),(claim,))
    req=AudioRequest('1.0.0',source,'lesson',(Clip('clip',audio,tr,0,'en','voice'),),(CaptionTrack('cap','clip',cap,'srt','en'),),(PronunciationEvidence('clip',pe),))
    n=Narration('clip',('claim',),text,'en','voice',0,1000,8000)
    p=AudioPolicy('audio-policy',Policy('source-policy',('output',)),'lesson',(n,),(Cue('cue','clip',0,0,250,10),),(Term('force','clip',0,5,'Force','en',('fɔːs',)),))
    return req,p,cand

def key(**changes):return replace(ReviewKey('key',b'SYNTHETIC_AUDIO_KEY_NOT_FOR_PRODUCTION','assessor','1','group',('inventory','mapping','calibration'),'operator_managed'),**changes)
def source_key(**changes):return replace(AssessmentKey('source-key',b'SYNTHETIC_AUDIO_SOURCE_NOT_FOR_PRODUCTION','source-assessor','1',('semantic','extraction','nonfactual'),'operator_managed'),**changes)
def sign(r,k):return replace(r,signature=hmac.new(k.secret,r.signing_bytes(),hashlib.sha256).hexdigest())
def signed_reviews(r,p,k=None):
    k=k or key()
    return tuple(sign(Review('review-'+str(i)+'-'+k.key_id,r.content_digest,p.content_digest,subject,purpose,'VERIFIED',evidence,950000,'SYNTHETIC fixture only; no real assessor or acoustic proof.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id),k) for i,((purpose,subject),evidence) in enumerate(sorted(review_targets(r,p).items())))
def options(r,p,**changes):
    k,sk=key(),source_key()
    source=tuple(sign(Assessment('source-'+c.claim_id,r.source.content_digest,p.source.content_digest,c.claim_id,'semantic','SUPPORTED',950000,'SYNTHETIC authored source fixture.',sk.evaluator_id,sk.evaluator_version,NOW-10,NOW+60,sk.key_id),sk) for c in r.source.claims)
    out=dict(reviews=signed_reviews(r,p,k),verifier=ReviewVerifier((k,)),source_assessments=source,source_verifier=AssessmentVerifier((sk,)));out.update(changes);return out

def codes(result):return {f.code for k in ('sync','captions','pronunciation') for f in getattr(result,k).findings}
class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.r,self.p,self.c=fixture(self.root)
    def check(self,r=None,p=None,**kw):
        r=self.r if r is None else r;p=self.p if p is None else p
        return evaluate(r,self.root,p,as_of=NOW,**options(r,p,**kw))
    def assertCode(self,result,code):self.assertIn(code,codes(result));self.assertFalse(result.product_accepted)
    def timing(self,**changes):
        from bie.qa.audio_v2.codec import decode
        t=decode(json.loads((self.root/self.r.clips[0].timing.path).read_bytes()),TimingReceipt);t=replace(t,**changes)
        a=artifact(self.root,'audio/changed-timing.json',canonical_bytes(asdict(t)),'changed-timing')
        return replace(self.r,clips=(replace(self.r.clips[0],timing=a),))
    def captions(self,body,fmt='srt'):
        a=artifact(self.root,'audio/changed-cap.txt',body if isinstance(body,bytes) else body.encode(),'changed-captions')
        return replace(self.r,captions=(replace(self.r.captions[0],artifact=a,format=fmt),))
    def pronunciation(self,**changes):
        from bie.qa.audio_v2.codec import decode
        t=decode(json.loads((self.root/self.r.pronunciation[0].artifact.path).read_bytes()),PronunciationReceipt);t=replace(t,**changes)
        a=artifact(self.root,'audio/changed-pron.json',canonical_bytes(asdict(t)),'changed-pronunciation');return replace(self.r,pronunciation=(PronunciationEvidence('clip',a),))
