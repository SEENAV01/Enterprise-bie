import unittest
from dataclasses import replace
from bie.director.simulation_narration_sync import *
from sync_fixtures import simulation_case


class SimulationSyncTests(unittest.TestCase):
    def test_original_demonstration_cycle_schedules_declared_states(self):
        c,v,s,rows=simulation_case(); p=sync_simulation_narration(c,v,[s],rows)
        self.assertFalse(p.issues)
        self.assertEqual([x.kind for x in p.cues],['SETUP','ACTION','OBSERVE','INTERPRET'])
        self.assertEqual(dict(p.cues[1].parameters)['declared_values'],(('position',2),))

    def test_action_before_setup_is_blocked(self):
        c,v,s,rows=simulation_case(); p=sync_simulation_narration(c,v,[s],rows[1:])
        self.assertIn('SIMULATION_STATE_PRECONDITION',{i.code for i in p.issues})

    def test_observation_requires_an_action_and_interpretation_requires_observation(self):
        c,v,s,rows=simulation_case()
        for selected,code in ((rows[:1]+rows[2:],'OBSERVATION_WITHOUT_ACTION'),(rows[:2]+rows[3:],'INTERPRETATION_WITHOUT_OBSERVATION')):
            p=sync_simulation_narration(c,v,[s],selected)
            self.assertIn(code,{i.code for i in p.issues})

    def test_incomplete_cycle_blocks(self):
        c,v,s,rows=simulation_case(); p=sync_simulation_narration(c,v,[s],rows[:2])
        self.assertIn('INCOMPLETE_SIMULATION_CYCLE',{i.code for i in p.issues})

    def test_seed_model_or_state_changes_invalidate_old_cues(self):
        c,v,s,rows=simulation_case()
        for changed in (replace(s,seed=7),replace(s,model_fingerprint='sha256:'+'b'*64),replace(s,revision='v2')):
            with self.assertRaises(ValueError): sync_simulation_narration(c,v,[changed],rows)

    def test_parameter_domains_and_missing_values_rejected(self):
        c,v,s,rows=simulation_case()
        for state in (replace(s.states[1],values=(ParameterValue('position',11),)),
                      replace(s.states[1],values=(ParameterValue('position',float('nan')),)),
                      replace(s.states[1],values=())):
            with self.assertRaises(ValueError): sync_simulation_narration(c,v,[replace(s,states=(s.states[0],state))],rows)

    def test_transition_change_set_and_destination_must_match(self):
        c,v,s,rows=simulation_case()
        bad=replace(s,transitions=(replace(s.transitions[0],changed_parameter_ids=()),))
        with self.assertRaises(ValueError): sync_simulation_narration(c,v,[bad],rows)
        with self.assertRaises(ValueError): sync_simulation_narration(c,v,[s],(rows[0],replace(rows[1],state_id='initial'))+rows[2:])

    def test_exact_demonstration_narration_and_evidence_required(self):
        c,v,s,rows=simulation_case()
        for step in (replace(rows[1].narration_step,narration='different'),replace(rows[1].narration_step,evidence_ids=('outside',))):
            with self.assertRaises(ValueError): sync_simulation_narration(c,v,[s],(rows[0],replace(rows[1],narration_step=step))+rows[2:])

    def test_transition_duration_cannot_be_squeezed_into_narration(self):
        c,v,s,rows=simulation_case(); s=replace(s,transitions=(replace(s.transitions[0],minimum_duration_ms=100000),))
        rows=tuple(replace(r,simulation_fingerprint=s.fingerprint()) for r in rows)
        p=sync_simulation_narration(c,v,[s],rows)
        self.assertIn('SIMULATION_ACTION_TOO_SHORT',{i.code for i in p.issues})

    def test_determinism_preserves_seed_but_does_not_claim_execution(self):
        c,v,s,rows=simulation_case()
        a=sync_simulation_narration(c,v,[s],rows); b=sync_simulation_narration(c,v,(x for x in [s]),reversed(rows))
        self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertEqual(dict(a.cues[1].parameters)['seed'],42)
        self.assertEqual(dict(a.cues[1].parameters)['execution_status'],'DECLARED_NOT_EXECUTED')
        self.assertFalse(a.accepted)
