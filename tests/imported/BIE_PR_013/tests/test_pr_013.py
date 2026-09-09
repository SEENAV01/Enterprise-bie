import unittest
from bie.prerequisite_intelligence.missing import *
class T(unittest.TestCase):
 def test_missing(self): self.assertEqual(find_missing_prerequisites({"b"},{"b":{"a"}})[0].prerequisite,"a")
 def test_present(self): self.assertEqual(find_missing_prerequisites({"a","b"},{"b":{"a"}}),[])
 def test_multiuse(self): self.assertEqual(find_missing_prerequisites(set(),{"b":{"a"},"c":{"a"}})[0].required_by,("b","c"))
 def test_strength(self): self.assertEqual(find_missing_prerequisites(set(),{"b":{"a"}},{("a","b"):.9})[0].severity,.9)
if __name__=="__main__": unittest.main()
