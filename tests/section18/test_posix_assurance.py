"""Required supported-POSIX integration lane. Windows NOT_RUN, never skipped.

Execute directly only on supported POSIX. It uses exact canonical repair
fixtures/approvals and actual native worker/controller/journal, not made-up
receipts. All source/media/proof identities remain SYNTHETIC_TEST.
"""
from pathlib import Path
import sys,unittest,os
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(1,str(ROOT/'tests/qa_repair16'))
from test_batch002 import ViewBase
from repair_helpers import Fixture,ArtifactRef,NOW
from apps.operator.assurance import Assurance
from apps.operator.artifacts import ProductArtifacts
from bie.infrastructure.persistence import PersistedArtifactRecord

class NativePosixRepair(ViewBase):
    def setUp(self):
        super().setUp();self.f=Fixture('runTest');self.f.setUp();self.journal=None
        with self.service.native(self.body) as native:
            source=ProductArtifacts(self.service).canonical_api({r:native.persistence.load_artifact(r) for r in native.persistence.artifacts_for_run(self.body['native_job_id'])},native).content(self.ref)
            ref=self.f.write(self.ref,'sources/book.pdf',source,'source')
            self.f.snapshot=replace(self.f.snapshot,run_id=self.body['native_job_id'],artifacts=(ref,)+self.f.snapshot.artifacts[1:])
            for a in self.f.snapshot.artifacts[1:]:
                blob=native.cas.put_bytes((self.f.root/a.path).read_bytes());native.persistence.register_artifact(PersistedArtifactRecord(a.artifact_id,
                    'fixture.'+a.role,'sha256',blob.digest,blob.size,self.body['native_job_id'],'QA',False,{'evidence_origin':'SYNTHETIC_TEST'},[self.ref]))
        self.f.make_batch();self.plan=self.f.plan();self.journal=self.f.journal();self.a=Assurance(self.service)
    def tearDown(self):
        if self.journal:self.journal.close()
        self.f.tearDown();super().tearDown()
    def bind(self,receipts):return self.a.bind_repairs(self.p,self.run,self.journal,self.plan,tuple(receipts),evidence_origin='SYNTHETIC_TEST')
    def test_actual_native_worker_controller_and_verified_journal(self):
        r=self.f.run_proposal(journal=self.journal);self.assertTrue(r['worker_executed']);self.assertEqual(r['status'],'STAGED_FOR_REVIEW')
        v=self.bind((r,))['view'];self.assertEqual(v['attempts'][0]['status'],'STAGED_FOR_REVIEW');self.assertFalse(v['product_accepted'])
        self.assertEqual((self.f.root/'generated/lesson.txt').read_bytes(),b'2+4')
    def test_failed_parent_then_successful_attempt_retained(self):
        r1=self.f.run_proposal(self.f.proposal(b'2+8'),journal=self.journal)
        r2=self.f.run_proposal(self.f.proposal(b'2+3',pid='second'),journal=self.journal)
        v=self.bind((r1,r2))['view'];self.assertEqual([r['status'] for r in v['attempts']],['REJECTED','STAGED_FOR_REVIEW'])
        self.assertEqual([r['attempt'] for r in v['attempts']],[1,2])
    def test_pending_real_reservation_not_repaired(self):
        self.journal.reserve(self.f.proposal(),NOW);v=self.bind(())['view'];self.assertEqual(v['attempts'][0]['status'],'REVIEW_REQUIRED')

if __name__=='__main__':
    if os.name!='posix' or not hasattr(os,'O_NOFOLLOW'):raise SystemExit('NOT_RUN: supported native POSIX required; no Windows security fallback')
    unittest.main(verbosity=2)
