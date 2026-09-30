import unittest,tempfile,sys,hashlib,time,os
from pathlib import Path
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.process import *
class H2002(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.cwd=Path(self.t.name)
 def run_child(self,code,**kw):return capture([sys.executable,'-c',code],self.cwd,Deadline(kw.pop('seconds',3)),**kw)
 def test_stdout_exact_hash(self):
  data,r=self.run_child('import sys;sys.stdout.buffer.write(b"abc")');self.assertEqual(data,b'abc');self.assertEqual(r['stdout_sha256'],hashlib.sha256(data).hexdigest())
 def test_stdout_budget(self):
  with self.assertRaises(BenchmarkError):self.run_child('print("x"*200)',limit=10)
 def test_stderr_not_silently_accepted(self):
  with self.assertRaises(BenchmarkError):self.run_child('import sys;sys.stderr.write("warning")')
 def test_nonzero_exit(self):
  with self.assertRaises(BenchmarkError):self.run_child('raise SystemExit(2)')
 def test_deadline_terminates_hang(self):
  start=time.monotonic()
  with self.assertRaises(BenchmarkError) as e:self.run_child('import time;time.sleep(20)',seconds=.12)
  self.assertEqual(e.exception.code,'AV_DEADLINE');self.assertLess(time.monotonic()-start,4)
 def test_group_descendant_with_open_pipe(self):
  with self.assertRaises(BenchmarkError):self.run_child('import subprocess,time,sys;subprocess.Popen([sys.executable,"-c","import time;time.sleep(20)"]);time.sleep(20)',seconds=.15)
 def test_callback_error_aborts(self):
  def consume(b):raise BenchmarkError('CALLBACK_REJECTED')
  with self.assertRaises(BenchmarkError):stream([sys.executable,'-c','print("x")'],self.cwd,Deadline(2),consume,max_stdout=10)
 def test_relative_executable_blocked(self):
  with self.assertRaises(BenchmarkError):capture(['python','-V'],self.cwd,Deadline(1))
 def test_argv_no_shell_substitution(self):
  data,r=self.run_child('import sys;print("$HOME; touch evil")');self.assertIn(b'$HOME',data);self.assertFalse((self.cwd/'evil').exists())
 def test_stderr_flood_budget(self):
  with self.assertRaises(BenchmarkError) as e:stream([sys.executable,'-c','import sys;sys.stderr.write("x"*5000)'],self.cwd,Deadline(2),lambda b:None,max_stdout=10,max_stderr=20)
  self.assertEqual(e.exception.code,'AV_STDERR_LIMIT')
 def test_invalid_deadline(self):
  with self.assertRaises(BenchmarkError):Deadline(float('inf'))
 def test_missing_tool(self):
  with self.assertRaises(BenchmarkError):executable('bie_missing_tool_32')
 def test_framer_chunk_and_final_line(self):
  rows=[];p=Lines(rows.append);p.feed(b'abc');p.feed(b'\ndef');p.finish();self.assertEqual(rows,['abc','def'])
 def test_framer_long_line(self):
  with self.assertRaises(BenchmarkError):Lines(lambda x:None,max_line=3).feed(b'abcd')
 def test_framer_unicode_boundary(self):
  rows=[];p=Lines(rows.append);b='नमस्ते\n'.encode();p.feed(b[:2]);p.feed(b[2:]);p.finish();self.assertEqual(rows,['नमस्ते'])
 def test_environment_secrets_not_inherited(self):
  os.environ['BIE_TEST_SECRET']='secret'
  try:data,r=self.run_child('import os;print(os.environ.get("BIE_TEST_SECRET","ABSENT"))')
  finally:os.environ.pop('BIE_TEST_SECRET')
  self.assertEqual(data.strip(),b'ABSENT')
 def test_invalid_output_limit(self):
  with self.assertRaises(BenchmarkError):stream([sys.executable,'-c','pass'],self.cwd,Deadline(2),lambda b:None,max_stdout=-1)
 def test_invalid_line_framer_limit(self):
  with self.assertRaises(BenchmarkError):Lines(lambda b:None,max_line=0)
