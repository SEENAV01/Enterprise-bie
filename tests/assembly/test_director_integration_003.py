"""Canonical DIR integration, preservation, and acceptance-boundary checks."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DirectorIntegration003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "manifests/director_integration_003.json").read_text())
        cls.registry = json.loads((ROOT / "task_registry/director_integration_003.json").read_text())

    def test_all_atomic_archives_and_members_are_declared(self):
        self.assertEqual(self.manifest["archive_count"], 59)
        self.assertEqual(self.manifest["member_count"], 610)
        self.assertEqual(len(self.manifest["archives"]), 59)
        self.assertEqual(len(self.manifest["members"]), 610)
        self.assertTrue(all((ROOT / row["backup_path"]).is_file() for row in self.manifest["archives"]))

    def test_all_task_records_are_present(self):
        task_ids = {row["task_id"] for row in self.manifest["archives"]}
        self.assertEqual(task_ids, set(self.registry["task_ids"]))
        self.assertTrue(all((ROOT / "docs/tasks" / task / "TASK_RESULT.json").is_file() for task in task_ids))

    def test_active_director_tree_is_source_not_archive_runtime(self):
        modules = sorted((ROOT / "bie/director").glob("*.py"))
        self.assertEqual(len(modules), 71)
        for module in modules:
            tree = ast.parse(module.read_text(), filename=str(module))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [item.name for item in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                    self.assertFalse(any("zip" in name.lower() or "backup" in name.lower() for name in names), module)

    def test_standalone_completion_evidence_is_exact(self):
        report = json.loads((ROOT / "docs/evidence/director-integration-003/dir_completion_tests.json").read_text())
        self.assertEqual(report["summary"]["tests"], 683)
        self.assertEqual(report["summary"]["test_files"], 72)
        self.assertTrue(report["summary"]["passed"])

    def test_implementation_is_not_product_acceptance(self):
        self.assertEqual(self.registry["state"], "DIR = IMPLEMENTATION-SCOPE COMPLETE — NOT ACCEPTED")
        self.assertFalse(self.registry["accepted"])
        self.assertFalse(self.manifest["accepted"])
        self.assertGreaterEqual(len(self.registry["acceptance_blockers"]), 4)


if __name__ == "__main__":
    unittest.main()
