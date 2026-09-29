"""Executable native integration and release-bridge boundary checks."""
from dir_helpers import *
import json
from bie.qa.director_v2.adapters import to_native
from bie.qa.director_v2.bridge import prepare_release_evidence
from bie.director.lesson_architecture_contract import validate_lesson_architecture
from bie.director.script_plan import validate_script_plan
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.release_v2.policy import enterprise_policy


class NativeAdapters(FixtureCase):
    def test_native_builders_validate_actual_types(self):
        n=to_native(self.request,self.policy.policy_id)
        self.assertIs(validate_lesson_architecture(n.architecture),n.architecture)
        self.assertIs(validate_script_plan(n.script),n.script)
        self.assertTrue(n.requires_review)

    def test_native_fingerprints_match_executed_evaluation(self):
        n=to_native(self.request,self.policy.policy_id);result=self.run_check()
        self.assertEqual(n.architecture.fingerprint(),result.native_architecture_fingerprint)
        self.assertEqual(n.script.fingerprint(),result.native_script_fingerprint)

    def test_native_id_order_is_not_timeline_order(self):
        n=to_native(self.request)
        native=[s.segment_id for s in n.script.segments]
        timeline=[b.beat_id for b in self.request.beats if b.channel!='pause']
        self.assertEqual(native,sorted(native));self.assertNotEqual(native,timeline)
        self.assertEqual(self.request.routes[0].scene_ids,('s1','s2'))

    def test_pause_is_not_fake_script_text(self):
        n=to_native(self.request)
        self.assertNotIn('b-pause',{s.segment_id for s in n.script.segments})

    def test_spoken_form_native_projection_preserves_inspected_text(self):
        text='Two collections with three counters in each contain six counters in total.'
        r,p,c=with_readout(self.root,self.request,self.policy,self.candidate,text)
        n=to_native(r);segment=next(x for x in n.script.segments if x.segment_id=='b-example')
        self.assertEqual(segment.text_intent,text)
        self.assertIn('c-readout',segment.evidence_ids)
        self.assertEqual(self.run_check(r,p).status,'CHECKS_PASSED')

    def test_native_invalid_request_type(self):
        with self.assertRaisesRegex(ContractError,'DIR_NATIVE_REQUEST_TYPE'):to_native({})

    def test_unknown_native_text_reference(self):
        r=self.beat('b-example',claim_ids=('no-claim',))
        with self.assertRaises(ContractError):to_native(r)

    def test_native_dependency_content_identity(self):
        root=Path(__file__).resolve().parents[2]
        entries=json.loads((root/'evidence/qa_section16/native_dependencies_007.json').read_text())
        self.assertEqual(len(entries),1)
        e=entries[0];raw=(root/e['path']).read_bytes()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),e['git_blob_sha'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),e['sha256'])
        self.assertEqual(len(raw),e['bytes'])


class ReleaseBridge(FixtureCase):
    def prepared(self,r=None,p=None,c=None,**kwargs):
        r=r or self.request;p=p or self.policy;c=c or self.candidate
        return prepare_release_evidence(r,c,self.root,p,as_of=NOW,**options(r,p),**kwargs)

    def test_healthy_text_plan_never_media_pass(self):
        out=self.prepared()
        self.assertEqual(out.envelope.status,'NOT_RUN')
        self.assertEqual(out.envelope.gate_id,'director_quality')
        self.assertEqual(out.envelope.signature,'')
        self.assertEqual(out.envelope.signer_key_id,'UNSIGNED')
        self.assertIn('ACTUAL_MEDIA_DIR_NOT_EVALUATED',out.envelope.diagnostics)

    def test_failed_plan_is_fail(self):
        r=self.beat('b-example',end_ms=40000)
        self.assertEqual(self.prepared(r).envelope.status,'FAIL')

    def test_unsigned_plan_stays_not_run(self):
        out=prepare_release_evidence(self.request,self.candidate,self.root,self.policy,as_of=NOW)
        self.assertEqual(out.envelope.status,'NOT_RUN')
        self.assertEqual(json.loads(out.report_bytes)['declared_director_plan']['status'],'REVIEW_REQUIRED')

    def test_report_hash_and_byte_length(self):
        out=self.prepared()
        self.assertEqual(out.envelope.report.sha256,hashlib.sha256(out.report_bytes).hexdigest())
        self.assertEqual(out.envelope.report.size,len(out.report_bytes))

    def test_report_contains_no_acceptance_claim(self):
        d=json.loads(self.prepared().report_bytes)
        self.assertFalse(d['actual_media_evaluated']);self.assertFalse(d['product_accepted'])
        self.assertFalse(d['declared_director_plan']['product_accepted'])

    def test_bridge_is_pure_no_report_write(self):
        out=self.prepared();self.assertFalse((self.root/out.envelope.report.path).exists())

    def test_repeat_bridge_bytes_identical(self):
        self.assertEqual(self.prepared(),self.prepared())

    def test_actual_release_evaluator_blocks_incomplete_bundle(self):
        out=self.prepared();path=self.root/out.envelope.report.path
        path.parent.mkdir(parents=True);path.write_bytes(out.report_bytes)
        evaluated=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.candidate,(out.envelope,)),self.root,as_of=NOW)
        self.assertEqual(evaluated.release_status,'BLOCKED');self.assertFalse(evaluated.product_accepted)

    def test_candidate_digest_mismatch_rejected(self):
        c=replace(self.candidate,candidate_id='different-candidate')
        with self.assertRaisesRegex(ContractError,'DIR_CANDIDATE_BINDING_MISMATCH'):self.prepared(c=c)

    def test_candidate_revision_mismatch_rejected(self):
        c=replace(self.candidate,revision='f'*40)
        with self.assertRaisesRegex(ContractError,'DIR_CANDIDATE_BINDING_MISMATCH'):self.prepared(c=c)

    def test_artifact_identity_mismatch_rejected_even_with_digest_rebound(self):
        a=replace(self.candidate.artifacts[0],sha256='0'*64)
        c=replace(self.candidate,artifacts=(a,)+self.candidate.artifacts[1:])
        r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaisesRegex(ContractError,'DIR_CANDIDATE_ARTIFACT_MISMATCH'):self.prepared(r,c=c)

    def test_extra_source_candidate_is_not_silently_ignored(self):
        a=artifact(self.root,'sources/other.txt',b'Uninspected source.','extra-source','source')
        c=replace(self.candidate,artifacts=self.candidate.artifacts+(a,))
        r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaisesRegex(ContractError,'DIR_CANDIDATE_SOURCE_COVERAGE'):self.prepared(r,c=c)

    def test_report_identity_collision_rejected(self):
        a=artifact(self.root,'outputs/collision.txt',b'collision','qa16-director-quality-report')
        c=replace(self.candidate,artifacts=self.candidate.artifacts+(a,))
        r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
        with self.assertRaisesRegex(ContractError,'DIR_REPORT_COLLISION'):self.prepared(r,c=c)

    def test_release_policy_type_rejected(self):
        with self.assertRaisesRegex(ContractError,'DIR_RELEASE_POLICY_TYPE'):self.prepared(release_policy={})

    def test_source_and_output_actual_bytes_are_only_inspected_inventory(self):
        out=self.prepared()
        self.assertEqual(set(out.envelope.inspected_artifact_ids),{'dir-source','dir-script'})
        self.assertNotIn('fixture-video',out.envelope.inspected_artifact_ids)
        self.assertNotIn('fixture-game',out.envelope.inspected_artifact_ids)

    def test_evidence_expiry_is_bounded_by_director_policy(self):
        p=replace(self.policy,max_receipt_age_seconds=120)
        out=self.prepared(p=p)
        self.assertEqual(out.envelope.expires_at,NOW+120)
