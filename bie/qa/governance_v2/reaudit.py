"""HARD039: complete local evidence crosswalk, not an operational exit authority.

Input identities are compared against the existing independent catalog. The CLI
first revalidates the index against actual current files and executed tests.
Historical open obligations cannot be erased, or closed merely by changing JSON.
"""
from __future__ import annotations
from .catalog import ORIGINAL_TASK_IDS, HARDENING_TASK_IDS
from .index import load, reference, verify_index
from ..release_v2.contracts import ContractError


def _rows(value, field, expected, key):
    rows = value.get(field)
    if type(rows) is not list or any(type(r) is not dict for r in rows):
        raise ContractError('REAUDIT_ROWS', field)
    ids = [r.get(key) for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ContractError('REAUDIT_CENSUS', field)
    return rows


def scope_crosswalk(index, catalog, registry, matrices):
    originals = _rows(index, 'original_tasks', ORIGINAL_TASK_IDS, 'task_id')
    tasks = _rows(index, 'hardening_tasks', HARDENING_TASK_IDS, 'task_id')
    expected = catalog.get('obligations')
    if type(expected) is not list or not expected:
        raise ContractError('REAUDIT_CATALOG')
    expected_ids = [r['obligation_id'] for r in expected]
    if len(expected_ids) != len(set(expected_ids)):
        raise ContractError('REAUDIT_CATALOG_DUPLICATE')
    obligations = _rows(registry, 'records', expected_ids, 'obligation_id')
    baseline = {r['obligation_id']: r for r in expected}
    for row in obligations:
        base = baseline[row['obligation_id']]
        if row['definition_digest'] != base['definition_digest'] or row['definition'] != base['definition']:
            raise ContractError('REAUDIT_OBLIGATION_REDEFINED')
        if row.get('current_closure_status') != 'UNVERIFIED_OPEN_PENDING_SCOPE_EVIDENCE' or row.get('closure_evidence') is not None:
            raise ContractError('REAUDIT_CLOSURE_AUTHORITY_REQUIRED')
    # Retain exact task-specific remaining scope; never equate a local test pass
    # with native execution, calibration, operational services or legal clearance.
    closure_by_task = {}
    for matrix in matrices:
        schema = matrix.get('schema_version')
        if schema not in {'bie.qa.h%d-closure-matrix/1' % n for n in range(3,9)}:
            raise ContractError('REAUDIT_CLOSURE_SCHEMA')
        for original_row in matrix.get('tasks', []):
            # H3 predates the explicit remaining/closed-history fields. Its
            # registered schema uses `open`; preserve that original, not a
            # status-only fallback for unknown formats.
            row = dict(original_row)
            if schema == 'bie.qa.h3-closure-matrix/1':
                row['remaining'] = row.pop('open', None)
                row['closed_historical_obligations'] = original_row.get('closed_historical_obligations', [])
            task = row['task_id']
            if task not in HARDENING_TASK_IDS or task in closure_by_task:
                raise ContractError('REAUDIT_CLOSURE_TASK_CENSUS')
            if row.get('full_scope_closed') is not False or row.get('closed_historical_obligations') != []:
                raise ContractError('REAUDIT_UNVERIFIED_CLOSURE')
            if type(row.get('remaining')) is not list or not row['remaining']:
                raise ContractError('REAUDIT_REMAINING_SCOPE_MISSING')
            closure_by_task[task] = row
    required_matrices = set(HARDENING_TASK_IDS) - {
        'BIE-QA-HARD-001', 'BIE-QA-HARD-002', 'BIE-QA-HARD-003',
        'BIE-QA-HARD-004', 'BIE-QA-HARD-005', 'BIE-QA-HARD-006',
        'BIE-QA-HARD-039', 'BIE-QA-HARD-040'}
    if set(closure_by_task) != required_matrices:
        raise ContractError('REAUDIT_CLOSURE_MATRIX_MISSING')
    task_rows = []
    for row in tasks:
        tid = row['task_id']; closure = closure_by_task.get(tid)
        task_rows.append(dict(task_id=tid, implementation=row['status'],
            historical_obligation_ids=sorted(o['obligation_id'] for o in obligations if tid in o['hardening_task_ids']),
            operational_scope_closed=False,
            remaining_scope=closure['remaining'] if closure else [
                'Re-audit and native/canonical adoption must establish exact required scope; local metadata is not closure evidence.'],
            closure_matrix=closure))
    return dict(schema_version='bie.qa.reaudit-crosswalk/1',
        original_tasks=originals, hardening_tasks=task_rows,
        obligations=obligations, original_count=len(originals),
        hardening_count=len(tasks), historical_obligation_count=len(obligations),
        historical_obligations_closed=0, decision='BLOCKED',
        audit_scope='COMPLETE_METADATA_AND_EVIDENCE_CENSUS_PLUS_FOCUSED_EXECUTED_PROBES',
        exhaustive_code_or_security_audit=False, full_section_complete=False,
        canonical_integration_authorized=False, product_accepted=False)


def inspect_workspace(root, blueprint, *, receipt_path, suite_specs):
    index = load(root, 'metadata/section16/TASK_INTEGRATION_INDEX.json')
    checked = verify_index(root, index, blueprint, receipt_path=receipt_path, suite_specs=suite_specs)
    paths = ['hardening/section16_h%d/CLOSURE_MATRIX.json' % n for n in range(3, 9)]
    result = scope_crosswalk(index, load(root,'metadata/section16/BASELINE_CATALOG.json'),
        load(root,'metadata/section16/OBLIGATION_REGISTRY.json'), [load(root,p) for p in paths])
    result['verified_index'] = checked
    result['inspected_closure_matrices'] = [reference(root,p) for p in paths]
    return result
