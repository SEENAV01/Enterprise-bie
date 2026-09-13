import unittest
from bie.pedagogy.adaptive_depth import choose_depth
class T(unittest.TestCase):
 def test_bridge(self): self.assertEqual(choose_depth(.3,"APPLY",.8),"BRIDGE")
 def test_deep(self): self.assertEqual(choose_depth(.9,"ANALYZE",.9),"DEEP")
