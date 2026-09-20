import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.layout_hierarchy import *

def mk(i,role,x,y,p=50,parent=None,box=None):
    return LayoutNode(i,role,box or Box(x,y,.2,.2),("s",),priority=p,parent_id=parent)
def plan(nodes): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=nodes)

class T(unittest.TestCase):
    def test_priority_rank(self):
        p=plan([mk("a","secondary",0,0,20),mk("b","primary",.4,0,90)])
        self.assertEqual(build_hierarchy(p)[0].node_id,"b")
    def test_depth(self):
        p=plan([mk("p","primary",0,0,50,box=Box(0,0,.8,.8)),mk("c","annotation",.1,.1,50,parent="p")])
        e={x.node_id:x for x in build_hierarchy(p)}; self.assertEqual(e["c"].depth,1)
    def test_reading_order(self):
        p=plan([mk("b","secondary",.4,.5),mk("a","secondary",0,.1)])
        self.assertEqual(reading_order(p),("a","b"))
    def test_containment_ok(self):
        p=plan([mk("p","primary",0,0,box=Box(0,0,.8,.8)),mk("c","annotation",.1,.1,parent="p")])
        self.assertEqual(validate_parent_containment(p),())
    def test_containment_bad(self):
        p=plan([mk("p","primary",0,0,box=Box(0,0,.3,.3)),mk("c","annotation",.5,.5,parent="p")])
        self.assertEqual(validate_parent_containment(p),("c",))
    def test_unknown_parent_rejected_by_contract(self):
        with self.assertRaises(LayoutValidationError): plan([mk("a","x",0,0,parent="x")])
    def test_deterministic(self):
        p=plan([mk("x","primary",0,0),mk("y","primary",.4,0)])
        self.assertEqual(build_hierarchy(p),build_hierarchy(p))
    def test_role_bonus_breaks_equal_priority(self):
        p=plan([mk("a","caption",0,0),mk("b","primary",.4,0)])
        self.assertEqual(build_hierarchy(p)[0].node_id,"b")

if __name__=="__main__": unittest.main()
