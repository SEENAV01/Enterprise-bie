from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "metadata" / "section18" / "BATCH001_TASKS.json"
CONTINUATION = ROOT / "docs" / "section18" / "CONTINUATION.json"

EXPECTED = [
    "BIE-APP-RUN-001", "BIE-APP-RUN-002", "BIE-APP-RUN-003", "BIE-APP-RUN-004",
    "BIE-APP-RUN-005", "BIE-APP-RUN-006", "BIE-APP-RUN-007", "BIE-APP-RUN-008",
    "BIE-APP-GRAPH-001", "BIE-APP-GRAPH-002",
]


class Batch001MetadataTests(unittest.TestCase):
    def test_001_exact_original_task_ids(self):
        data = json.loads(META.read_text())
        self.assertEqual(data["task_ids"], EXPECTED)
        self.assertEqual(data["task_count"], 10)

    def test_002_registry_total_remains_33(self):
        self.assertEqual(json.loads(META.read_text())["original_registry_count"], 33)

    def test_003_each_task_has_code_and_tests(self):
        data = json.loads(META.read_text())
        for task in data["tasks"]:
            self.assertTrue(task["owned_paths"], task["task_id"])
            self.assertTrue(task["test_modules"], task["task_id"])
            for path in task["owned_paths"]:
                self.assertTrue((ROOT / path).is_file(), (task["task_id"], path))

    def test_004_baseline_is_section17_merge(self):
        data = json.loads(META.read_text())
        self.assertEqual(data["baseline_main_sha"], "47cafba8975061555764c3c579ae6daad696ae64")

    def test_005_continuation_has_23_remaining_original_tasks(self):
        data = json.loads(CONTINUATION.read_text())
        self.assertEqual(len(data["remaining_original_task_ids"]), 23)
        self.assertEqual(len(set(data["remaining_original_task_ids"])), 23)
        self.assertFalse(set(data["remaining_original_task_ids"]) & set(EXPECTED))

    def test_006_next_batch_is_ten_tasks_and_begins_graph_003(self):
        data = json.loads(CONTINUATION.read_text())
        self.assertEqual(len(data["next_batch_candidate"]), 10)
        self.assertEqual(data["next_batch_candidate"][0], "BIE-APP-GRAPH-003")

    def test_007_task028_and_section_completion_are_not_advanced(self):
        data = json.loads(CONTINUATION.read_text())
        self.assertEqual(data["task028"], "PAUSED_UNCHANGED")
        self.assertFalse(data["section_complete"])
        self.assertFalse(data["product_accepted"])


if __name__ == "__main__":
    unittest.main()
