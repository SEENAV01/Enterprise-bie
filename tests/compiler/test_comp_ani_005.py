import unittest
from bie.compiler.graph_transition_compiler import *
class T(unittest.TestCase):
 def t(self,a=[[0,0],[1,1]],b=[[0,1],[1,0]]):return {"track_id":"gt","element_id":"g","action":"transform","start_ms":0,"end_ms":1000,"parameters":{"from_points":a,"to_points":b},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_interpolate(self):self.assertIn("const points = fromPoints.map",compile_graph_transition(self.t()).source_text)
 def test_path(self):self.assertIn("<path",compile_graph_transition(self.t()).source_text)
 def test_crossfade_fallback(self):
  r=compile_graph_transition(self.t([[0,0]],[[0,0],[1,1]]));self.assertTrue(r.warnings);self.assertIn("opacity={1-progress}",r.source_text)
 def test_missing(self):
  x=self.t();x["parameters"]["from_points"]=[]
  with self.assertRaises(AnimationCompilerError):compile_graph_transition(x)
 def test_action(self):
  x=self.t();x["action"]="reveal"
  with self.assertRaises(AnimationCompilerError):compile_graph_transition(x)
 def test_not_accepted(self):self.assertFalse(compile_graph_transition(self.t()).accepted)
