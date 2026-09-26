import unittest,tempfile,subprocess,shutil,pathlib
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.compiler_engine.fixtures import compiler_context
class TypeScriptCompileTests(unittest.TestCase):
 def test_emitted_typescript_typechecks(self):
  tsc=shutil.which('tsc');self.assertIsNotNone(tsc)
  b=compile_game(compiler_context());sources=[a for a in b.artifacts if a.media_type=='text/typescript']
  with tempfile.TemporaryDirectory(prefix='bie-game-comp-') as td:
   td=pathlib.Path(td)
   for a in sources:(td/pathlib.Path(a.path).name).write_text(a.content)
   p=subprocess.run([tsc,'--target','ES2020','--module','commonjs','--strict','--noEmit',*[x.name for x in td.glob('*.ts')]],cwd=td,text=True,capture_output=True,timeout=60)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
