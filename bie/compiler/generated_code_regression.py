"""QA-004: golden-tree regression, real TypeScript AST checks, and build gates.

Initial baseline recording is explicit and never occurs as a side effect of a
failed check. Parser success is distinct from full typechecking and rendering.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
import json
import posixpath
import re
import shutil
import tempfile
from .qa_common import CompilerQAError, QAFinding, digest, ordered_findings, source_files, token
from .artifact_hashing import canonical_json, require_sha256, safe_relative, confined_path
from .deterministic_output_qa import DeterminismContext, GeneratedSnapshot, snapshot_generated
from .render_process import run_bounded_process
from .generated_lint import lint_generated_sources
from .generated_static_analysis import analyze_generated_sources
from .compile_diagnostics_mapping import RawCompileDiagnostic, parse_compile_output

@dataclass(frozen=True)
class GeneratedCodeBaseline:
    baseline_id: str
    fixture_id: str
    approval_ref: str
    snapshot: GeneratedSnapshot
    baseline_sha256: str
    status: str = "INITIAL_GOLDEN_SOURCE_NOT_PRODUCT_APPROVAL"
    accepted: bool = False


def record_generated_baseline(*, baseline_id: str, fixture_id: str, approval_ref: str,
                              files: Iterable, context: DeterminismContext) -> GeneratedCodeBaseline:
    for value in (baseline_id, fixture_id, approval_ref):
        token(value)
    snap = snapshot_generated(files, context)
    payload = {"baseline_id": baseline_id, "fixture_id": fixture_id, "approval_ref": approval_ref,
               "snapshot": asdict(snap)}
    return GeneratedCodeBaseline(baseline_id, fixture_id, approval_ref, snap, digest(payload))


def baseline_from_dict(raw: dict) -> GeneratedCodeBaseline:
    try:
        snap = dict(raw["snapshot"])
        snap["files"] = tuple(tuple(x) for x in snap["files"])
        result = GeneratedCodeBaseline(raw["baseline_id"], raw["fixture_id"], raw["approval_ref"],
                    GeneratedSnapshot(**snap), raw["baseline_sha256"], raw["status"], raw["accepted"])
        validate_baseline(result)
        return result
    except (KeyError, TypeError) as exc:
        raise CompilerQAError("invalid generated-source baseline") from exc


def validate_baseline(baseline: GeneratedCodeBaseline) -> None:
    from .deterministic_output_qa import compare_snapshots
    for v in (baseline.baseline_id, baseline.fixture_id, baseline.approval_ref):
        token(v)
    expected = digest({"baseline_id": baseline.baseline_id, "fixture_id": baseline.fixture_id,
               "approval_ref": baseline.approval_ref, "snapshot": asdict(baseline.snapshot)})
    if expected != baseline.baseline_sha256 or baseline.accepted is not False:
        raise CompilerQAError("baseline identity/acceptance tampering")
    if baseline.status != "INITIAL_GOLDEN_SOURCE_NOT_PRODUCT_APPROVAL":
        raise CompilerQAError("unknown baseline governance status")
    compare_snapshots((baseline.snapshot, baseline.snapshot), expected_runs=2)

@dataclass(frozen=True)
class SyntaxProbeReceipt:
    status: str
    typescript_version: str | None
    files_parsed: int
    diagnostics: tuple[RawCompileDiagnostic, ...]
    findings: tuple[QAFinding, ...]
    imports: tuple[tuple[str, str], ...]
    stdout: str
    stderr: str
    execution_kind: str = "REAL_TYPESCRIPT_AST_PARSER"
    full_typecheck: bool = False
    accepted: bool = False


def _typescript_library(explicit: str | Path | None) -> Path | None:
    if explicit is not None:
        path = Path(explicit).resolve()
        return path if path.is_file() else None
    tsc = shutil.which("tsc")
    if not tsc:
        return None
    path = Path(tsc).resolve().parent.parent / "lib/typescript.js"
    return path if path.is_file() else None


def probe_typescript_sources(files: Iterable, *, node_bin: str = "node",
                             typescript_library: str | Path | None = None,
                             timeout_s: float = 45) -> SyntaxProbeReceipt:
    normalized = source_files(files)
    scripts = [(p, c) for p, c, _ in normalized if p.endswith((".ts", ".tsx", ".js", ".jsx"))]
    if not scripts:
        return SyntaxProbeReceipt("FAIL", None, 0, (),
            (QAFinding("GENERATED_CODE_EMPTY", "ERROR", "No generated TypeScript/JavaScript files were found."),), (), "", "")
    library = _typescript_library(typescript_library)
    if library is None:
        return SyntaxProbeReceipt("BLOCKED", None, 0, (),
            (QAFinding("TYPESCRIPT_PARSER_UNAVAILABLE", "ERROR", "Real TypeScript parser is not installed."),), (), "", "")
    with tempfile.TemporaryDirectory(prefix="bie-ts-qa-") as tmp:
        req = Path(tmp) / "request.json"
        req.write_bytes(canonical_json({"files": [{"path": p, "content": c} for p, c in scripts]}))
        script = Path(__file__).parent / "qa_support/typescript_source_probe.cjs"
        result = run_bounded_process((node_bin, str(script), str(req), str(library)),
                                     cwd=tmp, timeout_s=timeout_s, max_output_bytes=4 * 1024 * 1024)
    if not result.process.passed:
        return SyntaxProbeReceipt("BLOCKED" if not result.started else "FAIL", None, 0, (),
           (QAFinding("TYPESCRIPT_PROBE_FAILED", "ERROR", f"Parser process failed: {result.outcome}."),),
           (), result.process.stdout, result.process.stderr)
    try:
        raw = json.loads(result.process.stdout)
        from hashlib import sha256
        expected_input = canonical_json({"files": [{"path": p, "content": c} for p, c in scripts]})
        if raw.get("request_sha256") != sha256(expected_input).hexdigest() or raw.get("execution_kind") != "REAL_TYPESCRIPT_AST_PARSER":
            raise CompilerQAError("probe is not bound to the supplied source request")
        if raw["schema_version"] != "bie.typescript-source-probe.v1" or raw["full_typecheck"] is not False:
            raise CompilerQAError("invalid probe scope")
        if raw["files_parsed"] != len(scripts) or raw["accepted"] is not False:
            raise CompilerQAError("incomplete probe coverage")
        diagnostics = tuple(RawCompileDiagnostic(d["code"], d["severity"], "typescript-ast", d["message"],
                       d["path"], d["line"], d["column"]) for d in raw["findings"])
        findings = [QAFinding(d.code, d.severity, d.message, d.file) for d in diagnostics]
        imports = tuple(sorted(set((i["file"], i["specifier"]) for i in raw["imports"])))
    except (ValueError, KeyError, TypeError) as exc:
        raise CompilerQAError("malformed TypeScript probe receipt") from exc
    paths = {p for p, _, _ in normalized}
    package = next((c for p, c, _ in normalized if p == "package.json"), None)
    deps = {"react", "react-dom", "remotion"} if package is None else set()
    if package is not None:
        try:
            parsed_package = json.loads(package)
            deps = set(parsed_package.get("dependencies", {})) | set(parsed_package.get("devDependencies", {}))
        except (ValueError, TypeError) as exc:
            raise CompilerQAError("invalid generated package.json") from exc
    for origin, specifier in imports:
        if specifier.startswith("."):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(origin), specifier))
            try:
                safe_relative(target)
            except ValueError:
                findings.append(QAFinding("GENERATED_IMPORT_ESCAPES_ROOT", "ERROR", "Relative import escapes generated root.", origin))
                continue
            candidates = {target, *(target + ext for ext in (".ts", ".tsx", ".js", ".jsx", ".json")),
                          *(target + "/index" + ext for ext in (".ts", ".tsx", ".js", ".jsx"))}
            if target.endswith(".js"):
                candidates |= {target[:-3] + ".ts", target[:-3] + ".tsx"}
            if not candidates & paths:
                findings.append(QAFinding("GENERATED_IMPORT_MISSING", "ERROR", "Unresolved generated relative import: " + specifier, origin))
        elif not specifier.startswith(("node:", "http:", "https:", "/", "data:", "file:")):
            parts = specifier.split("/")
            name = "/".join(parts[:2]) if specifier.startswith("@") else parts[0]
            if name not in deps:
                findings.append(QAFinding("GENERATED_DEPENDENCY_UNDECLARED", "ERROR", "Undeclared package: " + name, origin))
    findings = ordered_findings(findings)
    return SyntaxProbeReceipt("FAIL" if any(f.severity == "ERROR" for f in findings) else "PASS",
               raw["typescript_version"], raw["files_parsed"], diagnostics, findings, imports,
               result.process.stdout, result.process.stderr)

@dataclass(frozen=True)
class TypecheckGate:
    status: str
    missing_dependencies: tuple[str, ...]
    diagnostics: tuple[RawCompileDiagnostic, ...]
    stdout: str
    stderr: str
    execution_kind: str
    accepted: bool = False


def typecheck_generated_workspace(workspace: Path, *, tsc_bin: str | None = None,
                                  timeout_s: float = 90, process_runner=None) -> TypecheckGate:
    execute = process_runner or run_bounded_process
    root = Path(workspace).resolve()
    if not root.is_dir() or not (root / "tsconfig.json").is_file():
        raise CompilerQAError("generated TypeScript workspace/config missing")
    config = json.loads((root / "tsconfig.json").read_text(encoding="utf-8"))
    options = config.get("compilerOptions", {})
    strict_flags = ("noImplicitAny", "strictNullChecks", "strictFunctionTypes", "strictBindCallApply",
                    "strictPropertyInitialization", "useUnknownInCatchVariables", "alwaysStrict",
                    "strictBuiltinIteratorReturn")
    if (options.get("strict") is not True or options.get("noCheck") is True
            or any(options.get(name) is False for name in strict_flags)):
        return TypecheckGate("BLOCKED_CONFIG", (),
             (RawCompileDiagnostic("QA_TYPECHECK_CONFIG_WEAKENED", "ERROR", "typescript",
                 "Strict source checking is disabled or weakened.", "tsconfig.json"),), "", "", "NOT_RUN")
    package_path = root / "package.json"
    missing = []
    if package_path.is_file():
        package = json.loads(package_path.read_text())
        for name, version in {**package.get("dependencies", {}), **package.get("devDependencies", {})}.items():
            try:
                installed = root / "node_modules" / safe_relative(name) / "package.json"
                if not installed.is_file():
                    missing.append(name); continue
                installed_version = json.loads(installed.read_text()).get("version")
                if re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", str(version)) and installed_version != version:
                    missing.append(name + "@VERSION_MISMATCH")
            except (ValueError, TypeError, OSError):
                missing.append(str(name) + "@INVALID")
    if missing:
        return TypecheckGate("BLOCKED_DEPENDENCIES", tuple(sorted(missing)), (), "", "", "NOT_RUN")
    executable = tsc_bin or str(root / "node_modules/.bin/tsc")
    if tsc_bin is None and not Path(executable).is_file():
        return TypecheckGate("BLOCKED_TOOLCHAIN", (), (), "", "", "NOT_RUN")
    expected_sources = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if "node_modules" in relative.parts or any(p.startswith(".") for p in relative.parts):
            continue
        if path.suffix in {".ts", ".tsx", ".js", ".jsx"} and path.is_file():
            if path.is_symlink():
                raise CompilerQAError("generated TypeScript source must not be a symlink")
            expected_sources.add(str(path.resolve()))
    coverage = execute((executable, "--project", str(root / "tsconfig.json"),
                                    "--listFilesOnly", "--pretty", "false"), cwd=root, timeout_s=timeout_s)
    included = set(coverage.process.stdout.splitlines())
    if not coverage.process.passed or not expected_sources or not expected_sources <= included:
        return TypecheckGate("BLOCKED_INPUT_COVERAGE", (),
              (RawCompileDiagnostic("QA_TYPECHECK_SOURCE_EXCLUDED", "ERROR", "typescript",
                   "The compiler program does not include every inspected generated source file.", "tsconfig.json"),),
              coverage.process.stdout, coverage.process.stderr, "REAL_TSC_PROGRAM_FILE_LIST")
    process = execute((executable, "--project", str(root / "tsconfig.json"),
                                   "--noEmit", "--pretty", "false"), cwd=root, timeout_s=timeout_s)
    diagnostics = parse_compile_output(process.process.stdout + "\n" + process.process.stderr)
    return TypecheckGate("PASS" if process.process.passed else "FAIL", (), diagnostics,
                        process.process.stdout, process.process.stderr, "REAL_TSC_PROCESS")

@dataclass(frozen=True)
class GeneratedCodeRegressionReceipt:
    baseline_id: str | None
    current_snapshot: GeneratedSnapshot
    baseline_status: str
    source_findings: tuple[QAFinding, ...]
    syntax_probe: SyntaxProbeReceipt
    full_typecheck: TypecheckGate
    source_checks_passed: bool
    compile_verified: bool
    passed: bool
    scope: str = "GENERATED_CODE_REGRESSION_NOT_RENDER_OR_LEARNING_QUALITY"
    accepted: bool = False


def evaluate_generated_regression(*, files: Iterable, context: DeterminismContext,
                                  baseline: GeneratedCodeBaseline | None,
                                  workspace: Path | None = None,
                                  require_full_typecheck: bool = True,
                                  typescript_library: str | Path | None = None) -> GeneratedCodeRegressionReceipt:
    files = tuple(files)
    normalized = source_files(files)
    current = snapshot_generated(files, context)
    findings = []
    baseline_status = "MISSING"
    if baseline is None:
        findings.append(QAFinding("GENERATED_BASELINE_MISSING", "ERROR", "Explicit approved source baseline is required."))
    else:
        validate_baseline(baseline)
        from .deterministic_output_qa import compare_snapshots
        comparison = compare_snapshots((baseline.snapshot, current), expected_runs=2)
        findings.extend(QAFinding(f.code.replace("DETERMINISM", "REGRESSION"), f.severity, f.message, f.path)
                        for f in comparison.findings)
        baseline_status = "MATCH" if comparison.passed else "DIFF"
    syntax = probe_typescript_sources(files, typescript_library=typescript_library)
    findings.extend(syntax.findings)
    # Existing BUILD-004/005 gates run over exact generated source in a disposable root.
    with tempfile.TemporaryDirectory(prefix="bie-regression-") as tmp:
        root = Path(tmp)
        for path, content, _ in normalized:
            dest = root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8", newline="")
        lint = lint_generated_sources(root)
        static = analyze_generated_sources(root)
        findings.extend(QAFinding(x.code, x.severity, x.message, x.path) for x in lint.issues)
        findings.extend(QAFinding(x.code, "ERROR" if x.severity == "BLOCKER" else "WARNING", x.message, x.path)
                        for x in static.findings)
        if workspace is not None:
            # Prevent compiling an unrelated, stale or augmented source tree.
            generated_names = {p for p, _, _ in normalized}
            for observed in Path(workspace).rglob("*"):
                rel = observed.relative_to(workspace).as_posix()
                if "node_modules" in observed.relative_to(workspace).parts:
                    continue
                if observed.suffix in {".ts", ".tsx", ".js", ".jsx"} and observed.is_file() and rel not in generated_names:
                    raise CompilerQAError("uninspected generated source in typecheck workspace: " + rel)
            for path, content, h in normalized:
                from hashlib import sha256
                target = confined_path(workspace, path, must_exist=True)
                if sha256(target.read_bytes()).hexdigest() != h:
                    raise CompilerQAError("typecheck workspace differs from inspected generated bytes")
        typecheck_root = Path(workspace) if workspace is not None else root
        full = typecheck_generated_workspace(typecheck_root) if require_full_typecheck else TypecheckGate("NOT_REQUESTED", (), (), "", "", "NOT_RUN")
    findings = ordered_findings(findings)
    source_passed = baseline_status == "MATCH" and syntax.status == "PASS" and not any(f.severity == "ERROR" for f in findings)
    compile_verified = source_passed and full.status == "PASS"
    return GeneratedCodeRegressionReceipt(baseline.baseline_id if baseline else None, current, baseline_status,
                findings, syntax, full, source_passed, compile_verified,
                compile_verified if require_full_typecheck else source_passed)
