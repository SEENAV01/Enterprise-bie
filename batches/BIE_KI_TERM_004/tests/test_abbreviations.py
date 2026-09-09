import unittest
from knowledge_intelligence.abbreviations import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(register("DNA","deoxyribonucleic acid","p")["short"],"DNA")
  self.assertEqual(register("SI","International System of Units","p","chapter")["scope"],"chapter")
  with self.assertRaises(E):register("","x","p")
  with self.assertRaises(E):register("DNA","dna","p")
if __name__=='__main__':unittest.main()
