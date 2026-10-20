"""Task 037C test helper: temporary roots reproduce the state the amendment chain authenticates.

The compiler amendment chain authenticates the exact baseline copies kept in
``docs/evidence/source-baseline-037c/``; the live working files may evolve. Tests that copy
working files into a temporary root and then tamper with them call ``overlay_baseline`` after
copying, so the temporary root starts from the authenticated bytes and every tamper control
keeps its original meaning.
"""
from pathlib import Path

BASELINE_DIR = 'docs/evidence/source-baseline-037c/'


def overlay_baseline(repo_root, temp_root):
    """Overwrite each copied working file that has a baseline copy with the baseline bytes."""
    base = Path(repo_root) / BASELINE_DIR
    replaced = []
    for source in sorted(base.rglob('*')):
        relative = source.relative_to(base).as_posix()
        if not source.is_file() or relative in ('BASELINE.json', '.gitattributes'):
            continue
        target = Path(temp_root) / relative
        if target.is_file():
            target.write_bytes(source.read_bytes())
            replaced.append(relative)
    return replaced
