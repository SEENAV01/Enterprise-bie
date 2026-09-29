"""Synthetic test fixtures only. No real evaluator/model/book/media acceptance."""
from pathlib import Path
from dataclasses import replace
import hashlib, hmac, tempfile, unittest
from bie.qa.release_v2.contracts import ArtifactRef, ReleaseCandidate, canonical_bytes, ContractError
from bie.qa.source_v2 import *

NOW=1_800_000_000
REV='375d99af0edd0086206817dae932156ddf61c569'
TEXT='The lamp uses 5 watts.'


def artifact(root, path, payload, aid, role):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    return ArtifactRef(aid,path,hashlib.sha256(payload).hexdigest(),len(payload),role)


def fixture(root, source_text=TEXT, output_text=None):
    output_text=source_text if output_text is None else output_text
    sref=artifact(root,'inputs/source.txt',source_text.encode(),'source-file','source')
    oref=artifact(root,'surfaces/narration.txt',output_text.encode(),'narration-file','support')
    video=artifact(root,'fixtures/video.bin',b'NOT_A_RENDER_TEST_FIXTURE','video-fixture','video')
    game=artifact(root,'fixtures/game.bin',b'NOT_A_GAME_TEST_FIXTURE','game-fixture','game')
    candidate=ReleaseCandidate('2.0.0','fixture-candidate','fixture-run',REV,(sref,oref,video,game))
    source=Source('book',sref,'utf8',1)
    block=Block('block-1','book',sref.sha256,1,'region-1',(0,0,1000000,1000000),source_text,'utf8','1',1000000)
    output=Output('narration',oref,'narration')
    citation=Citation('cite-1','block-1',block.content_digest,0,len(source_text),source_text)
    claim=Claim('claim-1','narration',oref.sha256,0,len(output_text),output_text,'FACT',('cite-1',))
    request=Request('1.0.0','fixture-run',REV,candidate.content_digest,(source,),(block,),(output,),(citation,),(claim,))
    return request,candidate,Policy('test-policy',('narration',))


def key(assurance='operator_managed', **changes):
    # Test harness simulation of deployment provisioning. Never export this key
    # as a real trusted key or interpret synthetic judgments as execution proof.
    k=AssessmentKey('test-key',b'TEST_ONLY_DO_NOT_DEPLOY_KEY_1234567','test-assessor','1',('semantic','extraction','nonfactual'),assurance)
    return replace(k,**changes)


def signed(request,policy,k=None,**changes):
    k=key() if k is None else k
    a=Assessment('assessment-1',request.content_digest,policy.content_digest,'claim-1','semantic','SUPPORTED',950000,
                 'Synthetic test judgment; no real assessment executed.',k.evaluator_id,k.evaluator_version,NOW-10,NOW+60,k.key_id)
    a=replace(a,**changes)
    return replace(a,signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest())


def codes(report):return {f.code for f in report.findings}


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.request,self.candidate,self.policy=fixture(self.root)

    def check(self,request=None,policy=None,**kwargs):
        return evaluate(self.request if request is None else request,self.root,
                        self.policy if policy is None else policy,as_of=NOW,**kwargs)

    def operator(self,request=None,policy=None,**changes):
        r=self.request if request is None else request;p=self.policy if policy is None else policy;k=key()
        return self.check(r,p,assessments=(signed(r,p,k,**changes),),verifier=AssessmentVerifier((k,)))

    def blocked(self,request,code):
        result=self.check(request)
        self.assertEqual(result.provenance.status,'BLOCKED');self.assertIn(code,codes(result.provenance))
        self.assertFalse(result.grounding.product_accepted)
        return result
