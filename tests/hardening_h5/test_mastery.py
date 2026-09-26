import unittest,sqlite3
from tests.hardening_h5.support import context_assets
from bie.game_engine.operations_engine.mastery import PersistentMasteryStore
class MasteryTests(unittest.TestCase):
 def setUp(self):self.db=sqlite3.connect(':memory:');self.s=PersistentMasteryStore(self.db);self.l='a'*64
 def tearDown(self):self.db.close()
 def test_success_updates(self):r=self.s.update(self.l,'obj:motion','applied',1,.9,'event:1');self.assertGreater(r.estimate,0);self.assertGreater(r.confidence,0);self.assertEqual(r.version,1)
 def test_second_update_versions(self):self.s.update(self.l,'obj:motion','applied',1,.9,'event:1');r=self.s.update(self.l,'obj:motion','applied',1,.9,'event:2');self.assertEqual((r.version,r.attempts),(2,2));self.assertGreater(r.estimate,.5)
 def test_failure_decreases_prior(self):self.s.update(self.l,'obj:motion','applied',1,1,'event:1');a=self.s.get(self.l,'obj:motion').estimate;r=self.s.update(self.l,'obj:motion','incorrect',1,1,'event:2');self.assertLess(r.estimate,a)
 def test_persistence_get(self):r=self.s.update(self.l,'obj:motion','applied',.8,.8,'event:1');self.assertEqual(self.s.get(self.l,'obj:motion'),r)
 def test_adaptation_remediate(self):r=self.s.update(self.l,'obj:motion','incorrect',1,1,'event:1');self.assertEqual(self.s.adaptation_for(r,.8,True),'remediate')
 def test_adaptation_advance_after_evidence(self):
  r=None
  for i in range(6):r=self.s.update(self.l,'obj:motion','applied',1,1,f'event:{i}')
  self.assertEqual(self.s.adaptation_for(r,.8,False),'advance')
 def test_future_director_signal(self):
  ctx,_=context_assets();self.s.update(self.l,'obj:motion','applied',1,.9,'event:1');sig=self.s.signals_for(ctx.document,self.l);self.assertEqual(sig[0].objective_id,'obj:motion');self.assertEqual(sig[0].attempts,1)
