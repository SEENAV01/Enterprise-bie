import unittest
from bie.knowledge_intelligence.canonical_concepts import *
class T(unittest.TestCase):
 def test_contract(self):
  a=canonicalize(" Electric   Field ");b=canonicalize("electric field")
  self.assertEqual(a["concept_id"],b["concept_id"])
  self.assertEqual(a["canonical_label"],"Electric Field")
  self.assertEqual(len(a["concept_id"]),18)
  with self.assertRaises(E):canonicalize(" ")
if __name__=='__main__':unittest.main()
