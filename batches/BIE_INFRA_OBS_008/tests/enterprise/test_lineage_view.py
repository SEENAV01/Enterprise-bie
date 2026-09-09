
import unittest
from enterprise.lineage_view import *
class T(unittest.TestCase):
 def test_nodes(self): self.assertEqual(len(build_lineage_view([{"artifact_id":"a"}])["nodes"]),1)
 def test_edge(self): self.assertEqual(build_lineage_view([{"artifact_id":"a"},{"artifact_id":"b","parent_refs":["a"]}])["edges"][0]["to"],"b")
 def test_missing(self):
  with self.assertRaises(LineageViewError): build_lineage_view([{"artifact_id":"b","parent_refs":["x"]}])
 def test_sorted(self): self.assertEqual([x["artifact_id"] for x in build_lineage_view([{"artifact_id":"b"},{"artifact_id":"a"}])["nodes"]],["a","b"])
if __name__=="__main__": unittest.main()
