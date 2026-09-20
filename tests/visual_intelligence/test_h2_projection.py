import unittest
from bie.visual_intelligence.grammar_layout_projection import *
class T(unittest.TestCase):
 def test_project(self):
  p=project_grammar_to_layout([GrammarElement("a","node",("e",)),GrammarElement("b","node",("e",),parent_id="a")],[]);self.assertEqual(len(p.nodes),2);self.assertEqual(p.constraints[0].kind,"contains")
 def test_relation(self):
  p=project_grammar_to_layout([GrammarElement("a","x",("e",)),GrammarElement("b","x",("e",))],[GrammarRelation("r","left_of","a","b",("e",),{"value":.1})]);self.assertEqual(p.constraints[0].kind,"left_of")
 def test_required_omit(self):
  with self.assertRaises(ProjectionError):project_grammar_to_layout([GrammarElement("a","x",("e",),True)],[],explicit_omissions={"a":"x"})
 def test_optional_omit(self):
  p=project_grammar_to_layout([GrammarElement("a","x",("e",),False)],[],explicit_omissions={"a":"not needed"});self.assertEqual(p.trace[0].disposition,"OMITTED")
 def test_bad_endpoint(self):
  with self.assertRaises(ProjectionError):project_grammar_to_layout([GrammarElement("a","x",("e",))],[GrammarRelation("r","left_of","a","b",("e",))])
 def test_source_preserved(self):self.assertEqual(project_grammar_to_layout([GrammarElement("a","x",("e1","e2"))],[]).nodes[0].source_ids,("e1","e2"))
 def test_deterministic(self):
  a=project_grammar_to_layout([GrammarElement("a","x",("e",))],[]);b=project_grammar_to_layout([GrammarElement("a","x",("e",))],[]);self.assertEqual(a.fingerprint,b.fingerprint)
