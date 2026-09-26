import unittest
from bie.game_engine.mechanics_engine.common import sample_context
from bie.game_engine.mechanics_engine.replay import verify_replay
from bie.game_engine.mechanics_engine.studio_policy import validate_studio_mechanic
from bie.game_engine.mechanics_engine.errors import MechanicError
ctx=sample_context
from bie.game_engine.mechanics_engine import graph_exploration
def valid():return graph_exploration.execute(ctx(),{}, {'A':['B'],'B':['C'],'C':[]},'A','C')
def invalids():return [(lambda:graph_exploration.execute(ctx(),{}, {},'A',None)),(lambda:graph_exploration.execute(ctx(),{}, {'A':[],'B':[]},'A','B'))]
from bie.game_engine.mechanics_engine import graph_exploration as MODULE

class MechanicTaskTests(unittest.TestCase):
    def test_definition_valid_and_studio_grade(self):
        d=MODULE.define(ctx());self.assertIs(validate_studio_mechanic(d),d);self.assertFalse(d.product_accepted);self.assertTrue(d.reset_supported)
    def test_execution_changes_state_and_receipt_is_bound(self):
        after,out,r=valid();self.assertTrue(r.state_changed);self.assertTrue(r.replay_verified);self.assertFalse(r.product_accepted);self.assertNotEqual(r.before_fingerprint,r.after_fingerprint);self.assertTrue(r.semantic_motion_ids)
    def test_deterministic_execution(self):
        a=valid();b=valid();self.assertEqual(a,b)
    def test_replay_verification(self):
        result=verify_replay(valid);self.assertTrue(result['verified']);self.assertFalse(result['product_accepted'])
    def test_missing_runtime_fails_closed(self):
        c=ctx();object.__setattr__(c,'runtime_capabilities',('keyboard_input',))
        with self.assertRaises(Exception):MODULE.define(c)
    def test_missing_provenance_fails_closed(self):
        c=ctx();object.__setattr__(c,'source_refs',())
        with self.assertRaises(Exception):MODULE.define(c)
    def test_task_specific_invalid_cases_fail_closed(self):
        for fn in invalids():
            with self.assertRaises(Exception):fn()
    def test_no_premature_answer_reveal_or_speed_pressure(self):
        d=MODULE.define(ctx());self.assertFalse(d.quality.answer_reveal_before_attempt);self.assertFalse(d.quality.speed_pressure_required)
    def test_accessibility_and_motion_are_explicit(self):
        d=MODULE.define(ctx());self.assertTrue(all(a.accessible_label for a in d.actions));self.assertTrue(d.motion)
    def test_definition_is_deterministic(self):self.assertEqual(MODULE.define(ctx()),MODULE.define(ctx()))
