import unittest
from knowledge_intelligence.concept_properties import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(make("charge","sign","+/-","p")["property"],"sign")
  self.assertEqual(make("mass","unit","kg","p")["value"],"kg")
  with self.assertRaises(E):make("c","",1,"p")
  with self.assertRaises(E):make("c","x",None,"p")
