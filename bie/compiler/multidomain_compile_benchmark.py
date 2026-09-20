"""QA-005: executable, provenance-bound multi-domain generated-code benchmark.

Expected-negative fixtures measure defect detection, not product success. Timing
measures real source generation; full TS/Remotion/render/learning gates stay separate.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import median
import json
import math
import sys
import time
from typing import Iterable
from .qa_common import CompilerQAError, QAFinding, digest, ordered_findings, token, write_json
from .qa_scene_compile import CompilerQATarget, compile_scene_for_qa
from .deterministic_codegen import write_codegen_plan
from .deterministic_output_qa import check_deterministic_generator, check_subprocess_generator, compare_snapshots, snapshot_generated
from .generated_code_regression import baseline_from_dict, evaluate_generated_regression
from .compile_diagnostics_mapping import map_compile_diagnostics
from .artifact_hashing import canonical_json, safe_relative

@dataclass(frozen=True)
class CompileBenchmarkCase:
    case_id: str
    domain: str
    document: dict
    expected_source_passed: bool
    expected_error_codes: tuple[str, ...] = ()
    max_codegen_ms: float = 5000
    max_source_bytes: int = 500000
    source_kind: str = "SYNTHETIC_TECHNICAL_FIXTURE_NOT_TEXTBOOK"
    def __post_init__(self):
        token(self.case_id); safe_relative(self.case_id)
        if "/" in self.case_id:
            raise CompilerQAError("case ID must be a single path component")
        token(self.domain)
        if not isinstance(self.document, dict):
            raise CompilerQAError("benchmark document must be JSON object")
        canonical_json(self.document)
        if type(self.expected_source_passed) is not bool:
            raise CompilerQAError("expected_source_passed must be a boolean")
        codes = tuple(self.expected_error_codes)
        for code in codes:
            token(code)
        if self.expected_source_passed and codes or not self.expected_source_passed and not codes:
            raise CompilerQAError("positive cases cannot expect errors; negative cases must name expected errors")
        object.__setattr__(self, "expected_error_codes", codes)
        if (isinstance(self.max_codegen_ms, bool) or not isinstance(self.max_codegen_ms, (float, int))
                or not math.isfinite(self.max_codegen_ms) or self.max_codegen_ms <= 0):
            raise CompilerQAError("max_codegen_ms must be positive and finite")
        if type(self.max_source_bytes) is not int or self.max_source_bytes < 1:
            raise CompilerQAError("max_source_bytes must be a positive integer")
        if self.source_kind != "SYNTHETIC_TECHNICAL_FIXTURE_NOT_TEXTBOOK":
            raise CompilerQAError("this benchmark does not authenticate book provenance")
        if self.document.get("metadata", {}).get("fixture_id") != self.case_id:
            raise CompilerQAError("fixture metadata must bind case ID")

@dataclass(frozen=True)
class CompileBenchmarkCaseResult:
    case_id: str
    domain: str
    fixture_sha256: str
    source_gate_passed: bool
    expected_source_passed: bool
    expectation_matched: bool
    error_codes: tuple[str, ...]
    source_bytes: int
    codegen_samples_ms: tuple[float, ...]
    median_codegen_ms: float | None
    p95_codegen_ms: float | None
    budget_passed: bool
    determinism_passed: bool
    subprocess_determinism_status: str
    generated_regression_status: str
    full_typecheck_status: str
    compile_verified: bool
    diagnostic_mapping_count: int
    evidence_directory: str
    failure: str | None
    accepted: bool = False

@dataclass(frozen=True)
class MultidomainCompileBenchmarkReceipt:
    corpus_sha256: str
    cases: tuple[CompileBenchmarkCaseResult, ...]
    domains: tuple[str, ...]
    expectation_matches: int
    positive_source_passes: int
    negative_cases_detected: int
    compile_verified_cases: int
    source_benchmark_passed: bool
    full_compile_benchmark_passed: bool
    real_render_status: str = "NOT_RUN"
    real_book_e2e: str = "NOT_RUN"
    learning_quality: str = "NOT_EVALUATED"
    scope: str = "TECHNICAL_MULTI_DOMAIN_FIXTURES_NOT_SUBJECT_PACK_ACCEPTANCE"
    accepted: bool = False


def load_benchmark_corpus(path: Path) -> tuple[CompileBenchmarkCase, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version") != "bie.comp-qa-corpus.v1" or raw.get("accepted") is not False:
        raise CompilerQAError("invalid benchmark corpus scope")
    cases = tuple(CompileBenchmarkCase(**c) for c in raw["cases"])
    validate_corpus(cases)
    return cases


def validate_corpus(cases: Iterable[CompileBenchmarkCase]) -> tuple[CompileBenchmarkCase, ...]:
    cases = tuple(cases)
    if not cases or len({c.case_id for c in cases}) != len(cases):
        raise CompilerQAError("benchmark corpus must have unique, nonempty case IDs")
    if len({c.domain for c in cases}) < 2:
        raise CompilerQAError("a multi-domain benchmark requires at least two domains")
    if not any(c.expected_source_passed for c in cases) or not any(not c.expected_source_passed for c in cases):
        raise CompilerQAError("benchmark requires positive and expected-negative cases")
    return tuple(sorted(cases, key=lambda c: (c.domain, c.case_id)))


def run_multidomain_compile_benchmark(cases: Iterable[CompileBenchmarkCase], *,
          output_directory: Path, baseline_directory: Path, target: CompilerQATarget | None = None,
          runs: int = 3, require_full_typecheck: bool = True,
          worker_script: Path | None = None) -> MultidomainCompileBenchmarkReceipt:
    cases = validate_corpus(cases)
    if type(runs) is not int or not 2 <= runs <= 20:
        raise CompilerQAError("benchmark repeats must be 2..20")
    output = Path(output_directory)
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        raise CompilerQAError("benchmark evidence output must be fresh; previous runs are immutable")
    output.mkdir(parents=True, exist_ok=True)
    baseline_directory = Path(baseline_directory)
    target = target or CompilerQATarget()
    results = []
    for case in cases:
        folder = output / case.case_id
        folder.mkdir()
        fixture_hash = digest(asdict(case))
        write_json(folder / "FIXTURE.json", {"fixture_sha256": fixture_hash, "case": asdict(case)})
        timings, codes, failure = [], set(), None
        size, det_passed, sub_status, regression_status, full_status, compile_verified, map_count = 0, False, "NOT_REQUESTED", "NOT_RUN", "NOT_RUN", False, 0
        source_passed, budget = False, False
        try:
            def generate():
                start = time.perf_counter_ns()
                value = compile_scene_for_qa(case.document, target=target)
                timings.append((time.perf_counter_ns() - start) / 1e6)
                return value
            bundle = generate()
            write_codegen_plan(bundle.codegen, folder / "project")
            write_json(folder / "project/SOURCE_MAP.json", asdict(bundle.source_map))
            size = sum(len(f.content.encode("utf-8")) for f in bundle.codegen.files)
            determinism = check_deterministic_generator(lambda: generate().codegen.files, bundle.context, runs=runs)
            original_determinism = determinism
            determinism = compare_snapshots((snapshot_generated(bundle.codegen.files, bundle.context), *determinism.snapshots),
                          expected_runs=runs + 1, execution_kind="INITIAL_ARTIFACT_PLUS_REPEAT_GENERATION")
            if original_determinism.findings:
                determinism = replace(determinism, findings=ordered_findings((*determinism.findings, *original_determinism.findings)), passed=False)
            det_passed = determinism.passed
            write_json(folder / "DETERMINISM.json", asdict(determinism))
            if worker_script is not None:
                request = folder / "WORKER_REQUEST.json"
                write_json(request, {"document": case.document, "target": asdict(target)})
                sub = check_subprocess_generator((sys.executable, str(Path(worker_script).resolve())),
                    request_file=request, context=bundle.context, working_directory=Path(worker_script).resolve().parent.parent)
                sub_status = "PASS" if sub.passed else "FAIL"
                write_json(folder / "SUBPROCESS_DETERMINISM.json", asdict(sub))
                codes.update(f.code for f in sub.findings if f.severity == "ERROR")
            baseline_path = baseline_directory / (case.case_id + ".json")
            baseline = baseline_from_dict(json.loads(baseline_path.read_text(encoding="utf-8"))) if baseline_path.is_file() else None
            if baseline is not None and baseline.fixture_id != case.case_id:
                raise CompilerQAError("baseline belongs to another fixture")
            regression = evaluate_generated_regression(files=bundle.codegen.files, context=bundle.context,
                baseline=baseline, workspace=folder / "project", require_full_typecheck=require_full_typecheck)
            regression_status = "PASS" if regression.source_checks_passed else "FAIL"
            full_status = regression.full_typecheck.status
            compile_verified = regression.compile_verified and bundle.source_contract_passed
            write_json(folder / "GENERATED_REGRESSION.json", asdict(regression))
            mapped = map_compile_diagnostics(regression.syntax_probe.diagnostics + regression.full_typecheck.diagnostics,
                  source_map=bundle.source_map, files=bundle.codegen.files, workspace=folder / "project")
            map_count = len(mapped.diagnostics)
            write_json(folder / "MAPPED_DIAGNOSTICS.json", asdict(mapped))
            write_json(folder / "CAPABILITY_QA.json", asdict(bundle.capability_qa))
            write_json(folder / "SOURCE_CONTRACT.json", {"findings": [asdict(x) for x in bundle.findings],
                         "source_contract_passed": bundle.source_contract_passed, "accepted": False})
            codes.update(f.code for f in (*bundle.findings, *regression.source_findings, *determinism.findings) if f.severity == "ERROR")
            budget = size <= case.max_source_bytes and max(timings) <= case.max_codegen_ms
            if not budget:
                codes.add("BENCHMARK_BUDGET_EXCEEDED")
            source_passed = bundle.source_contract_passed and regression.source_checks_passed and det_passed and sub_status != "FAIL" and budget
        except Exception as exc:
            # Per-case crash is a failed case, not an early-success truncation of the corpus.
            failure = f"{type(exc).__name__}: {str(exc)}"
            codes.add("BENCHMARK_CASE_EXCEPTION")
        observed = tuple(sorted(codes))
        # Unexpected additional errors also fail the expectation, rather than masking a crash.
        matched = (source_passed == case.expected_source_passed and set(observed) == set(case.expected_error_codes))
        samples = tuple(round(x, 6) for x in timings)
        p95 = sorted(timings)[max(0, math.ceil(0.95 * len(timings)) - 1)] if timings else None
        result = CompileBenchmarkCaseResult(case.case_id, case.domain, fixture_hash, source_passed,
                  case.expected_source_passed, matched, observed, size, samples,
                  round(median(timings), 6) if timings else None, round(p95, 6) if p95 is not None else None,
                  budget, det_passed, sub_status, regression_status, full_status, compile_verified,
                  map_count, case.case_id, failure)
        write_json(folder / "CASE_RESULT.json", asdict(result))
        results.append(result)
    source_ok = all(r.expectation_matched and r.budget_passed and r.determinism_passed for r in results)
    positives = [r for r in results if r.expected_source_passed]
    full_ok = source_ok and bool(positives) and all(r.compile_verified for r in positives)
    receipt = MultidomainCompileBenchmarkReceipt(digest([asdict(c) for c in cases]), tuple(results),
            tuple(sorted({r.domain for r in results})), sum(r.expectation_matched for r in results),
            sum(r.source_gate_passed and r.expected_source_passed for r in results),
            sum(r.expectation_matched and not r.expected_source_passed for r in results),
            sum(r.compile_verified for r in results), source_ok, full_ok)
    write_json(output / "BENCHMARK_RESULT.json", asdict(receipt))
    return receipt
