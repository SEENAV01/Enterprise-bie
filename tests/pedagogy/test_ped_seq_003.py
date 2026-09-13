import unittest
from bie.pedagogy.prerequisite_aware_ordering import prerequisite_order
class T(unittest.TestCase):
 def test_strong(self): self.assertEqual(prerequisite_order(["a","b"],[("b","a",.9)]),("b","a"))
