import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.spatial_grouping import *
def n(i,x,y,g=None,tags=()): return LayoutNode(i,"secondary",Box(x,y,.1,.1),("s",),group_id=g,tags=tags)
def p(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_explicit(self):
  g=group_nodes(p([n("a",0,0,"g"),n("b",.2,0,"g")]))[0]; self.assertTrue(g.explicit); self.assertEqual(g.node_ids,("a","b"))
 def test_near(self): self.assertEqual(len(group_nodes(p([n("a",0,0),n("b",.01,.01)]),proximity=.1)),1)
 def test_far(self): self.assertEqual(len(group_nodes(p([n("a",0,0),n("b",.8,.8)]),proximity=.05)),2)
 def test_tags(self): self.assertEqual(len(group_nodes(p([n("a",0,0,tags=("x",)),n("b",.15,0,tags=("x",))]),proximity=.1)),1)
 def test_bounds(self): self.assertGreater(group_nodes(p([n("a",0,0,"g"),n("b",.2,.2,"g")]))[0].bounds.width,.2)
 def test_bad(self):
  with self.assertRaises(GroupingError): group_nodes(p([n("a",0,0)]),proximity=.8)
 def test_deterministic(self):
  q=p([n("b",.8,.8),n("a",0,0)]); self.assertEqual(group_nodes(q),group_nodes(q))
 def test_single(self): self.assertEqual(group_nodes(p([n("a",0,0,"semantic")]))[0].node_ids,("a",))
if __name__=="__main__": unittest.main()
