import unittest,sqlite3
from bie.game_engine.operations_engine.telemetry import GovernedTelemetrySink
from bie.game_engine.operations_engine.contracts import TelemetryConsent
from bie.game_engine.operations_engine.errors import GameOperationsError
class TelemetryTests(unittest.TestCase):
 def setUp(self):self.db=sqlite3.connect(':memory:');self.s=GovernedTelemetrySink(self.db);self.c=TelemetryConsent(True,'policy:telemetry:v1',7)
 def tearDown(self):self.db.close()
 def event(self):return {'event':'mechanic_completed','game_id':'game:1','level_id':'level:1','challenge_id':'challenge:1','attempt_number':1,'outcome_code':'applied','mechanic_id':'drag','objective_id':'obj:1','adaptation_id':'adapt:1'}
 def test_sequence_monotonic(self):
  a=self.s.record('session:1',self.event(),self.c,('mechanic_completed',));b=self.s.record('session:1',self.event(),self.c,('mechanic_completed',));self.assertEqual((a['sequence_id'],b['sequence_id']),(1,2))
 def test_export_order(self):
  self.s.record('session:1',self.event(),self.c,('mechanic_completed',));self.s.record('session:1',self.event(),self.c,('mechanic_completed',));self.assertEqual([x['sequence_id'] for x in self.s.export('session:1')],[1,2])
 def test_consent_disabled_no_record(self):self.assertIsNone(self.s.record('session:1',self.event(),TelemetryConsent(False,'policy:telemetry:v1'),('mechanic_completed',)));self.assertEqual(self.s.export('session:1'),())
 def test_unallowlisted_event_fails(self):self.assertRaises(GameOperationsError,self.s.record,'session:1',self.event(),self.c,('game_started',))
 def test_raw_text_field_fails(self):e=self.event();e['raw_text']='secret';self.assertRaises(GameOperationsError,self.s.record,'session:1',e,self.c,('mechanic_completed',))
 def test_unknown_field_fails(self):e=self.event();e['gps']='x';self.assertRaises(GameOperationsError,self.s.record,'session:1',e,self.c,('mechanic_completed',))
 def test_event_id_stable_shape(self):self.assertTrue(self.s.record('session:1',self.event(),self.c,('mechanic_completed',))['event_id'].startswith('telemetry:'))
