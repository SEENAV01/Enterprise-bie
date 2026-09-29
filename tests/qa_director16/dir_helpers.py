"""Authored SYNTHETIC text and reviewer fixtures, never real assessor execution."""
from pathlib import Path
from dataclasses import replace, asdict
import hashlib, hmac, tempfile, unittest
from bie.qa.release_v2.contracts import ArtifactRef, ReleaseCandidate, ContractError, canonical_bytes
from bie.qa.source_v2.models import Source, Block, Output, Citation, Claim, Request, Policy
from bie.qa.source_v2.attestation import Assessment, AssessmentKey, AssessmentVerifier
from bie.qa.director_v2 import *
from bie.qa.director_v2.attestation import review_targets
NOW = 1800000000
REV = '375d99af0edd0086206817dae932156ddf61c569'


def artifact(root, path, payload, aid, role='support'):
    p = root/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(payload)
    return ArtifactRef(aid, path, hashlib.sha256(payload).hexdigest(), len(payload), role)


def fixture(root, source_overrides=None, output_overrides=None):
    sentences = (
        ('c-hook', 'How can we count several equal-sized collections without recounting every object?', 'QUESTION'),
        ('c-definition', 'A group is a collection considered together. Equal groups contain the same number of objects.', 'FACT'),
        ('c-example', 'With two equal groups of three counters, there are six counters altogether.', 'FACT'),
        ('c-transition', 'Now use the same idea to check another arrangement.', 'INSTRUCTION'),
        ('c-condition', 'Use this count only when every object belongs to exactly one group.', 'INSTRUCTION'),
        ('c-payoff', 'Three equal groups of two counters also contain six counters.', 'FACT'),
        ('c-recap', 'Recap: count the groups and objects in each group, then explain the total.', 'INSTRUCTION'),
    )
    so = source_overrides or {}; oo = output_overrides or {}
    st = '\n'.join(so.get(cid, s) for cid, s, k in sentences)
    ot = '\n'.join(oo.get(cid, so.get(cid, s)) for cid, s, k in sentences)
    sr = artifact(root, 'sources/authored-director.txt', st.encode(), 'dir-source', 'source')
    out = artifact(root, 'outputs/director-script.txt', ot.encode(), 'dir-script')
    v = artifact(root, 'fixtures/video.bin', b'SYNTHETIC_NOT_A_RENDER', 'fixture-video', 'video')
    g = artifact(root, 'fixtures/game.bin', b'SYNTHETIC_NOT_A_GAME', 'fixture-game', 'game')
    candidate = ReleaseCandidate('2.0.0', 'dir-candidate', 'dir-run', REV, (sr, out, v, g))
    block = Block('dir-block', 'authored-dir', sr.sha256, 1, 'dir-region', (0,0,1000000,1000000), st, 'utf8', '1', 1000000)
    citations = []; claims = []; sp = op = 0
    for cid, text, kind in sentences:
        s = so.get(cid, text); o = oo.get(cid, s); cite = 'cite-' + cid
        citations.append(Citation(cite, block.block_id, block.content_digest, sp, sp+len(s), s))
        claims.append(Claim(cid, 'dir-output', out.sha256, op, op+len(o), o, kind, (cite,)))
        sp += len(s)+1; op += len(o)+1
    src = Request('1.0.0', 'dir-run', REV, candidate.content_digest,
                  (Source('authored-dir', sr, 'utf8', 1),), (block,), (Output('dir-output', out, 'narration'),), tuple(citations), tuple(claims))
    scenes = (Scene('s1', 'hook', 'Pose the counting problem and explain equal groups', ('obj-count',), (), 30000),
              Scene('s2', 'recap', 'Apply, qualify and recap the counting method', ('obj-count',), ('s1',), 30000))
    beats = (
        Beat('b-hook', 's1', 'hook', 'narration', 0, 5000, ('c-hook',), ('obj-count',)),
        Beat('b-definition', 's1', 'explanation', 'narration', 5000, 17000, ('c-definition',), ('obj-count',)),
        Beat('b-example', 's1', 'demonstration', 'narration', 17000, 27000, ('c-example',), ('obj-count',)),
        Beat('b-pause', 's1', 'pause', 'pause', 27000, 30000, (), ()),
        Beat('b-transition', 's2', 'transition', 'narration', 0, 5000, ('c-transition',), ('obj-count',)),
        Beat('b-payoff', 's2', 'payoff', 'narration', 5000, 20000, ('c-condition', 'c-payoff'), ('obj-count',)),
        Beat('b-recap', 's2', 'recap', 'narration', 20000, 30000, ('c-recap',), ('obj-count',)),
    )
    mappings = []
    for cid, _, kind in sentences:
        fid = {'c-definition':'facet-definition', 'c-example':'facet-example', 'c-payoff':'facet-payoff'}.get(cid)
        mode = 'quote' if kind == 'FACT' else ('question' if kind == 'QUESTION' else 'instruction')
        cond = (ConditionWitness('disjoint-groups', 'c-condition'),) if cid == 'c-payoff' else ()
        mappings.append(FidelityMapping('map-' + cid, cid, mode, ('cite-'+cid,), (fid,) if fid else (), cond))
    request = DirectorRequest('1.0.0', src, 'lesson-count', 'beginner', 'en', scenes, beats, (Route('route-main', ('s1','s2')),),
                              (Transition('bridge-12', 's1', 's2', ('c-transition',)),),
                              (Promise('promise-count', 'b-hook', ('b-example','b-payoff')),),
                              (TermIntroduction('intro-equal-groups', 'term-equal-groups', 'b-definition'),), (), tuple(mappings))
    facets = (FacetRequirement('facet-definition', ('cite-c-definition',)), FacetRequirement('facet-example', ('cite-c-example',)),
              FacetRequirement('facet-payoff', ('cite-c-payoff',), ('disjoint-groups',)))
    specs = tuple(SceneRequirement(s.scene_id, s.objective_ids, s.parent_scene_ids, (s.role,)) for s in scenes)
    rp = RouteRequirement('route-main', ('s1','s2'), ('obj-count',), tuple(f.facet_id for f in facets), max_duration_ms=65000)
    policy = DirectorPolicy('dir-test-policy', Policy('dir-source-policy', ('dir-output',)), 'lesson-count', 'beginner', 'en', specs, (rp,),
                            (TermRequirement('term-equal-groups', ('equal groups',)),), facets, ('promise-count',),
                            (TimingConstraint('reflect-after-example', 'b-example', 'b-transition', 3000, 5000),))
    return request, policy, candidate


def key(**changes):
    return replace(ReviewKey('dir-key', b'SYNTHETIC_DIR_TEST_KEY_NOT_PRODUCTION_001', 'dir-assessor', '1', 'dir-group',
                             ('inventory','mapping','teaching','support','inference'), 'operator_managed'), **changes)


def source_key(**changes):
    return replace(AssessmentKey('source-key', b'SYNTHETIC_DIR_SOURCE_KEY_NOT_PRODUCTION_1', 'source-assessor', '1',
                                 ('semantic','extraction','nonfactual'), 'operator_managed'), **changes)


def sign(a, k): return replace(a, signature=hmac.new(k.secret, a.signing_bytes(), hashlib.sha256).hexdigest())


def signed_reviews(r, p, k=None):
    k = k or key()
    return tuple(sign(Review(f'dir-review-{i}-{k.key_id}', r.content_digest, p.content_digest, s, purpose, 'VERIFIED', evidence, 950000,
                             'SYNTHETIC contextual assessment fixture; no actual assessor service.', k.evaluator_id, k.evaluator_version,
                             NOW-10, NOW+60, k.key_id), k) for i, ((purpose,s),evidence) in enumerate(sorted(review_targets(r).items())))


def source_reviews(r, p, k=None):
    k = k or source_key()
    return tuple(sign(Assessment('source-'+c.claim_id, r.source.content_digest, p.source.content_digest, c.claim_id,
                                 'semantic' if c.kind == 'FACT' else 'nonfactual',
                                 'SUPPORTED' if c.kind == 'FACT' else 'NO_FACTUAL_ASSERTION', 950000,
                                 'SYNTHETIC source review fixture.', k.evaluator_id, k.evaluator_version,
                                 NOW-10, NOW+60, k.key_id), k) for c in r.source.claims)


def options(r, p, **changes):
    k, sk = key(), source_key()
    out = dict(reviews=signed_reviews(r,p,k), verifier=ReviewVerifier((k,)), source_assessments=source_reviews(r,p,sk), source_verifier=AssessmentVerifier((sk,)))
    out.update(changes); return out


def change(rows, key, value, **kwargs):
    return tuple(replace(x, **kwargs) if getattr(x,key) == value else x for x in rows)


def codes(report): return {f.code for f in report.findings}


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)
        self.request, self.policy, self.candidate = fixture(self.root)
    def run_check(self, r=None, p=None, **kwargs):
        r = self.request if r is None else r; p = self.policy if p is None else p
        return evaluate(r, self.root, p, as_of=NOW, **options(r,p,**kwargs))
    def beat(self, bid, **changes): return replace(self.request, beats=change(self.request.beats, 'beat_id', bid, **changes))
    def limit(self, **changes): return replace(self.policy, pacing=replace(self.policy.pacing, **changes))
    def assertCode(self, result, area, code, status=None):
        report = getattr(result, area); self.assertIn(code, codes(report))
        if status: self.assertEqual(report.status,status)
        self.assertFalse(result.product_accepted)


def with_readout(root, r, p, candidate, text, beat_id='b-example'):
    """Add actual UTF-8 narration bytes and their source-linked claims to the fixture."""
    ref=artifact(root,'outputs/expanded-readout.txt',text.encode(),'readout-artifact')
    candidate=replace(candidate,artifacts=candidate.artifacts+(ref,))
    claim=Claim('c-readout','readout-output',ref.sha256,0,len(text),text,'FACT',('cite-c-example',))
    source=replace(r.source,candidate_digest=candidate.content_digest,outputs=r.source.outputs+(Output('readout-output',ref,'narration'),),claims=r.source.claims+(claim,))
    r=replace(r,source=source,spoken_forms=(SpokenForm(beat_id,text,('c-readout',)),),fidelity=r.fidelity+(FidelityMapping('map-readout','c-readout','paraphrase',('cite-c-example',),('facet-example',)),))
    p=replace(p,source=replace(p.source,expected_output_ids=p.source.expected_output_ids+('readout-output',)))
    return r,p,candidate
