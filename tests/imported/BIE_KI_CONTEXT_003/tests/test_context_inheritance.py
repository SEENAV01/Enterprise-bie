import unittest
from bie.knowledge_intelligence.context_inheritance import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(resolve("x","y","z")["source"],"LOCAL")
  self.assertEqual(resolve(None,"y","z")["value"],"y")
  self.assertEqual(resolve(None,None,"z")["source"],"BOOK")
  with self.assertRaises(E):resolve(None,None,None)
