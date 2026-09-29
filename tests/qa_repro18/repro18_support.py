"""Authored diagnostic producers and SYNTHETIC reviewer credentials, never production."""
from pathlib import Path
from dataclasses import replace,asdict
import copy,hashlib,hmac,json,tempfile,shutil
from bie.qa.release_v2.contracts import ArtifactRef,canonical_bytes,digest
from bie.qa.repair_v2.models import Snapshot
from bie.qa.reproducibility_v2 import *
from bie.qa.reasoning_v2.attestation import Review,ReviewKey,ReviewVerifier
NOW=1801000000
SECRET=b'SYNTHETIC-REPRO018-TEST-KEY-NOT-PRODUCTION'
KEY=ReviewKey('test-key',SECRET,'synthetic-assessor','1','test-group',('inventory','support'),'operator_managed')
VERIFIER=ReviewVerifier((KEY,))
GOOD='''import json,sys,random\nfrom pathlib import Path\nr=json.loads(Path(sys.argv[1]).read_text())\np=Path(sys.argv[2]);rng=random.Random(r['seed'])\nsource=Path(r['input_directory'],'lesson.txt').read_text()\na={'text':source,'sample':rng.randrange(100000),'epoch':r['source_date_epoch'],'parameters':r['parameters']}\n(p/'lesson.json').write_text(json.dumps(a,sort_keys=True,separators=(',',':')))\n(p/'game.json').write_text(json.dumps({'states':['start','done'],'score':1},sort_keys=True))\n'''
NONDETERMINISTIC=GOOD+"\nimport uuid\n(p/'game.json').write_text(str(uuid.uuid4()))\n"
EXTRA=GOOD+"\n(p/'extra.txt').write_text('unexpected')\n"
MISSING=GOOD+"\n(p/'game.json').unlink()\n"
LINK=GOOD+"\n(p/'game.json').unlink();(p/'game.json').symlink_to(p/'lesson.json')\n"
MUTATE=GOOD+"\nPath(r['input_directory'],'lesson.txt').write_text('changed')\n"
FAIL="raise RuntimeError('authored producer failure')\n"
TIMEOUT="import time\ntime.sleep(5)\n"


def ref(aid,path,data,role='support'):return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),role)

def codes(result):return {f.code for r in result.reports for f in r.findings}

class Fixture:
    def __init__(self,environment,script=GOOD,root=None):
        self.tmp=tempfile.TemporaryDirectory() if root is None else None
        self.root=Path(self.tmp.name) if self.tmp else Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.source_root=self.root/'source';self.source_root.mkdir()
        records=[]
        for aid,path,data,role in [('producer','producer.py',script.encode(),'support'),('source','lesson.txt','Two plus two is four. जोड़ का अभ्यास।'.encode(),'source'),('video','video.bin',b'authored-video-placeholder-not-rendered','video'),('game','game.bin',b'authored-game-placeholder-not-runtime','game')]:
            (self.source_root/path).write_bytes(data);records.append(ref(aid,path,data,role))
        self.source=Snapshot('demo-run','a'*40,tuple(records))
        self.policy=ReproPolicy('test-repro-policy',self.source.content_digest,'stdlib-emitter','producer',records[0].sha256,environment,
            (OutputSpec('lesson','lesson.json'),OutputSpec('game','game.json','game')))
        self.evidence=self.root/'evidence'
    def actual(self):
        self.request=collect('demo-job',self.source,self.source_root,self.evidence,self.policy,as_of=NOW)
        self.record=json.loads((self.evidence/'execution.json').read_text());self.rebind();return self.record
    def rebind(self):
        data=canonical_bytes(self.record);(self.evidence/'execution.json').write_bytes(data)
        self.request=ReproRequest('demo-job',self.source,ref('repro-execution','execution.json',data,'report'))
        groups=[('repro-inventory','inventory',tuple(sorted(a.artifact_id for a in self.source.artifacts))),('repro-execution','support',('repro-execution',))]
        self.reviews=[]
        for i,(subject,purpose,ids) in enumerate(groups):
            r=Review('synthetic-'+str(i),self.request.content_digest,self.policy.content_digest,subject,purpose,'VERIFIED',ids,1000000,
                'SYNTHETIC authorization used only in diagnostic tests.','synthetic-assessor','1',NOW-1,NOW+100,'test-key')
            self.reviews.append(replace(r,signature=hmac.new(SECRET,r.signing_bytes(),hashlib.sha256).hexdigest()))
        self.reviews=tuple(self.reviews)
    def evaluate(self,**kw):
        return evaluate(self.request,self.source_root,self.evidence,self.policy,as_of=kw.pop('as_of',NOW),reviews=kw.pop('reviews',self.reviews),verifier=kw.pop('verifier',VERIFIER),**kw)
    def close(self):
        if self.tmp:self.tmp.cleanup()
    @classmethod
    def clone(cls,original):
        f=object.__new__(cls);f.tmp=tempfile.TemporaryDirectory();f.root=Path(f.tmp.name)
        shutil.copytree(original.source_root,f.root/'source');shutil.copytree(original.evidence,f.root/'evidence')
        f.source_root=f.root/'source';f.evidence=f.root/'evidence';f.source=original.source;f.policy=original.policy
        f.record=copy.deepcopy(original.record);f.rebind();return f
