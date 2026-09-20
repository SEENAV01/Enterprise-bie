import unittest
from bie.scene_ir.five_pane_adapter import *
class T(unittest.TestCase):
 def doc(self):
  return {"format":"five-pane","scene_id":"s","duration_ms":1000,"source_refs":["src"],"reasoning_refs":["r"],
          "panes":{"title":{"content":"Topic"},"left":{"content":"A"},"center":{"content":"B"},"right":{"content":"C"},"footer":{"content":"Note"}}}
 def test_pass(self):
  d,e=adapt_five_pane(self.doc());self.assertEqual(len(d["elements"]),5);self.assertTrue(require_lossless_lineage(e))
 def test_boxes(self):self.assertTrue(all("normalized_box" in e for e in adapt_five_pane(self.doc())[0]["elements"]))
 def test_order(self):self.assertEqual([e["accessibility"]["reading_order"] for e in adapt_five_pane(self.doc())[0]["elements"]],list(range(5)))
 def test_unknown_pane(self):
  x=self.doc();x["panes"]["extra"]={"content":"x"}
  with self.assertRaises(DSLMigrationError):adapt_five_pane(x)
 def test_empty(self):
  x=self.doc();x["panes"]={}
  with self.assertRaises(DSLMigrationError):adapt_five_pane(x)
 def test_not_accepted(self):self.assertFalse(adapt_five_pane(self.doc())[1].accepted)
