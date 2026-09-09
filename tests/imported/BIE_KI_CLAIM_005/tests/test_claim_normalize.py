import unittest
from knowledge_intelligence.claim_normalize import *
class T(unittest.TestCase):
 def test_contract(self):
  a=normalize(" Force  causes motion. ");b=normalize("force causes motion")
  self.assertEqual(a["claim_key"],b["claim_key"])
  self.assertEqual(a["text"],"Force causes motion.")
  self.assertTrue(a["claim_key"].startswith("cl_"))
  with self.assertRaises(E):normalize(" ")
if __name__=='__main__':unittest.main()
