import unittest
from bie.knowledge_intelligence.definition_consistency import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(compare([{"text":"force push pull"}])["consistent"])
  self.assertTrue(compare([{"text":"force push pull"},{"text":"force is push pull"}])["consistent"])
  self.assertFalse(compare([{"text":"force push"},{"text":"chemical atom"}])["consistent"])
  with self.assertRaises(E):compare([{"text":""},{"text":"x"}])
if __name__=='__main__':unittest.main()
