import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.semantic_layout_constraints import *

def node(i,x,y,w=.2,h=.2,role="primary"):
    return LayoutNode(i, role, Box(x,y,w,h), ("s",), priority=50)

class T(unittest.TestCase):
    def plan(self,*nodes):
        return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=nodes)
    def test_fingerprint_deterministic(self):
        p=self.plan(node("a",0,0)); self.assertEqual(p.fingerprint,p.fingerprint)
    def test_unbound_source(self):
        with self.assertRaises(LayoutEvidenceError):
            make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=[LayoutNode("a","x",Box(0,0,.2,.2),("z",))])
    def test_parent_cycle(self):
        a=LayoutNode("a","x",Box(0,0,.5,.5),("s",),parent_id="b")
        b=LayoutNode("b","x",Box(0,0,.5,.5),("s",),parent_id="a")
        with self.assertRaises(LayoutValidationError): self.plan(a,b)
    def test_non_overlap_violation(self):
        p=self.plan(node("a",0,0),node("b",.1,.1))
        v=evaluate_constraints(p,[{"id":"c","kind":"non_overlap","nodes":["a","b"]}]); self.assertEqual(len(v),1)
    def test_non_overlap_pass(self):
        p=self.plan(node("a",0,0),node("b",.5,.5))
        self.assertEqual(evaluate_constraints(p,[{"id":"c","kind":"non_overlap","nodes":["a","b"]}]),())
    def test_contains(self):
        p=self.plan(node("a",0,0,.8,.8),node("b",.1,.1,.2,.2))
        self.assertEqual(evaluate_constraints(p,[{"id":"c","kind":"contains","nodes":["a","b"]}]),())
    def test_left_of(self):
        p=self.plan(node("a",0,0),node("b",.5,0))
        self.assertEqual(evaluate_constraints(p,[{"id":"c","kind":"left_of","nodes":["a","b"],"value":.05}]),())
    def test_align_left_violation(self):
        p=self.plan(node("a",0,0),node("b",.1,.4))
        self.assertTrue(evaluate_constraints(p,[{"id":"c","kind":"align_left","nodes":["a","b"]}]))
    def test_min_width(self):
        p=self.plan(node("a",0,0,.1,.2))
        self.assertTrue(evaluate_constraints(p,[{"id":"c","kind":"min_width","nodes":["a"],"value":.2}]))
    def test_bad_kind(self):
        p=self.plan(node("a",0,0))
        with self.assertRaises(ConstraintError): evaluate_constraints(p,[{"id":"c","kind":"magic","nodes":["a"]}])
    def test_unknown_node(self):
        p=self.plan(node("a",0,0))
        with self.assertRaises(ConstraintError): evaluate_constraints(p,[{"id":"c","kind":"min_width","nodes":["x"],"value":.2}])
    def test_box_outside_rejected(self):
        with self.assertRaises(LayoutGeometryError): Box(.9,.9,.2,.2)

if __name__=="__main__": unittest.main()
