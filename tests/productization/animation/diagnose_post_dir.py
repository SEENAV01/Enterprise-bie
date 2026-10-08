"""Task035 CI-R1 observations only; never substitutes for a regression gate.

Run unchanged synthetic Post-DIR tests in fresh interpreters at exact base and
candidate roots. Keep exception messages/source lines/raw output private; emit
only fixed allowlists and repository-relative canonical stack locations. This
does not install the suspected compiler prerequisites or alter test assertions.
"""
from __future__ import annotations

import argparse
import contextlib
from hashlib import sha1, sha256
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import unittest

BASE = "46977a2fb1d43fb655fb4be01d93a34f6151af09"
ROOT = Path(__file__).resolve().parents[3]
TEST_FILE = "tests/post_dir/test_canonical_adoption.py"
METHODS = (
    "test_actual_cross_section_source_publication",
    "test_actual_dsl_output_compiles_to_source",
)
TEST_METHODS = frozenset(METHODS) | {
    "test_all_supplied_names_retained", "test_no_same_name_overwrite",
    "test_every_supplied_file_exact", "test_source_mapping_exact",
    "test_rebuild_and_history_not_conflated", "test_missing_historical_bytes_not_fabricated",
    "test_canonical_alias_layer_preserved", "test_old_scene_contract_retained",
    "test_required_workers_live_in_canonical_tree", "test_known_cross_section_amendments_recorded",
    "test_existing_enterprise_families_still_discovered", "test_vis_alias_same_class",
    "test_ani_alias_same_class", "test_dsl_alias_same_class", "test_comp_alias_same_function",
    "test_actual_vis_producer_consumed_by_ani", "test_actual_ani_producer_consumed_by_dsl",
    "test_source_and_reasoning_refs_survive", "test_handoff_cannot_claim_acceptance",
    "test_stale_vis_handoff_blocks_before_downstream",
}
BLOBS = {
    TEST_FILE: "6801194add84de0f752a18aaac86c8c4005bebce",
    "bie/compiler/hardened_scene_compile.py": "082745cdc787495e68b419526a6d7008a38bb0c5",
    "bie/compiler/host_toolchain.py": "9c113ec948a9324cf76032f2de937a6ae27e8cf5",
    "bie/compiler/generated_code_regression.py": "1d350a3676728256653c26b2d94bead339704e6d",
}
TRACE_PATHS = frozenset(BLOBS) | {
    "bie/compiler/operational_math.py", "bie/compiler/isolated_math_worker.py",
    "bie/compiler/linux_worker.py", "bie/compiler/render_process.py",
    "bie/compiler/qa_scene_compile.py", "bie/compiler/generated_lint.py",
    "bie/compiler/generated_static_analysis.py", "bie/compiler/qa_common.py",
    "scripts/verify_post_dir.py",
}
PACKAGES = {
    "matplotlib": "matplotlib", "numpy": "numpy", "PIL": "pillow",
    "pyparsing": "pyparsing", "cycler": "cycler", "kiwisolver": "kiwisolver",
    "contourpy": "contourpy", "fontTools": "fonttools", "packaging": "packaging",
    "dateutil": "python-dateutil", "playwright": "playwright", "pypdf": "pypdf",
    "pdfplumber": "pdfplumber", "pymupdf": "PyMuPDF", "jsonschema": "jsonschema",
    "cryptography": "cryptography", "fastapi": "fastapi", "uvicorn": "uvicorn",
    "httpx": "httpx",
}
CLASSES = frozenset({
    "CompilerQAError", "BuildError", "ModuleNotFoundError", "ImportError",
    "PackageNotFoundError", "AssertionError", "FileNotFoundError", "PermissionError",
    "OSError", "RuntimeError", "ValueError", "TypeError", "KeyError",
    "TimeoutError", "TimeoutExpired", "CalledProcessError",
})
CODES = frozenset({
    "HOST_TOOLCHAIN_UNAVAILABLE", "TOOLCHAIN_CHANGED_DURING_HASH",
    "H3_TOOLCHAIN_CHANGED_DURING_COMPILE", "H3_SOURCE_PUBLICATION_BLOCKED",
    "H3_HOST_IDENTITY_CHANGED", "H3_REVALIDATION_BLOCKED", "HOST_IDENTITY_INVALID",
    "HOST_IDENTITY_TAMPERED", "TYPESCRIPT_PARSER_UNAVAILABLE", "TYPESCRIPT_PROBE_FAILED",
    "MATH_OPERATIONAL_WORKER_BLOCKED", "MATH_OPERATIONAL_REPORT_MISMATCH",
    "MATH_HOST_CHANGED", "MATH_INPUT_LIMIT", "MATH_OUTPUT_LIMIT",
    "ISOLATION_UNAVAILABLE", "ISOLATION_REQUIRED", "SANDBOX_UNAVAILABLE",
})
MISSING_MODULES = frozenset(PACKAGES) | {"fcntl", "resource", "seccomp"}
CHILD_TIMEOUT_SECONDS = 120
MAX_RECEIPT_BYTES = 128 * 1024


def safe_version(value: object) -> str:
    """Versions are observations, never arbitrary subprocess text."""
    value = str(value)
    return value if len(value) <= 64 and re.fullmatch(
        r"[0-9]+(?:\.[0-9]+){0,4}(?:(?:a|b|rc)[0-9]+)?(?:\.post[0-9]+)?(?:\.dev[0-9]+)?", value) else "UNKNOWN"


def safe_exception(exc: BaseException, root: Path) -> dict:
    """Inspect actual exception chains without exporting messages or source."""
    rows = []
    seen = set()
    current = exc
    while current is not None and id(current) not in seen and len(rows) < 8:
        seen.add(id(current))
        name = type(current).__name__
        message = str(current)[:8192]
        codes = sorted(code for code in CODES if re.search(
            r"(?<![A-Z0-9_])" + re.escape(code) + r"(?![A-Z0-9_])", message))
        missing = getattr(current, "name", None)
        frames = []
        tb = current.__traceback__
        while tb is not None:
            path = Path(tb.tb_frame.f_code.co_filename).resolve()
            try:
                relative = path.relative_to(root).as_posix()
            except ValueError:
                relative = None
            if relative in TRACE_PATHS:
                frames.append({"path": relative, "line": tb.tb_lineno})
            tb = tb.tb_next
        rows.append({"class": name if name in CLASSES else "OTHER_EXCEPTION",
                     "codes": codes or ["UNCLASSIFIED"],
                     "missing_module": missing if missing in MISSING_MODULES else None,
                     "canonical_frames": frames[-20:]})
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    return {"chain": rows}


def canonical_origins(root: Path) -> dict:
    """An editable candidate install must not contaminate base module imports."""
    checked = 0
    outside = 0
    for name, module in tuple(sys.modules.items()):
        if not any(name == prefix or name.startswith(prefix + ".")
                   for prefix in ("bie", "app.bie", "scripts")):
            continue
        locations = []
        if getattr(module, "__file__", None):
            locations.append(module.__file__)
        locations.extend(getattr(module, "__path__", ()))
        for location in locations:
            checked += 1
            if not Path(location).resolve().is_relative_to(root):
                outside += 1
    return {"checked_locations": checked, "foreign_locations": outside,
            "valid": checked > 0 and outside == 0}


class PrivateVerboseBuffer(io.StringIO):
    """A bounded private verbose unittest stream, never returned or uploaded."""
    def write(self, value: str) -> int:
        remaining = 64 * 1024 - self.tell()
        if remaining > 0:
            super().write(value[:remaining])
        return len(value)


class SafeResult(unittest.TextTestResult):
    def __init__(self, *args, root: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = root
        self.observations = []

    def record(self, test, kind, err):
        # The method name is accepted only from the unchanged sealed test file.
        method = getattr(test, "_testMethodName", None)
        self.observations.append({"kind": kind,
                                  "method": method if method in self.allowed_methods else "UNIDENTIFIED_TEST",
                                  "exception": safe_exception(err[1], self.root)})

    def addError(self, test, err):
        self.record(test, "ERROR", err)
        super().addError(test, err)

    def addFailure(self, test, err):
        self.record(test, "FAILURE", err)
        super().addFailure(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.record(test, "SUBTEST_ERROR", err)
        super().addSubTest(test, subtest, err)


def child_test(root: Path, selection: str) -> dict:
    for path, expected in BLOBS.items():
        raw = (root / path).read_bytes()
        normalized = raw.replace(b"\r\n", b"\n")
        identities = {sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
                      for data in (raw, normalized)}
        if expected not in identities:
            raise ValueError("UNCHANGED_SOURCE_BYTES_REQUIRED")
    if canonical_origins(root)["foreign_locations"]:
        raise ValueError("FOREIGN_CANONICAL_IMPORT")
    # -I excludes CWD/PYTHONPATH. Add exactly the selected exported/root checkout.
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("task035_unchanged_post_dir", root / TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loader = unittest.TestLoader()
    suite = (loader.loadTestsFromModule(module) if selection == "whole_file" else
             loader.loadTestsFromName("CanonicalIdentityAndHandoff." + selection, module))
    expected = 22 if selection == "whole_file" else 1
    allowed = set()
    for cls in (module.PreservedInputs, module.CanonicalIdentityAndHandoff):
        allowed.update(loader.getTestCaseNames(cls))
    if allowed != TEST_METHODS:
        raise ValueError("UNCHANGED_TEST_INVENTORY_REQUIRED")
    private = PrivateVerboseBuffer()

    def result_factory(*args, **kwargs):
        result = SafeResult(*args, root=root, **kwargs)
        result.allowed_methods = allowed
        return result

    result = unittest.TextTestRunner(stream=private, verbosity=2, resultclass=result_factory).run(suite)
    private.close()
    origins = canonical_origins(root)
    valid = result.testsRun == expected and origins["valid"]
    return {"observation_valid": valid,
            "outcome": ("PASS" if result.wasSuccessful() and not result.skipped else "FAIL") if valid else "UNKNOWN",
            "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "skips": len(result.skipped), "diagnostics": result.observations,
            "canonical_module_origins": origins}


def tool_version(name: str) -> dict:
    executable = shutil.which(name)
    if executable is None:
        return {"available": False, "version": None}
    try:
        # Fixed version-only commands, bounded time and private output.
        completed = subprocess.run([executable, "--version"], capture_output=True, timeout=10, check=False)
        text = completed.stdout[:256].decode("ascii", errors="replace").strip()
        pattern = r"v([0-9][A-Za-z0-9.+_-]{0,63})" if name == "node" else r"Version ([0-9][A-Za-z0-9.+_-]{0,63})"
        matched = re.fullmatch(pattern, text)
        return {"available": True, "version": safe_version(matched.group(1)) if completed.returncode == 0 and matched else "UNKNOWN"}
    except (OSError, subprocess.SubprocessError):
        return {"available": True, "version": "UNKNOWN"}


def environment_observation(provisioning_phase: str = "original") -> dict:
    if provisioning_phase not in {"original", "approved_after"}:
        raise ValueError("UNKNOWN_PROVISIONING_PHASE")
    dependencies = {}
    for module, distribution in PACKAGES.items():
        try:
            available = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            available = False
        try:
            version = safe_version(importlib.metadata.version(distribution))
        except importlib.metadata.PackageNotFoundError:
            version = None
        dependencies[module] = {"import_spec_available": available, "distribution_version": version}
    tsc = shutil.which("tsc")
    library = Path(tsc).resolve().parent.parent / "lib/typescript.js" if tsc else None
    executable = Path(sys.executable).resolve()
    # Executable identity is reported without disclosing a user-specific path.
    executable_hash = sha256(executable.read_bytes()).hexdigest()
    os_id = os_version = "UNKNOWN"
    if platform.system() == "Linux":
        release = platform.freedesktop_os_release()
        os_id = release.get("ID", "UNKNOWN")
        if os_id not in {"ubuntu", "debian", "fedora", "alpine"}:
            os_id = "OTHER"
        os_version = safe_version(release.get("VERSION_ID", "UNKNOWN"))
    return {"os": platform.system() if platform.system() in {"Linux", "Windows", "Darwin"} else "OTHER",
            "os_id": os_id, "os_version": os_version,
            "python_version": safe_version(platform.python_version()),
            "python_executable_role": "SAME_INTERPRETER_AS_MANDATORY_WORKFLOW_STEPS",
            "python_executable_sha256": executable_hash,
            "isolated_python": bool(sys.flags.isolated),
            "dependencies": dependencies, "node": tool_version("node"), "tsc": tool_version("tsc"),
            "canonical_typescript_library_present": bool(library and library.is_file()),
            "canonical_python_prefix_present": Path("/opt/pyvenv/bin/python3.13").is_file() if os.name == "posix" else False,
            "canonical_node_prefix_present": Path("/opt/nvm/versions/node/v22.16.0/bin/node").is_file() if os.name == "posix" else False,
            "unshare_available": shutil.which("unshare") is not None,
            "bubblewrap_available": shutil.which("bwrap") is not None,
            "provisioning_changed": provisioning_phase == "approved_after",
            "provisioning_phase": provisioning_phase}


def _validate_child_receipt(value: object, selection: str) -> bool:
    """Fail closed on missing counts, unknown/private keys, and invented PASS."""
    keys = {"observation_valid", "outcome", "tests", "failures", "errors", "skips",
            "diagnostics", "canonical_module_origins"}
    if not isinstance(value, dict) or set(value) != keys:
        return False
    if selection not in (*METHODS, "whole_file"):
        return False
    expected = 22 if selection == "whole_file" else 1
    if any(type(value[key]) is not int or not 0 <= value[key] <= 100 for key in
           ("tests", "failures", "errors", "skips")) or value["tests"] != expected:
        return False
    if value["failures"] + value["errors"] + value["skips"] > expected:
        return False
    origins = value["canonical_module_origins"]
    if not isinstance(origins, dict) or set(origins) != {"checked_locations", "foreign_locations", "valid"}:
        return False
    if (type(origins["checked_locations"]) is not int or not 0 < origins["checked_locations"] <= 10000
            or type(origins["foreign_locations"]) is not int or origins["foreign_locations"] != 0
            or origins["valid"] is not True or value["observation_valid"] is not True):
        return False
    diagnostics = value["diagnostics"]
    if not isinstance(diagnostics, list) or len(diagnostics) != value["failures"] + value["errors"]:
        return False
    for row in diagnostics:
        if (not isinstance(row, dict) or set(row) != {"kind", "method", "exception"}
                or row["kind"] not in {"ERROR", "FAILURE", "SUBTEST_ERROR"}
                or row["method"] not in (TEST_METHODS if selection == "whole_file" else {selection})):
            return False
        exception = row["exception"]
        if not isinstance(exception, dict) or set(exception) != {"chain"}:
            return False
        chain = exception["chain"]
        if not isinstance(chain, list) or not 1 <= len(chain) <= 8:
            return False
        for entry in chain:
            if not isinstance(entry, dict) or set(entry) != {"class", "codes", "missing_module", "canonical_frames"}:
                return False
            if entry["class"] not in CLASSES | {"OTHER_EXCEPTION"}:
                return False
            if (not isinstance(entry["codes"], list) or not 1 <= len(entry["codes"]) <= len(CODES)
                    or any(code not in CODES | {"UNCLASSIFIED"} for code in entry["codes"])
                    or entry["missing_module"] not in MISSING_MODULES | {None}):
                return False
            frames = entry["canonical_frames"]
            if not isinstance(frames, list) or len(frames) > 20:
                return False
            for frame in frames:
                if (not isinstance(frame, dict) or set(frame) != {"path", "line"}
                        or frame["path"] not in TRACE_PATHS or type(frame["line"]) is not int
                        or not 0 < frame["line"] < 1000000):
                    return False
    outcome = "PASS" if value["failures"] == value["errors"] == value["skips"] == 0 else "FAIL"
    return value["outcome"] == outcome


def validate_child_receipt(value: object, selection: str) -> bool:
    try:
        return _validate_child_receipt(value, selection)
    except (TypeError, ValueError, KeyError):
        return False


def run_child(root: Path, selection: str, destination: Path) -> dict:
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
               "--child-root", str(root), "--selection", selection, "--output", str(destination)]
    # Child stdout/stderr can contain paths or generated source. Never retain it.
    process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=os.name == "posix")
    try:
        code = process.wait(timeout=CHILD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=10)
        return {"observation_valid": False, "outcome": "UNKNOWN", "diagnostic_status": "TIMEOUT"}
    if code != 0 or not destination.is_file() or not 0 < destination.stat().st_size <= MAX_RECEIPT_BYTES:
        return {"observation_valid": False, "outcome": "UNKNOWN", "diagnostic_status": "CHILD_RECEIPT_UNAVAILABLE"}
    try:
        result = json.loads(destination.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        return {"observation_valid": False, "outcome": "UNKNOWN", "diagnostic_status": "INVALID_CHILD_RECEIPT"}
    if not validate_child_receipt(result, selection):
        return {"observation_valid": False, "outcome": "UNKNOWN", "diagnostic_status": "INVALID_CHILD_RECEIPT"}
    return result


def git_text(*args: str) -> str:
    value = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, timeout=30, check=True)
    return value.stdout.decode("ascii").strip()


def collect(provisioning_phase: str = "original") -> dict:
    if provisioning_phase not in {"original", "approved_after"}:
        raise ValueError("UNKNOWN_PROVISIONING_PHASE")
    identities = {}
    for path, expected in BLOBS.items():
        base = git_text("rev-parse", BASE + ":" + path)
        candidate = git_text("rev-parse", "HEAD:" + path)
        working = git_text("hash-object", path)
        if base != expected or candidate != expected or working != expected:
            raise ValueError("UNCHANGED_BLOB_IDENTITY_REQUIRED")
        identities[path] = {"base_blob": base, "candidate_blob": candidate, "working_blob": working, "equal": True}
    head = git_text("rev-parse", "HEAD")
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("INVALID_HEAD_IDENTITY")
    receipt = {"schema": "bie.task035.post-dir-diagnostic/1", "scope": "SYNTHETIC_TEST_DIAGNOSTICS_ONLY",
               "original_run_traceback_recovered": False, "base": BASE, "candidate": head,
               "unchanged_blobs": identities, "environment": environment_observation(provisioning_phase),
               "probes": [], "mandatory_regression_substituted": False, "product_accepted": False}
    with tempfile.TemporaryDirectory(prefix="bie-task035-ci-r1-") as temporary:
        private = Path(temporary)
        archive = private / "base.tar"
        base_root = private / "base"
        base_root.mkdir()
        with archive.open("wb") as output:
            subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", BASE], stdout=output,
                           stderr=subprocess.DEVNULL, timeout=120, check=True)
        with tarfile.open(archive) as source:
            source.extractall(base_root, filter="data")
        for label, root in (("candidate", ROOT), ("base", base_root)):
            for index, selection in enumerate((*METHODS, "whole_file")):
                result = run_child(root, selection, private / f"{label}-{index}.json")
                receipt["probes"].append({"root": label, "selection": selection, **result})
    receipt["diagnostics_complete"] = all(row["observation_valid"] for row in receipt["probes"])
    receipt["test_outcome"] = ("PASS" if all(row["outcome"] == "PASS" for row in receipt["probes"])
                               else "FAIL" if receipt["diagnostics_complete"] else "UNKNOWN")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--child-root", type=Path)
    parser.add_argument("--selection", choices=(*METHODS, "whole_file"))
    args = parser.parse_args()
    try:
        if args.child_root is not None:
            if args.selection is None:
                raise ValueError("CHILD_SELECTION_REQUIRED")
            with open(os.devnull, "w", encoding="utf-8") as private:
                with contextlib.redirect_stdout(private), contextlib.redirect_stderr(private):
                    receipt = child_test(args.child_root.resolve(strict=True), args.selection)
        else:
            receipt = collect()
    except Exception as exc:
        receipt = {"observation_valid": False, "diagnostics_complete": False,
                   "outcome": "UNKNOWN", "diagnostic_status": "COLLECTION_FAILED",
                   "exception": safe_exception(exc, ROOT), "product_accepted": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Observed test failures are data, not suppressed mandatory gate failures.
    complete = receipt.get("observation_valid") if args.child_root else receipt.get("diagnostics_complete")
    return 0 if complete is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
