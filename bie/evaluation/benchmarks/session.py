"""REG-004 trusted-operator structured submission bridge.

Accept data, not candidate-supplied scores or executable code. This does not
attest that the file came from BIE. The operator must bind actual code/run
identity separately before downstream native/production use.
"""
from __future__ import annotations
from .models import BenchmarkError, canonical_json, digest, exact_fields, ident, strict_loads
from .versioning import Snapshot
from .anti_gaming import AttemptLedger
from .runner import grade_case


def grade_submission(ledger: AttemptLedger, run_id: str, snapshot: Snapshot,
                     answers: list[dict]) -> dict:
    """Grade against the frozen snapshot and finalize exactly once.

    Missing cases count as failures. Invalid envelopes/duplicate IDs raise;
    they do not erase the already consumed attempt. Numeric/content failures
    are recorded in the report, not converted into an overall success.
    """
    row = ledger._row(run_id)
    if row['state'] != 'OPEN':
        raise BenchmarkError('RUN_ALREADY_CLOSED')
    binding = strict_loads(row['binding_json'])
    if binding['dataset_sha256'] != snapshot.sha256:
        raise BenchmarkError('SUBMISSION_DATASET_MISMATCH')
    if type(answers) is not list or len(answers) > len(snapshot.cases):
        raise BenchmarkError('INVALID_ANSWER_COLLECTION')
    canonical_json(answers)
    roster = set(strict_loads(row['roster_json']))
    by_case = {c.case_id: c for c in snapshot.cases if c.case_id in roster}
    seen: set[str] = set()
    grades: list[dict] = []
    for answer in answers:
        exact_fields(answer, {'case_id', 'output'})
        case_id = ident(answer['case_id'])
        if case_id in seen:
            raise BenchmarkError('DUPLICATE_ANSWER')
        if case_id not in by_case:
            raise BenchmarkError('UNEXPECTED_CASE_RESULT')
        seen.add(case_id)
        grades.append(grade_case(by_case[case_id], answer['output']))
    rows = [{'case_id': g['case_id'], 'status': g['status'], 'evidence_sha256': digest(g)} for g in grades]
    report = ledger.finalize(run_id, rows)
    return {'schema_version': '1.0.0', 'submission_sha256': digest(answers),
            'scope': 'EXTERNAL_STRUCTURED_OUTPUTS_NOT_NATIVE_ATTESTATION',
            'report': report, 'case_grades': grades, 'report_sha256': digest(report),
            'native_bie_execution_verified': False, 'golden_benchmark_certified': False,
            'release_authorized': False, 'product_accepted': False}
