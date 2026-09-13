import unittest
from bie.pedagogy.lesson_boundary_detection import lesson_boundaries
class T(unittest.TestCase):
 def test_topic(self): self.assertEqual(lesson_boundaries([("a","x",1),("b","y",1)]),(("a",),("b",)))
