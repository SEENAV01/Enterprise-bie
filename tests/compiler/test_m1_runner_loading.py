"""M1 CI-R1 loader fixtures, not native compiler/render acceptance evidence."""
from contextlib import contextmanager
import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from tests.compiler import run_m1_tests as runner

CASE = "import unittest\nclass Example(unittest.TestCase):\n    def test_value(self): self.assertTrue(True)\n"


class PackageCollectionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="m1-runner-fixture-")
        self.root = Path(self.temp.name).resolve()
        self.original_path = sys.path[:]
        self.original_modules = dict(sys.modules)

    def tearDown(self):
        sys.path[:] = self.original_path
        for name in list(sys.modules):
            if name.startswith("r1_") or name == "sibling_guard":
                if name in self.original_modules: sys.modules[name] = self.original_modules[name]
                else: sys.modules.pop(name, None)
        self.temp.cleanup()

    def write(self, relative, source):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def package(self, name):
        for depth in range(1, len(name.split("/")) + 1):
            self.write("/".join(name.split("/")[:depth]) + "/__init__.py", "")

    def row(self, path, seen=None):
        return runner.run_file(path, set() if seen is None else seen, self.root)

    def test_relative_sibling_real_package_and_origins(self):
        self.package("r1_pkg")
        self.write("r1_pkg/helper.py", "VALUE=17\n")
        self.write("r1_pkg/test_case.py", "from .helper import VALUE\n" + CASE.replace("self.assertTrue(True)", "self.assertEqual(VALUE,17)"))
        row = self.row("r1_pkg/test_case.py")
        self.assertTrue(row["passed"], row)
        self.assertEqual(row["import_origins"]["r1_pkg.helper"], "r1_pkg/helper.py")
        self.assertEqual(row["import_origins"]["r1_pkg"], "r1_pkg/__init__.py")

    def test_nested_namespace_package_is_real_not_fabricated(self):
        self.write("r1_namespace/nested/helper.py", "VALUE=1\n")
        self.write("r1_namespace/nested/test_case.py", "from .helper import VALUE\n" + CASE)
        row = self.row("r1_namespace/nested/test_case.py")
        self.assertTrue(row["passed"], row)
        self.assertEqual(row["import_origins"]["r1_namespace.nested"], "r1_namespace/nested/")

    def test_standalone_sibling_import_and_path_restoration(self):
        self.write("sibling_guard.py", "VALUE=1\n")
        self.write("r1_test_case.py", "from sibling_guard import VALUE\n" + CASE)
        self.assertTrue(self.row("r1_test_case.py")["passed"])
        self.assertEqual(sys.path, self.original_path)
        self.assertNotIn("sibling_guard", sys.modules)
        self.assertNotIn("r1_test_case", sys.modules)

    def test_same_basename_different_packages_and_helpers(self):
        seen = set()
        for pkg, value in (("r1_a", 1), ("r1_b", 2)):
            self.package(pkg)
            self.write(pkg + "/sibling_guard.py", "VALUE=" + str(value) + "\n")
            self.write(pkg + "/test_case.py", "from sibling_guard import VALUE\n" + CASE.replace("self.assertTrue(True)", "self.assertEqual(VALUE," + str(value) + ")"))
            self.assertTrue(self.row(pkg + "/test_case.py", seen)["passed"])
        self.assertEqual(len(seen), 2)
        self.assertNotIn("sibling_guard", sys.modules)

    def test_selected_suite_keeps_selected_subclass_and_subtests(self):
        self.package("r1_selected")
        self.write("r1_selected/base.py", CASE.replace("self.assertTrue(True)", "self.fail('not selected')"))
        self.write("r1_selected/test_case.py", """import unittest
from .base import Example
class Selected(Example):
    def test_value(self):
        for i in range(3):
            with self.subTest(i=i): self.assertLess(i,3)
def selected_suite(): return unittest.defaultTestLoader.loadTestsFromTestCase(Selected)
""")
        row = self.row("r1_selected/test_case.py")
        self.assertTrue(row["passed"], row)
        self.assertEqual(row["selected"], 1)
        self.assertEqual(row["logical_identities"], ["r1_selected/test_case.py::Selected.test_value"])

    def test_stable_identity_removes_known_entire_module_prefix(self):
        self.package("r1_pkg/nested")
        path = self.write("r1_pkg/nested/test_case.py", CASE)
        with runner.repository_module("r1_pkg/nested/test_case.py", self.root) as (module, _):
            suite, expected = runner.collect_suite(module, self.root, set())
            spec = importlib.util.spec_from_file_location("r1_old_alias", path)
            old = importlib.util.module_from_spec(spec); sys.modules[spec.name] = old
            spec.loader.exec_module(old)
            actual = runner.logical_identity(old.Example("test_value"), self.root)
            self.assertEqual(actual, expected[0])
            self.assertEqual(actual, "r1_pkg/nested/test_case.py::Example.test_value")

    def test_custom_parameter_identity_stays_distinct_without_raw_values(self):
        self.write("r1_parameters.py", CASE + """
class Parameter(Example):
    def id(self): return super().id() + '[' + self.variant + ']'
def selected_suite():
    a=Parameter('test_value');a.variant='PRIVATE-A'
    b=Parameter('test_value');b.variant='PRIVATE-B'
    return unittest.TestSuite([a,b])
""")
        row = self.row("r1_parameters.py")
        self.assertTrue(row["passed"], row)
        self.assertEqual(len(set(row["logical_identities"])), 2)
        self.assertNotIn("PRIVATE", str(row))

    def test_duplicate_within_selected_suite_fails_closed(self):
        self.write("r1_duplicate.py", CASE + "\ndef selected_suite(): return unittest.TestSuite([Example('test_value'),Example('test_value')])\n")
        row = self.row("r1_duplicate.py")
        self.assertFalse(row["passed"])
        self.assertEqual(row["collector_error"]["code"], "M1_DUPLICATE_TEST_IDENTITY")
        self.assertEqual(row["executed"], 0)

    def test_cross_file_imported_case_duplicate_not_counted_again(self):
        self.package("r1_shared")
        self.write("r1_shared/test_one.py", CASE)
        self.write("r1_shared/test_two.py", "from .test_one import Example\n")
        seen = set()
        self.assertTrue(self.row("r1_shared/test_one.py", seen)["passed"])
        row = self.row("r1_shared/test_two.py", seen)
        self.assertFalse(row["passed"])
        self.assertEqual(row["collector_error"]["code"], "M1_DUPLICATE_TEST_IDENTITY")
        self.assertEqual(len(seen), 1)

    @contextmanager
    def foreign_import(self, relative, name):
        with tempfile.TemporaryDirectory(prefix="m1-foreign-fixture-") as td:
            other = Path(td)
            path = other / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(CASE, encoding="utf-8")
            if "." in name: (path.parent / "__init__.py").write_text("")
            sys.path.insert(0, td)
            try:
                foreign = importlib.import_module(name)
                yield foreign
            finally:
                sys.path.remove(td)
                for key in list(sys.modules):
                    if key == name.split(".")[0] or key.startswith(name.split(".")[0] + "."):
                        sys.modules.pop(key, None)

    def test_foreign_parent_package_rejected_not_replaced(self):
        self.package("r1_foreign")
        self.write("r1_foreign/test_case.py", CASE)
        with self.foreign_import("r1_foreign/test_case.py", "r1_foreign.test_case") as foreign:
            row = self.row("r1_foreign/test_case.py")
            self.assertFalse(row["passed"])
            self.assertEqual(row["collector_error"]["code"], "M1_COLLECTION_FOREIGN_PACKAGE")
            self.assertIs(sys.modules["r1_foreign.test_case"], foreign)

    def test_foreign_standalone_target_rejected(self):
        self.write("r1_target.py", CASE)
        with self.foreign_import("r1_target.py", "r1_target"):
            row = self.row("r1_target.py")
            self.assertFalse(row["passed"])
            self.assertEqual(row["collector_error"]["code"], "M1_COLLECTION_FOREIGN_MODULE")

    def test_foreign_bare_helper_alias_rejected(self):
        self.package("r1_pkg")
        self.write("r1_pkg/sibling_guard.py", "VALUE=1\n")
        self.write("r1_pkg/test_case.py", "import sibling_guard\n" + CASE)
        with self.foreign_import("sibling_guard.py", "sibling_guard"):
            row = self.row("r1_pkg/test_case.py")
            self.assertFalse(row["passed"])
            self.assertEqual(row["collector_error"]["code"], "M1_COLLECTION_FOREIGN_MODULE")

    def test_import_error_is_collection_error_not_executed_test(self):
        self.package("r1_pkg")
        self.write("r1_pkg/test_case.py", "raise ImportError('PRIVATE payload /machine/path')\n")
        row = self.row("r1_pkg/test_case.py")
        self.assertEqual((row["selected"], row["executed"], row["errors"], row["collection_errors"]), (0, 0, 0, 1))
        self.assertFalse(row["passed"])
        self.assertNotIn("PRIVATE", str(row))
        self.assertNotIn(str(self.root), str(row))

    def test_empty_file_cannot_pass(self):
        self.write("r1_empty.py", "")
        row = self.row("r1_empty.py")
        self.assertFalse(row["passed"])
        self.assertEqual(row["collector_error"]["code"], "M1_COLLECTION_EMPTY_SUITE")

    def test_missing_source_cannot_pass(self):
        row = self.row("r1_missing.py")
        self.assertFalse(row["passed"])
        self.assertEqual(row["collection_errors"], 1)

    def test_path_and_module_context_restored_after_import_failure(self):
        self.package("r1_pkg")
        self.write("r1_pkg/helper.py", "VALUE=1\n")
        self.write("r1_pkg/test_case.py", "from .helper import VALUE\nraise ImportError('failed')\n")
        self.row("r1_pkg/test_case.py")
        self.assertEqual(sys.path, self.original_path)
        self.assertFalse(any(n == "r1_pkg" or n.startswith("r1_pkg.") for n in sys.modules))

    def test_preexisting_package_object_and_child_attributes_restored(self):
        self.package("r1_pkg")
        self.write("r1_pkg/test_case.py", CASE)
        sys.path.insert(0, str(self.root))
        package = importlib.import_module("r1_pkg")
        previous = sys.path[:]
        self.assertTrue(self.row("r1_pkg/test_case.py")["passed"])
        self.assertIs(sys.modules["r1_pkg"], package)
        self.assertFalse(hasattr(package, "test_case"))
        self.assertEqual(sys.path, previous)

    def test_execution_failure_and_skip_keep_gate_red(self):
        for source in (CASE.replace("self.assertTrue(True)", "self.fail('expected')"),
                       CASE.replace("self.assertTrue(True)", "self.skipTest('expected')")):
            self.write("r1_nonpass.py", source)
            row = self.row("r1_nonpass.py")
            self.assertFalse(row["passed"])
            self.assertEqual(row["executed"], 1)
            self.assertEqual(row["collection_errors"], 0)

    def test_new_nested_parent_does_not_leak_on_preexisting_outer_package(self):
        self.package("r1_pkg/nested")
        self.write("r1_pkg/nested/test_case.py", CASE)
        sys.path.insert(0, str(self.root))
        package = importlib.import_module("r1_pkg")
        self.assertFalse(hasattr(package, "nested"))
        row = self.row("r1_pkg/nested/test_case.py")
        self.assertTrue(row["passed"], row)
        self.assertIs(sys.modules["r1_pkg"], package)
        self.assertNotIn("r1_pkg.nested", sys.modules)
        self.assertFalse(hasattr(package, "nested"))

    def test_inventory_retains_all_214_paths_and_assigns_runner_tests_once(self):
        before = sys.path[:]
        selected, inherited = runner.inventory()
        self.assertEqual(sys.path, before)
        self.assertEqual(len(selected["native-extra"]), 214)
        for filename in ("test_comp_build_007.py", "test_comp_build_008.py", "test_comp_render_integration.py"):
            self.assertIn("tests/compiler/" + filename, selected["native-extra"])
        relative = "tests/compiler/test_m1_runner_loading.py"
        self.assertEqual(selected["new"].count(relative), 1)
        self.assertNotIn(relative, selected["native-extra"])
        self.assertFalse(set(selected["native-extra"]) & inherited)
        diagnostic = "tests/compiler/test_m1_safe_paint_diagnostics.py"
        self.assertEqual(selected["new"].count(diagnostic), 1)
        self.assertNotIn(diagnostic, selected["native-extra"])
        self.assertNotIn(diagnostic, selected["safety"])
        self.assertNotIn(diagnostic, inherited)
        capture = "tests/compiler/test_m1_capture_diagnostics.py"
        self.assertEqual(selected["new"].count(capture), 1)
        self.assertNotIn(capture, selected["native-extra"])
        self.assertNotIn(capture, selected["safety"])
        self.assertNotIn(capture, inherited)
        media = "tests/compiler/test_m1_media_diagnostics.py"
        self.assertEqual(selected["new"].count(media), 1)
        self.assertNotIn(media, selected["native-extra"])
        self.assertNotIn(media, selected["safety"])
        self.assertNotIn(media, inherited)

    def test_explicit_native_preimage_alias_checks_actual_checkout_origin(self):
        self.package("r1_native")
        self.package("r1_cases")
        self.write("evidence/source.py.before", "VALUE=1\n")
        self.write("r1_cases/test_case.py", """import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec,spec_from_loader
import r1_native
loader=SourceFileLoader('r1_native._before',str(Path(__file__).parents[1]/'evidence/source.py.before'))
spec=spec_from_loader(loader.name,loader);module=module_from_spec(spec)
sys.modules[loader.name]=module;loader.exec_module(module)
""" + CASE)
        row=self.row("r1_cases/test_case.py")
        self.assertTrue(row["passed"],row)
        self.assertEqual(row["import_origins"]["r1_native._before"],"evidence/source.py.before")

    def test_counterfeit_collection_code_cannot_leak_private_message(self):
        value=runner.collection_diagnostic(runner.CollectionError("PRIVATE source text"),self.root)
        self.assertEqual(value["code"],"M1_COLLECTION_EXCEPTION")
        self.assertNotIn("PRIVATE",str(value))


if __name__ == "__main__": unittest.main()
