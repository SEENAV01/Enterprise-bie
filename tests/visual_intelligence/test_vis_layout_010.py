import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.layout_fallback import *
def n(i,x,p=50,req=True): return LayoutNode(i,"primary",Box(x,.1,.25,.2),("s",),priority=p,required=req)
def plan(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_preserve(self):
  q,r=fallback_layout(plan([n("a",0,req=True),n("b",.5,req=False)]),reason="solver_failed",allow_optional_omission=True)
  self.assertEqual(r.preserved_required_ids,("a",)); self.assertEqual(r.omitted_optional_ids,("b",))
 def test_default_keeps(self): self.assertEqual(len(fallback_layout(plan([n("a",0),n("b",.5,req=False)]),reason="x")[0].nodes),2)
 def test_no_overlap(self):
  q,r=fallback_layout(plan([n("a",0),n("b",.5)]),reason="x"); self.assertFalse(q.nodes[0].box.overlaps(q.nodes[1].box))
 def test_priority(self): self.assertEqual(fallback_layout(plan([n("low",0,10),n("high",.5,90)]),reason="x")[0].nodes[0].node_id,"high")
 def test_reason(self):
  with self.assertRaises(LayoutFallbackError): fallback_layout(plan([n("a",0)]),reason=" ")
 def test_warning(self): self.assertIn("layout-fallback:solver_failed",fallback_layout(plan([n("a",0)]),reason="solver_failed")[0].warnings)
 def test_review(self):
  q,r=fallback_layout(plan([n("a",0)]),reason="x"); self.assertTrue(r.review_required); self.assertFalse(q.accepted)
 def test_source(self): self.assertEqual(fallback_layout(plan([n("a",0)]),reason="x")[0].nodes[0].source_ids,("s",))
 def test_deterministic(self):
  p=plan([n("a",0),n("b",.5)]); self.assertEqual(fallback_layout(p,reason="x")[0].fingerprint,fallback_layout(p,reason="x")[0].fingerprint)
if __name__=="__main__": unittest.main()
