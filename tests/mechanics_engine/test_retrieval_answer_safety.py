import unittest
from bie.game_engine.mechanics_engine import retrieval
from bie.game_engine.mechanics_engine.common import sample_context
class RetrievalSafety(unittest.TestCase):
 def test_answer_hidden_before_submission(self):
  pool=[{'id':'a','prompt_ref':'p:a','answer_ref':'a:a','evidence_ref':'s:a'}];_,out,_=retrieval.execute(sample_context(),{},pool,[],False);self.assertIsNone(out['answer_ref']);self.assertFalse(out['answer_revealed'])
 def test_answer_available_only_after_submission(self):
  pool=[{'id':'a','prompt_ref':'p:a','answer_ref':'a:a','evidence_ref':'s:a'}];_,out,_=retrieval.execute(sample_context(),{},pool,[],True);self.assertEqual(out['answer_ref'],'a:a');self.assertTrue(out['answer_revealed'])
