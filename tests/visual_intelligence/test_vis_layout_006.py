import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.safe_area import *
def n(i,b,req=True): return LayoutNode(i,"primary",b,("s",),required=req)
def p(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_box(self): self.assertAlmostEqual(SafeArea().box.x,.04)
 def test_invalid(self):
  with self.assertRaises(SafeAreaError): SafeArea(.5,.1,.1,.1)
 def test_detect(self): self.assertEqual(outside_safe_area(p([n("a",Box(0,0,.2,.2))]),SafeArea()),("a",))
 def test_move(self): self.assertGreaterEqual(enforce_safe_area(p([n("a",Box(0,0,.2,.2))]),SafeArea()).nodes[0].box.x,.04)
 def test_warning(self): self.assertTrue(enforce_safe_area(p([n("a",Box(0,0,.2,.2))]),SafeArea()).warnings)
 def test_no_shrink(self):
  with self.assertRaises(SafeAreaError): enforce_safe_area(p([n("a",Box(0,0,.2,.2))]),SafeArea(),shrink=False)
 def test_inside(self):
  q=p([n("a",Box(.1,.1,.2,.2))]); self.assertEqual(enforce_safe_area(q,SafeArea()).nodes[0].box,q.nodes[0].box)
 def test_huge(self): self.assertTrue(SafeArea().box.contains(enforce_safe_area(p([n("a",Box(0,0,1,1),False)]),SafeArea()).nodes[0].box))
if __name__=="__main__": unittest.main()
