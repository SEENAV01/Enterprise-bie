"""Verify the complete Batch-01 recovery against its immutable original archive."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import zipfile

ARCHIVE_SHA256 = '2cc616bab6634e2a325c1141d607c3ee9235cb17a35310c16f806b35f7c8c814'
ARCHIVE_PREFIX = 'BIE_GAME_SECTION15_BATCH01_DSL_CORE_STUDIO_ENTERPRISE/'

# H7_AMENDMENT_PINS_BEGIN
AMENDMENTS = {'bie/game_engine/codec.py': '30e01b556594aec8f77471fa7bb2820076aea1452b85e4b1c2d580b2d8de73d9', 'bie/game_engine/expressions.py': '824ef1377dd80ae9c9d4b098633c309bbad5bec5610322c9bb7aa7b030c6ccbd'}
# H7_AMENDMENT_PINS_END

class TraceabilityError(ValueError):
    pass

def confined(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise TraceabilityError('UNSAFE_PATH')
    rel = PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise TraceabilityError('UNSAFE_PATH')
    target = root.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise TraceabilityError('PATH_ESCAPE')
    return target

def destination(member):
    if not member.startswith(ARCHIVE_PREFIX):
        raise TraceabilityError('ARCHIVE_PREFIX')
    rel = member[len(ARCHIVE_PREFIX):]
    if rel == 'bie/__init__.py':
        return 'docs/evidence/game-section15/checkpoint/bie/__init__.py', 'preserved_original_package_initializer_canonical_package_retained'
    if rel.startswith('bie/'):
        if rel in AMENDMENTS:
            return rel, 'h7_amended_active_source_original_archive_preserved'
        return rel, 'existing_active_source_byte_identical'
    if rel.startswith('tests/'):
        return 'tests/dsl_core/' + rel[6:], 'restored_active_test_byte_identical'
    return 'lineage/batch01/' + rel, 'preserved_historical_document_or_evidence'

def verify(root):
    root = Path(root).resolve()
    ledger = json.loads((root / 'DSL_TRACEABILITY.json').read_text(encoding='utf-8'))
    if (ledger.get('task_id'), ledger.get('audit_id'), ledger.get('product_accepted')) != (
            'BIE-GAME-DSL-001', 'GAME-AUD-022', False):
        raise TraceabilityError('TASK_IDENTITY')
    if ledger.get('archive_path') != 'lineage/batch01/original.zip':
        raise TraceabilityError('ARCHIVE_LOCATION')
    archive = confined(root, ledger['archive_path'])
    if ledger.get('archive_sha256') != ARCHIVE_SHA256 or hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise TraceabilityError('ARCHIVE_HASH')
    with zipfile.ZipFile(archive) as z:
        members = [x.filename for x in z.infolist() if not x.is_dir()]
        rows = ledger['records']
        names = [r['archive_member'] for r in rows]
        if len(names) != len(set(names)) or set(names) != set(members):
            raise TraceabilityError('ARCHIVE_COVERAGE')
        targets = set()
        for row in rows:
            expected, disposition = destination(row['archive_member'])
            if row['target'] != expected or row['disposition'] != disposition:
                raise TraceabilityError('DISPOSITION_MISMATCH')
            if expected in targets:
                raise TraceabilityError('DUPLICATE_TARGET')
            targets.add(expected)
            original = z.read(row['archive_member'])
            digest = hashlib.sha256(original).hexdigest()
            if row['sha256'] != digest or row['size_bytes'] != len(original):
                raise TraceabilityError('RECORD_HASH')
            target = confined(root, expected)
            if expected in AMENDMENTS:
                if row.get('active_sha256') != AMENDMENTS[expected]:
                    raise TraceabilityError('ACTIVE_AMENDMENT_HASH')
                if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != AMENDMENTS[expected]:
                    raise TraceabilityError('RECOVERED_BYTES_MISMATCH:' + expected)
            elif not target.is_file() or target.read_bytes() != original:
                raise TraceabilityError('RECOVERED_BYTES_MISMATCH:' + expected)
        discovered = {'tests/dsl_core/' + p.name for p in (root / 'tests/dsl_core').glob('test_*.py')}
        expected_tests = {x for x in targets if x.startswith('tests/dsl_core/test_')}
        if discovered != expected_tests or len(discovered) != 11:
            raise TraceabilityError('TEST_DISCOVERY_COVERAGE')
    return {'audit_id': 'GAME-AUD-022', 'records_verified': len(rows),
            'test_modules_verified': len(discovered), 'archive_sha256': ARCHIVE_SHA256,
            'traceability_passed': True, 'tests_executed_by_this_check': 0, 'product_accepted': False}

if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]), indent=2))
