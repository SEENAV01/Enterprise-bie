"""SYNTHETIC unit fixtures. No fixture key is production trust or native render proof."""
from pathlib import Path
from dataclasses import asdict,replace
from tempfile import TemporaryDirectory
from fractions import Fraction
from unittest.mock import patch
import unittest,hashlib,hmac,json,io
from PIL import Image,ImageDraw
from bie.qa.release_v2.contracts import *
from bie.qa.video_v2.models import *
from bie.qa.video_v2.evaluator import evaluate,encode_log,review_targets
from bie.qa.video_v2.media import DecodedVideo
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
NOW=1800000000
ROOT=Path(__file__).resolve().parents[2]

def signed(r,p,*,assurance='operator_managed',verdict='VERIFIED'):
    key=ReviewKey('synthetic-key',b'unit-fixture-key-never-production!'*2,'fixture-assessor','1','fixture-group',('calibration','inventory'),assurance)
    out=[]
    for i,((purpose,subject),ids) in enumerate(review_targets(r,p).items()):
        a=Review('review-'+str(i),r.content_digest,p.content_digest,subject,purpose,verdict,ids,1000000,'SYNTHETIC test assessment; no empirical production claim.',key.evaluator_id,key.evaluator_version,NOW-1,NOW+100,key.key_id)
        out.append(replace(a,signature=hmac.new(key.secret,a.signing_bytes(),hashlib.sha256).hexdigest()))
    return tuple(out),ReviewVerifier((key,))

class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.inventory={}
        self.code=self.put('input-code','const x: number = 1;\n'.encode(),'input.ts')
        self.lock=self.put('input-lock',b'{"diagnostic":"not a Remotion dependency lock"}','lock.json')
        self.output=self.put('output-js',b'const x = 1;\n','output.js')
        self.movie=self.put('movie',b'SYNTHETIC unit media; inspector patched in unit tests','movie.mp4','video')
        self.logs=tuple(self.put('log-'+str(i),encode_log(b''),'logs/'+str(i)+'.json') for i in range(4))
        self.frames=[]
        for i in range(8):
            im=Image.new('RGB',(32,24),(20,30,40));d=ImageDraw.Draw(im);d.rectangle((1,1,4,4),fill=(240,240,240));d.rectangle((5+i,10,8+i,14),fill=(220,150,30));self.frames.append(im.tobytes())
        patchimg=Image.frombytes('RGB',(32,24),self.frames[0]).crop((1,1,5,5));buf=io.BytesIO();patchimg.save(buf,format='PNG')
        self.template=self.put('template',buf.getvalue(),'template.png')
        self.cr=ExecutionReceipt(VERSION,'compile','run','a'*40,'lesson',artifact_digest((self.code,self.lock)),artifact_digest((self.output,)),'0'*64,'tsc','fixture-1','1'*64,('tsc','input.ts'),'2'*64,0,True,False,self.logs[0],self.logs[1],NOW-1,'native','compile',0,0)
        cr=self.put('compile-receipt',canonical_bytes(asdict(self.cr)),'compile.json')
        self.rr=ExecutionReceipt(VERSION,'render','run','a'*40,'lesson',artifact_digest((self.output,)),artifact_digest((self.movie,)),cr.sha256,'remotion','fixture-1','3'*64,('remotion','render'),'4'*64,0,True,False,self.logs[2],self.logs[3],NOW-1,'native','full',0,8)
        rr=self.put('render-receipt',canonical_bytes(asdict(self.rr)),'render.json')
        self.book=self.put('book',b'Author-written source fixture.','book.txt','source');self.game=self.put('game',b'Unexecuted placeholder fixture.','game.txt','game')
        self.c=ReleaseCandidate('2.0.0','candidate','run','a'*40,tuple(self.inventory.values()))
        self.r=VideoRequest(VERSION,'run','a'*40,self.c.content_digest,'lesson',self.movie,cr,rr,(self.code,self.lock),(self.output,))
        self.p=VideoPolicy('lesson',artifact_digest(self.r.inputs),32,24,4,1,8,regions=(RegionExpectation('essential',0,1,1,4,4,self.template),),sample_stride=3,expected_motion=(Window(0,8),),max_repeated_frames=2)
        self.obs=DecodedVideo(32,24,'h264','yuv420p',0,Fraction(4),Fraction(1,4),tuple(range(8)),(1,)*8,tuple(self.frames),'5'*64,'6'*64,'7'*64)
    def put(self,aid,data,path,role='support'):
        dest=self.root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        r=ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role);self.inventory[aid]=r;return r
    def receipt(self,stage,**changes):
        old=self.cr if stage=='compile' else self.rr;new=replace(old,**changes)
        ref=self.put(stage+'-receipt',canonical_bytes(asdict(new)),stage+'.json')
        r=replace(self.r,**{stage+'_receipt':ref})
        if stage=='compile':
            rr=replace(self.rr,parent_receipt_sha256=ref.sha256)
            r=replace(r,render_receipt=self.put('render-receipt',canonical_bytes(asdict(rr)),'render.json'))
        return r
    def run_eval(self,r=None,p=None,obs=None,*,authenticated=True,extra=None):
        r=self.r if r is None else r;p=self.p if p is None else p;obs=self.obs if obs is None else obs
        reviews,verifier=signed(r,p) if authenticated else ((),ReviewVerifier())
        options=dict(reviews=reviews,verifier=verifier)
        if extra:options.update(extra)
        with patch('bie.qa.video_v2.evaluator.inspect_bytes',return_value=obs):return evaluate(r,self.root,p,as_of=NOW,**options)
    def codes(self,res):return {f.code for r in res.reports for f in r.findings}
    def check_code(self,code,r=None,p=None,obs=None,**kwargs):
        result=self.run_eval(r,p,obs,**kwargs);self.assertIn(code,self.codes(result));return result
