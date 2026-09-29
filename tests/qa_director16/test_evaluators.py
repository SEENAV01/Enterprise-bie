from dir_helpers import *
from bie.qa.director_v2.evaluator import verify_reports

class Evaluators(FixtureCase):
    def test_healthy_declared_plan_with_synthetic_reviews(self):
        x = self.run_check(); self.assertEqual(x.status,'CHECKS_PASSED'); self.assertFalse(x.product_accepted)
        self.assertTrue(x.native_architecture_fingerprint.startswith('sha256:'))
    def test_unsigned_is_review_not_acceptance(self):
        x = evaluate(self.request,self.root,self.policy,as_of=NOW)
        self.assertEqual(x.status,'REVIEW_REQUIRED'); self.assertFalse(x.product_accepted)
    def test_four_original_task_ids(self):
        x = self.run_check()
        self.assertEqual([getattr(x,a).task_id for a in ('narrative','script','pacing','fidelity')],[f'BIE-QA-DIR-00{i}' for i in range(1,5)])
    def test_changed_file_blocks_all_checks(self):
        (self.root/'outputs/director-script.txt').write_text('tampered bytes')
        x = self.run_check()
        for a in ('narrative','script','pacing','fidelity'): self.assertEqual(getattr(x,a).status,'BLOCKED')
    def test_changed_source_blocks(self):
        (self.root/'sources/authored-director.txt').write_bytes(b'changed')
        self.assertEqual(self.run_check().status,'BLOCKED')
    def test_missing_source_blocks(self):
        (self.root/'sources/authored-director.txt').unlink(); self.assertEqual(self.run_check().status,'BLOCKED')
    def test_artifact_symlink_blocks(self):
        p=self.root/'outputs/director-script.txt'; data=p.read_bytes(); p.unlink()
        outside=self.root/'outside.txt';outside.write_bytes(data);p.symlink_to(outside)
        self.assertEqual(self.run_check().status,'BLOCKED')
    def test_empty_beats_cannot_pass(self):
        self.assertCode(self.run_check(replace(self.request,beats=())), 'narrative','DIR_EMPTY_BEATS','BLOCKED')
    def test_missing_scene(self):
        self.assertCode(self.run_check(replace(self.request,scenes=self.request.scenes[:1])), 'narrative','DIR_SCENE_SCOPE_MISMATCH')
    def test_missing_route(self):
        self.assertCode(self.run_check(replace(self.request,routes=())), 'narrative','DIR_ROUTE_SCOPE_MISMATCH')
    def test_unpresented_output_claim(self):
        r=replace(self.request,beats=tuple(b for b in self.request.beats if b.beat_id!='b-recap'))
        self.assertCode(self.run_check(r),'script','DIR_UNPRESENTED_CLAIMS')
    def test_wrong_output_channel(self):
        r=self.beat('b-example',channel='on_screen')
        self.assertCode(self.run_check(r),'script','DIR_CHANNEL_MISMATCH')
    def test_unknown_beat_scene(self):
        self.assertCode(self.run_check(self.beat('b-example',scene_id='absent')),'script','DIR_BEAT_REFERENCE_MISSING')
    def test_unknown_beat_claim(self):
        self.assertCode(self.run_check(self.beat('b-example',claim_ids=('absent',))),'script','DIR_BEAT_REFERENCE_MISSING')
    def test_wrong_audience(self):
        self.assertCode(self.run_check(replace(self.request,audience_id='expert')),'script','DIR_LEARNER_SCOPE_MISMATCH')
    def test_wrong_language(self):
        self.assertCode(self.run_check(replace(self.request,language='hi')),'script','DIR_LEARNER_SCOPE_MISMATCH')
    def test_wrong_lesson(self):
        self.assertCode(self.run_check(replace(self.request,lesson_id='other-lesson')),'script','DIR_LEARNER_SCOPE_MISMATCH')
    def test_deterministic_reports(self):
        self.assertEqual(self.run_check().content_digest,self.run_check().content_digest)
    def test_review_order_not_nondeterminism(self):
        reviews=tuple(reversed(signed_reviews(self.request,self.policy)))
        self.assertEqual(self.run_check().content_digest,self.run_check(reviews=reviews).content_digest)
    def test_report_edit_rejected(self):
        x=self.run_check();bad=replace(x,native_script_fingerprint='forged')
        with self.assertRaisesRegex(ContractError,'DIR_STALE_OR_EDITED_REPORT'):
            verify_reports(bad,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy))
    def test_report_recomputation(self):
        x=self.run_check()
        self.assertIs(verify_reports(x,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy)),x)
    def test_code_change_not_implied_by_native_flags(self):
        self.assertFalse(self.run_check().product_accepted)
        self.assertNotIn('PASS',[getattr(self.run_check(),a).status for a in ('narrative','script','pacing','fidelity')])
