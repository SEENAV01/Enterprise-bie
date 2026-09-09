import unittest
from knowledge_intelligence.property_scope import *
class T(unittest.TestCase):
 def test_contract(self):
  p={"concept_id":"c"};self.assertEqual(scope(p,"CHAPTER","ch1")["scope"]["id"],"ch1")
  self.assertEqual(scope(p,"BOOK","b")["scope"]["type"],"BOOK")
  with self.assertRaises(E):scope(p,"BAD","x")
  with self.assertRaises(E):scope(p,"SECTION","")
