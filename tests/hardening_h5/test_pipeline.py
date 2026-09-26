import unittest,tempfile,sqlite3,json
from pathlib import Path
from tests.hardening_h5.support import *
from bie.game_engine.operations_engine.pipeline import run_enterprise_session,load_persisted_mastery_signals
from bie.game_engine.operations_engine.errors import GameOperationsError
class PipelineTests(unittest.TestCase):
 def test_end_to_end_durable_session(self):
  with tempfile.TemporaryDirectory() as td:
   c,a=context_assets();r=run_enterprise_session(c,a,Path(td),request(61));self.assertTrue(r.result_artifact_id.startswith('game.session.result:'));self.assertIsNotNone(r.telemetry_artifact_id);self.assertEqual(r.mastery[0].version,1)
 def test_idempotent_replay_no_double_learning(self):
  with tempfile.TemporaryDirectory() as td:
   c,a=context_assets();q=request(62);r1=run_enterprise_session(c,a,Path(td),q);r2=run_enterprise_session(c,a,Path(td),q);self.assertTrue(r2.idempotent_replay);self.assertEqual(r2.result_artifact_id,r1.result_artifact_id);self.assertEqual(r2.mastery[0].version,1)
 def test_crash_after_build_resumes(self):
  with tempfile.TemporaryDirectory() as td:
   c,a=context_assets();q=request(63)
   self.assertRaises(GameOperationsError,run_enterprise_session,c,a,Path(td),q,None,'build')
   r=run_enterprise_session(c,a,Path(td),q);self.assertTrue(r.resumed_from_checkpoint);self.assertEqual(r.mastery[0].version,1)
 def test_crash_after_learning_does_not_double_update(self):
  with tempfile.TemporaryDirectory() as td:
   c,a=context_assets();q=request(64)
   self.assertRaises(GameOperationsError,run_enterprise_session,c,a,Path(td),q,None,'learning')
   r=run_enterprise_session(c,a,Path(td),q);self.assertTrue(r.resumed_from_checkpoint);self.assertEqual(r.mastery[0].version,1)
 def test_consent_disabled_still_learns_without_telemetry(self):
  with tempfile.TemporaryDirectory() as td:
   c,a=context_assets();r=run_enterprise_session(c,a,Path(td),request(65,consent=False));self.assertIsNone(r.telemetry_artifact_id);self.assertEqual(r.mastery[0].version,1)
 def test_mastery_feeds_future_director_signal(self):
  with tempfile.TemporaryDirectory() as td:
   c,a=context_assets();q=request(66);run_enterprise_session(c,a,Path(td),q);sig=load_persisted_mastery_signals(Path(td),c.document,q.learner_key_hash);self.assertEqual(sig[0].objective_id,'obj:motion');self.assertGreater(sig[0].current_mastery,0)
