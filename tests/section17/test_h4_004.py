import unittest
from h4_support import receipt
class H4004(unittest.TestCase):
 def setUp(self):self.rows={x['step_id']:x for x in receipt()['observed']['runs'][0]['steps']}
 def test_step_sequence_executed(self):self.assertEqual(len(self.rows),7)
 def test_first_tab_observed(self):self.assertTrue(self.rows['keyboard-wrong']['observations']['#wrong']['focused'])
 def test_enter_wrong_feedback(self):self.assertTrue(self.rows['wrong-answer']['observations']['#feedback']['text'].startswith('Try again.'))
 def test_wrong_gets_no_credit(self):self.assertEqual(self.rows['wrong-answer']['observations']['#progress']['text'],'Solved: 0/1')
 def test_second_tab_observed(self):self.assertTrue(self.rows['keyboard-right']['observations']['#right']['focused'])
 def test_enter_correct_feedback(self):self.assertEqual(self.rows['right-answer']['observations']['#feedback']['text'],'Correct. 1/2 = 2/4.')
 def test_correct_progress(self):self.assertEqual(self.rows['right-answer']['observations']['#progress']['text'],'Solved: 1/1')
 def test_fill_actual_input(self):self.assertEqual(self.rows['fill-note']['observations']['#note']['value'],'Equivalent')
 def test_local_document_reset(self):self.assertEqual(self.rows['reset']['observations']['#progress']['text'],'Solved: 0/1')
 def test_url_reload_not_misrepresented(self):self.assertFalse(receipt()['observed']['transport']['url_reload_verified'])
