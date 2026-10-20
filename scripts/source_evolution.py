"""Task 037C: working source may evolve; evidence stays byte-exact.

The adoption ledgers (``manifests/lossless_migration.csv``, the ``*_integration_*.json``
manifests, the Section 17 adoption map and the reviewed amendments) recorded the hash of every
file at the moment it entered this repository. They prove that the migration and each adoption
lost nothing, and they keep doing so: every original archive member and every recorded
before-image is still checked byte for byte.

What they must not do is freeze the product's working code forever. Under this policy a ledger
check on a working-source path accepts the current file when its bytes differ from the recorded
hash; the verifier reports it as *evolved since adoption* instead of failing. Working source is
changed only through reviewed pull requests whose tests and CI gates pass; git history keeps
every earlier version.

Evidence never evolves: every ledger-recorded file outside the working prefixes (``batches/``,
``historical/``, ``backups/``, recorded ``docs/`` evidence and before-images, ``manifests/``,
``metadata/``) stays byte-exact. A working-source file that disappears is still an error, so a
deletion is a deliberate, visible change to the ledger checks.
"""
from __future__ import annotations

from pathlib import PurePosixPath

WORKING_SOURCE_PREFIXES = ('bie/', 'apps/', 'tests/', 'tools/', 'scripts/')
POLICY = 'bie.source-evolution/1'


def is_working_source(relative: str) -> bool:
    """True for a repository-relative POSIX path under the working-source prefixes."""
    if not isinstance(relative, str) or not relative or '\\' in relative:
        return False
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in ('', '.', '..') for part in path.parts):
        return False
    return relative.startswith(WORKING_SOURCE_PREFIXES)


def accepts(relative: str, expected: str, actual: str) -> bool:
    """A recorded hash check passes when the bytes match, or the path is working source."""
    return actual == expected or is_working_source(relative)


def report(evolved) -> dict:
    """Uniform receipt fragment for verifiers."""
    paths = sorted(set(evolved))
    return {'source_evolution_policy': POLICY, 'working_source_evolved_since_adoption': len(paths),
            'working_source_evolved_paths': paths[:200]}


BASELINE_DIR = 'docs/evidence/source-baseline-037c/'


def verify_baseline(root) -> list:
    """Errors if the 037C baseline copies differ from their manifest (empty list when exact)."""
    import hashlib
    import json
    from pathlib import Path
    base = Path(root) / BASELINE_DIR
    manifest_path = base / 'BASELINE.json'
    if not manifest_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        expected = {row['path']: (row['bytes'], row['sha256']) for row in manifest['files']}
    except (OSError, ValueError, KeyError, TypeError):
        return ['SOURCE_BASELINE_MANIFEST_INVALID']
    errors = []
    actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()} - {'BASELINE.json', '.gitattributes'}
    if actual != set(expected):
        errors.append('SOURCE_BASELINE_INVENTORY_MISMATCH')
    for relative, (size, digest) in sorted(expected.items()):
        target = base / relative
        if not is_working_source(relative) or target.is_symlink() or not target.is_file():
            errors.append('SOURCE_BASELINE_FILE_INVALID:' + relative)
            continue
        data = target.read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            errors.append('SOURCE_BASELINE_BYTES:' + relative)
    return errors
