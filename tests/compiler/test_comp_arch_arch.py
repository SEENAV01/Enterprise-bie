import unittest
from bie.compiler.compiler_architecture import *
class T(unittest.TestCase):
 def req(self):
  return CompilerRequest("r","s","a"*64,CompilerTargetProfile("web",1920,1080,30),"1.0.0",7)
 def test_plan(self):
  p=make_compiler_plan(self.req());self.assertEqual(len(p.stages),6);self.assertTrue(p.plan_id.startswith("comp-plan:"))
 def test_deterministic(self):self.assertEqual(make_compiler_plan(self.req()).plan_id,make_compiler_plan(self.req()).plan_id)
 def test_graph(self):self.assertTrue(validate_stage_graph(canonical_compiler_stages()))
 def test_bad_graph(self):
  with self.assertRaises(CompilerArchitectureError):validate_stage_graph((CompilerStage("b",("a",),"x"),))
 def test_target(self):
  with self.assertRaises(CompilerArchitectureError):CompilerTargetProfile("x",0,1080,30)
 def test_truth(self):
  p=make_compiler_plan(self.req());self.assertEqual((p.build_status,p.render_status),("NOT_RUN","NOT_RUN"));self.assertFalse(p.accepted)
