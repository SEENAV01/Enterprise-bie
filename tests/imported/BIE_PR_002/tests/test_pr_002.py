import unittest
from app.bie.prerequisite_intelligence.explicit_prerequisites import *
class T(unittest.TestCase):
 def test_requires(self):
  r=extract_explicit_prerequisites("Coulomb law","This topic requires vectors and electric charge.")
  self.assertEqual([x.prerequisite for x in r],["vectors","electric charge"])
 def test_depends(self): self.assertEqual(extract_explicit_prerequisites("x","It depends on algebra.")[0].prerequisite,"algebra")
 def test_dedup(self):
  r=extract_explicit_prerequisites("x","Requires algebra. Depends on algebra.")
  self.assertEqual(len(r),1)
 def test_invalid(self):
  with self.assertRaises(ValueError): extract_explicit_prerequisites("","Requires x.")
if __name__=="__main__": unittest.main()
