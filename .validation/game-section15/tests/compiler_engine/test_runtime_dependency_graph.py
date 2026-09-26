import unittest,json
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.fixtures import compiler_context
class RuntimeDependencyGraphTests(unittest.TestCase):
 def manifest(self):
  b=compile_game(compiler_context());a=next(x for x in b.artifacts if x.path=='runtime/manifest.json');return b,json.loads(a.content)
 def test_manifest_lists_14_pre_manifest_artifacts(self):
  b,m=self.manifest();self.assertEqual(len(m['artifacts']),14);self.assertEqual(len(b.artifacts),15)
 def test_dependency_graph_has_bootstrap_edges(self):
  _,m=self.manifest();edges={tuple(x) for x in m['dependency_edges']};self.assertIn(('runtime/index.html','runtime/bootstrap.js'),edges);self.assertIn(('runtime/bootstrap.js','runtime/rules.js'),edges);self.assertIn(('runtime/bootstrap.js','runtime/adaptation.js'),edges)
 def test_dependency_targets_are_resolvable(self):
  b,m=self.manifest();compiled={a.path for a in b.artifacts};expected=set(m['expected_build_outputs']);known=compiled|expected
  self.assertTrue(all(src in known and dst in known for src,dst in m['dependency_edges']))
 def test_dependency_graph_is_acyclic(self):
  _,m=self.manifest();g={}
  for a,b in m['dependency_edges']:g.setdefault(a,[]).append(b)
  visiting=set();done=set()
  def dfs(n):
   if n in visiting:raise AssertionError('cycle:'+n)
   if n in done:return
   visiting.add(n)
   for x in g.get(n,[]):dfs(x)
   visiting.remove(n);done.add(n)
  for n in list(g):dfs(n)
 def test_studio_quality_flags_are_all_strict(self):
  _,m=self.manifest();q=m['quality'];self.assertTrue(q['studio_grade']);self.assertTrue(q['semantic_visuals']);self.assertTrue(q['stateful_interaction']);self.assertTrue(q['pedagogical_motion']);self.assertTrue(q['accessibility']);self.assertFalse(q['slide_deck_default'])
 def test_security_flags_all_closed(self):
  _,m=self.manifest();self.assertFalse(any(m['security'].values()))
