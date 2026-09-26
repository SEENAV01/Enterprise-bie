import unittest
from bie.game_engine.state_engine.fixtures import sample_level,sample_snapshot
from bie.game_engine.mechanics_engine.state_bridge import StateBinding,propose_patch
class StateBridgeTests(unittest.TestCase):
 def test_parameter_outcome_projects_typed_patch_without_applying(self):
  level=sample_level();snap=sample_snapshot();p=propose_patch(level.state,snap,'mechanic:parameter',{'value':snap.as_dict()['x']},{'value':2.0},(StateBinding('value','x'),));self.assertEqual(p.deltas[0].variable_id,'x');self.assertEqual(p.deltas[0].after,2.0);self.assertFalse(p.authoritative_applied)
 def test_stale_local_state_rejected(self):
  level=sample_level();snap=sample_snapshot()
  with self.assertRaises(Exception):propose_patch(level.state,snap,'mechanic:parameter',{'value':99},{'value':2},(StateBinding('value','x'),))
 def test_range_violation_rejected_by_state_engine_schema(self):
  level=sample_level();snap=sample_snapshot()
  with self.assertRaises(Exception):propose_patch(level.state,snap,'mechanic:parameter',{'value':snap.as_dict()['x']},{'value':999},(StateBinding('value','x'),))
 def test_readonly_binding_rejected_on_change(self):
  level=sample_level();snap=sample_snapshot()
  with self.assertRaises(Exception):propose_patch(level.state,snap,'mechanic:parameter',{'value':snap.as_dict()['x']},{'value':2},(StateBinding('value','x',False),))
 def test_noop_rejected(self):
  level=sample_level();snap=sample_snapshot();x=snap.as_dict()['x']
  with self.assertRaises(Exception):propose_patch(level.state,snap,'mechanic:parameter',{'value':x},{'value':x},(StateBinding('value','x'),))
