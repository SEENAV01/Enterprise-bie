import unittest
from bie.visual_intelligence.grammar_layout_projection import *
from bie.visual_intelligence.constraint_solver_hardened import *
from bie.visual_intelligence.typography_metrics import *
from bie.visual_intelligence.narration_sync import *
from bie.visual_intelligence.continuity_ledger import *
class T(unittest.TestCase):
 def test_h2_spine(self):
  p=project_grammar_to_layout([GrammarElement("a","label",("e",),payload={"preferred_box":(.1,.1,.2,.1)}),GrammarElement("b","diagram",("e",),payload={"preferred_box":(.4,.1,.3,.3)})],
      [GrammarRelation("r","left_of","a","b",("e",),{"value":.05})])
  nodes=[Node(x.node_id,Box(*(x.preferred_box or (.1,.1,.2,.2)))) for x in p.nodes]
  cs=[Constraint(c.constraint_id,c.kind,c.node_ids,c.value,c.hard) for c in p.constraints]
  s=solve(nodes,cs);self.assertTrue(s.solved)
  self.assertFalse(measure(TypographyRequest("Force",18,120,40,mode="label")).overflow)
  sync=bind_visuals([Cue("c","intent",0,500,3,"visual")],{"intent":["b"]},3);self.assertEqual(sync.bindings[0].visual_id,"b")
  l=ContinuityLedger();l.observe("scene1",VisualIdentity("force","red","arrow","F","xy","vector","physics"),("e",));self.assertEqual(l.token_for("force").symbol_token,"arrow")
