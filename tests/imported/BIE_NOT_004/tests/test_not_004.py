import unittest
from bie.notation_intelligence.units import *
class T(unittest.TestCase):
 def test_units(self): self.assertEqual([x.raw for x in extract_units("5 kg and 2 m")],["kg","m"])
 def test_family(self): self.assertEqual(extract_units("10 N")[0].family,"force")
 def test_boundary(self): self.assertEqual(extract_units("mass"),[])
 def test_dedup(self): self.assertEqual(len(extract_units("1 m + 2 m")),1)
if __name__=="__main__": unittest.main()
