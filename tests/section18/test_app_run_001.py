from __future__ import annotations

import concurrent.futures
import json

from batch001_support import OperatorCase

from bie.product_app_v1.models import OperatorError
from bie.product_app_v1.run_create import create_run


class AppRun001Tests(OperatorCase):
    def test_create_run_is_persisted_draft(self):
        value = self.create("alpha")
        self.assertEqual(value["state"], "DRAFT")
        self.assertEqual(self.context.operator.get_run(value["run_id"]).state, "DRAFT")

    def test_run_id_is_deterministic_and_idempotent(self):
        first = self.create("same-key")
        second = self.create("same-key")
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(len(self.context.operator.list_runs()), 1)

    def test_create_event_is_written_once(self):
        run = self.create("event-key")
        self.create("event-key")
        events = self.context.operator.events(run["run_id"])
        self.assertEqual([e.event_type for e in events], ["RUN_CREATED"])

    def test_create_key_has_strict_contract(self):
        for key in ("", "bad key", "x" * 129, "line\nbreak"):
            with self.subTest(key=repr(key)):
                with self.assertRaises(OperatorError):
                    create_run(self.context.operator, key)

    def test_run_snapshot_exposes_no_fake_progress(self):
        run = self.create("progress")
        self.assertIsNone(run["progress_percent"])

    def test_restart_recovers_same_run(self):
        run = self.create("restart")
        from bie.product_app_v1.context import OperatorContext
        reopened = OperatorContext(self.root)
        self.assertEqual(reopened.operator.get_run(run["run_id"]).to_safe_dict(), run)

    def test_concurrent_create_collapses_to_one_identity(self):
        def invoke(_):
            return self.create("concurrent")["run_id"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(invoke, range(24)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(len(self.context.operator.list_runs()), 1)

    def test_store_contains_metadata_not_source_bytes(self):
        self.create("metadata-only")
        snapshot = json.dumps(self.context.operator.snapshot(), sort_keys=True)
        self.assertNotIn("%PDF", snapshot)


if __name__ == "__main__":
    import unittest
    unittest.main()
