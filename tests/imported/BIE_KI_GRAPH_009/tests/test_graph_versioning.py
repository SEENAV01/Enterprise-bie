import unittest
from bie.knowledge_intelligence.graph_versioning import *
class T(unittest.TestCase):
 def test_contract(self):
  g={"nodes":{"a":{}},"edges":[]};a=version(g);b=version(g)
  self.assertEqual(a["version_id"],b["version_id"])
  self.assertEqual(len(a["version_id"]),64)
  self.assertIsNone(a["parent_version"])
  with self.assertRaises(E):version(g,a["version_id"])
if __name__=='__main__':unittest.main()
