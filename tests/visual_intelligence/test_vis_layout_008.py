import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.collision_avoidance import *
def n(i,x,y,p=50,req=True,g=None): return LayoutNode(i,"primary",Box(x,y,.25,.2),("s",),priority=p,required=req,group_id=g)
def plan(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_detect(self): self.assertEqual(len(detect_collisions(plan([n("a",0,0),n("b",.1,.1)]))),1)
 def test_none(self): self.assertEqual(detect_collisions(plan([n("a",0,0),n("b",.6,.6)])),())
 def test_ignore(self): self.assertEqual(detect_collisions(plan([n("a",0,0,g="g"),n("b",.1,.1,g="g")]),ignore_same_group=True),())
 def test_avoid(self): self.assertEqual(detect_collisions(avoid_collisions(plan([n("a",0,0,90),n("b",.1,.1,10)]))),())
 def test_priority_stays(self):
  p=plan([n("a",0,0,90),n("b",.1,.1,10)]); q=avoid_collisions(p); self.assertEqual(q.nodes[0].box,p.nodes[0].box)
 def test_warning(self): self.assertIn("collision-avoidance-applied",avoid_collisions(plan([n("a",0,0,90),n("b",.1,.1,10)])).warnings)
 def test_pinned(self):
  with self.assertRaises(CollisionError): avoid_collisions(plan([n("a",0,0,100),n("b",.1,.1,100)]))
 def test_iterations(self):
  with self.assertRaises(CollisionError): avoid_collisions(plan([n("a",0,0)]),max_iterations=0)
 def test_deterministic(self):
  p=plan([n("a",0,0,90),n("b",.1,.1,10)]); self.assertEqual(avoid_collisions(p).fingerprint,avoid_collisions(p).fingerprint)
if __name__=="__main__": unittest.main()
