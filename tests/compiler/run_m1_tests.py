"""Unique supplemental M1/native inventory; original Task035 lanes stay separate."""
import argparse
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from types import TracebackType
import unittest

ROOT = Path(__file__).resolve().parents[2]
NEW = ("tests/compiler/test_producer_motion_m1.py", "tests/compiler/test_motion_m1_preservation.py",
       "tests/compiler/test_motion_m1_evidence.py", "tests/compiler/test_m1_runner_loading.py",
       "tests/compiler/test_m1_safe_paint_diagnostics.py", "tests/compiler/test_m1_capture_diagnostics.py",
       "tests/compiler/test_m1_media_diagnostics.py", "tests/compiler/test_m1_media_threads.py",
       "tests/compiler/test_m1_media_policy_observation.py", "tests/compiler/test_m1_media_source_pin.py",
       "tests/compiler/test_m1_stitch_inputs.py", "tests/compiler/test_m1_lifecycle_diagnostics.py",
       "tests/compiler/test_m1_parent_exception_observation.py", "tests/compiler/test_m1_pr_source_contract.py")
SAFETY = ("tests/productization/animation/test_ci_r1_diagnostics.py",
          "tests/productization/animation/test_ci_r2_provisioning.py")


def inventory():
    spec = importlib.util.spec_from_file_location("m1_task035_inventory", ROOT / "tools/run_task035_tests.py")
    module = importlib.util.module_from_spec(spec)
    # Historical inventories add sibling paths at import time. They are not
    # collection authority and must not leave precedence behind between files.
    previous_path = sys.path[:]
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = previous_path
    inherited = set(module.runner.NEW + module.runner.AFFECTED)
    extra = sorted({p.relative_to(ROOT).as_posix() for folder in ("tests/compiler", "tests/scene_ir")
                    for p in (ROOT / folder).glob("test*.py")} - inherited - set(NEW) - set(SAFETY))
    return {"new": list(NEW), "native-extra": extra, "safety": list(SAFETY)}, inherited


def cases(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite): yield from cases(test)
        else: yield test


class CollectionError(ValueError):
    """Fixed source-free diagnostic code, never a raw import/exception message."""


COLLECTION_CODES = frozenset({"M1_COLLECTION_SOURCE_PATH", "M1_COLLECTION_SOURCE_MISSING_OR_FOREIGN",
    "M1_COLLECTION_MODULE_NAME", "M1_COLLECTION_FOREIGN_PACKAGE", "M1_COLLECTION_FOREIGN_NAMESPACE",
    "M1_COLLECTION_PACKAGE_PATH", "M1_COLLECTION_FOREIGN_MODULE", "M1_COLLECTION_FOREIGN_TEST_CLASS",
    "M1_COLLECTION_TEST_SOURCE", "M1_COLLECTION_TEST_ID", "M1_COLLECTION_TEST_NAME",
    "M1_COLLECTION_EMPTY_SUITE", "M1_DUPLICATE_TEST_IDENTITY"})
COLLECTION_LOCATIONS = frozenset({"tests/compiler/run_m1_tests.py",
    "tests/compiler/test_comp_build_007.py", "tests/compiler/test_comp_build_008.py",
    "tests/compiler/test_comp_render_integration.py", "tests/compiler/render_test_support.py",
    "tests/compiler/test_comp_h10_001.py", "tests/compiler/test_comp_h4_005.py",
    "bie/compiler/linux_worker.py", "bie/compiler/operational_math.py",
    "bie/compiler/host_toolchain.py", "bie/compiler/generated_code_regression.py"})


def require(value, code):
    if not value:
        raise CollectionError(code)


def source_path(root, relative):
    root = Path(root).resolve()
    path = root / relative
    require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
            "M1_COLLECTION_SOURCE_PATH")
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
            "M1_COLLECTION_SOURCE_MISSING_OR_FOREIGN")
    require(path.suffix == ".py" and all(p.isidentifier() for p in path.relative_to(root).with_suffix("").parts),
            "M1_COLLECTION_MODULE_NAME")
    return path.resolve()


def verify_origin(module, expected):
    expected = Path(expected).resolve()
    require(expected.exists(), "M1_COLLECTION_SOURCE_MISSING_OR_FOREIGN")
    origin = getattr(module, "__file__", None)
    if expected.is_dir():
        init = expected / "__init__.py"
        if init.is_file():
            require(origin is not None and Path(origin).resolve() == init, "M1_COLLECTION_FOREIGN_PACKAGE")
        else:
            require(origin is None and getattr(getattr(module, "__spec__", None), "origin", None) is None,
                    "M1_COLLECTION_FOREIGN_NAMESPACE")
        require({Path(p).resolve() for p in getattr(module, "__path__", ())} == {expected},
                "M1_COLLECTION_PACKAGE_PATH")
    else:
        require(origin is not None and Path(origin).resolve() == expected, "M1_COLLECTION_FOREIGN_MODULE")


@contextmanager
def repository_module(relative, root=ROOT):
    """Real package import with bounded sibling precedence and origin auditing.

    No fabricated parents. Regular and namespace packages come from this root.
    Only this file's sibling directory is temporarily available for the native
    standalone helper convention. Imported local test modules/aliases are removed
    afterward; pre-existing valid modules and parent attributes are restored.
    """
    root = Path(root).resolve(); path = source_path(root, relative)
    parts = path.relative_to(root).with_suffix("").parts
    name = ".".join(parts)
    previous_path, previous_modules = sys.path[:], dict(sys.modules)
    top = parts[0] if len(parts) > 1 else None
    repository_packages = {p.name for p in root.iterdir() if p.is_dir() and p.name.isidentifier()}
    siblings = {p.stem: p.resolve() for p in path.parent.glob("*.py") if p.name != "__init__.py"}
    # Snapshot before importing any new parent: importing a nested package also
    # installs a child attribute on an already-loaded outer package.
    parent_attributes = {key: dict(vars(module)) for key, module in previous_modules.items()
                         if top and module is not None and (key == top or key.startswith(top + "."))}
    origins = {}

    def audit():
        checked = {}
        # Some inherited test sources explicitly install their own repository
        # helper directories. Authenticate those bare helpers too, then restore
        # all path changes and newly imported local aliases at scope exit.
        bare = {}
        for entry in sys.path:
            directory = Path(entry or ".").resolve()
            if directory.is_dir() and directory.is_relative_to(root):
                for candidate in directory.glob("*.py"):
                    if candidate.name != "__init__.py": bare.setdefault(candidate.stem, candidate)
        bare.update(siblings)
        for key, module in list(sys.modules.items()):
            if module is None:
                continue
            expected = None
            if top and (key == top or key.startswith(top + ".")):
                candidate = root.joinpath(*key.split("."))
                expected = candidate if candidate.is_dir() else candidate.with_suffix(".py")
            elif key.split(".", 1)[0] in repository_packages:
                # Inherited preservation tests deliberately load sealed native
                # preimages under private native aliases. Their actual bytes
                # must still be in this checkout; do not invent a .py path from
                # that alias or change the native preservation test contract.
                origin = getattr(module, "__file__", None)
                if origin:
                    actual = Path(origin).resolve()
                    require(actual.is_file() and actual.is_relative_to(root), "M1_COLLECTION_FOREIGN_MODULE")
                    checked[key] = actual.relative_to(root).as_posix()
                    continue
                expected = root.joinpath(*key.split("."))
            elif key in bare:
                expected = bare[key]
            if expected is not None:
                verify_origin(module, expected)
                file = getattr(module, "__file__", None)
                checked[key] = Path(file).resolve().relative_to(root).as_posix() if file else expected.relative_to(root).as_posix() + "/"
        return checked

    try:
        # Fail rather than quietly replacing another checkout or site-packages.
        audit()
        sys.path[:] = [str(root), str(path.parent)] + [p for p in previous_path if p not in {str(root), str(path.parent)}]
        for index in range(1, len(parts)):
            parent_name = ".".join(parts[:index])
            package = importlib.import_module(parent_name)
            verify_origin(package, root.joinpath(*parts[:index]))
        if name in sys.modules:
            verify_origin(sys.modules[name], path)
            # Always execute the requested source, not a cached test alias.
            sys.modules.pop(name)
        importlib.invalidate_caches()
        module = importlib.import_module(name)
        verify_origin(module, path)
        origins.update(audit())
        yield module, origins
        origins.update(audit())
    finally:
        sys.path[:] = previous_path
        for key, module in list(sys.modules.items()):
            file = getattr(module, "__file__", None)
            local_test = bool(file and Path(file).resolve().is_relative_to(root / parts[0])) if top else key in siblings
            if key == name or key in siblings or (top and (key == top or key.startswith(top + "."))) or local_test:
                if key in previous_modules:
                    sys.modules[key] = previous_modules[key]
                else:
                    sys.modules.pop(key, None)
        # Import machinery sets child attributes on packages. Restore those too,
        # without erasing ordinary state mutations made by the inherited tests.
        for key, old in parent_attributes.items():
            package = previous_modules.get(key)
            if package is None:
                continue
            for attr, value in list(vars(package).items()):
                if isinstance(value, type(sys)) and (getattr(value, "__name__", "").startswith(key + ".")):
                    if attr in old: setattr(package, attr, old[attr])
                    else: delattr(package, attr)


def logical_identity(test, root=ROOT):
    """Defining source + class/method; aliases cannot duplicate a logical case."""
    module_name = type(test).__module__
    module = sys.modules.get(module_name)
    origin = getattr(module, "__file__", None)
    require(origin is not None and Path(origin).resolve().is_relative_to(Path(root).resolve()),
            "M1_COLLECTION_FOREIGN_TEST_CLASS")
    relative = Path(origin).resolve().relative_to(Path(root).resolve()).as_posix()
    require(relative.endswith(".py"), "M1_COLLECTION_TEST_SOURCE")
    test_id = test.id()
    require(test_id.startswith(module_name + "."), "M1_COLLECTION_TEST_ID")
    suffix = test_id[len(module_name) + 1:]
    standard = type(test).__qualname__ + "." + test._testMethodName
    require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", standard) is not None, "M1_COLLECTION_TEST_NAME")
    # Explicit custom parameter identities remain distinct without leaking their
    # potentially private values. Standard native identities keep their old form.
    variant = "" if suffix == standard else "::variant_" + hashlib.sha256(suffix.encode()).hexdigest()
    return relative + "::" + standard + variant


def collect_suite(module, root, identities):
    suite = module.selected_suite() if hasattr(module, "selected_suite") else unittest.defaultTestLoader.loadTestsFromModule(module)
    local = [logical_identity(t, root) for t in cases(suite)]
    require(local, "M1_COLLECTION_EMPTY_SUITE")
    require(len(local) == len(set(local)) and not identities.intersection(local), "M1_DUPLICATE_TEST_IDENTITY")
    return suite, local


def collection_diagnostic(exc, root):
    """Literal trusted types and bounded source locations; never format errors."""
    output = {"class": "OTHER", "code": "M1_COLLECTION_EXCEPTION", "location": None, "package_aware": True}
    try:
        allowed = ((ImportError, "ImportError"), (ModuleNotFoundError, "ModuleNotFoundError"),
            (ValueError, "ValueError"), (TypeError, "TypeError"), (SyntaxError, "SyntaxError"),
            (FileNotFoundError, "FileNotFoundError"), (CollectionError, "CollectionError"))
        actual_type = type(exc)
        output["class"] = next((label for cls, label in allowed if actual_type is cls), "OTHER")
        if actual_type is ImportError or actual_type is ModuleNotFoundError:
            output["code"] = "M1_COLLECTION_IMPORT_ERROR"
        elif actual_type is CollectionError:
            arguments = exc.args
            if type(arguments) is tuple and len(arguments) == 1:
                code = arguments[0]
                if type(code) is str and len(code) <= 80 and code in COLLECTION_CODES:
                    output["code"] = code
        # Use the base descriptor, not an overridden foreign traceback getter.
        if not isinstance(exc, BaseException): return output
        tb = BaseException.__traceback__.__get__(exc)
        count = 0
        while tb is not None and count < 64:
            if type(tb) is not TracebackType: return output
            filename, line = tb.tb_frame.f_code.co_filename, tb.tb_lineno
            if type(filename) is not str or len(filename) > 4096: return output
            path = Path(filename).resolve()
            if path.is_relative_to(Path(root).resolve()):
                relative = path.relative_to(Path(root).resolve()).as_posix()
                if (relative in COLLECTION_LOCATIONS
                        and type(line) is int and 1 <= line <= 100000):
                    output["location"] = {"file": relative, "line": line}
            count += 1; tb = tb.tb_next
    except BaseException:
        pass  # Optional observation cannot replace collection's original verdict.
    return output


FAILURE_DIAGNOSTIC_SCHEMA = "bie.task036.m1.test-failure-diagnostic/1"
FAILURE_LOCATIONS = frozenset({"tests/compiler/test_comp_h4_005.py", "bie/compiler/layout_repair.py",
    "bie/compiler/layout_browser.py", "bie/compiler/hardened_scene_compile.py",
    "bie/compiler/host_toolchain.py", "bie/compiler/generated_code_regression.py"})
FAILURE_CODES = frozenset({"HOST_TOOLCHAIN_UNAVAILABLE", "TYPESCRIPT_PARSER_UNAVAILABLE",
    "LAYOUT_BROWSER_UNAVAILABLE", "LAYOUT_BROWSER_TIMEOUT_INVALID", "LAYOUT_BROWSER_NOT_STARTED",
    "LAYOUT_EVIDENCE_ALREADY_EXISTS", "LAYOUT_BROWSER_WORK_BUDGET", "LAYOUT_BRIDGE_FAILED",
    "LAYOUT_BRIDGE_SCOPE_MISMATCH", "LAYOUT_BRIDGE_COVERAGE_MISMATCH",
    "REPAIR_OUTPUT_EXISTS_OR_SYMLINK", "REPAIR_DESTINATION_EXISTS_OR_SYMLINK",
    "REPAIR_PATHS_MUST_BE_SEPARATE", "REPAIR_RESULT_IDENTITY_CHANGED",
    "REPAIR_SOURCE_CHANGED_DURING_PUBLICATION"})


def failure_diagnostic(error, root, lifecycle):
    """Project only fixed enums/booleans and known source locations, never messages.

    H4's unchanged setup assertion can carry a PRIVATE repair result dictionary.
    Only its explicitly typed status and already-classified attempt codes are
    observed. runtime_block/error/stdout/stderr and every other member are unread.
    This is evidence, not a gate verdict or a diagnosis of historical failures.
    """
    output = {"schema": FAILURE_DIAGNOSTIC_SCHEMA, "exception_class": "OTHER",
              "lifecycle": lifecycle if type(lifecycle) is str and lifecycle in {"TEST", "LIFECYCLE"} else "UNKNOWN", "source_locations": [], "repair_observation": None,
              "observation_complete": False}
    try:
        if type(error) is not tuple or len(error) != 3 or not isinstance(error[1], BaseException):
            return output
        exc, tb = error[1], error[2]
        from bie.compiler.qa_common import CompilerQAError
        allowed = ((AssertionError, "AssertionError"), (CompilerQAError, "CompilerQAError"),
            (ValueError, "ValueError"), (TypeError, "TypeError"), (TimeoutError, "TimeoutError"),
            (FileNotFoundError, "FileNotFoundError"), (PermissionError, "PermissionError"),
            (OSError, "OSError"), (subprocess.CalledProcessError, "CalledProcessError"))
        # Identity matching cannot invoke a foreign exception metaclass/name.
        output["exception_class"] = next((label for cls, label in allowed if type(exc) is cls), "OTHER")
        # No exception formatting, chained-message traversal or test repr/id.
        count = 0
        while tb is not None and count < 64:
            if type(tb) is not TracebackType:
                return output
            filename = tb.tb_frame.f_code.co_filename
            if type(filename) is not str or len(filename) > 4096:
                return output
            path = Path(filename).resolve()
            if path.is_relative_to(Path(root).resolve()):
                relative = path.relative_to(Path(root).resolve()).as_posix()
                if relative in FAILURE_LOCATIONS and type(tb.tb_lineno) is int and 1 <= tb.tb_lineno <= 100000:
                    output["source_locations"].append({"file": relative, "line": tb.tb_lineno})
                    output["source_locations"] = output["source_locations"][-4:]
            count += 1; tb = tb.tb_next
        # Strict known H4 boundary only: do not project arbitrary exception args.
        arguments = exc.args if type(exc) is AssertionError else None
        payload = arguments[0] if type(arguments) is tuple and len(arguments) == 1 else None
        if (type(exc) is AssertionError and output["lifecycle"] == "LIFECYCLE"
                and any(p["file"] == "tests/compiler/test_comp_h4_005.py" for p in output["source_locations"])
                and type(payload) is dict):
            schema = payload.get("schema_version")
            if type(schema) is str and schema == "bie.layout-repair-run.v1":
                status = payload.get("status")
                published, fitted = payload.get("source_published"), payload.get("local_fit_passed")
                statuses = {"ENVIRONMENT_OR_VALIDATOR_BLOCKED", "LOCAL_MEASURED_CANDIDATE", "UPSTREAM_REVISION_REQUIRED"}
                observation = {"status": status if type(status) is str and status in statuses else "UNKNOWN",
                    "source_published": published if type(published) is bool else None,
                    "local_fit_passed": fitted if type(fitted) is bool else None,
                    "attempts": [], "attempts_available": False}
                rows = payload.get("attempts")
                bounded_rows = rows[:33] if type(rows) is list else None
                if bounded_rows is not None and len(bounded_rows) <= 32:
                    for row in bounded_rows:
                        if type(row) is not dict: break
                        codes = row.get("codes")
                        bounded_codes = codes[:33] if type(codes) is list else None
                        source_passed, fit_passed = row.get("source_gate_passed"), row.get("local_fit_passed")
                        codes_available = bounded_codes is not None and len(bounded_codes) <= 32
                        safe_codes = []
                        if codes_available:
                            safe_codes = [c if type(c) is str and c in FAILURE_CODES else "UNCLASSIFIED" for c in bounded_codes]
                        observation["attempts"].append({
                            "source_gate_passed": source_passed if type(source_passed) is bool else None,
                            "local_fit_passed": fit_passed if type(fit_passed) is bool else None,
                            "codes": safe_codes, "codes_available": codes_available})
                    else: observation["attempts_available"] = True
                output["repair_observation"] = observation
        output["observation_complete"] = True
    except BaseException:
        # Diagnostic failure never replaces a unittest error or masks its verdict.
        output["observation_complete"] = False
    return output


class SafeFailureResult(unittest.TextTestResult):
    def __init__(self, *args, diagnostic_root=ROOT, **kwargs):
        super().__init__(*args, **kwargs)
        self.diagnostic_root = diagnostic_root
        self.safe_diagnostics = []

    def observe(self, test, error):
        lifecycle = "UNKNOWN"
        try:
            lifecycle = "TEST" if isinstance(test, unittest.TestCase) else "LIFECYCLE"
            self.safe_diagnostics.append(failure_diagnostic(error, self.diagnostic_root, lifecycle))
        except BaseException:
            try:
                self.safe_diagnostics.append({"schema": FAILURE_DIAGNOSTIC_SCHEMA,
                    "exception_class": "OTHER", "lifecycle": lifecycle, "source_locations": [],
                    "repair_observation": None, "observation_complete": False})
            except BaseException:
                pass  # Even a failed diagnostic sink cannot terminate the suite.

    def addError(self, test, error):
        super().addError(test, error)
        self.observe(test, error)

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.observe(test, error)

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error is not None: self.observe(test, error)


def run_file(path, identities, root=ROOT):
    row = {"file": path, "selected": 0, "executed": 0, "failures": 0, "errors": 0, "skips": 0,
           "collection_errors": 0, "failure_diagnostics": []}
    capture = io.StringIO()
    try:
        with redirect_stdout(capture), redirect_stderr(capture), repository_module(path, root) as (module, origins):
            suite, local = collect_suite(module, root, identities)
            identities.update(local); row["selected"] = len(local)
            row["logical_identities"] = local
            labels = {id(test): identity for test, identity in zip(cases(suite), local)}
            result = unittest.TextTestRunner(stream=capture,
                resultclass=lambda *a, **k: SafeFailureResult(*a, diagnostic_root=root, **k)).run(suite)
            row.update(executed=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                skips=len(result.skipped), failed_methods=[labels.get(id(t), labels.get(id(getattr(t, "test_case", None)),
                    "M1_TEST_LIFECYCLE_ERROR")) for t, _ in result.failures + result.errors],
                failure_diagnostics=result.safe_diagnostics)
        row["import_origins"] = origins
        row["import_origins_verified"] = True
    except Exception as exc:
        row["collection_errors"] = 1
        try:
            row["collector_error"] = collection_diagnostic(exc, root)
        except BaseException:
            row["collector_error"] = {"class": "OTHER", "code": "M1_COLLECTION_EXCEPTION",
                "location": None, "package_aware": True}
    finally:
        capture.close()
    row["passed"] = row["selected"] > 0 and row["executed"] == row["selected"] and not any(row[k] for k in ("failures", "errors", "skips", "collection_errors"))
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=("new", "native-extra", "safety"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected, inherited = inventory()
    rows, identities = [], set()
    started = time.monotonic()
    for path in selected[args.lane]:
        row = run_file(path, identities)
        rows.append(row); print(json.dumps(row, sort_keys=True), flush=True)
    summary = {k: sum(r[k] for r in rows) for k in ("selected","executed","failures","errors","skips","collection_errors")}
    summary.update(passed=bool(rows) and all(r["passed"] for r in rows), platform=platform.system(),
        lane=args.lane, source_files=len(rows), unique_identity_sha256=hashlib.sha256("\n".join(sorted(identities)).encode()).hexdigest(),
        elapsed_s=round(time.monotonic()-started,3), diagnostic_repeats_counted=False, product_accepted=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"summary":summary,"results":rows},indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True)); return 0 if summary["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
