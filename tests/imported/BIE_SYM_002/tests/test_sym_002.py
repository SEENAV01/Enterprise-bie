import unittest
from app.bie.math_intelligence.constants import *
class T(unittest.TestCase):
 def test_pi(self): self.assertEqual(resolve_constant("π").name,"pi")
 def test_c(self): self.assertEqual(resolve_constant("c","physics").value,299792458.0)
 def test_context(self): self.assertIsNone(resolve_constant("c","mathematics"))
 def test_unknown(self): self.assertIsNone(resolve_constant("k"))
if __name__=="__main__":unittest.main()
