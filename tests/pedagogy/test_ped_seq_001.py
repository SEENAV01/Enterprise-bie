import unittest
from bie.pedagogy.lesson_sequencing import sequence_lessons
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(sequence_lessons(["b","a"],[("a","b")]),("a","b"))
