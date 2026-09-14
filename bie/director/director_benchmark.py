"""BIE-DIR-QA-007: execute a director and score independently held expectations.

Candidates receive the source/PED request only. Expected narration and QA
outcomes remain with the runner. There is no caller-supplied score or PASS flag.
The in-process boundary prevents accidental oracle use, not malicious code access.
"""
from dataclasses import dataclass
import hashlib
import re
from .qa_contract import (ScriptSnapshot, SourceCatalog, ScriptClaim, QAReport,
    immutable, rows, validate_catalog, validate_snapshot, validate_claims)
from .timing_contract import fingerprint, nonblank, identifiers, integer, digest_id
from .lesson_architecture_contract import LessonArchitecture
from .game_handoff import GameHandoff
from .speech_timing import SpeechTimingPlan
from .pause_timing import PauseTimingPlan
from .emphasis_timing import EmphasisTimingPlan
from .scene_duration_fit import SceneDurationPlan
from .factual_script_qa import factual_qa
from .source_grounding_qa import SourceBytes, source_grounding_qa
from .script_coherence_qa import DiscourseBeat, coherence_qa
from .repetition_detection import repetition_qa
from .age_level_qa import age_level_qa
from .pacing_qa import PacingBeat, PacingPolicy, pacing_qa, validate_timing
from bie.pedagogy.learning_objective_generator import LearningObjective
from bie.pedagogy.pedagogy_plan_contract import UnifiedPedagogyPlan, build_pedagogy_plan


@dataclass(frozen=True)
class DirectorRequest:
    request_id: str
    title: str
    language: str
    catalog: SourceCatalog
    pedagogy: UnifiedPedagogyPlan
    objectives: tuple[LearningObjective, ...]

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class DirectorExecution:
    snapshot: ScriptSnapshot
    architecture: LessonArchitecture
    game_handoff: GameHandoff
    speech: SpeechTimingPlan
    pauses: PauseTimingPlan
    emphasis: EmphasisTimingPlan
    timeline: SceneDurationPlan
    claims: tuple[ScriptClaim, ...] = ()
    discourse: tuple[DiscourseBeat, ...] = ()
    pacing: tuple[PacingBeat, ...] = ()

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class NarrativeExpectation:
    check_id: str
    kind: str  # PRESENT, ABSENT, ORDER; exact normalized lexical spans, not semantics
    phrases: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class FindingExpectation:
    task_id: str
    code: str
    severity: str
    must_be_present: bool


@dataclass(frozen=True)
class DirectorBenchmarkCase:
    case_id: str
    domain: str
    request: DirectorRequest
    narrative: tuple[NarrativeExpectation, ...]
    findings: tuple[FindingExpectation, ...] = ()


@dataclass(frozen=True)
class DirectorBenchmarkSuite:
    suite_id: str
    version: str
    provenance: str  # ENGINEERING_FIXTURES or CURATED_SOURCE_CASES; not a certification
    oracle_author: str
    oracle_method: str
    required_domains: tuple[str, ...]
    cases: tuple[DirectorBenchmarkCase, ...]
    pacing_policy: PacingPolicy = PacingPolicy()

    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class CandidateIdentity:
    name: str
    version: str
    code_sha256: str
    configuration_sha256: str


@dataclass(frozen=True)
class BenchmarkAttempt:
    case_id: str
    repetition: int
    request_fingerprint: str
    output: DirectorExecution | None
    output_fingerprint: str | None
    failed_checks: tuple[str, ...]
    reports: tuple[QAReport, ...]
    error_type: str | None = None

    @property
    def checks_passed(self):
        return not self.failed_checks and self.error_type is None


@dataclass(frozen=True)
class DirectorBenchmarkReport:
    task_id: str
    suite_fingerprint: str
    candidate: CandidateIdentity
    source_byte_receipts: tuple[tuple[str, str, str, int], ...]
    attempts: tuple[BenchmarkAttempt, ...]
    unstable_cases: tuple[str, ...]
    case_results: tuple[tuple[str, bool], ...]
    domain_results: tuple[tuple[str, int, int], ...]
    limitations: tuple[str, ...]

    @property
    def checks_passed(self):
        return bool(self.case_results) and all(ok for _, ok in self.case_results)

    @property
    def passed_case_fraction(self):
        return sum(ok for _, ok in self.case_results)/len(self.case_results) if self.case_results else 0.0

    @property
    def qa_status(self):
        if any(a.error_type or any(r.status == "BLOCKED" for r in a.reports) for a in self.attempts):
            return "BLOCKED"
        if any(r.status == "REVIEW_REQUIRED" for a in self.attempts for r in a.reports):
            return "REVIEW_REQUIRED"
        return "CHECKS_PASSED"

    @property
    def accepted(self):
        return False

    def fingerprint(self):
        return fingerprint(self)


def validate_request(request):
    if not isinstance(request, DirectorRequest):
        raise ValueError("expected DirectorRequest")
    immutable(request)
    for name in ("request_id", "title", "language"):
        nonblank(getattr(request, name), name)
    pages, passages = validate_catalog(request.catalog)
    if not pages or not passages:
        raise ValueError("benchmark source catalog must be nonempty")
    p = request.pedagogy
    if not isinstance(p, UnifiedPedagogyPlan):
        raise ValueError("expected canonical UnifiedPedagogyPlan")
    rebuilt = build_pedagogy_plan(plan_id=p.plan_id, source_id=p.source_id, objective_ids=p.objective_ids,
        lesson_ids=p.lesson_ids, decisions=p.decisions, policy_version=p.policy_version)
    if p != rebuilt or p.source_id not in {page.source_id for page in pages.values()}:
        raise ValueError("stale or ungrounded PED plan")
    rows(request.objectives, LearningObjective, "learning objectives", "objective_id")
    if {o.objective_id for o in request.objectives} != set(p.objective_ids):
        raise ValueError("objectives do not cover the PED plan")
    for o in request.objectives:
        nonblank(o.concept_id, "objective concept")
        nonblank(o.statement, "objective statement")
        identifiers(o.evidence_ids, "objective evidence")
        if not set(o.evidence_ids) <= passages.keys():
            raise ValueError("objective evidence outside source")
    for d in p.decisions:
        if not set(d.evidence_ids) <= passages.keys():
            raise ValueError("PED evidence outside source")
    return passages


def validate_suite(suite):
    if not isinstance(suite, DirectorBenchmarkSuite):
        raise ValueError("expected DirectorBenchmarkSuite")
    immutable(suite)
    for name in ("suite_id", "version", "oracle_author", "oracle_method"):
        nonblank(getattr(suite, name), name)
    if suite.provenance not in ("ENGINEERING_FIXTURES", "CURATED_SOURCE_CASES"):
        raise ValueError("declare actual suite provenance")
    identifiers(suite.required_domains, "required benchmark domains")
    suite.pacing_policy.validate()
    rows(suite.cases, DirectorBenchmarkCase, "benchmark cases", "case_id")
    if not suite.cases or {c.domain for c in suite.cases} != set(suite.required_domains):
        raise ValueError("suite must cover all and only its declared domains")
    request_ids = []
    for case in suite.cases:
        nonblank(case.domain, "domain")
        passages = validate_request(case.request)
        request_ids.append(case.request.request_id)
        rows(case.narrative, NarrativeExpectation, "narrative expectations", "check_id")
        if not case.narrative:
            raise ValueError("independent narration expectations are required")
        for e in case.narrative:
            if e.kind not in ("PRESENT", "ABSENT", "ORDER"):
                raise ValueError("unknown narrative check")
            identifiers(e.phrases, "expected phrases")
            identifiers(e.evidence_ids, "oracle evidence")
            nonblank(e.rationale, "oracle rationale")
            if not set(e.evidence_ids) <= passages.keys() or (e.kind == "ORDER" and len(e.phrases) < 2):
                raise ValueError("invalid independent source expectation")
            if any(not _normalize(phrase) for phrase in e.phrases):
                raise ValueError("expectations need lexical words")
        rows(case.findings, FindingExpectation, "finding expectations")
        if len({(f.task_id, f.code, f.severity) for f in case.findings}) != len(case.findings):
            raise ValueError("duplicate/conflicting expected finding")
        for f in case.findings:
            if f.task_id not in {f"BIE-DIR-QA-{n:03}" for n in range(1, 7)} or f.severity not in ("BLOCKER", "REVIEW", "INFO"):
                raise ValueError("invalid expected QA finding")
            nonblank(f.code, "expected finding code")
            if type(f.must_be_present) is not bool:
                raise ValueError("finding expectation must be boolean")
    identifiers(tuple(request_ids), "benchmark request ids")


def _normalize(text):
    # Preserve punctuation/operators/negation; only whitespace and case normalize.
    return " ".join(text.casefold().split())


def _positions(text, phrase):
    return tuple(m.start() for m in re.finditer(r"(?<!\w)"+re.escape(_normalize(phrase))+r"(?!\w)", text))


def _evaluate(case, output, artifacts, policy):
    if not isinstance(output, DirectorExecution):
        raise ValueError("candidate must return DirectorExecution, not scores or QA reports")
    immutable(output)
    validate_snapshot(output.snapshot)
    validate_timing(output.snapshot, output.speech, output.pauses, output.emphasis, output.timeline)
    validate_claims(output.snapshot, output.claims)
    if not isinstance(output.architecture, LessonArchitecture) or not isinstance(output.game_handoff, GameHandoff):
        raise ValueError("candidate must expose lesson and game handoff contracts")
    request, failed = case.request, []
    s, h = output.snapshot, output.game_handoff
    wanted = {o.objective_id for o in request.objectives}
    actual = {o for u in s.utterances for o in u.objective_ids}
    if actual != wanted or set(output.architecture.objective_ids) != wanted:
        failed.append("PED_OBJECTIVE_COVERAGE")
    if s.script.lesson_id not in request.pedagogy.lesson_ids or output.architecture.lesson_id != s.script.lesson_id:
        failed.append("PED_LESSON_BINDING")
    if s.language != request.language:
        failed.append("REQUEST_LANGUAGE")
    if set(output.architecture.source_ids) != {p.source_id for p in request.catalog.pages}:
        failed.append("LESSON_SOURCE_BINDING")
    # Known legacy handoff validation is shallow. Independently reject empty
    # identifiers here without rewriting preserved SCRIPT-010 source.
    for name in ("objective_ids", "concept_ids", "mastery_checks", "evidence_ids"):
        identifiers(getattr(h, name), "game " + name)
    identifiers(h.misconception_ids, "game misconceptions", allow_empty=True)
    if (h.lesson_id != s.script.lesson_id or set(h.objective_ids) != wanted
        or not {o.concept_id for o in request.objectives} <= set(h.concept_ids)
        or set(h.evidence_ids) != {e for o in request.objectives for e in o.evidence_ids}
        or h.forbidden_ungrounded_mechanics is not True):
        failed.append("GAME_LEARNING_MODEL_BINDING")
    if request.pedagogy.requires_review and not (output.architecture.requires_review and s.utterances
                                               and all(u.review_reasons for u in s.utterances)):
        failed.append("UPSTREAM_PED_REVIEW_DROPPED")
    # Run the actual QA modules here. A candidate cannot submit a self-awarded PASS.
    reports = (factual_qa(s, output.claims, request.catalog),
        source_grounding_qa(s, output.claims, request.catalog, artifacts),
        coherence_qa(s, output.architecture, output.discourse), repetition_qa(s), age_level_qa(s),
        pacing_qa(s, output.speech, output.pauses, output.emphasis, output.timeline, output.pacing, policy))
    # Narrative tests inspect actual speech, independently of labels/claim metadata.
    text = _normalize(" ".join(u.text for u in s.utterances))
    for expected in case.narrative:
        locations = [_positions(text, phrase) for phrase in expected.phrases]
        ok = all(locations) if expected.kind == "PRESENT" else not any(locations)
        if expected.kind == "ORDER":
            after, ok = -1, True
            for phrase, positions in zip(expected.phrases, locations):
                eligible = [p for p in positions if p >= after]
                if not eligible:
                    ok = False
                    break
                after = eligible[0] + len(_normalize(phrase))
        if not ok:
            failed.append("NARRATIVE:"+expected.check_id)
    observed = {(r.task_id, f.code, f.severity) for r in reports for f in r.findings}
    expected_blockers = {(f.task_id, f.code, f.severity) for f in case.findings
                         if f.must_be_present and f.severity == "BLOCKER"}
    for task, code, severity in sorted(observed - expected_blockers):
        if severity == "BLOCKER":
            failed.append("UNEXPECTED_BLOCKER:"+task+":"+code)
    for f in case.findings:
        if ((f.task_id, f.code, f.severity) in observed) != f.must_be_present:
            failed.append("FINDING:"+f.task_id+":"+f.code)
    return tuple(failed), reports


def run_director_benchmark(suite, candidate, artifacts, identity, repetitions=2):
    validate_suite(suite)
    if not callable(candidate) or not isinstance(identity, CandidateIdentity):
        raise ValueError("versioned executable candidate required")
    immutable(identity)
    nonblank(identity.name, "candidate name")
    nonblank(identity.version, "candidate version")
    digest_id(identity.code_sha256, "candidate code digest")
    digest_id(identity.configuration_sha256, "configuration digest")
    integer(repetitions, "repetitions", 2)
    if type(artifacts) is not tuple or any(not isinstance(a, SourceBytes) or type(a.data) is not bytes for a in artifacts):
        raise ValueError("immutable actual source bytes required")
    identifiers(tuple(a.source_id for a in artifacts), "source artifacts")
    source_index = {a.source_id: a for a in artifacts}
    needed, receipts = {}, []
    for case in suite.cases:
        for page in case.request.catalog.pages:
            if page.source_id in needed and needed[page.source_id] != page.source_sha256:
                raise ValueError("conflicting source revisions in suite")
            needed[page.source_id] = page.source_sha256
    if set(source_index) != set(needed):
        raise ValueError("source artifacts must exactly cover the benchmark")
    for sid, declared in sorted(needed.items()):
        a = source_index[sid]
        nonblank(a.media_type, "source media type")
        computed = "sha256:"+hashlib.sha256(a.data).hexdigest()
        if computed != declared:
            raise ValueError("benchmark source bytes do not match pinned source")
        receipts.append((sid, computed, a.media_type, len(a.data)))
    attempts, unstable, outcomes = [], [], []
    for case in suite.cases:
        case_attempts = []
        selected = tuple(source_index[s] for s in sorted({p.source_id for p in case.request.catalog.pages}))
        for repetition in range(1, repetitions+1):
            try:
                output = candidate(case.request)
                failed, reports = _evaluate(case, output, selected, suite.pacing_policy)
                attempt = BenchmarkAttempt(case.case_id, repetition, case.request.fingerprint(), output,
                    output.fingerprint(), failed, reports)
            except Exception as exc:
                # Fail the case and retain its place in the denominator. Exception
                # text may contain private source/provider data; record type only.
                attempt = BenchmarkAttempt(case.case_id, repetition, case.request.fingerprint(), None, None,
                    ("EXECUTION_OR_CONTRACT_FAILURE",), (), type(exc).__name__)
            attempts.append(attempt)
            case_attempts.append(attempt)
        if len({a.output_fingerprint for a in case_attempts}) != 1:
            unstable.append(case.case_id)
        outcomes.append((case.case_id, all(a.checks_passed for a in case_attempts) and case.case_id not in unstable))
    by_case = dict(outcomes)
    domains = tuple((domain, sum(by_case[c.case_id] for c in suite.cases if c.domain == domain),
                     sum(c.domain == domain for c in suite.cases)) for domain in suite.required_domains)
    return DirectorBenchmarkReport("BIE-DIR-QA-007", suite.fingerprint(), identity, tuple(receipts), tuple(attempts),
        tuple(unstable), tuple(outcomes), domains,
        ("Narration expectations are source-referenced lexical checks, not general semantic or teaching-quality judgments.",
         "This benchmark path executes six QA modules; production semantic/annotation providers and calibrated audience evaluation require separate evidence.",
         "Candidate identity is declared provenance; the runner is not a sandbox or cryptographic attestation service.",
         "Repeated exact-output comparison tests deterministic replay; stochastic providers require a governed evaluation policy.",
         "A handoff is not a playable game, and a timeline is not rendered/audio-verified media.",
         "Regression expectations may pass while QA requires review or a negative case is correctly blocked; accepted is always false."))
