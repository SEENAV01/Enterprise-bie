"""SYNTHETIC authored diagnostics; never operational approval or native media proof."""
from pathlib import Path
from dataclasses import asdict,replace
from fractions import Fraction
import hashlib,json,sys,tempfile,io,wave,subprocess,unittest,copy
import numpy as np
from bie.qa.media_runtime_v2.common import *
from bie.qa.media_runtime_v2.storage import StreamArtifact
ROOT=Path(__file__).resolve().parents[2]
NOW=1800000000
REV='a68e054025b8fe7756a71e998d9e9103dad8e0f4'
def bind(policy,run='run-h5'):
    return Binding(run,REV,'c'*64,digest(asdict(policy)))
def tool(name):
    import shutil
    p=Path(shutil.which(name)).resolve();return Tool(str(p),hashlib.sha256(p.read_bytes()).hexdigest())
def ref(root,path,data,aid='artifact',stream=False,role='support'):
    p=Path(root)/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    cls=StreamArtifact if stream else ArtifactRef
    return cls(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)
def save(root,path,value,aid):return ref(root,path,canonical_bytes(value),aid)
def codes(r):return {f['code'] for f in r['report']['findings']}
def wav(samples,rate=8000):
    out=io.BytesIO()
    with wave.open(out,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(np.asarray(samples,dtype='<i2').tobytes())
    return out.getvalue()
def encode(root,name='healthy',n=12,w=64,h=48,fps=12,mode='normal',audio=False):
    # Small deterministic diagnostic pixels; no files/fonts from the environment.
    frames=[]
    for i in range(n):
        p=np.zeros((h,w,3),dtype=np.uint8);p[:,:,1]=30
        p[8:32,8+(i%8):30+(i%8),:]=[130,180,220]
        if mode=='black' and i==4:p[:]=0
        if mode=='freeze':p[8:32,:,:]=[130,180,220]
        if mode=='jump' and i>=4:p=255-p
        if mode=='flash':p[:]=230 if i%2 else 10;p[0,0]=100
        frames.append(p.tobytes())
    raw=Path(root)/(name+'.rgb');raw.write_bytes(b''.join(frames));dest=Path(root)/(name+'.mp4')
    argv=['/usr/bin/ffmpeg','-v','error','-threads','1','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate',str(fps),'-i',str(raw)]
    if audio:argv+=['-f','lavfi','-i','sine=frequency=440:sample_rate=8000']
    argv+=['-frames:v',str(n),'-c:v','libx264','-threads','1','-crf','0','-pix_fmt','yuv420p']
    if audio:argv+=['-c:a','aac','-shortest']
    argv+=['-y',str(dest)]
    r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);assert r.returncode==0,r.stderr
    raw.unlink();data=dest.read_bytes();return StreamArtifact(name,dest.name,hashlib.sha256(data).hexdigest(),len(data),'video')
class Case(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def has(self,r,code):self.assertIn(code,codes(r));self.assertEqual(r['report']['status'],'BLOCKED')
    def unchanged(self,r):self.assertFalse(r['production_authorized']);self.assertFalse(r['product_accepted'])
