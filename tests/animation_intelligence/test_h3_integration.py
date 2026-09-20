import unittest
from bie.animation_intelligence.domain_animation_registry import *
from bie.animation_intelligence.chemistry_animation_grammar import *
from bie.animation_intelligence.economics_animation_grammar import *
from bie.animation_intelligence.data_animation_grammar import *
from bie.animation_intelligence.ani_qa_repair_contract import *

class T(unittest.TestCase):
 def test_registry_cross_domain(self):
  r=DomainAnimationRegistry()
  r.register(DomainAdapter("chem","chemistry","1",("reaction",),10))
  r.register(DomainAdapter("econ","economics","1",("curve_shift",),10))
  r.register(DomainAdapter("data","data","1",("series_transition",),10))
  self.assertEqual(
   (r.resolve("chemistry","reaction").adapter_id,
    r.resolve("economics","curve_shift").adapter_id,
    r.resolve("data","series_transition").adapter_id),
   ("chem","econ","data")
  )
 def test_domain_truth_boundaries(self):
  h=Species("h","H2",1,("s",),("r",))
  o=Species("o","O2",1,("s",),("r",))
  self.assertEqual(plan_reaction("r",[h,o],[h]).status,"BLOCKED")
  c=Curve("d","demand",((1,2),(2,1)),("s",),("r",))
  self.assertEqual(plan_curve_shift("e",c,c,driver="income").status,"PASS")
  ds=DataSeries("x",((0,1),(1,2)),("s",))
  self.assertEqual(plan_series_transition("d",ds,ds).status,"PASS")
 def test_repair_mapping(self):
  x=make_repair_instruction("r","qa",("t",),"DOMAIN","repair_domain_semantics","domain_violation",("s",),"domain QA passes")
  self.assertEqual(x.owner_stage,"DOMAIN")
