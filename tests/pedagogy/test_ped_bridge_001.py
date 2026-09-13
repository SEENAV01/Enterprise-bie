import unittest
from bie.pedagogy.remedial_bridge_planner import *
class T(unittest.TestCase):
 def test_material_gap(self): self.assertEqual(plan_remedial_bridge([MissingPrerequisite('a','A',.2,('e1',)),MissingPrerequisite('b','B',.8,('e2',))]).steps[0].concept_id,'b')
 def test_grounding(self):
  with self.assertRaises(ValueError): plan_remedial_bridge([MissingPrerequisite('a','A',.8,())])
 def test_deterministic(self):
  a=MissingPrerequisite('a','A',.8,('e1',)); b=MissingPrerequisite('b','B',.8,('e2',)); self.assertEqual(plan_remedial_bridge([b,a]).steps,plan_remedial_bridge([a,b]).steps)
