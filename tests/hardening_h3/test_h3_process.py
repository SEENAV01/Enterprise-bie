import unittest,sys,os,json
from bie.game_engine.build_runtime_engine.process import run_bounded
from bie.game_engine.build_runtime_engine.errors import GameBuildError
class H3Process(unittest.TestCase):
 def test_ambient_secret_not_inherited(self):
  os.environ['BIE_SUPER_SECRET']='do-not-leak'
  r=run_bounded([sys.executable,'-c','import os;print(os.getenv("BIE_SUPER_SECRET","MISSING"))']);self.assertEqual(r.stdout.strip(),'MISSING')
 def test_no_new_privs_is_one(self):
  code='import re; s=open("/proc/self/status").read(); print(re.search(r"^NoNewPrivs:\\s*(\\d+)",s,re.M).group(1))'
  self.assertEqual(run_bounded([sys.executable,'-c',code]).stdout.strip(),'1')
 def test_cpu_limit_visible(self):
  r=run_bounded([sys.executable,'-c','import resource;print(resource.getrlimit(resource.RLIMIT_CPU)[0])'],cpu_seconds=7);self.assertEqual(r.stdout.strip(),'7')
 def test_memory_limit_visible(self):
  r=run_bounded([sys.executable,'-c','import resource;print(resource.getrlimit(resource.RLIMIT_AS)[0])'],memory_bytes=500_000_000);self.assertEqual(r.stdout.strip(),'500000000')
 def test_process_limit_visible(self):
  r=run_bounded([sys.executable,'-c','import resource;print(resource.getrlimit(resource.RLIMIT_NPROC)[0])'],max_processes=31);self.assertEqual(r.stdout.strip(),'31')
 def test_open_file_limit_visible(self):
  r=run_bounded([sys.executable,'-c','import resource;print(resource.getrlimit(resource.RLIMIT_NOFILE)[0])'],max_open_files=63);self.assertEqual(r.stdout.strip(),'63')
 def test_unknown_environment_key_rejected(self):
  with self.assertRaisesRegex(GameBuildError,'ENV_KEY_FORBIDDEN'):run_bounded([sys.executable,'-c','print(1)'],env={'AWS_SECRET_ACCESS_KEY':'x'})
