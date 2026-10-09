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
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
NEW = ("tests/compiler/test_producer_motion_m1.py", "tests/compiler/test_motion_m1_preservation.py",
       "tests/compiler/test_motion_m1_evidence.py", "tests/compiler/test_m1_runner_loading.py",
       "tests/compiler/test_m1_safe_paint_diagnostics.py")
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
    code = str(exc) if isinstance(exc, CollectionError) and str(exc) in COLLECTION_CODES else "M1_COLLECTION_IMPORT_ERROR" if isinstance(exc, ImportError) else "M1_COLLECTION_EXCEPTION"
    allowed = {"ImportError", "ModuleNotFoundError", "ValueError", "TypeError", "SyntaxError", "FileNotFoundError", "CollectionError"}
    location = None; tb = exc.__traceback__
    while tb:
        path = Path(tb.tb_frame.f_code.co_filename).resolve()
        if path.is_relative_to(Path(root).resolve()):
            location = {"file": path.relative_to(Path(root).resolve()).as_posix(), "line": tb.tb_lineno}
        tb = tb.tb_next
    return {"class": type(exc).__name__ if type(exc).__name__ in allowed else "OTHER", "code": code,
            "location": location, "package_aware": True}


def run_file(path, identities, root=ROOT):
    row = {"file": path, "selected": 0, "executed": 0, "failures": 0, "errors": 0, "skips": 0,
           "collection_errors": 0}
    capture = io.StringIO()
    try:
        with redirect_stdout(capture), redirect_stderr(capture), repository_module(path, root) as (module, origins):
            suite, local = collect_suite(module, root, identities)
            identities.update(local); row["selected"] = len(local)
            row["logical_identities"] = local
            labels = {id(test): identity for test, identity in zip(cases(suite), local)}
            result = unittest.TextTestRunner(stream=capture).run(suite)
            row.update(executed=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                skips=len(result.skipped), failed_methods=[labels.get(id(t), labels.get(id(getattr(t, "test_case", None)),
                    "M1_TEST_LIFECYCLE_ERROR")) for t, _ in result.failures + result.errors])
        row["import_origins"] = origins
        row["import_origins_verified"] = True
    except Exception as exc:
        row.update(collection_errors=1, collector_error=collection_diagnostic(exc, root))
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
