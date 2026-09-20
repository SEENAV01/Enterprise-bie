import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.focus_region import *

def node(i,role,x,p=50,req=True):
    return LayoutNode(i,role,Box(x,.2,.2,.2),("s",),priority=p,required=req)
def plan(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)

class T(unittest.TestCase):
    def test_high_priority_focus(self):
        d=choose_focus(plan([node("a","secondary",0,20),node("b","primary",.4,90)])); self.assertEqual(d.node_id,"b")
    def test_preferred_bonus(self):
        d=choose_focus(plan([node("a","secondary",0,20),node("b","primary",.4,90)]),preferred_ids=["a"]); self.assertEqual(d.node_id,"a")
    def test_unknown_preferred(self):
        with self.assertRaises(FocusRegionError): choose_focus(plan([node("a","primary",0)]),preferred_ids=["x"])
    def test_margin_bounds(self):
        d=choose_focus(plan([node("a","focus",0,90)]),margin=.05); self.assertGreaterEqual(d.region.width,.2)
    def test_bad_margin(self):
        with self.assertRaises(FocusRegionError): choose_focus(plan([node("a","focus",0)]),margin=.5)
    def test_optional_penalty(self):
        d=choose_focus(plan([node("a","primary",0,50,False),node("b","secondary",.4,50,True)])); self.assertEqual(d.node_id,"b")
    def test_conflicts(self):
        p=plan([node("a","focus",0,95),node("b","primary",.1,90)])
        d=choose_focus(p); self.assertEqual(focus_conflicts(p,d),("b",))
    def test_review_required(self):
        self.assertTrue(choose_focus(plan([node("a","focus",0)])).review_required)

if __name__=="__main__": unittest.main()
