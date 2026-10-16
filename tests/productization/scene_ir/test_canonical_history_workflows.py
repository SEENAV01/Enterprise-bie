"""Complete-history provisioning for the unchanged canonical preimage gates.

These source-contract checks do not execute Linux CI or replace its outcomes.
They need no additional YAML parser/dependency: known job/step blocks are bounded
by their canonical indentation. Complete YAML/source-diff review is separate.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = {
    ".github/workflows/post-dir-canonical-catchup.yml": 45,
    ".github/workflows/qa-section16-combined.yml": 90,
    ".github/workflows/section18-implementation.yml": 90,
}
CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
OWNED = "tests/productization/scene_ir/test_canonical_history_workflows.py"


def job(path, name):
    text = (ROOT / path).read_text(encoding="utf-8")
    marker = "\n  " + name + ":\n"
    if text.count(marker) != 1:
        raise ValueError("TASK036_CANONICAL_JOB_IDENTITY")
    body = text.split(marker, 1)[1]
    return re.split(r"\n  [a-zA-Z0-9_-]+:\n", body, maxsplit=1)[0]


def checkout(body):
    steps = body.split("      - uses: " + CHECKOUT + "\n")
    if len(steps) != 2:
        raise ValueError("TASK036_CANONICAL_CHECKOUT_IDENTITY")
    # The separator owns the newline ending the preceding block; retain that
    # line terminator rather than misreporting a valid last option as absent.
    return steps[1].split("\n      - ", 1)[0] + "\n"


class CanonicalHistoryWorkflowControls(unittest.TestCase):
    def test_every_complete_canonical_gate_has_full_history(self):
        for path in WORKFLOWS:
            with self.subTest(path=path):
                block = checkout(job(path, "canonical-regression"))
                self.assertEqual(block.count("          fetch-depth: 0\n"), 1)
                self.assertNotRegex(block, r"fetch-depth: (?:1|[2-9][0-9]*)\b")

    def test_checkout_keeps_pin_credentials_and_default_candidate_selection(self):
        for path in WORKFLOWS:
            with self.subTest(path=path):
                self.assertEqual(checkout(job(path, "canonical-regression")),
                    "        with:\n          persist-credentials: false\n          fetch-depth: 0\n")

    def test_existing_canonical_regression_and_preservation_remain_required(self):
        for path in WORKFLOWS:
            with self.subTest(path=path):
                body = job(path, "canonical-regression")
                self.assertIn("python -B scripts/integrated_check.py --output-dir", body)
                self.assertIn("set -euo pipefail", body)
                self.assertIn("python -B scripts/verify_post_dir.py --output", body)
                self.assertIn("'failures','errors','skipped'", body)
                self.assertIn("AUDIO_GATE_FAILED", body)
                self.assertIn("GAME_GATE_COVERAGE_FAILED", body)
                self.assertIn("2023", body)
                self.assertNotIn("continue-on-error:", body)

    def test_original_canonical_job_budgets_are_not_increased(self):
        for path, limit in WORKFLOWS.items():
            with self.subTest(path=path):
                body = job(path, "canonical-regression")
                self.assertEqual(re.findall(r"^    timeout-minutes: (\d+)$", body, re.M), [str(limit)])

    def test_section18_other_job_checkouts_and_limits_are_not_broadened(self):
        path = ".github/workflows/section18-implementation.yml"
        for name, limit in (("native-render", 20), ("section16-regression", 60)):
            with self.subTest(job=name):
                body = job(path, name)
                self.assertEqual(checkout(body), "        with:\n          persist-credentials: false\n")
                self.assertEqual(re.findall(r"^    timeout-minutes: (\d+)$", body, re.M), [str(limit)])

    def test_new_file_owned_once_without_original_inventory_loss_or_overlap(self):
        from tools.run_task036_tests import NEW
        from tests.compiler.run_m1_tests import NEW as m1_new, SAFETY, inventory
        original = {
            "tests/productization/scene_ir/test_scene_ir_admission.py",
            "tests/productization/scene_ir/test_scene_ir_contract.py",
            "tests/productization/scene_ir/test_scene_ir_producer.py",
            "tests/productization/scene_ir/test_scene_ir_conservation.py",
            "tests/productization/scene_ir/test_scene_ir_currentness.py",
            "tests/productization/scene_ir/test_scene_ir_recovery.py",
            "tests/productization/scene_ir/test_recovery_observations.py",
            "tests/productization/scene_ir/test_status_composition.py",
        }
        lanes, inherited = inventory()
        self.assertEqual(NEW.count(OWNED), 1)
        self.assertTrue(original.issubset(NEW))
        self.assertEqual(len(NEW), len(set(NEW)))
        self.assertNotIn(OWNED, set(m1_new) | set(SAFETY) | set(lanes["native-extra"]) | inherited)


if __name__ == "__main__":
    unittest.main()
