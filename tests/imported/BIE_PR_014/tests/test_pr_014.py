import unittest
from bie.prerequisite_intelligence.external import *
class T(unittest.TestCase):
 def test_external(self): self.assertTrue(classify_external({"algebra"},{"vectors"})[0].external)
 def test_internal(self): self.assertFalse(classify_external({"vectors"},{"vectors"})[0].external)
 def test_alias(self): self.assertFalse(classify_external({"vec"},{"vectors"},{"vec":"vectors"})[0].external)
 def test_sorted(self): self.assertEqual([x.id for x in classify_external({"b","a"},set())],["a","b"])
if __name__=="__main__": unittest.main()
