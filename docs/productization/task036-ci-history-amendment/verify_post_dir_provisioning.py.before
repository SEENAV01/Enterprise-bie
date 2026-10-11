"""Task035 CI-R2 strict AFTER gate; no production compiler or test replacements.

Reuse the real R1 six-probe harness. All runtime observations are finite and
source-free; executable/library origins are checked privately and exposed only
as roles, booleans and SHA256 identities. Completion is never equivalent to PASS.
"""
from __future__ import annotations

import argparse
import contextlib
from hashlib import sha1, sha256
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "task035_ci_r2_original_diagnostics", Path(__file__).with_name("diagnose_post_dir.py"))
diagnostics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diagnostics)
PHASE = "approved_after"
SCHEMA = "bie.task035.post-dir-after/1"
SCOPE = "SYNTHETIC_TEST_PROVISIONING_GATE_ONLY"
PROFILE_BLOBS = {
    "requirements-comp-h3.txt": "c0b36a1f5f9d3bc898a0a1954bf23bcd0ba55397",
    ".integration/tools/requirements-validation.txt": "c0b36a1f5f9d3bc898a0a1954bf23bcd0ba55397",
    "requirements-qa-section16-validation.txt": "253a91bfb7b4793fd4cb88705288f4f677158c8f",
    "pyproject.toml": "491ba3d5e007e3510da820e3bb3ae21008fe85a6",
    "bie/compiler/render_process.py": "b140256eb6eb62cfc4d18dc7142911a5d356020d",
    ".integration/tools/setup_ci_environment.sh": "99f1fbe9312c0dc8ad0fc5e7a1c358c713354b94",
    ".github/workflows/post-dir-canonical-catchup.yml": "3f95bbff25fa7e9cd18d054eb5bee04d76933655",
}
APPROVED_PACKAGES = {
    "matplotlib": ("matplotlib", "3.10.8"), "numpy": ("numpy", "2.3.5"),
    "PIL": ("pillow", "12.3.0"), "pyparsing": ("pyparsing", "3.3.2"),
    "cycler": ("cycler", "0.12.1"), "kiwisolver": ("kiwisolver", "1.5.0"),
    "contourpy": ("contourpy", "1.3.3"), "fontTools": ("fonttools", "4.63.0"),
    "packaging": ("packaging", "25.0"), "dateutil": ("python-dateutil", "2.9.0.post0"),
    "playwright": ("playwright", "1.57.0"), "pypdf": ("pypdf", "6.19.0"),
    "pdfplumber": ("pdfplumber", "0.11.10"), "pymupdf": ("PyMuPDF", "1.26.7"),
    "jsonschema": ("jsonschema", "4.26.0"), "cryptography": ("cryptography", "46.0.4"),
    "fastapi": ("fastapi", "0.141.1"), "uvicorn": ("uvicorn", "0.53.0"),
    "httpx": ("httpx", "0.28.1"),
}


def _digest_file(path: Path) -> str:
    value = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _is_sha(value: object, length: int = 64) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{%d}" % length, value) is not None


def approved_profiles() -> dict:
    """Bind the observed version map to unchanged canonical setup inputs."""
    for relative, expected in PROFILE_BLOBS.items():
        data = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        if sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest() != expected:
            raise ValueError("APPROVED_PROFILE_IDENTITY_MISMATCH")
    left = (ROOT / "requirements-comp-h3.txt").read_bytes()
    right = (ROOT / ".integration/tools/requirements-validation.txt").read_bytes()
    if left != right:
        raise ValueError("APPROVED_PROFILE_EQUIVALENCE_REQUIRED")
    requirements = []
    for relative in ("requirements-comp-h3.txt", "requirements-qa-section16-validation.txt"):
        requirements.extend(line.strip() for line in (ROOT / relative).read_text().splitlines()
                            if line.strip() and not line.lstrip().startswith("#"))
    extras = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["optional-dependencies"]
    for extra in ("document-intelligence", "document-intelligence-layout", "api", "api-test"):
        requirements.extend(extras[extra])
    observed = {}
    for item in requirements:
        name, separator, version = item.partition("==")
        if not separator or diagnostics.safe_version(version) == "UNKNOWN":
            raise ValueError("APPROVED_PROFILE_PIN_REQUIRED")
        key = name.lower()
        if key in observed and observed[key] != version:
            raise ValueError("APPROVED_PROFILE_VERSION_CONFLICT")
        observed[key] = version
    if observed != {distribution.lower(): version for distribution, version in APPROVED_PACKAGES.values()}:
        raise ValueError("APPROVED_PROFILE_VERSION_MISMATCH")
    return dict(PROFILE_BLOBS)


def runtime_preflight() -> dict:
    """Execute real imports, pip check and parser with canonical sanitized PATH."""
    profiles = approved_profiles()
    interpreter = Path(sys.executable).resolve(strict=True)
    shell_python = shutil.which("python")
    dependencies = {}
    for module, (distribution, expected) in APPROVED_PACKAGES.items():
        row = {"distribution": distribution, "expected_version": expected,
               "distribution_version": None, "importable": False,
               "origin_in_interpreter": False, "origin_sha256": None}
        try:
            imported = importlib.import_module(module)
            origin = Path(imported.__file__).resolve(strict=True)
            row.update(distribution_version=diagnostics.safe_version(importlib.metadata.version(distribution)),
                       importable=True, origin_in_interpreter=origin.is_relative_to(Path(sys.prefix).resolve()),
                       origin_sha256=_digest_file(origin))
        except Exception as exc:
            row["exception"] = diagnostics.safe_exception(exc, ROOT)
        dependencies[module] = row
    # Import only the verified canonical process/parser adapters; base comparison
    # executes in independent -I child interpreters, not this module namespace.
    sys.path.insert(0, str(ROOT))
    from bie.compiler.render_process import run_bounded_process
    from bie.compiler.generated_code_regression import _typescript_library
    pip = run_bounded_process((str(interpreter), "-m", "pip", "check"), cwd=ROOT,
                              timeout_s=60, max_output_bytes=64 * 1024)
    node_path, tsc_path = shutil.which("node"), shutil.which("tsc")
    node = {"version": "UNKNOWN", "executable_sha256": None,
            "path_executable_matches": False, "tsc_version": "UNKNOWN",
            "typescript_version": "UNKNOWN", "typescript_library_sha256": None,
            "library_resolution_matches": False, "sanitized_environment_used": True,
            "parser_library_loaded": False}
    library = _typescript_library(None)
    if node_path and tsc_path and library:
        executable = Path(node_path).resolve(strict=True)
        library = library.resolve(strict=True)
        resolved = Path(tsc_path).resolve(strict=True).parent.parent / "lib/typescript.js"
        # No raw output/path is exported. This loads the same real JS library as
        # the native source probe and verifies the binary that actually ran it.
        script = ("const ts=require(process.argv[1]);process.stdout.write(JSON.stringify({"
                  "node:process.versions.node,typescript:ts.version,executable:process.execPath,"
                  "library:require.resolve(process.argv[1])}));")
        actual = run_bounded_process((str(executable), "-e", script, str(library)), cwd=ROOT,
                                    timeout_s=10, max_output_bytes=64 * 1024)
        if actual.process.passed:
            raw = json.loads(actual.process.stdout)
            if set(raw) != {"node", "typescript", "executable", "library"}:
                raise ValueError("SOURCE_PARSER_OBSERVATION_INVALID")
            node.update(version=diagnostics.safe_version(raw["node"]),
                        executable_sha256=_digest_file(executable),
                        path_executable_matches=Path(raw["executable"]).resolve(strict=True) == executable,
                        typescript_version=diagnostics.safe_version(raw["typescript"]),
                        typescript_library_sha256=_digest_file(library),
                        library_resolution_matches=resolved.resolve(strict=True) == library ==
                        Path(raw["library"]).resolve(strict=True), parser_library_loaded=True)
        tsc = run_bounded_process((str(executable), str(Path(tsc_path).resolve(strict=True)), "--version"),
                                 cwd=ROOT, timeout_s=10, max_output_bytes=64 * 1024)
        match = re.fullmatch(r"Version ([0-9.]+)\s*", tsc.process.stdout) if tsc.process.passed else None
        node["tsc_version"] = diagnostics.safe_version(match.group(1)) if match else "UNKNOWN"
    release = platform.freedesktop_os_release() if platform.system() == "Linux" else {}
    return {"os": platform.system() if platform.system() in {"Linux", "Windows", "Darwin"} else "OTHER",
            "os_id": release.get("ID") if release.get("ID") in {"ubuntu", "debian", "fedora", "alpine"} else "UNKNOWN",
            "os_version": diagnostics.safe_version(release.get("VERSION_ID", "UNKNOWN")),
            "python": {"version": diagnostics.safe_version(platform.python_version()),
                       "executable_sha256": _digest_file(interpreter),
                       "role": "SAME_INTERPRETER_AS_MANDATORY_WORKFLOW_STEPS",
                       "path_python_matches": bool(shell_python and Path(shell_python).resolve() == interpreter),
                       "isolated": bool(sys.flags.isolated)},
            "profile_blobs": profiles, "requirements_identical": True,
            "packages": dependencies, "pip_check_passed": pip.process.passed,
            "node": node, "provisioning_phase": PHASE, "provisioning_changed": True}


def validate_runtime(value: object) -> bool:
    try:
        if not isinstance(value, dict) or set(value) != {"os", "os_id", "os_version", "python", "profile_blobs",
                "requirements_identical", "packages", "pip_check_passed", "node", "provisioning_phase", "provisioning_changed"}:
            return False
        if (value["os"], value["os_id"], value["os_version"]) != ("Linux", "ubuntu", "24.04"):
            return False
        if value["profile_blobs"] != PROFILE_BLOBS or value["requirements_identical"] is not True:
            return False
        if value["pip_check_passed"] is not True or value["provisioning_phase"] != PHASE or value["provisioning_changed"] is not True:
            return False
        python = value["python"]
        if not isinstance(python, dict) or set(python) != {"version", "executable_sha256", "role", "path_python_matches", "isolated"}:
            return False
        if (python["version"] != "3.13.5" or not _is_sha(python["executable_sha256"])
                or python["role"] != "SAME_INTERPRETER_AS_MANDATORY_WORKFLOW_STEPS"
                or python["path_python_matches"] is not True or python["isolated"] is not True):
            return False
        if not isinstance(value["packages"], dict) or set(value["packages"]) != set(APPROVED_PACKAGES):
            return False
        for module, (distribution, expected) in APPROVED_PACKAGES.items():
            row = value["packages"][module]
            if not isinstance(row, dict) or set(row) != {"distribution", "expected_version", "distribution_version",
                                                        "importable", "origin_in_interpreter", "origin_sha256"}:
                return False
            if (row["distribution"] != distribution or row["expected_version"] != expected
                    or row["distribution_version"] != expected or row["importable"] is not True
                    or row["origin_in_interpreter"] is not True or not _is_sha(row["origin_sha256"])):
                return False
        node = value["node"]
        if not isinstance(node, dict) or set(node) != {"version", "executable_sha256", "path_executable_matches",
                "tsc_version", "typescript_version", "typescript_library_sha256", "library_resolution_matches",
                "sanitized_environment_used", "parser_library_loaded"}:
            return False
        return (node["version"] == "22.16.0" and node["tsc_version"] == node["typescript_version"] == "5.8.3"
                and _is_sha(node["executable_sha256"]) and _is_sha(node["typescript_library_sha256"])
                and all(node[key] is True for key in ("path_executable_matches", "library_resolution_matches",
                                                       "sanitized_environment_used", "parser_library_loaded")))
    except (KeyError, TypeError, ValueError):
        return False


def validate_comparison(value: object, expected_head: str) -> bool:
    try:
        if not isinstance(value, dict) or set(value) != {"schema", "scope", "original_run_traceback_recovered", "base", "candidate",
                "unchanged_blobs", "environment", "probes", "mandatory_regression_substituted", "product_accepted",
                "diagnostics_complete", "test_outcome"}:
            return False
        if (value["schema"] != "bie.task035.post-dir-diagnostic/1" or value["scope"] != "SYNTHETIC_TEST_DIAGNOSTICS_ONLY"
                or value["original_run_traceback_recovered"] is not False or value["base"] != diagnostics.BASE
                or not _is_sha(expected_head, 40) or value["candidate"] != expected_head
                or value["mandatory_regression_substituted"] is not False or value["product_accepted"] is not False
                or value["diagnostics_complete"] is not True or value["test_outcome"] != "PASS"):
            return False
        expected_blobs = {path: {"base_blob": identity, "candidate_blob": identity, "working_blob": identity, "equal": True}
                          for path, identity in diagnostics.BLOBS.items()}
        if (value["unchanged_blobs"] != expected_blobs
                or any(row["equal"] is not True for row in value["unchanged_blobs"].values())):
            return False
        env = value["environment"]
        if not isinstance(env, dict) or set(env) != {"os", "os_id", "os_version", "python_version", "python_executable_role",
                "python_executable_sha256", "isolated_python", "dependencies", "node", "tsc", "canonical_typescript_library_present",
                "canonical_python_prefix_present", "canonical_node_prefix_present", "unshare_available", "bubblewrap_available",
                "provisioning_changed", "provisioning_phase"}:
            return False
        if ((env["os"], env["os_id"], env["os_version"], env["python_version"]) != ("Linux", "ubuntu", "24.04", "3.13.5")
                or env["python_executable_role"] != "SAME_INTERPRETER_AS_MANDATORY_WORKFLOW_STEPS"
                or not _is_sha(env["python_executable_sha256"]) or env["isolated_python"] is not True
                or env["provisioning_changed"] is not True or env["provisioning_phase"] != PHASE
                or env["canonical_typescript_library_present"] is not True
                or env["node"] != {"available": True, "version": "22.16.0"}
                or env["tsc"] != {"available": True, "version": "5.8.3"}
                or env["node"]["available"] is not True or env["tsc"]["available"] is not True):
            return False
        if any(type(env[key]) is not bool for key in ("canonical_python_prefix_present", "canonical_node_prefix_present", "unshare_available", "bubblewrap_available")):
            return False
        if not isinstance(env["dependencies"], dict) or set(env["dependencies"]) != set(APPROVED_PACKAGES):
            return False
        if any(env["dependencies"][module] != {"import_spec_available": True, "distribution_version": version}
               or env["dependencies"][module]["import_spec_available"] is not True
               for module, (_, version) in APPROVED_PACKAGES.items()):
            return False
        probes = value["probes"]
        expected_keys = {(root, selection) for root in ("candidate", "base") for selection in (*diagnostics.METHODS, "whole_file")}
        if not isinstance(probes, list) or len(probes) != 6:
            return False
        observed = set()
        for row in probes:
            if not isinstance(row, dict) or not {"root", "selection"} <= set(row):
                return False
            key = row["root"], row["selection"]
            if key not in expected_keys or key in observed:
                return False
            observed.add(key)
            child = {name: item for name, item in row.items() if name not in {"root", "selection"}}
            if not diagnostics.validate_child_receipt(child, row["selection"]) or child["outcome"] != "PASS":
                return False
        return observed == expected_keys
    except (KeyError, TypeError, ValueError):
        return False


def validate_after_receipt(value: object, expected_head: str) -> bool:
    try:
        return (isinstance(value, dict) and set(value) == {"schema", "scope", "phase", "base", "candidate", "runtime",
                    "comparison", "after_gate_passed", "mandatory_regression_substituted", "product_accepted"}
                and value["schema"] == SCHEMA and value["scope"] == SCOPE and value["phase"] == PHASE
                and value["base"] == diagnostics.BASE and value["candidate"] == expected_head
                and value["after_gate_passed"] is True and value["mandatory_regression_substituted"] is False
                and value["product_accepted"] is False and validate_runtime(value["runtime"])
                and validate_comparison(value["comparison"], expected_head)
                and value["runtime"]["python"]["executable_sha256"] == value["comparison"]["environment"]["python_executable_sha256"])
    except (KeyError, TypeError, ValueError):
        return False


def collect_after() -> dict:
    head = diagnostics.git_text("rev-parse", "HEAD")
    comparison = diagnostics.collect(provisioning_phase=PHASE)
    try:
        runtime = runtime_preflight()
    except Exception as exc:
        # Do not discard real unchanged-test outcomes if a later environment
        # observation fails. This failure object never passes validate_runtime.
        runtime = {"status": "RUNTIME_PREFLIGHT_FAILED", "provisioning_phase": PHASE,
                   "provisioning_changed": True, "exception": diagnostics.safe_exception(exc, ROOT)}
    receipt = {"schema": SCHEMA, "scope": SCOPE, "phase": PHASE, "base": diagnostics.BASE,
               "candidate": head, "runtime": runtime, "comparison": comparison,
               "after_gate_passed": True, "mandatory_regression_substituted": False, "product_accepted": False}
    receipt["after_gate_passed"] = validate_after_receipt(receipt, head)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        # Third-party import/probe output is private; the file below contains only
        # the finite observation schema, never source, environment or raw output.
        with open(os.devnull, "w", encoding="utf-8") as private:
            with contextlib.redirect_stdout(private), contextlib.redirect_stderr(private):
                receipt = collect_after()
    except Exception as exc:
        receipt = {"schema": SCHEMA, "scope": SCOPE, "phase": PHASE, "after_gate_passed": False,
                   "status": "AFTER_COLLECTION_FAILED", "exception": diagnostics.safe_exception(exc, ROOT),
                   "mandatory_regression_substituted": False, "product_accepted": False}
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if len(encoded.encode("utf-8")) > diagnostics.MAX_RECEIPT_BYTES:
        receipt = {"schema": SCHEMA, "scope": SCOPE, "phase": PHASE, "after_gate_passed": False,
                   "status": "AFTER_RECEIPT_LIMIT", "mandatory_regression_substituted": False,
                   "product_accepted": False}
        encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    return 0 if validate_after_receipt(receipt, receipt.get("candidate", "")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
