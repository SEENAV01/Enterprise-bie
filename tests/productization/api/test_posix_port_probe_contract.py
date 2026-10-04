"""Portable diagnostic-contract tests, NOT evidence of Linux reproduction."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_posix_port_restart as probe


class ProbeContractTests(unittest.TestCase):
    def positive(self):
        return {
            "active_listener_plain_bind_rejected": True,
            "genuine_connection_accepted": True, "payload_exchange_verified": True,
            "close_order_verified": True, "listener_closed": True,
            "no_active_listener_observed": True, "connection_refused_after_close": True,
            "time_wait_condition_observed": True,
            "active_listener_reuseaddr_bind_rejected": True,
            "closed_listener_plain_bind": "EADDRINUSE",
            "current_production_preflight": "EADDRINUSE",
            "closed_listener_reuseaddr_bind": "SUCCESS",
        }

    def test_parser_selects_exact_time_wait_tuple(self):
        snapshot = "header\n0: 0100007F:1234 0100007F:5678 06 rest\n"
        self.assertEqual(probe.tuple_states(snapshot, 0x1234, 0x5678), {"06"})

    def test_parser_ignores_unrelated_tuple_and_host(self):
        snapshot = ("header\n0: 0100007F:1234 0100007F:5679 06 rest\n"
                    "1: 0200007F:1234 0100007F:5678 06 rest\n"
                    "2: 0100007F:1235 0100007F:5678 06 rest\n")
        self.assertEqual(probe.tuple_states(snapshot, 0x1234, 0x5678), set())

    def test_parser_distinguishes_listener_from_time_wait(self):
        snapshot = ("header\n0: 0100007F:1234 00000000:0000 0A rest\n"
                    "1: 0100007F:1234 0100007F:5678 06 rest\n")
        self.assertEqual(probe.tuple_states(snapshot, 0x1234), {"0A", "06"})
        self.assertEqual(probe.tuple_states(snapshot, 0x1234, 0x5678), {"06"})

    def test_reproduction_contract_requires_complete_evidence(self):
        self.assertTrue(probe.reproduced(self.positive()))
        self.assertFalse(probe.reproduced({}))

    def test_each_boolean_condition_is_mandatory(self):
        baseline = self.positive()
        for key, value in baseline.items():
            if value is True:
                for bad in (False, None, "true", 1):
                    with self.subTest(key=key, bad=bad):
                        self.assertFalse(probe.reproduced({**baseline, key: bad}))

    def test_each_bind_result_is_mandatory(self):
        baseline = self.positive()
        for key in ("closed_listener_plain_bind", "current_production_preflight", "closed_listener_reuseaddr_bind"):
            for bad in ("NOT_RUN", "OTHER_ERROR", None):
                with self.subTest(key=key, bad=bad):
                    self.assertFalse(probe.reproduced({**baseline, key: bad}))

    def test_unsupported_platform_never_claims_reproduction(self):
        with patch.object(probe.sys, "platform", "win32"):
            result = probe.run_probe()
        self.assertEqual(result["outcome"], "NOT_AVAILABLE")
        self.assertFalse(result["suspected_defect_reproduced"])
        self.assertFalse(result["diagnostic_completed"])

    def test_cli_records_unavailable_without_leaking_output_path(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.json"
            with patch.object(probe.sys, "platform", "win32"), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(probe.main(["--output", str(target)]), 1)
            self.assertEqual(json.loads(output.getvalue()), json.loads(target.read_text()))
            self.assertNotIn(directory, output.getvalue())

    def test_reproduced_bug_does_not_intentionally_fail_diagnostic_step(self):
        # CLI contract only; this injected report is NEVER a native receipt.
        with tempfile.TemporaryDirectory() as directory:
            result = {"diagnostic_completed": True, "outcome": "REPRODUCED"}
            with patch.object(probe, "run_probe", return_value=result), redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(["--output", str(Path(directory) / "result.json")]), 0)

    def test_completed_negative_result_is_not_reported_as_reproduced(self):
        with tempfile.TemporaryDirectory() as directory:
            result = {"diagnostic_completed": True, "outcome": "NOT_REPRODUCED", "suspected_defect_reproduced": False}
            with patch.object(probe, "run_probe", return_value=result), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(probe.main(["--output", str(Path(directory) / "result.json")]), 0)
            self.assertFalse(json.loads(output.getvalue())["suspected_defect_reproduced"])


if __name__ == "__main__":
    unittest.main()
