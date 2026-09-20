import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.responsive_composition import *
def n(i,x,y,p=50): return LayoutNode(i,"primary",Box(x,y,.25,.2),("s",),priority=p)
def plan(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_viewport(self):
  with self.assertRaises(ResponsiveCompositionError): Viewport(100,100)
 def test_portrait(self):
  q=compose_responsive(plan([n("a",0,0),n("b",.5,0)]),Viewport(400,900)); self.assertIn("responsive:portrait_stack",q.warnings)
 def test_no_overlap(self):
  q=compose_responsive(plan([n("a",0,0),n("b",.5,0)]),Viewport(400,900)); self.assertFalse(q.nodes[0].box.overlaps(q.nodes[1].box))
 def test_ultrawide(self): self.assertIn("responsive:ultrawide_readable_band",compose_responsive(plan([n("a",0,0)]),Viewport(2400,800)).warnings)
 def test_normal(self):
  p=plan([n("a",.1,.1)]); self.assertEqual(compose_responsive(p,Viewport(1280,720)).nodes[0].box,p.nodes[0].box)
 def test_bad_gutter(self):
  with self.assertRaises(ResponsiveCompositionError): compose_responsive(plan([n("a",0,0)]),Viewport(400,900),gutter=.2)
 def test_priority(self):
  q=compose_responsive(plan([n("low",0,0,10),n("high",.5,0,90)]),Viewport(400,900)); self.assertEqual(q.nodes[0].node_id,"high")
 def test_sources(self): self.assertEqual(compose_responsive(plan([n("a",0,0)]),Viewport(400,900)).nodes[0].source_ids,("s",))
if __name__=="__main__": unittest.main()
