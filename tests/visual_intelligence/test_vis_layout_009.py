import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.layout_solver import *
from bie.visual_intelligence.safe_area import SafeArea
from bie.visual_intelligence.subtitle_safe_layout import SubtitleZone
def n(i,x,y,p=50): return LayoutNode(i,"primary",Box(x,y,.25,.15),("s",),priority=p)
def plan(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_collision(self): self.assertTrue(solve_layout(plan([n("a",.1,.1,90),n("b",.2,.1,10)]))[1].solved)
 def test_safe(self): self.assertGreaterEqual(solve_layout(plan([n("a",0,0)]),safe_area=SafeArea())[0].nodes[0].box.x,.04)
 def test_subtitle(self): self.assertTrue(solve_layout(plan([n("a",.1,.8)]),subtitle_zone=SubtitleZone())[1].solved)
 def test_constraint(self):
  q,r=solve_layout(plan([n("a",0,0)]),constraints=[{"id":"wide","kind":"min_width","nodes":["a"],"value":.5}],avoid_overlap=False)
  self.assertFalse(r.solved); self.assertEqual(r.remaining_constraint_ids,("wide",))
 def test_iterations(self): self.assertEqual(solve_layout(plan([n("a",.1,.1)]),safe_area=SafeArea(),subtitle_zone=SubtitleZone())[1].iterations,3)
 def test_fp(self):
  q,r=solve_layout(plan([n("a",.1,.1)])); self.assertEqual(r.fingerprint,q.fingerprint)
 def test_no_overlap_option(self): self.assertTrue(solve_layout(plan([n("a",0,0),n("b",.1,.1)]),avoid_overlap=False)[1].solved)
 def test_not_accepted(self):
  q,r=solve_layout(plan([n("a",.1,.1)])); self.assertTrue(q.review_required); self.assertFalse(q.accepted)
if __name__=="__main__": unittest.main()
