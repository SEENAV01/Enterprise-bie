"""Authored synthetic fixtures. No textbook/provider/production acceptance.

The explicit operational_simulation helper tests provisioned-key behavior with
invented judgments, including deliberately wrong judgments in negative tests.
These credentials and receipts must never become deployed trusted evidence.
"""
from pathlib import Path
from dataclasses import replace
import hashlib, hmac, tempfile, unittest
from bie.qa.release_v2.contracts import ArtifactRef, ReleaseCandidate, ContractError, canonical_bytes
from bie.qa.source_v2 import models as source
from bie.qa.source_v2.attestation import Assessment, AssessmentKey, AssessmentVerifier
from bie.qa.semantic_v2 import *
from bie.qa.semantic_v2.attestation import PURPOSES

NOW = 1800000000
REV = '375d99af0edd0086206817dae932156ddf61c569'
CONTEXT = (('domain', 'synthetic-demonstration'), ('trial', 'A'))


def artifact(root, path, payload, aid, role):
    p = root/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(payload)
    return ArtifactRef(aid, path, hashlib.sha256(payload).hexdigest(), len(payload), role)


def quantity(lower='5', upper=None, **changes):
    p = Proposition('demo-lamp', 'power', Value('quantity', lower=lower,
        upper=lower if upper is None else upper, unit='W'), 'positive', CONTEXT)
    return replace(p, **changes)


def fixture(root, values=('5',), ref_values=('5',), channels=None):
    channels = ('narration',)*len(values) if channels is None else channels
    lines = [f'The demo lamp consumes {v} watts in trial A.' for v in ref_values]
    text = '\n'.join(lines)
    sref = artifact(root, 'inputs/reference.txt', text.encode(), 'source-file', 'source')
    block = source.Block('block-1', 'book', sref.sha256, 1, 'region-1',
        (0, 0, 1000000, 1000000), text, 'utf8', '1', 1000000)
    citations=[]; offset=0
    for i, line in enumerate(lines):
        citations.append(source.Citation(f'cite-{i+1}', 'block-1', block.content_digest, offset, offset+len(line), line))
        offset += len(line)+1
    outputs=[]; claims=[]; normals=[]
    for i, (v, channel) in enumerate(zip(values, channels), 1):
        line=f'The demo lamp consumes {v} watts in trial A.'
        oref=artifact(root, f'surfaces/output-{i}.txt', line.encode(), f'output-file-{i}', 'support')
        outputs.append(source.Output(f'output-{i}', oref, channel))
        claims.append(source.Claim(f'claim-{i}', f'output-{i}', oref.sha256, 0, len(line), line, 'FACT', tuple(c.citation_id for c in citations)))
        normals.append(Normalization(f'claim-{i}', (quantity(v),)))
    video=artifact(root, 'fixtures/video.bin', b'NOT_A_RENDER_SYNTHETIC_FIXTURE', 'video-fixture', 'video')
    game=artifact(root, 'fixtures/game.bin', b'NOT_A_GAME_SYNTHETIC_FIXTURE', 'game-fixture', 'game')
    candidate=ReleaseCandidate('2.0.0','fixture-candidate','fixture-run',REV,
        (sref, video, game)+tuple(o.artifact for o in outputs))
    sr=source.Request('1.0.0','fixture-run',REV,candidate.content_digest,
        (source.Source('book',sref,'utf8',1),),(block,),tuple(outputs),tuple(citations),tuple(claims))
    refs=tuple(ReferenceFact(f'ref-{i}',quantity(v),(f'cite-{i}',)) for i,v in enumerate(ref_values,1))
    request=SemanticRequest('1.0.0',sr,tuple(normals),refs,(CoverageLink('link-1','req-1',('claim-1',),2),))
    policy=SemanticPolicy('synthetic-policy',source.Policy('synthetic-source-policy',tuple(o.output_id for o in outputs)),
        tuple(r.reference_id for r in refs),('book',),
        (PredicateRule('power','quantity','single','W',('domain','trial')),),
        (Requirement('req-1','power','meaning','Teach power in the authored toy example.',2,1,True,
            ('narration','caption','on_screen','game_feedback','game_prompt','lesson')),))
    return request,policy,candidate


def semantic_key(**changes):
    k=SemanticKey('synthetic-key',b'SYNTHETIC_TEST_SECRET_DO_NOT_DEPLOY_1234','synthetic-reviewer','1',
        'synthetic-independent-group',PURPOSES,'operator_managed')
    return replace(k,**changes)


def signed(a,k):
    return replace(a,signature=hmac.new(k.secret,a.signing_bytes(),hashlib.sha256).hexdigest())


def operational_simulation(request,policy,k=None):
    k=semantic_key() if k is None else k
    sk=AssessmentKey('synthetic-source-key',b'SYNTHETIC_SOURCE_KEY_NOT_FOR_DEPLOYMENT_123','synthetic-source-reviewer','1',
        ('semantic','extraction','nonfactual'),'operator_managed')
    sas=[]
    for c in request.source.claims:
        purpose='semantic' if c.kind=='FACT' else 'nonfactual'
        a=Assessment('source-assessment-'+c.claim_id,request.source.content_digest,policy.source.content_digest,
            c.claim_id,purpose,'SUPPORTED' if purpose=='semantic' else 'NO_FACTUAL_ASSERTION',950000,
            'Synthetic test judgment. No source provider or human service ran.',sk.evaluator_id,sk.evaluator_version,
            NOW-10,NOW+60,sk.key_id)
        sas.append(signed(a,sk))
    claims={c.claim_id:c for c in request.source.claims}
    targets=[]
    for n in request.normalizations:
        if n.claim_id in claims:targets.append(('normalization',n.claim_id,claims[n.claim_id].citation_ids))
    for r in request.references:targets.append(('reference',r.reference_id,r.citation_ids))
    for l in request.coverage_links:
        es=tuple(sorted({e for cid in l.claim_ids if cid in claims for e in claims[cid].citation_ids}))
        if es:targets.append(('coverage',l.link_id,es))
    targets.append(('consistency','semantic-scope',tuple(sorted(c.citation_id for c in request.source.citations))))
    assessments=[]
    for i,(purpose,subject,es) in enumerate(targets):
        a=SemanticAssessment('assessment-'+str(i),request.content_digest,policy.content_digest,subject,purpose,'VERIFIED',es,
            950000,'Synthetic test judgment; not evidence of real-world semantic quality.',k.evaluator_id,k.evaluator_version,
            NOW-10,NOW+60,k.key_id)
        assessments.append(signed(a,k))
    return dict(assessments=tuple(assessments),verifier=SemanticVerifier((k,)),
        source_assessments=tuple(sas),source_verifier=AssessmentVerifier((sk,)))


def codes(report):return {f.code for f in report.findings}

def all_codes(result):return codes(result.factual)|codes(result.coverage)|codes(result.contradiction)


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.request,self.policy,self.candidate=fixture(self.root)

    def run_case(self,request=None,policy=None,**options):
        return evaluate(self.request if request is None else request,self.root,
            self.policy if policy is None else policy,as_of=NOW,**options)

    def op(self,request=None,policy=None):
        r=self.request if request is None else request;p=self.policy if policy is None else policy
        return self.run_case(r,p,**operational_simulation(r,p))
