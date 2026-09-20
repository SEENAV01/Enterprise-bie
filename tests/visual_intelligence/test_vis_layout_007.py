import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"app"))
from bie.visual_intelligence.layout_contracts import *
from bie.visual_intelligence.subtitle_safe_layout import *
def n(i,b,tags=()): return LayoutNode(i,"primary",b,("s",),tags=tags)
def p(ns): return make_layout_plan(evidence_refs=["s"],reasoning_refs=["r"],nodes=ns)
class T(unittest.TestCase):
 def test_zone(self): self.assertGreater(SubtitleZone().box.y,.7)
 def test_bad(self):
  with self.assertRaises(SubtitleSafeError): SubtitleZone(.6,.1)
 def test_conflict(self): self.assertEqual(subtitle_conflicts(p([n("a",Box(.1,.8,.3,.15))]),SubtitleZone()),("a",))
 def test_tag(self): self.assertEqual(subtitle_conflicts(p([n("a",Box(.1,.8,.3,.15),("subtitle",))]),SubtitleZone()),())
 def test_relocate(self):
  z=SubtitleZone(); q=enforce_subtitle_safe(p([n("a",Box(.1,.8,.3,.15))]),z); self.assertFalse(q.nodes[0].box.overlaps(z.box))
 def test_warning(self): self.assertTrue(enforce_subtitle_safe(p([n("a",Box(.1,.8,.3,.15))]),SubtitleZone()).warnings)
 def test_source(self): self.assertEqual(enforce_subtitle_safe(p([n("a",Box(.1,.8,.3,.15))]),SubtitleZone()).nodes[0].source_ids,("s",))
 def test_gap(self):
  with self.assertRaises(SubtitleSafeError): enforce_subtitle_safe(p([n("a",Box(.1,.8,.3,.15))]),SubtitleZone(),gap=.2)
if __name__=="__main__": unittest.main()
