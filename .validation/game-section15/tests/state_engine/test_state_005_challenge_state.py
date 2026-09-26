import unittest
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.challenge_state import *
from bie.game_engine.state_engine.fixtures import sample_snapshot
from bie.game_engine.state_engine.contracts import ChallengeStatus

class ChallengeStateTests(unittest.TestCase):
 def setUp(self):self.sid=sample_snapshot().snapshot_id
 def test_new_ready(self):self.assertEqual(new_progress('challenge:1',self.sid).status,ChallengeStatus.READY)
 def test_new_locked(self):self.assertEqual(new_progress('challenge:1',self.sid,False).status,ChallengeStatus.LOCKED)
 def test_start(self):self.assertEqual(start_challenge(new_progress('challenge:1',self.sid),self.sid).status,ChallengeStatus.ACTIVE)
 def test_locked_cannot_start(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_CHALLENGE_START_INVALID'):start_challenge(new_progress('challenge:1',self.sid,False),self.sid)
 def test_attempt_increments(self):
  p=start_challenge(new_progress('challenge:1',self.sid),self.sid);self.assertEqual(record_attempt(p,self.sid).attempts,1)
 def test_hint_increments(self):
  p=start_challenge(new_progress('challenge:1',self.sid),self.sid);self.assertEqual(use_hint(p).hints_used,1)
 def test_finish_success(self):
  p=start_challenge(new_progress('challenge:1',self.sid),self.sid);self.assertEqual(finish_challenge(p,True,self.sid).status,ChallengeStatus.SUCCEEDED)
 def test_finish_failure(self):
  p=start_challenge(new_progress('challenge:1',self.sid),self.sid);self.assertEqual(finish_challenge(p,False,self.sid).status,ChallengeStatus.FAILED)
 def test_terminal_attempt_rejected(self):
  p=finish_challenge(start_challenge(new_progress('challenge:1',self.sid),self.sid),True,self.sid)
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_CHALLENGE_ATTEMPT_INVALID'):record_attempt(p,self.sid)
 def test_history_fingerprint_changes(self):
  p=new_progress('challenge:1',self.sid);q=start_challenge(p,self.sid);self.assertNotEqual(p.history_fingerprint,q.history_fingerprint)
 def test_deterministic(self):self.assertEqual(new_progress('challenge:1',self.sid),new_progress('challenge:1',self.sid))
 def test_product_acceptance_false(self):self.assertFalse(new_progress('challenge:1',self.sid).product_accepted)
