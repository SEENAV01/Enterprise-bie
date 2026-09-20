import unittest
from copy import deepcopy

from bie.compiler.implementation_exit import evaluate_implementation_scope_exit
from bie.compiler.section_closure import REQUIRED, evaluate_section_closure


def complete_rows():
    return [
        {
            "capability": capability,
            "status": "VERIFIED_ACTUAL" if capability in {"pinned_compile", "actual_render"} else "IMPLEMENTED_TESTED",
            "evidence": ["evidence:" + capability],
            "remaining": [],
        }
        for capability in REQUIRED
    ]


class ImplementationScopeExitTests(unittest.TestCase):
    def test_environment_block_does_not_become_implementation_gap(self):
        rows = complete_rows()
        for name in ("operational_isolation", "pinned_compile", "actual_render"):
            item = next(x for x in rows if x["capability"] == name)
            item.update(status="BLOCKED_ENVIRONMENT", remaining=["required runtime environment unavailable"])
        result = evaluate_implementation_scope_exit(rows)
        self.assertTrue(result["implementation_scope_complete"])
        self.assertTrue(result["implementation_scope_exit_permitted"])
        self.assertFalse(result["runtime_verification_complete"])
        self.assertEqual(set(result["blocked_execution"]), {"operational_isolation", "pinned_compile", "actual_render"})

    def test_open_implementation_blocks_development_exit(self):
        rows = complete_rows()
        rows[0].update(status="OPEN_IMPLEMENTATION", remaining=["required compiler path missing"])
        result = evaluate_implementation_scope_exit(rows)
        self.assertFalse(result["implementation_scope_complete"])
        self.assertFalse(result["implementation_scope_exit_permitted"])
        self.assertEqual(result["open_implementation"], [rows[0]["capability"]])

    def test_all_runtime_verified_is_still_not_product_acceptance(self):
        result = evaluate_implementation_scope_exit(complete_rows())
        self.assertTrue(result["runtime_verification_complete"])
        self.assertTrue(result["implementation_scope_exit_permitted"])
        self.assertFalse(result["actual_render_authorization"])
        self.assertFalse(result["product_accepted"])
        self.assertFalse(result["accepted"])

    def test_historical_runtime_gate_remains_strict(self):
        rows = complete_rows()
        rows[-1].update(status="BLOCKED_ENVIRONMENT", remaining=["renderer dependency unavailable"])
        self.assertFalse(evaluate_section_closure(rows)["section_exit_permitted"])
        self.assertTrue(evaluate_implementation_scope_exit(rows)["implementation_scope_exit_permitted"])

    def test_runtime_blockers_are_preserved_not_erased(self):
        rows = complete_rows()
        item = next(x for x in rows if x["capability"] == "pinned_compile")
        item.update(status="BLOCKED_ENVIRONMENT", remaining=["exact node_modules unavailable"])
        result = evaluate_implementation_scope_exit(rows)
        self.assertEqual(result["blocked_execution"], ["pinned_compile"])
        self.assertEqual(result["status"], "IMPLEMENTATION_SCOPE_COMPLETE_RUNTIME_VERIFICATION_PENDING")

    def test_register_digest_is_inherited_from_validated_v1_register(self):
        rows = complete_rows()
        first = evaluate_implementation_scope_exit(rows)["register_sha256"]
        changed = deepcopy(rows)
        changed[0]["evidence"].append("different-evidence")
        second = evaluate_implementation_scope_exit(changed)["register_sha256"]
        self.assertNotEqual(first, second)

    def test_missing_required_capability_still_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_implementation_scope_exit(complete_rows()[:-1])

    def test_required_capability_cannot_be_scoped_out(self):
        rows = complete_rows()
        rows[0]["status"] = "OUT_OF_SCOPE"
        with self.assertRaises(ValueError):
            evaluate_implementation_scope_exit(rows)

    def test_complete_status_cannot_hide_remaining_work(self):
        rows = complete_rows()
        rows[0]["remaining"] = ["still missing"]
        with self.assertRaises(ValueError):
            evaluate_implementation_scope_exit(rows)

    def test_blocked_status_requires_reason(self):
        rows = complete_rows()
        rows[-1]["status"] = "BLOCKED_ENVIRONMENT"
        with self.assertRaises(ValueError):
            evaluate_implementation_scope_exit(rows)

    def test_pinned_compile_cannot_claim_implemented_without_actual_verification(self):
        rows = complete_rows()
        item = next(x for x in rows if x["capability"] == "pinned_compile")
        item["status"] = "IMPLEMENTED_TESTED"
        with self.assertRaises(ValueError):
            evaluate_implementation_scope_exit(rows)

    def test_unknown_fields_still_rejected(self):
        rows = complete_rows()
        rows[0]["accepted"] = True
        with self.assertRaises(ValueError):
            evaluate_implementation_scope_exit(rows)
