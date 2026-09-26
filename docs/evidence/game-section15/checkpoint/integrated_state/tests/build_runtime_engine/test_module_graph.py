import unittest,tempfile
from pathlib import Path
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.workspace import build_workspace
from bie.game_engine.build_runtime_engine.module_graph import verify_module_graph
from bie.game_engine.build_runtime_engine.errors import GameBuildError
class ModuleGraph(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();c,a=build_inputs();self.w=build_workspace(c,a,Path(self.t.name));self.r=Path(self.t.name)/'dist/runtime'
 def tearDown(self):self.t.cleanup()
 def test_graph_closes(self):self.assertTrue(verify_module_graph(self.r)['passed'])
 def test_entry_to_bootstrap_edge(self):self.assertIn(('entry.js','bootstrap.js'),verify_module_graph(self.r)['edges'])
 def test_bootstrap_dependencies_present(self):
  edges=set(verify_module_graph(self.r)['edges']);self.assertIn(('bootstrap.js','react-runtime.js'),edges);self.assertIn(('bootstrap.js','state-machine.js'),edges)
 def test_dangling_import_rejected(self):
  p=self.r/'entry.js';p.write_text(p.read_text()+'\nimport {x} from "./missing.js";')
  with self.assertRaisesRegex(GameBuildError,'DANGLING_IMPORT'):verify_module_graph(self.r)
 def test_dynamic_import_rejected(self):
  p=self.r/'entry.js';p.write_text(p.read_text()+'\nimport("./bootstrap.js");')
  with self.assertRaisesRegex(GameBuildError,'DYNAMIC_IMPORT_FORBIDDEN'):verify_module_graph(self.r)
 def test_graph_fingerprint_deterministic(self):self.assertEqual(verify_module_graph(self.r)['graph_fingerprint'],verify_module_graph(self.r)['graph_fingerprint'])
