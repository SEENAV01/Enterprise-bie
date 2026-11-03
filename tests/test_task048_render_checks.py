"""Task 048, first slice: the render checks and the one-button plumbing.

Navin, 3 November 2026: "then start the render/player and one-button plumbing (Task 048)". Offline: the render report carries
the text check (tools/text_audit.py, measured on the drawn frames) and the respec record (tools/respec_video.py); the render
workflow runs both; one VM chain job can go from the book to the canvas director's video specs (--with-canvas). The chain run
itself is tested in tests/test_task046c_real_world_chain.py (it needs the PDF libraries of the Task 045 lane).
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import cost, formats  # noqa: E402
from bie.brain.video import text_audit as ta  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "task046c-render.yml"


def audit_record():
    frames = [{"frame": f, "texts": [{"t": "tiny label", "px": 22, "box": [0, 0, 90, 22]},
                                      {"t": "₹1,500", "px": 40, "box": [100, 100, 120, 40]},
                                      {"t": "₹1,000", "px": 40, "box": [110, 105, 120, 40]}]} for f in (0, 30, 60)]
    return ta.summarize(frames, every=30)


RESPEC = {"schema": "bie.respec/1", "run": "runs/x", "videos": [
    {"video_id": "v4", "status": "spec_written", "compiled": 2, "refused": 1, "scenes": 3, "seconds": 40.0,
     "parts": [{"id": "v4_s1", "mode": "B", "status": "compiled"}, {"id": "v4_s2", "mode": "C", "status": "compiled"},
               {"id": "v4_s3", "mode": "B", "status": "refused", "problem": "history: a timeline picture needs at least 3 rows (CV-17)"}]}]}


class RenderReport(unittest.TestCase):
    def test_the_report_carries_the_text_check_and_the_parts_compiled_again(self):
        import render_spec
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / "audit.json").write_text(json.dumps(dict(audit_record(), spec="video_spec.json")), encoding="utf-8")
            (out / "RESPEC.json").write_text(json.dumps(RESPEC), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(render_spec.main(["summary", "--out", folder, "--run-id", "7", "--sha", "abc"]), 0)
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(formats.problems("render_summary", summary), [])
            check = summary["text_check"]
            self.assertEqual((check["floor_px"], check["lasting_small_count"], check["lasting_overlap_count"]), (36, 1, 1))
            self.assertEqual(summary["respec"], [{"video_id": "v4", "status": "spec_written", "compiled": 2, "refused": 1, "seconds": 40.0}])
            report = (out / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("1 texts under 36 px for a second or more", report)
            self.assertIn('small: "tiny label" 22 px', report)
            self.assertIn('on each other: "₹1,000" and "₹1,500"', report)
            self.assertIn("v4 2 parts compiled, 1 refused", report)
            self.assertIn("v4_s3 refused: history: a timeline picture", report)

    def test_a_render_without_the_checks_reports_as_before(self):
        import render_spec
        with tempfile.TemporaryDirectory() as folder:
            with contextlib.redirect_stdout(io.StringIO()):
                render_spec.main(["summary", "--out", folder])
            summary = json.loads(Path(folder, "summary.json").read_text(encoding="utf-8"))
            self.assertNotIn("text_check", summary)
            self.assertNotIn("respec", summary)

    def test_the_two_records_are_registered_formats(self):
        self.assertEqual(formats.problems("text_audit", audit_record()), [])
        self.assertEqual(formats.problems("respec", RESPEC), [])
        self.assertTrue(formats.problems("respec", {"schema": "bie.respec/1", "videos": [{"video_id": "v4"}]}))
        self.assertEqual((formats.FORMATS["text_audit"].tag, formats.FORMATS["respec"].tag), ("bie.text-audit/1", "bie.respec/1"))


class RenderWorkflow(unittest.TestCase):
    """Read as text (the repository has no YAML library): the jobs are split at their two-space keys."""

    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        body = self.text.split("\njobs:\n", 1)[1]
        parts = re.split(r"^  ([a-z]+):\n", body, flags=re.M)
        self.jobs = dict(zip(parts[1::2], parts[2::2]))

    def test_every_render_runs_the_text_check_and_publishes_it(self):
        self.assertIn("needs: [prepare]", self.jobs["audit"])
        self.assertIn("needs: [prepare, render, audit]", self.jobs["finish"])
        self.assertIn("tools/text_audit.py", self.jobs["audit"])
        self.assertIn("set -euo pipefail", self.jobs["audit"])              # a failed check is never hidden by the tee
        self.assertIn("name: t046c-audit", self.jobs["finish"])
        self.assertIn("for f in audit.json RESPEC.json", self.jobs["finish"])

    def test_respec_is_an_input_and_compiles_the_plans_again_before_the_render(self):
        inputs = self.text.split("pull_request:", 1)[0]
        self.assertRegex(inputs, r"respec:\n\s+description: [^\n]+\n\s+type: boolean\n\s+default: false")
        self.assertIn("tools/respec_video.py", self.jobs["prepare"])
        self.assertIn("RESPEC.json", self.jobs["prepare"])
        self.assertIn("- 'tools/text_audit.py'", self.text.split("pull_request:", 1)[1].split("permissions:", 1)[0])


class OneButtonPlumbing(unittest.TestCase):
    def test_the_vm_accepts_a_chain_job_with_the_canvas_director(self):
        import codex_vm
        job = codex_vm.validate({"job": codex_vm.JOB_SCHEMA, "id": "t048-chain", "section": "chain", "with_canvas": True,
                                 "source": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/book.pdf"})
        cmd = codex_vm.argv(job, Path("/tmp/out"))
        self.assertIn("--with-canvas", cmd)
        self.assertEqual(cmd[cmd.index("--section") + 1], "chain")
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(job, with_canvas="yes"))

    def test_the_estimate_counts_the_canvas_plans_in_a_chain_with_the_canvas(self):
        plain = cost.estimate("chain", 10, rate=88.0)
        with_canvas = cost.estimate("chain", 10, rate=88.0, with_canvas=True)
        self.assertNotIn("canvas", plain["sections"])
        self.assertIn("canvas", with_canvas["sections"])
        self.assertGreater(with_canvas["total_inr"], plain["total_inr"])
        self.assertNotIn("canvas", cost.estimate("lesson", 10, rate=88.0, with_canvas=True)["sections"])


if __name__ == "__main__":
    unittest.main()
