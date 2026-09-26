import unittest,tempfile,json
from pathlib import Path
from tests.hardening_h5.support import context_assets
from bie.game_engine.operations_engine.durable_store import DurableGameStore
from bie.game_engine.operations_engine.errors import GameOperationsError
class DurableStoreTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.ctx,_=context_assets();self.s=DurableGameStore(Path(self.t.name))
 def tearDown(self):self.s.close();self.t.cleanup()
 def test_source_envelope_cas(self):e=self.s.source_envelope('00000000-0000-4000-8000-000000000001',self.ctx.document.fingerprint(),self.ctx.document.provenance.refs);r=self.s.put_envelope(e,'source');self.assertTrue(self.s.cas.exists(self.s.catalog.get_record(r.artifact_id).blob))
 def test_artifact_index_survives_restart(self):
  e=self.s.source_envelope('00000000-0000-4000-8000-000000000001',self.ctx.document.fingerprint(),self.ctx.document.provenance.refs);r=self.s.put_envelope(e,'source');self.s.close();self.s=DurableGameStore(Path(self.t.name));self.assertEqual(self.s.catalog.get_record(r.artifact_id).artifact_id,r.artifact_id)
 def test_job_checkpoint_survives(self):self.s.begin_job('key:1','sha256:'+'1'*64,'00000000-0000-4000-8000-000000000001','session:1','owner:1');self.s.checkpoint('key:1','x','y');self.assertEqual(self.s.begin_job('key:1','sha256:'+'1'*64,'00000000-0000-4000-8000-000000000001','session:1','owner:1')['checkpoint']['x'],'y')
 def test_idempotency_conflict(self):self.s.begin_job('key:1','sha256:'+'1'*64,'00000000-0000-4000-8000-000000000001','session:1','owner:1');self.assertRaises(Exception,self.s.begin_job,'key:1','sha256:'+'2'*64,'00000000-0000-4000-8000-000000000001','session:1','owner:1')
 def test_foreign_owner_incomplete_fails(self):self.s.begin_job('key:1','sha256:'+'1'*64,'00000000-0000-4000-8000-000000000001','session:1','owner:1');self.assertRaises(GameOperationsError,self.s.begin_job,'key:1','sha256:'+'1'*64,'00000000-0000-4000-8000-000000000001','session:1','owner:2')
