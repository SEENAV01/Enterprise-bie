import unittest,sys,tempfile
from bie.game_engine.build_runtime_engine.process import run_bounded
from bie.game_engine.build_runtime_engine.errors import GameBuildError
class Bounds(unittest.TestCase):
 def test_timeout_fails_closed(self):
  with self.assertRaisesRegex(GameBuildError,'PROCESS_TIMEOUT'):run_bounded([sys.executable,'-c','import time;time.sleep(2)'],timeout=1)
 def test_output_limit_fails_closed(self):
  with self.assertRaisesRegex(GameBuildError,'OUTPUT_LIMIT'):run_bounded([sys.executable,'-c','print("x"*10000)'],max_output=100)
 def test_nonzero_return_preserved(self):self.assertEqual(run_bounded([sys.executable,'-c','raise SystemExit(7)']).returncode,7)
