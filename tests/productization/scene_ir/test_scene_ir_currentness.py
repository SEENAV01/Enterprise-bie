"""Authorized reopen, exact ancestry and publication tamper controls in real stores."""
from contextlib import closing
from copy import deepcopy
from dataclasses import replace
import json
import sqlite3
import unittest

from .test_scene_ir_producer import PreparedSceneFixture, CHART
from bie.productization.contracts import ProducerError
from scripts.smoke_bie_director import excludes_private


class CommittedSceneFixture(PreparedSceneFixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        result = cls._prepared.step()
        cls._prepared.assertEqual(result['stages']['SCENE_IR'], 'SUCCEEDED', result.get('safe_diagnostics'))


class CurrentnessControls(CommittedSceneFixture):
    def receipt(self):
        with self.port.native(self.p, self.run, 'read') as service:
            return service.verified_scene_ir(self.run, self.p.tenant)[1]

    def change_db(self, statement, values=()):
        with self.port.native(self.p, self.run, 'read') as service:
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db: db.execute(statement, values)

    def rejected(self):
        with self.assertRaises(Exception):
            self.port.status(self.p, self.run)

    def tamper(self, stage):
        with self.port.native(self.p, self.run, 'read') as service:
            _, row = service.stage_ref(self.run, stage)
            service.cas._path(row.blob_digest).write_bytes(b'deliberate-test-only-corruption')
        self.rejected()

    def foreign(self, stage):
        with self.port.native(self.p, self.run, 'read') as service:
            ref, _ = service.stage_ref(self.run, stage)
        self.change_db("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (ref,))
        self.rejected()

    def forge_receipt(self, change):
        original = self.receipt()
        forged = deepcopy(original); change(forged)
        with self.port.native(self.p, self.run, 'worker') as service:
            attempt = service.persistence.load_run_state(self.run)['stages']['SCENE_IR']['attempts'][-1]
            old = service.record(self.run, attempt['evidence_refs'][0])
            aid = service.put(self.run, 'SCENE_IR', 'producer.evidence', forged, old.parent_artifact_ids, True)
            with closing(sqlite3.connect(service.persistence.path)) as db:
                with db:
                    db.execute("UPDATE attempts SET evidence_refs_json=? WHERE run_id=? AND stage_id='SCENE_IR' AND attempt=?",
                        (json.dumps([aid]), self.run, attempt['attempt']))
        self.rejected()

    def test_source_bytes_tamper_blocks_current_retrieval(self): self.tamper('SOURCE')
    def test_visual_bytes_tamper_blocks_current_retrieval(self): self.tamper('VISUAL')
    def test_animation_bytes_tamper_blocks_current_retrieval(self): self.tamper('ANIMATION')
    def test_director_bytes_tamper_blocks_current_retrieval(self): self.tamper('DIRECTOR')
    def test_scene_bytes_tamper_blocks_current_retrieval(self): self.tamper('SCENE_IR')
    def test_foreign_visual_run_rejected(self): self.foreign('VISUAL')
    def test_foreign_animation_run_rejected(self): self.foreign('ANIMATION')
    def test_foreign_director_run_rejected(self): self.foreign('DIRECTOR')

    def test_exact_extra_parent_rejected_not_hidden_by_digest(self):
        receipt = self.receipt()
        with self.port.native(self.p, self.run, 'read') as service:
            source, _ = service.stage_ref(self.run, 'SOURCE')
        self.change_db('INSERT INTO artifact_parents(artifact_id,parent_artifact_id) VALUES(?,?)',
            (receipt['output_artifact_id'], source))
        self.rejected()

    def test_missing_parent_rejected(self):
        receipt = self.receipt()
        self.change_db('DELETE FROM artifact_parents WHERE artifact_id=? AND parent_artifact_id=?',
            (receipt['output_artifact_id'], receipt['input_artifact_ids'][0]))
        self.rejected()

    def test_foreign_private_supporting_record_rejected(self):
        receipt = self.receipt()
        self.change_db("UPDATE artifact_records SET run_id='foreign' WHERE artifact_id=?", (receipt['validation_id'],))
        self.rejected()

    def test_recomputed_hash_supporting_payload_cannot_self_certify(self):
        receipt = self.receipt()
        with self.port.native(self.p, self.run, 'worker') as service:
            old = service.record(self.run, receipt['validation_id'])
            value = service.read(self.run, old.artifact_id)
            value['inventory']['source_item_count'] += 1
            aid = service.put(self.run, 'SCENE_IR', old.artifact_type, value, old.parent_artifact_ids)
        self.forge_receipt(lambda r: r.update(validation_id=aid))

    def test_current_director_stale_rejects_old_scene(self):
        with self.port.native(self.p, self.run, 'read') as service:
            with closing(sqlite3.connect(service.root / 'director-state.sqlite3')) as db:
                with db: db.execute("UPDATE director_revisions SET state='STALE' WHERE run_id=?", (self.run,))
        self.rejected()

    def test_uncommitted_predecessor_does_not_grant_retrieval(self):
        self.change_db("UPDATE attempts SET state='FAILED' WHERE run_id=? AND stage_id='ANIMATION'", (self.run,))
        self.rejected()

    def test_cross_tenant_access_rejected(self):
        import secrets
        foreign = replace(self.p, actor='foreign-reader', tenant='foreign')
        self.credentials.grant(secrets.token_urlsafe(40), foreign)
        with self.assertRaises(Exception):
            self.port.status(foreign, self.run)

    def test_revoked_access_rejected(self):
        self.credentials._grants.clear()
        self.rejected()

    def test_replay_token_tamper_rejected(self):
        self.forge_receipt(lambda r: r['replay'].update(replay_id='a'*64))

    def test_extra_replay_dependency_rejected(self):
        self.forge_receipt(lambda r: r['replay']['dependency_fingerprints'].append(['foreign', 'a'*64]))

    def test_missing_replay_dependency_rejected(self):
        self.forge_receipt(lambda r: r['replay']['dependency_fingerprints'].pop())

    def test_reordered_global_input_receipt_rejected(self):
        self.forge_receipt(lambda r: r['input_artifact_ids'].reverse())

    def test_valid_cas_receipt_cannot_accept_product(self):
        self.forge_receipt(lambda r: r.update(accepted=True, product_accepted=True))

    def test_valid_cas_receipt_cannot_drop_review(self):
        self.forge_receipt(lambda r: r.update(requires_review=False))

    def test_valid_cas_receipt_cannot_claim_release(self):
        self.forge_receipt(lambda r: r.update(release_ready=True))

    def test_valid_cas_receipt_cannot_claim_audio_complete(self):
        self.forge_receipt(lambda r: r.update(audio_complete=True, audio_reconciliation_open=False))

    def test_valid_cas_receipt_cannot_claim_video_code(self):
        self.forge_receipt(lambda r: r.update(video_code_executed=True))

    def test_fencing_epoch_boolean_rejected(self):
        self.forge_receipt(lambda r: r.update(fencing_epoch=True))

    def test_fencing_epoch_future_rejected(self):
        self.forge_receipt(lambda r: r.update(fencing_epoch=1000000))

    def test_receipt_cannot_export_private_text(self):
        self.forge_receipt(lambda r: r.update(private_source=CHART))

    def test_actual_status_and_evidence_are_bounded_and_source_free(self):
        result = self.port.status(self.p, self.run)
        self.assertTrue(excludes_private(result, (CHART, str(self.root))))
        self.assertTrue(excludes_private(self.receipt(), (CHART, str(self.root))))
        self.assertEqual(self.stack.calls, dict(generator=0, critic=0, annotator=0, reviewer=0))

    def test_identical_intent_replays_committed_scene(self):
        result = self.port.status(self.p, self.run)
        self.assertEqual(self.port.admit(self.p, self.source['source_id'], 'scene', producer_config=self.config), result)

    def test_changed_source_same_key_conflicts(self):
        from .test_scene_ir_producer import pdf, CELL
        source = self.operator.import_pdf(self.p, pdf((CELL,)))
        with self.assertRaises(Exception):
            self.port.admit(self.p, source['source_id'], 'scene', producer_config=self.config)


if __name__ == '__main__':
    unittest.main()
