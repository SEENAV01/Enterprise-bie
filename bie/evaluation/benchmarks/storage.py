"""Single-owner SQLite helpers, Python 3.11+ API compatible.

Symlink preflight is not a race-proof filesystem sandbox. Use a directory owned
by the evaluator service. URI filenames are not accepted. In-memory use is explicit.
"""
from pathlib import Path
import os
import sqlite3
from .models import BenchmarkError


def database_path(value, *, allow_memory=False):
    if not isinstance(value, (str, os.PathLike)):
        raise BenchmarkError('INVALID_DATABASE_PATH')
    raw = os.fspath(value)
    if type(raw) is not str or not raw or '\x00' in raw:
        raise BenchmarkError('INVALID_DATABASE_PATH')
    if raw == ':memory:':
        if allow_memory:
            return raw
        raise BenchmarkError('MEMORY_DATABASE_NOT_DURABLE')
    if raw.startswith('file:'):
        raise BenchmarkError('DATABASE_URI_REFUSED')
    p = Path(raw).absolute()
    # Inspect the lexical path before resolving it; resolve() can hide symlinks.
    if '..' in p.parts:
        raise BenchmarkError('DATABASE_PARENT_TRAVERSAL_REFUSED')
    for node in (p, *p.parents):
        if node.is_symlink():
            raise BenchmarkError('DATABASE_SYMLINK_REFUSED')
    if not p.parent.is_dir() or (p.exists() and not p.is_file()):
        raise BenchmarkError('INVALID_DATABASE_PATH')
    return str(p)


def connect_manual(value, *, allow_memory=False, timeout=10):
    path = database_path(value, allow_memory=allow_memory)
    kwargs = {'timeout': timeout, 'isolation_level': None}
    # autocommit was introduced in Python 3.12. Do not access it on 3.11.
    if hasattr(sqlite3, 'LEGACY_TRANSACTION_CONTROL'):
        kwargs['autocommit'] = sqlite3.LEGACY_TRANSACTION_CONTROL
    return sqlite3.connect(path, **kwargs)
