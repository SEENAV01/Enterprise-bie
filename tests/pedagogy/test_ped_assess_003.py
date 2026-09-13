import unittest
from bie.pedagogy.transfer_questions import make_transfer_question
class T(unittest.TestCase):
 def test_novel(self): self.assertEqual(make_transfer_question('c','lab','space','apply',['e']).novel_context,'space')
 def test_same(self):
  with self.assertRaises(ValueError): make_transfer_question('c','lab','lab','apply',['e'])
