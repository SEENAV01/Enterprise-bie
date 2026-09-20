import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from bie.compiler.build_common import BuildError
from bie.compiler.render_logs import RenderEventLog, redact_text, verify_render_log
from bie.compiler.render_process import run_bounded_process

class TestBuild009(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.path=self.root/'events.jsonl'
    def tearDown(self):self.tmp.cleanup()
    def log(self):
        with RenderEventLog(self.path,'run-1') as log:
            log.append('created','STARTED');log.append('terminal','PASS',{'accepted':False})
    def test_valid_log_chain(self):self.log();self.assertTrue(verify_render_log(self.path))
    def test_modified_log_detected(self):
        self.log();self.path.write_text(self.path.read_text().replace('"PASS"','"FAIL"'));self.assertFalse(verify_render_log(self.path))
    def test_truncated_log_detected(self):
        self.log();self.path.write_text(self.path.read_text().splitlines()[0]+'\n');self.assertFalse(verify_render_log(self.path))
    def test_duplicate_log_record_detected(self):
        self.log();self.path.write_text(self.path.read_text()*2);self.assertFalse(verify_render_log(self.path))
    def test_cannot_append_after_terminal(self):
        with RenderEventLog(self.path,'r') as log:
            log.append('terminal','FAIL')
            with self.assertRaises(BuildError):log.append('render','PASS')
    def test_log_cannot_overwrite(self):
        self.log()
        with self.assertRaises(FileExistsError):RenderEventLog(self.path,'r')
    def test_terminal_started_rejected(self):
        with RenderEventLog(self.path,'r') as log:
            with self.assertRaises(BuildError):log.append('terminal','STARTED')
    def test_literal_secret_redaction(self):self.assertNotIn('exact-secret',redact_text('x exact-secret y',('exact-secret',)))
    def test_common_secret_redaction(self):
        text=redact_text('Authorization: Bearer xyz123\napi_key=abc123 https://u:pass@example.org/?token=qwerty')
        for secret in ('xyz123','abc123','qwerty','u:pass'):self.assertNotIn(secret,text)
    def test_json_secret_redaction(self):
        with RenderEventLog(self.path,'r') as log:log.append('terminal','FAIL',{'api_key':'hide-this','nested':{'password':'hidden'}})
        self.assertNotIn('hide-this',self.path.read_text());self.assertNotIn('hidden',self.path.read_text())
    def test_embedded_newline_cannot_inject_event(self):
        with RenderEventLog(self.path,'r') as log:log.append('terminal','FAIL',{'message':'hello\n{"event":"terminal"}'})
        self.assertEqual(len(self.path.read_text().splitlines()),1);self.assertTrue(verify_render_log(self.path))
    def test_real_process_success(self):
        r=run_bounded_process((sys.executable,'-S','-c','print("actual subprocess")'),cwd=self.root,timeout_s=2)
        self.assertEqual(r.outcome,'SUCCEEDED');self.assertIn('actual subprocess',r.process.stdout)
    def test_real_nonzero_exit(self):
        r=run_bounded_process((sys.executable,'-S','-c','raise SystemExit(7)'),cwd=self.root,timeout_s=2)
        self.assertEqual(r.outcome,'FAILED');self.assertEqual(r.process.exit_code,7)
    def test_real_timeout(self):
        r=run_bounded_process((sys.executable,'-S','-c','import time;print("start",flush=True);time.sleep(30)'),cwd=self.root,timeout_s=.6)
        self.assertEqual(r.outcome,'TIMED_OUT');self.assertIn('start',r.process.stdout);self.assertLess(r.process.duration_ms,2500)
    def test_real_cancellation(self):
        event=threading.Event();timer=threading.Timer(.1,event.set);timer.start()
        try:r=run_bounded_process((sys.executable,'-S','-c','import time;time.sleep(30)'),cwd=self.root,timeout_s=3,cancel_event=event)
        finally:timer.join()
        self.assertEqual(r.outcome,'CANCELLED')
    def test_cancelled_process_not_spawned(self):
        event=threading.Event();event.set()
        r=run_bounded_process(('does-not-exist',),cwd=self.root,timeout_s=1,cancel_event=event)
        self.assertFalse(r.started);self.assertEqual(r.outcome,'CANCELLED')
    def test_missing_executable_is_receipt(self):
        r=run_bounded_process(('/does/not/exist',),cwd=self.root,timeout_s=1)
        self.assertEqual(r.outcome,'SPAWN_ERROR');self.assertFalse(r.started)
    def test_output_limit_kills_process(self):
        r=run_bounded_process((sys.executable,'-S','-c','import os;os.write(1,b"x"*1000000)'),cwd=self.root,timeout_s=2,max_output_bytes=1024)
        self.assertEqual(r.outcome,'OUTPUT_LIMIT');self.assertLessEqual(r.stdout_bytes+r.stderr_bytes,1024)
    def test_arguments_are_not_shell_code(self):
        r=run_bounded_process((sys.executable,'-S','-c','import sys;print(sys.argv[1])',';touch INJECTED'),cwd=self.root,timeout_s=2)
        self.assertTrue(r.process.passed);self.assertFalse((self.root/'INJECTED').exists())
    def test_environment_secrets_not_inherited(self):
        from unittest.mock import patch
        with patch.dict(os.environ,{'BIE_TEST_SECRET':'never-send-this','NODE_OPTIONS':'bad-node-option'}):
            r=run_bounded_process((sys.executable,'-S','-c','import os;print(os.environ.get("BIE_TEST_SECRET"),os.environ.get("NODE_OPTIONS"))'),cwd=self.root,timeout_s=2)
        self.assertEqual(r.process.stdout.strip(),'None None')
    def test_process_secret_redaction(self):
        r=run_bounded_process((sys.executable,'-S','-c','print("secret-value")'),cwd=self.root,timeout_s=2,secrets=('secret-value',))
        self.assertNotIn('secret-value',r.process.stdout);self.assertNotIn('secret-value',' '.join(r.process.command))
    def test_invalid_timeout_rejected(self):
        for timeout in (0,-1,True,float('nan')):
            with self.subTest(timeout=timeout),self.assertRaises(BuildError):run_bounded_process(('echo',),cwd=self.root,timeout_s=timeout)
