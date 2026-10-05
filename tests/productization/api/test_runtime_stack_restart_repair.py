"""R2 option policy, real collisions, strict evidence and safe child diagnostics.

Linux TIME_WAIT execution is mandatory in the separate --require-repair CI lane;
portable contract tests never substitute a fabricated native receipt for it.
"""
from contextlib import redirect_stdout
import inspect
import io
import json
import os
from pathlib import Path
import queue
import socket
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripts import run_bie_local_stack as stack
from scripts import smoke_bie_local_stack as smoke
import probe_posix_port_restart as probe


class RestartRepairTests(unittest.TestCase):
    def option_calls(self, platform):
        owned = Mock()
        context = Mock()
        context.__enter__ = Mock(return_value=owned)
        context.__exit__ = Mock(return_value=False)
        module = SimpleNamespace(socket=Mock(return_value=context), AF_INET=socket.AF_INET,
                                 AF_INET6=socket.AF_INET6, SOCK_STREAM=socket.SOCK_STREAM,
                                 SOL_SOCKET=socket.SOL_SOCKET, SO_REUSEADDR=socket.SO_REUSEADDR,
                                 SO_EXCLUSIVEADDRUSE=-5)
        with patch.object(stack, "os", SimpleNamespace(name=platform)), patch.object(stack, "socket", module):
            stack.assert_port_available(stack.StackConfig(port=8765))
        return owned.method_calls, module

    def repaired_evidence(self):
        return {
            "active_listener_plain_bind_rejected": True, "genuine_connection_accepted": True,
            "payload_exchange_verified": True, "close_order_verified": True, "listener_closed": True,
            "no_active_listener_observed": True, "connection_refused_after_close": True,
            "time_wait_condition_observed": True, "active_listener_reuseaddr_bind_rejected": True,
            "closed_listener_plain_bind": "EADDRINUSE", "closed_listener_reuseaddr_bind": "SUCCESS",
            "current_production_preflight": "SUCCESS", "active_listener_production_preflight_rejected": True,
        }

    def dead_smoke_process(self, lines):
        value = smoke.StackProcess.__new__(smoke.StackProcess)
        value.lines = lines
        value.messages = queue.Queue()
        value.process = Mock()
        value.process.poll.return_value = 1
        value.readers = [Mock()]
        return value

    def test_windows_exclusive_option_precedes_bind_without_reuse(self):
        calls, module = self.option_calls("nt")
        self.assertEqual([(call[0], call.args) for call in calls], [
            ("setsockopt", (module.SOL_SOCKET, module.SO_EXCLUSIVEADDRUSE, 1)),
            ("bind", (('127.0.0.1', 8765),)),
        ])

    def test_posix_reuseaddr_option_precedes_bind(self):
        calls, module = self.option_calls("posix")
        self.assertEqual([(call[0], call.args) for call in calls], [
            ("setsockopt", (module.SOL_SOCKET, module.SO_REUSEADDR, 1)),
            ("bind", (('127.0.0.1', 8765),)),
        ])

    def test_preflight_forbids_reuseport_retry_sleep_and_error_suppression(self):
        import ast
        tree = ast.parse(inspect.getsource(stack.assert_port_available))
        self.assertFalse(any(isinstance(node, (ast.For, ast.While, ast.Try)) for node in ast.walk(tree)))
        self.assertNotIn("SO_REUSEPORT", inspect.getsource(stack.assert_port_available))
        self.assertFalse(any(isinstance(node, ast.Attribute) and node.attr == "sleep" for node in ast.walk(tree)))

    def test_real_active_listener_rejects_actual_production_preflight(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            option = socket.SO_EXCLUSIVEADDRUSE if os.name == "nt" else socket.SO_REUSEADDR
            listener.setsockopt(socket.SOL_SOCKET, option, 1)
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            with self.assertRaises(OSError):
                stack.assert_port_available(stack.StackConfig(port=listener.getsockname()[1]))

    def test_legacy_condition_and_repaired_production_are_distinct(self):
        result = self.repaired_evidence()
        self.assertTrue(probe.legacy_condition_reproduced(result))
        self.assertTrue(probe.repair_verified(result))
        self.assertFalse(probe.reproduced(result))
        broken = {**result, "current_production_preflight": "EADDRINUSE"}
        self.assertTrue(probe.reproduced(broken))
        self.assertFalse(probe.repair_verified(broken))

    def test_repair_verification_requires_every_native_condition(self):
        baseline = self.repaired_evidence()
        for key, value in baseline.items():
            for invalid in (None, False, "UNKNOWN"):
                with self.subTest(key=key, invalid=invalid):
                    self.assertFalse(probe.repair_verified({**baseline, key: invalid}))

    def test_required_repair_cli_rejects_completed_unverified_diagnostic(self):
        result = {"diagnostic_completed": True, "production_repair_verified": False}
        with tempfile.TemporaryDirectory() as directory, patch.object(probe, "run_probe", return_value=result), redirect_stdout(io.StringIO()):
            self.assertEqual(probe.main(["--require-repair", "--output", str(Path(directory)/"result.json")]), 1)

    def test_required_repair_cli_accepts_verified_result_and_writes_identical_json(self):
        result = {"diagnostic_completed": True, "production_repair_verified": True}
        with tempfile.TemporaryDirectory() as directory, patch.object(probe, "run_probe", return_value=result), redirect_stdout(io.StringIO()) as output:
            target = Path(directory)/"result.json"
            self.assertEqual(probe.main(["--require-repair", "--output", str(target)]), 0)
            self.assertEqual(json.loads(target.read_text()), json.loads(output.getvalue()))
            self.assertNotIn(directory, output.getvalue())

    def test_child_stop_reason_allowlist_discards_unknown_values_and_details(self):
        for reason, code in smoke.STACK_STOP_CODES.items():
            self.assertEqual(smoke.safe_stack_stop_code({"event":"stack_stopped", "reason":reason, "detail":"SECRET PATH"}), code)
        for value in (None, [], {"event":"other", "reason":"api_exited"},
                      {"event":"stack_stopped", "reason":"SECRET PATH"},
                      {"event":"stack_stopped", "reason":[]}):
            self.assertEqual(smoke.safe_stack_stop_code(value), "stack_exited_before_readiness")

    def test_dead_child_retains_safe_stop_reason(self):
        value = self.dead_smoke_process([b'{"event":"stack_stopped","reason":"startup_failed","detail":"SECRET PATH"}\n'])
        with self.assertRaisesRegex(smoke.SmokeCheck, '^stack_startup_failed$'):
            value.ready()
        value.readers[0].join.assert_called_once_with(timeout=1.0)

    def test_exit_before_reader_publishes_receipt_waits_for_reader_without_sleep(self):
        value = self.dead_smoke_process([])
        release, waiting = threading.Event(), threading.Event()
        def publish():
            waiting.set()
            if release.wait(5):
                value.lines.append(b'{"event":"stack_stopped","reason":"api_exited"}\n')
        reader = threading.Thread(target=publish)
        value.readers = [reader]
        reader.start()
        self.assertTrue(waiting.wait(5))
        value.process.poll.side_effect = lambda: (release.set(), 1)[1]
        try:
            with patch.object(smoke.time, "sleep", side_effect=AssertionError("no scheduling sleep")):
                with self.assertRaisesRegex(smoke.SmokeCheck, '^stack_api_exited$'):
                    value.ready()
        finally:
            release.set()
            reader.join(5)
        self.assertFalse(reader.is_alive())

    def test_missing_or_malformed_child_receipt_uses_generic_safe_code(self):
        value = self.dead_smoke_process([b"SECRET PATH malformed", b'[]', b'{"event":"stack_stopped","reason":"SECRET PATH"}'])
        with self.assertRaisesRegex(smoke.SmokeCheck, '^stack_exited_before_readiness$'):
            value.ready()

    def test_stop_message_before_exit_poll_changes_is_still_fail_closed(self):
        value = self.dead_smoke_process([])
        value.process.poll.return_value = None
        value.messages.put(b'{"event":"stack_stopped","reason":"readiness_timeout"}')
        with self.assertRaisesRegex(smoke.SmokeCheck, '^stack_readiness_timeout$'):
            value.ready()

    def test_real_owned_stack_reports_active_port_startup_failure_safely(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            option = socket.SO_EXCLUSIVEADDRUSE if os.name == "nt" else socket.SO_REUSEADDR
            listener.setsockopt(socket.SOL_SOCKET, option, 1)
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            child = smoke.StackProcess(Path(directory), listener.getsockname()[1])
            try:
                with self.assertRaisesRegex(smoke.SmokeCheck, '^stack_startup_failed$'):
                    child.ready()
            finally:
                with self.assertRaisesRegex(smoke.SmokeCheck, '^unclean_stack_shutdown$'):
                    child.stop()  # Owned startup failed: preserve its nonzero exit.
            self.assertIsNotNone(child.process.poll())
            self.assertNotIn(directory.encode(), b"".join(child.lines + child.errors))
            self.assertFalse(child.errors)


if __name__ == "__main__":
    unittest.main()
