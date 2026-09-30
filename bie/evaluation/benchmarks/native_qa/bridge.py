"""BIE-EVAL-NATIVE-QA-001: execute AV benchmarks and the real QA v2 consumer.

This is a local component-integration slice, not canonical caller deployment.
It never signs evidence. Authored/bounded technical checks cannot become a full
benchmark PASS. All candidate bytes are captured into a private workspace;
only files actually captured are listed as inspected. The supplied source/game
are byte-inspected, not semantically validated, built or played.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import importlib
import json
import os
from pathlib import Path
import tempfile

from ..models import BenchmarkError, canonical_json, digest, digest_string, strict_loads
from ..adoption.contracts import ExecutionContext, METRICS, validate_reference, validate_candidate
from ..adoption.custody import open_root, confined_stream, signature
from ..adoption.metric import AVCollectionBlocked
from .. import metrics

PIN = json.loads(Path(__file__).with_name('pin.json').read_text(encoding='utf-8'))
VERSION = 'section17-native-qa-slice-1'


def verify_native_runtime():
    """Operator-provisioned Python code is trusted to import, then content-pinned.

    This is not a sandbox for untrusted Python packages. No alternate checkout,
    module reload, network download or compatibility fallback is performed.
    """
    try:
        package = importlib.import_module('bie.qa.release_v2')
    except ImportError as exc:
        raise BenchmarkError('NATIVE_QA_DEPENDENCY_UNAVAILABLE') from exc
    root = Path(package.__file__).parent
    checked = {}
    for row in PIN['files']:
        path = root / Path(row['path']).name
        if path.is_symlink() or not path.is_file():
            raise BenchmarkError('NATIVE_QA_SOURCE_UNAVAILABLE')
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if len(raw) != row['size_bytes'] or sha != row['sha256']:
            raise BenchmarkError('NATIVE_QA_CODE_PIN_MISMATCH', row['path'])
        checked[row['path']] = sha
    return checked


def _copy_candidate(candidate, source_root, destination):
    """Stream exact artifacts once; reject links, replacements and changed bytes."""
    snapshots = []
    with open_root(source_root) as root_fd:
        for ref in sorted(candidate.artifacts, key=lambda a: a.artifact_id):
            target = destination / ref.path
            target.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            total = 0
            with confined_stream(root_fd, ref.path) as stream, target.open('xb') as output:
                before = os.fstat(stream.fileno())
                if before.st_nlink != 1 or before.st_size != ref.size:
                    raise BenchmarkError('NATIVE_QA_ARTIFACT_LINK_OR_SIZE')
                while block := stream.read(min(1024 * 1024, ref.size + 1 - total)):
                    total += len(block)
                    if total > ref.size:
                        raise BenchmarkError('NATIVE_QA_ARTIFACT_LIMIT')
                    output.write(block)
                    h.update(block)
                after = os.fstat(stream.fileno())
                if signature(before) != signature(after) or after.st_nlink != 1:
                    raise BenchmarkError('NATIVE_QA_ARTIFACT_CHANGED')
            if total != ref.size or h.hexdigest() != ref.sha256:
                raise BenchmarkError('NATIVE_QA_ARTIFACT_HASH_MISMATCH')
            with confined_stream(root_fd, ref.path) as stream:
                current = os.fstat(stream.fileno())
                if signature(current) != signature(after) or current.st_nlink != 1:
                    raise BenchmarkError('NATIVE_QA_ARTIFACT_REPLACED')
            target.chmod(0o400)
            snapshots.append({'artifact_id': ref.artifact_id, 'path': ref.path,
                              'sha256': h.hexdigest(), 'size_bytes': total})
    return snapshots


def _checks(value, candidate, context):
    if type(value) is not list or len(value) != len(METRICS):
        raise BenchmarkError('NATIVE_QA_REQUIRED_AV_ROSTER')
    # Detach nested mutable inputs before entering a collector.
    rows = strict_loads(canonical_json(value))
    expected_fields = {'metric_id', 'reference', 'candidate',
                       'expected_reference_sha256', 'expected_candidate_sha256'}
    if any(type(r) is not dict or set(r) != expected_fields for r in rows):
        raise BenchmarkError('NATIVE_QA_CHECK_FIELDS')
    if any(type(r['metric_id']) is not str for r in rows) or sorted(r['metric_id'] for r in rows) != sorted(METRICS):
        raise BenchmarkError('NATIVE_QA_REQUIRED_AV_ROSTER')
    artifacts = {r.path: r for r in candidate.artifacts}
    used_videos = set()
    for row in rows:
        metric = row['metric_id']
        if digest(row['reference']) != digest_string(row['expected_reference_sha256']):
            raise BenchmarkError('NATIVE_QA_REFERENCE_PIN_MISMATCH')
        if digest(row['candidate']) != digest_string(row['expected_candidate_sha256']):
            raise BenchmarkError('NATIVE_QA_METRIC_CANDIDATE_PIN_MISMATCH')
        validate_reference(row['reference'], metric)
        c = validate_candidate(row['candidate'], metric, context.limits)
        if row['reference']['limits_sha256'] != digest(asdict(context.limits)):
            raise BenchmarkError('NATIVE_QA_LIMITS_PIN_MISMATCH')
        for key in ('media', 'captions'):
            a = c[key]
            if a is None:
                continue
            ref = artifacts.get(a['path'])
            if ref is None or ref.sha256 != a['sha256'] or ref.size != a['size_bytes']:
                raise BenchmarkError('NATIVE_QA_SUBJECT_BINDING_MISMATCH')
            if (key == 'media' and ref.role != 'video') or (key == 'captions' and ref.role != 'support'):
                raise BenchmarkError('NATIVE_QA_SUBJECT_ROLE_MISMATCH')
        used_videos.add(c['media']['path'])
    # This initial slice measures exactly one video. Multiple videos need an
    # explicit roster extension; they must never be silently dropped.
    if len(used_videos) != 1 or used_videos != {a.path for a in candidate.artifacts if a.role == 'video'}:
        raise BenchmarkError('NATIVE_QA_VIDEO_COVERAGE_MISMATCH')
    return sorted(rows, key=lambda r: r['metric_id'])


def execute(candidate, checks, *, execution_context, as_of,
            expected_candidate_digest, expected_policy_digest, expected_checks_digest, release_policy=None):
    """Run existing S17 collectors, emit unsigned evidence, invoke canonical QA.

    No caller-provided measurement/receipt, signer or verifier parameter exists.
    The caller provisions the approved Python/FFmpeg environment separately.
    Returns exact report and envelope data for persistence by its operator.
    """
    native_before = verify_native_runtime()
    from bie.qa.release_v2.contracts import (
        ArtifactRef, ContractError, EvidenceBundle, GateEvidence, ReleaseCandidate, integer)
    from bie.qa.release_v2.evaluator import ReleaseEvaluator
    from bie.qa.release_v2.policy import ReleasePolicy, enterprise_policy

    if type(candidate) is not ReleaseCandidate:
        raise BenchmarkError('NATIVE_QA_CANDIDATE_TYPE')
    if type(execution_context) is not ExecutionContext:
        raise BenchmarkError('NATIVE_QA_EXECUTION_CONTEXT_REQUIRED')
    integer(as_of, 'as_of')
    policy = enterprise_policy() if release_policy is None else release_policy
    if type(policy) is not ReleasePolicy:
        raise BenchmarkError('NATIVE_QA_POLICY_TYPE')
    if candidate.content_digest != digest_string(expected_candidate_digest):
        raise BenchmarkError('NATIVE_QA_PRODUCT_CANDIDATE_PIN_MISMATCH')
    if policy.content_digest != digest_string(expected_policy_digest):
        raise BenchmarkError('NATIVE_QA_POLICY_PIN_MISMATCH')
    if candidate.revision != PIN['commit']:
        raise BenchmarkError('NATIVE_QA_REVISION_PIN_MISMATCH')
    if digest(checks) != digest_string(expected_checks_digest):
        raise BenchmarkError('NATIVE_QA_CHECK_PLAN_PIN_MISMATCH')
    rows = _checks(checks, candidate, execution_context)
    original_digest = candidate.content_digest
    before_code = metrics_code_digest()
    # Candidate constructor enforces file/total byte limits and role coverage.
    # Reject conflicting file/directory names before any copying.
    paths = {a.path for a in candidate.artifacts}
    if any('/'.join(p.split('/')[:i]) in paths for p in paths for i in range(1, len(p.split('/')))):
        raise BenchmarkError('NATIVE_QA_ARTIFACT_PREFIX_COLLISION')

    with tempfile.TemporaryDirectory(prefix='bie-eval-qa-slice-') as temp:
        work = Path(temp)
        try:
            snapshots = _copy_candidate(candidate, execution_context.artifact_root, work)
        except OSError as exc:
            raise BenchmarkError('NATIVE_QA_SNAPSHOT_IO_FAILED') from exc
        scoped = ExecutionContext(work, execution_context.limits)
        results = []
        for row in rows:
            try:
                result = metrics.evaluate(row['metric_id'], row['reference'], row['candidate'],
                    expected_reference_sha256=row['expected_reference_sha256'],
                    expected_candidate_sha256=row['expected_candidate_sha256'], execution_context=scoped)
            except AVCollectionBlocked as exc:
                result = {'metric_id': row['metric_id'], 'status': 'BLOCKED',
                          'error_code': exc.code, 'collector_receipt': exc.receipt}
            except BenchmarkError as exc:
                result = {'metric_id': row['metric_id'], 'status': 'BLOCKED', 'error_code': exc.code}
            # Unknown runtime failures propagate: they cannot produce an envelope.
            results.append(result)
        outcomes = [r.get('outcome', r.get('status')) for r in results]
        status = ('ERROR' if 'BLOCKED' in outcomes else
                  'FAIL' if 'FAIL' in outcomes else 'NOT_RUN')
        if any(v not in ('PASS', 'FAIL', 'BLOCKED') for v in outcomes):
            raise BenchmarkError('NATIVE_QA_UNEXPECTED_METRIC_RESULT')
        payload = {'schema_version': VERSION, 'candidate_digest': original_digest,
                   'candidate': candidate.to_dict(), 'policy_digest': policy.content_digest,
                   'canonical_commit': PIN['commit'], 'native_dependency_files': native_before,
                   'section17_code_sha256': before_code, 'as_of': as_of,
                   'artifact_snapshots': snapshots, 'measurements': results,
                   'metric_ids': list(METRICS), 'original_metric_roster_count': 17,
                   'coverage': 'ONLY_3_AV_METRICS_NOT_FULL_BENCHMARK',
                   'source_and_game_scope': 'BYTES_ONLY_NOT_LEARNING_OR_RUNTIME_VALIDATION',
                   'native_book_pipeline_executed': False, 'canonical_application_caller_adopted': False,
                   'independent_reviewed_benchmark': False,
                   'section_complete': False, 'release_authorized': False, 'product_accepted': False}
        raw = canonical_json(payload).encode('utf-8')
        sha = hashlib.sha256(raw).hexdigest()
        report_ref = ArtifactRef('qa17-av-benchmark', f'qa17-reports/{sha}.json', sha, len(raw), 'report')
        if report_ref.artifact_id in {a.artifact_id for a in candidate.artifacts} or any(
                p == report_ref.path or p.startswith('qa17-reports/') or p == 'qa17-reports' for p in paths):
            raise BenchmarkError('NATIVE_QA_REPORT_COLLISION')
        report_path = work / report_ref.path
        report_path.parent.mkdir()
        report_path.write_bytes(raw)
        envelope = GateEvidence('2.0.0', 'qa17-av-benchmark', 'benchmark', original_digest,
            policy.content_digest, candidate.run_id, candidate.revision, status,
            'bie-eval-native-qa-slice', '1.0.0', 'review',
            tuple(sorted(a.artifact_id for a in candidate.artifacts)), report_ref,
            as_of, as_of + min(3600, policy.max_evidence_lifetime_seconds),
            ('UNSIGNED_SECTION17_EVIDENCE', 'PARTIAL_AV_BENCHMARK_COVERAGE', 'FULL_BENCHMARK_ACCEPTANCE_OPEN'),
            'UNSIGNED', '')
        # Actual pinned canonical evaluator, with its deny-by-default verifier.
        qa = ReleaseEvaluator(policy=policy).evaluate(
            EvidenceBundle('2.0.0', candidate, (envelope,)), work, as_of=as_of)
        if qa.release_status != 'BLOCKED' or qa.release_authorized or qa.product_accepted:
            raise BenchmarkError('NATIVE_QA_UNEXPECTED_RELEASE_PROMOTION')
        if metrics_code_digest() != before_code or verify_native_runtime() != native_before:
            raise BenchmarkError('NATIVE_QA_CODE_CHANGED_DURING_RUN')
        if candidate.content_digest != original_digest:
            raise BenchmarkError('NATIVE_QA_CANDIDATE_CHANGED_DURING_RUN')
        return {'schema_version': VERSION, 'measurement_outcomes': dict(zip(METRICS, outcomes)),
                'envelope': envelope.to_dict(), 'report_json': raw.decode('utf-8'),
                'report_sha256': sha, 'native_qa_report': json.loads(qa.to_bytes()),
                'native_component_consumer_executed': True,
                'canonical_application_caller_adopted': False,
                'release_authorized': False, 'product_accepted': False}


def metrics_code_digest():
    from ..release.deterministic import service_code_sha256
    return service_code_sha256()
