"""Task028 launcher ownership, readiness bounds, and failure cleanup."""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import run_bie_local_stack as stack


class Child:
    def __init__(self, stubborn=False):
        self.returncode = None
        self.stdin = None
        self.actions = []
        self.stubborn = stubborn
    def poll(self):
        return self.returncode
    def send_signal(self, sig):
        self.actions.append("signal")
        if not self.stubborn:
            self.returncode = 0
    def wait(self, timeout):
        self.actions.append("wait")
        if self.returncode is None:
            raise subprocess.TimeoutExpired("owned child", timeout)
        return self.returncode
    def terminate(self):
        self.actions.append("terminate")
    def kill(self):
        self.actions.append("kill")
        self.returncode = -9


class LocalStackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bie-task028-stack-")
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"BIE_DATA_ROOT": str(self.root)})
        self.env.start()
        self.stop = threading.Event()
    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()
    def run_owned(self, on_ready=None, readiness=None, failure_index=None):
        self.api, self.worker = Child(), Child()
        calls, reports = [], []
        def popen(command, **kwargs):
            calls.append((command, kwargs))
            if failure_index == len(calls):
                raise OSError("sensitive storage path")
            child = [self.api, self.worker][len(calls) - 1]
            if kwargs["stdin"] == subprocess.PIPE:
                child.stdin = io.BytesIO()
            return child
        def report(value):
            reports.append(value)
            if value["event"] == "stack_ready":
                if on_ready:
                    on_ready()
                else:
                    self.stop.set()
        with patch.object(stack, "assert_port_available"):
            code = stack.run_stack(stack.StackConfig(shutdown_grace=.1), self.stop,
                                   popen=popen, readiness=readiness or (lambda *_: None), report=report)
        return code, calls, reports

    def test_defaults_are_loopback_8000(self):
        self.assertEqual((stack.StackConfig().host, stack.StackConfig().port), ("127.0.0.1", 8000))
    def test_non_loopback_hosts_rejected(self):
        for host in ("0.0.0.0", "::", "192.0.2.1", "example.com", "localhost", "127.0.0.1@evil"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                stack.StackConfig(host=host)
    def test_ipv6_literal_loopback_allowed(self):
        self.assertEqual(stack.StackConfig(host="::1").host, "::1")
    def test_ports_bounded(self):
        for port in (0, -1, 65536, True, "8000"):
            with self.subTest(port=port), self.assertRaises(ValueError):
                stack.StackConfig(port=port)
        self.assertEqual(stack.StackConfig(port=65535).port, 65535)
    def test_process_timeouts_bounded(self):
        for value in (0, -1, 121, float("nan"), float("inf"), True):
            for key in ("readiness_timeout", "shutdown_grace"):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    stack.StackConfig(**{key: value})
    def test_api_command_uses_existing_runner(self):
        api, _ = stack.child_commands(stack.StackConfig(port=8765))
        self.assertEqual(api, [sys.executable, str(ROOT / "scripts/run_bie_api.py"), "--host", "127.0.0.1", "--port", "8765"])
    def test_worker_command_uses_serve(self):
        _, worker = stack.child_commands(stack.StackConfig())
        self.assertEqual(worker, [sys.executable, str(ROOT / "scripts/run_bie_pdf_worker.py"), "--serve", "--poll-interval", "1.0"])
    def test_children_share_one_canonical_root(self):
        code, calls, _ = self.run_owned()
        self.assertEqual(code, 0)
        self.assertEqual(calls[0][1]["env"]["BIE_DATA_ROOT"], str(self.root.resolve()))
        self.assertEqual(calls[0][1]["env"]["BIE_DATA_ROOT"], calls[1][1]["env"]["BIE_DATA_ROOT"])
    def test_no_operator_process_or_import(self):
        commands = stack.child_commands(stack.StackConfig())
        self.assertNotIn("operator", json.dumps(commands))
        import ast
        for name in ("scripts/run_bie_local_stack.py", "scripts/run_bie_pdf_worker.py", "apps/api/pdf_worker_service.py"):
            tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or "").startswith("apps.operator"))
                if isinstance(node, ast.Import):
                    self.assertFalse(any(n.name.startswith("apps.operator") for n in node.names))
    def test_api_failure_stops_worker(self):
        code, _, reports = self.run_owned(lambda: setattr(self.api, "returncode", 3))
        self.assertEqual(code, 1)
        self.assertIn("signal", self.worker.actions)
        self.assertEqual(reports[-1]["reason"], "api_exited")
    def test_worker_failure_stops_api(self):
        code, _, reports = self.run_owned(lambda: setattr(self.worker, "returncode", 0))
        self.assertEqual(code, 1)  # even unexpected clean child exit is fatal
        self.assertIn("signal", self.api.actions)
        self.assertEqual(reports[-1]["reason"], "worker_exited")
    def assert_real_child_failure_cleanup(self, index):
        # Inject failure only after genuine TCP API readiness and both canonical
        # child processes exist. No fake subprocess implements the cleanup.
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        children, reports = [], []
        def popen(*args, **kwargs):
            child = subprocess.Popen(*args, **kwargs)
            children.append(child)
            return child
        def report(value):
            reports.append(value)
            if value["event"] == "stack_ready":
                children[index].terminate()
                children[index].wait(timeout=5)
        try:
            code = stack.run_stack(stack.StackConfig(port=port, shutdown_grace=.5), self.stop,
                                   popen=popen, report=report)
            self.assertEqual(code, 1)
            self.assertEqual(len(children), 2)
            self.assertTrue(all(child.poll() is not None for child in children))
            self.assertTrue(reports[-1]["children_reaped"])
            self.assertEqual(reports[-1]["reason"], ["api_exited", "worker_exited"][index])
            with socket.socket() as probe:
                probe.settimeout(.5)
                self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)
                if child.stdin is not None and not child.stdin.closed:
                    child.stdin.close()
    def test_real_api_process_failure_reaps_worker(self):
        self.assert_real_child_failure_cleanup(0)
    def test_real_worker_process_failure_reaps_api(self):
        self.assert_real_child_failure_cleanup(1)
    def test_normal_shutdown_closes_pipe_and_reaps_both(self):
        code, _, reports = self.run_owned()
        self.assertEqual(code, 0)
        self.assertTrue(self.worker.stdin.closed)
        self.assertTrue(reports[-1]["children_reaped"])
        self.assertFalse(reports[-1]["forced_termination"])
        self.assertIn("wait", self.api.actions)
        self.assertIn("wait", self.worker.actions)
    def test_readiness_failure_cleans_api_before_worker_start(self):
        def fail(*args):
            raise stack.StackError("readiness_timeout")
        code, calls, reports = self.run_owned(readiness=fail)
        self.assertEqual(code, 1)
        self.assertEqual(len(calls), 1)
        self.assertTrue(reports[-1]["children_reaped"])
    def test_worker_spawn_exception_reaps_api_and_redacts_detail(self):
        code, _, reports = self.run_owned(failure_index=2)
        self.assertEqual(code, 1)
        self.assertIsNotNone(self.api.poll())
        self.assertNotIn("sensitive", json.dumps(reports))
    def test_api_spawn_failure_fails_closed(self):
        code, _, reports = self.run_owned(failure_index=1)
        self.assertEqual(code, 1)
        self.assertEqual(reports[-1]["reason"], "startup_failed")
    def test_readiness_deadline_is_finite(self):
        now = [0.0]
        stop = Mock()
        stop.is_set.return_value = False
        stop.wait.side_effect = lambda interval: now.__setitem__(0, now[0] + interval)
        probe = Mock(return_value=False)
        with self.assertRaisesRegex(stack.StackError, "readiness_timeout"):
            stack.wait_ready(Child(), stop, stack.StackConfig(readiness_timeout=.2), clock=lambda: now[0], probe=probe)
        self.assertLessEqual(probe.call_count, 3)
        self.assertTrue(all(0 < c.args[1] <= .2 for c in probe.call_args_list))
    def test_readiness_detects_dead_api(self):
        api = Child()
        api.returncode = 1
        probe = Mock()
        with self.assertRaisesRegex(stack.StackError, "api_exited"):
            stack.wait_ready(api, self.stop, stack.StackConfig(), probe=probe)
        probe.assert_not_called()
    def test_readiness_stop_is_immediate(self):
        self.stop.set()
        probe = Mock()
        with self.assertRaisesRegex(stack.StackError, "stop_requested"):
            stack.wait_ready(Child(), self.stop, stack.StackConfig(), probe=probe)
        probe.assert_not_called()
    def test_stubborn_children_escalate_only_after_wait_and_are_reaped(self):
        child = Child(stubborn=True)
        self.assertTrue(stack.shutdown([child], .1))
        self.assertEqual(child.actions, ["signal", "wait", "terminate", "wait", "kill", "wait"])
        self.assertIsNotNone(child.poll())
    def test_output_has_no_data_root_or_user_path(self):
        _, calls, reports = self.run_owned()
        output = json.dumps(reports)
        self.assertNotIn(str(self.root), output)
        self.assertNotIn("BIE_DATA_ROOT", output)
        self.assertTrue(all(k[1]["stdout"] == subprocess.DEVNULL and k[1]["stderr"] == subprocess.DEVNULL for k in calls))
    def test_preexisting_stop_never_spawns(self):
        self.stop.set()
        code, calls, _ = self.run_owned()
        self.assertEqual((code, calls), (0, []))
    def test_operator_root_rejected_before_spawn(self):
        (self.root / "operator.sqlite3").touch()
        code, calls, reports = self.run_owned()
        self.assertEqual((code, calls), (1, []))
        self.assertNotIn(str(self.root), json.dumps(reports))
    def test_existing_port_is_not_mistaken_for_owned_api(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen()
            with self.assertRaises(OSError):
                stack.assert_port_available(stack.StackConfig(port=sock.getsockname()[1]))
    def test_health_requires_exact_bounded_contract(self):
        for body in (b"x" * 4097, b"{}", b'{"status":"ok"}', b"not json"):
            response = Mock(status=200)
            response.read.return_value = body
            context = Mock()
            context.__enter__ = Mock(return_value=response)
            context.__exit__ = Mock(return_value=False)
            with patch.object(stack, "build_opener") as opener:
                opener.return_value.open.return_value = context
                self.assertFalse(stack.healthy(stack.StackConfig(), .1))
                response.read.assert_called_once_with(4097)


if __name__ == "__main__":
    unittest.main()
