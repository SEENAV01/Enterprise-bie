import unittest
from bie.pedagogy.retrieval_questions import make_retrieval_question
class T(unittest.TestCase):
 def test_default(self): self.assertEqual(make_retrieval_question('c','What?','A',['e']).cue_level,'NONE')
 def test_bad(self):
  with self.assertRaises(ValueError): make_retrieval_question('c','p','a',['e'],cue_level='MAX')
