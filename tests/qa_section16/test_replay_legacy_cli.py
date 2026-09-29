from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import unittest

from bie.qa.release_contracts import GateEvidence as LegacyEvidence, enterprise_default_policy
from bie.qa.release_v2.codec import dumps
from bie.qa.release_v2.legacy import preview_legacy
from helpers import CaseTest, NOW

ROOT = Path(__file__).resolve().parents[2]


class ReplayLegacyCliTests(CaseTest):
    def test_repeat_evaluation_byte_identity(self):
        self.assertEqual(self.evaluate().to_bytes(), self.evaluate().to_bytes())

    def test_32_seeded_permutations_preserve_decision_bytes(self):
        baseline = self.evaluate().to_bytes()
        for seed in range(32):
            rng = random.Random(seed)
            evs = list(self.bundle.evidence)
            artifacts = list(self.bundle.candidate.artifacts)
            rng.shuffle(evs)
            rng.shuffle(artifacts)
            bundle = replace(self.bundle, candidate=replace(self.bundle.candidate, artifacts=tuple(artifacts)), evidence=tuple(evs))
            with self.subTest(seed=seed):
                self.assertEqual(self.evaluate(bundle).to_bytes(), baseline)

    def test_each_of_28_missing_gate_mutations_blocks(self):
        for gate in self.policy.gates:
            bundle = replace(self.bundle, evidence=tuple(e for e in self.bundle.evidence if e.gate_id != gate.gate_id))
            with self.subTest(gate=gate.gate_id):
                report = self.evaluate(bundle)
                self.assertBlocked(report)
                self.assertIn(gate.gate_id, report.blocking_gates)

    def test_each_of_28_failed_gate_mutations_blocks(self):
        for gate in self.policy.gates:
            bundle = self.replace_evidence(gate_id=gate.gate_id, status="FAIL", diagnostics=("INJECTED_FAILURE",))
            with self.subTest(gate=gate.gate_id):
                self.assertBlocked(self.evaluate(bundle))

    def test_legacy_success_is_not_promoted(self):
        policy = enterprise_default_policy(True, True)
        records = [LegacyEvidence("ev-" + g.gate_id, g.gate_id, "PASS", "fixture", "1.0.0",
                   ["missing-subject"], ["missing-report"], summary="metadata only",
                   created_at="2026-09-26T00:00:00+00:00") for g in policy.gates if g.mode == "REQUIRED"]
        preview = preview_legacy(policy, records)
        self.assertEqual(preview["legacy_decision"]["release_status"], "CONTRACT_ONLY")
        self.assertEqual(preview["release_status"], "BLOCKED")
        self.assertFalse(preview["release_authorized"])
        self.assertTrue(preview["migration_required"])

    def test_legacy_source_bytes_preserved(self):
        p = ROOT / "history/section16_pre_h1/bie/qa/release_contracts.py"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                         "3e721b622855667f7898097bb5bcbe26855a39f24d1f335b2312af7c34846b3b")

    def test_original_test_bytes_preserved(self):
        p = ROOT / "history/section16_pre_h1/upstream/tests/test_release_contracts.py"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                         "bbf1e21131862011156ecd8fb6ce3891c2f99b6a93a55956400f69ee46902cda")

    def test_legacy_malformed_input_rejected(self):
        from bie.qa.release_v2 import ContractError
        with self.assertRaises(ContractError):
            preview_legacy(object(), [])

    def test_cli_never_accepts_fixture_evidence(self):
        path = self.root / "input.json"
        path.write_bytes(dumps(self.bundle))
        env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
        run = subprocess.run([sys.executable, "-m", "bie.qa.release_v2", str(path),
                              "--artifact-root", str(self.root), "--as-of", str(NOW)],
                             cwd=self.root, env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stdout)["release_status"], "BLOCKED")

    def test_cli_malformed_input_structured_failure(self):
        path = self.root / "input.json"
        path.write_bytes(b"not json")
        env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
        run = subprocess.run([sys.executable, "-m", "bie.qa.release_v2", str(path),
                              "--artifact-root", str(self.root), "--as-of", str(NOW)],
                             cwd=self.root, env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)["diagnostic"], "MALFORMED_JSON")

    def test_cli_hashseed_independence(self):
        path = self.root / "input.json"
        path.write_bytes(dumps(self.bundle))
        outputs = []
        for seed in ("1", "99", "12345"):
            env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": seed}
            run = subprocess.run([sys.executable, "-m", "bie.qa.release_v2", str(path),
                                  "--artifact-root", str(self.root), "--as-of", str(NOW)],
                                 cwd=self.root, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 2, run.stderr)
            outputs.append(run.stdout)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])


if __name__ == "__main__":
    unittest.main()
