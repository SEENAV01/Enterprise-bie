"""Safe receipt and mandatory hosted-proof controls, separate from rendering."""
import ast
import json
from pathlib import Path
import unittest
from tests.compiler.run_motion_m1 import safe_error
from tests.compiler.run_m1_tests import inventory, NEW, SAFETY

ROOT=Path(__file__).resolve().parents[2]


class MotionEvidenceControls(unittest.TestCase):
    def test_error_message_private_content_not_exported(self):
        value=safe_error(ValueError("PRIVATE source text /private/path token secret"))
        self.assertEqual(value,{"exception_class":"ValueError","safe_code":"UNCLASSIFIED"})

    def test_safe_native_code_not_private_suffix_exported(self):
        value=safe_error(ValueError("ACTUAL_PAINT_EXECUTION_BLOCKED: private content"))
        self.assertEqual(value["safe_code"],"ACTUAL_PAINT_EXECUTION_BLOCKED")
        self.assertNotIn("private",json.dumps(value))

    def test_supplemental_inventory_excludes_originals_and_safety(self):
        selected,old=inventory()
        self.assertFalse(set(selected["native-extra"])&old)
        self.assertFalse(set(selected["native-extra"])&set(NEW))
        self.assertEqual(selected["safety"],list(SAFETY))
        self.assertEqual(len(selected["native-extra"]),len(set(selected["native-extra"])))
        self.assertIn("tests/compiler/test_comp_h3_003.py",selected["native-extra"])

    def test_original_runner_and_implementation_unchanged_in_task(self):
        # Exact identities are also verified by source preservation; this guard
        # makes the explicit original inventory and safety separation visible.
        self.assertEqual(len(SAFETY),2)
        text=(ROOT/"tools/run_task035_tests.py").read_text(encoding="utf-8")
        self.assertIn('"tests/post_dir/test_canonical_adoption.py"',text)
        self.assertNotIn("m1",text.lower())

    def test_real_h3_and_render_required_in_proof_driver(self):
        text=(ROOT/"tests/compiler/run_motion_m1.py").read_text(encoding="utf-8")
        calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr for n in ast.walk(ast.parse(text))
               if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))}
        self.assertTrue({"compile_h3_scene","publish_h3_scene","produce_actual_paint","require_actual_witness","decoded_frames"}<=calls)
        self.assertIn('for frame, record in enumerate(data["frames"])',text)
        self.assertIn('"COMPILER_FIXTURE_WINDOW"',(ROOT/"bie/compiler/producer_motion_admission.py").read_text(encoding="utf-8"))

    def test_original_worker_not_disabled_or_budgeted_by_new_driver(self):
        text=(ROOT/"tests/compiler/run_motion_m1.py").read_text(encoding="utf-8")
        self.assertNotIn("WorkerPolicy(",text)
        self.assertNotIn("continue_on_error",text)
        self.assertNotIn("mock",text)
        self.assertIn('return 0 if result["passed"] else 1',text)

    def test_scoped_render_supervisor_keeps_native_owned_engine(self):
        text=(ROOT/"tests/compiler/run_m1_owned_render.py").read_text(encoding="utf-8")
        self.assertIn('os.getuid()==0',text)
        self.assertIn('source_bytes_unchanged=True',text)
        self.assertIn('completed.returncode==0 and receipt.get("passed") is True',text)
        self.assertNotIn("chmod",text)
        self.assertNotIn("chown",text)

    def test_workflow_retains_proof_and_original_gates(self):
        # Textual policy guard, not a substitute for GitHub's YAML parser.
        scripts=(ROOT/".github/workflows/task036-motion-capability.yml").read_text(encoding="utf-8")
        for name in ("di_knowledge","pr_reasoning","math_evidence","pedagogy","director","visual","animation"):
            self.assertIn("scripts/smoke_bie_"+name+".py",scripts)
        for name in ("run_task035_tests.py --lane new","run_task035_tests.py --lane affected",
                     "verify_post_dir_provisioning.py","scripts/audit_canonical.py",
                     "run_motion_m1.py --mode source","run_m1_owned_render.py"):
            self.assertIn(name,scripts)
        self.assertIn("bash .integration/tools/setup_ci_environment.sh",scripts)
        self.assertIn("bash .integration/tools/setup_game_ci.sh",scripts)
        self.assertIn("timeout-minutes: 20",scripts.split("  render:",1)[1])
        self.assertIn("timeout-minutes: 45",scripts.split("  verify:",1)[1].split("  native-extra:",1)[0])
        self.assertNotIn("continue-on-error",scripts)


if __name__=="__main__":unittest.main()
