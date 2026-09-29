from vis_helpers import *
import json
from bie.qa.visual_v2.bridge import prepare_release_evidence
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator

class ReleaseBridge(FixtureCase):
    def prepared(self,r=None,p=None,c=None,**kwargs):
        r=r or self.request;p=p or self.policy;c=c or self.candidate
        return prepare_release_evidence(r,c,self.root,p,as_of=NOW,**options(r,p),**kwargs)
    def test_healthy_plan_never_full_visual_media_pass(self):
        a=self.prepared();self.assertEqual(a.envelope.status,'NOT_RUN');self.assertEqual(a.envelope.gate_id,'visual_quality')
        self.assertEqual(a.envelope.signature,'');self.assertEqual(a.envelope.signer_key_id,'UNSIGNED')
    def test_broken_geometry_is_fail(self):self.assertEqual(self.prepared(self.measured(displayed=False)).envelope.status,'FAIL')
    def test_report_byte_identity(self):
        a=self.prepared();self.assertEqual(a.envelope.report.size,len(a.report_bytes));self.assertEqual(a.envelope.report.sha256,hashlib.sha256(a.report_bytes).hexdigest())
    def test_report_no_acceptance(self):
        d=json.loads(self.prepared().report_bytes);self.assertFalse(d['actual_media_evaluated']);self.assertFalse(d['product_accepted'])
    def test_bridge_is_pure(self):
        a=self.prepared();self.assertFalse((self.root/a.envelope.report.path).exists())
    def test_release_evaluator_blocks_incomplete_unsigned_evidence(self):
        a=self.prepared();p=self.root/a.envelope.report.path;p.parent.mkdir(parents=True);p.write_bytes(a.report_bytes)
        result=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.candidate,(a.envelope,)),self.root,as_of=NOW)
        self.assertEqual(result.release_status,'BLOCKED');self.assertFalse(result.product_accepted)
    def test_candidate_digest_mismatch(self):
        with self.assertRaises(ContractError):self.prepared(c=replace(self.candidate,candidate_id='other'))
    def test_artifact_mismatch_even_if_candidate_digest_rebound(self):
        c=replace(self.candidate,artifacts=(replace(self.candidate.artifacts[0],sha256='0'*64),)+self.candidate.artifacts[1:])
        r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepared(r,c=c)
    def test_uninspected_extra_source_rejected(self):
        a=artifact(self.root,'sources/extra.txt',b'Uninspected','extra','source');c=replace(self.candidate,artifacts=self.candidate.artifacts+(a,))
        r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepared(r,c=c)
    def test_report_collision_rejected(self):
        a=artifact(self.root,'collision.txt',b'collision','qa16-visual-quality-report');c=replace(self.candidate,artifacts=self.candidate.artifacts+(a,))
        r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaises(ContractError):self.prepared(r,c=c)
    def test_capture_must_belong_to_candidate(self):
        r,cap=fake_capture(self.root,self.request,self.policy)
        with self.assertRaises(ContractError):self.prepared(r)
    def test_valid_capture_still_cannot_release_movie(self):
        r,cap=fake_capture(self.root,self.request,self.policy)
        c=replace(self.candidate,artifacts=self.candidate.artifacts+(cap.html,cap.measurements,cap.screenshot))
        r=replace(r,source=replace(r.source,candidate_digest=c.content_digest))
        a=self.prepared(r,c=c);self.assertEqual(a.envelope.status,'NOT_RUN');self.assertIn(cap.screenshot.artifact_id,a.envelope.inspected_artifact_ids)
        self.assertNotIn('fixture-video',a.envelope.inspected_artifact_ids)
    def test_bound_expiry(self):self.assertEqual(self.prepared(p=replace(self.policy,max_receipt_age_seconds=120)).envelope.expires_at,NOW+120)
    def test_repeat_bytes(self):self.assertEqual(self.prepared(),self.prepared())
