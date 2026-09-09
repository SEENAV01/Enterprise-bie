import unittest
from bie.knowledge_intelligence.table_claims import *
class T(unittest.TestCase):
 def test_contract(self):
  r=claim("t",1,2,"density",7.8,"p");self.assertEqual(r["cell"],(1,2))
  self.assertEqual(r["value"],7.8)
  with self.assertRaises(E):claim("t",-1,0,"x",1,"p")
  with self.assertRaises(E):claim("t",0,0,"x",None,"p")
